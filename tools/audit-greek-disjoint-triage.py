#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Triage non-quantity Greek stem differences with aggregate counts only.

Inputs may contain lexicon-derived records. Never print lemma, stem, header
text or a per-entry digest; this report is not a stem equivalence decision.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import runpy


STEM_AUDIT = runpy.run_path(str(Path(__file__).with_name("audit-lexical-stems.py")))
PARTIAL_AUDIT = runpy.run_path(str(Path(__file__).with_name("audit-greek-partial-novelty.py")))


def legacy_lemma_spelling(value):
    """Mirror stripmetachars for a spelling probe, not an equivalence test."""
    spelling = value.translate(str.maketrans("", "", "^_-"))
    if spelling.endswith("*"):
        spelling = spelling[:-1]
    return spelling[:1] + spelling[1:].replace("r)r(", "rr")


def projected_surface(value):
    """Compare an orth token with the variant's first-token quantity trial."""
    return value.replace("-", "", 1).translate(str.maketrans("", "", "^_"))


def audit(candidate, baseline, headers, split):
    produced, produced_meta = STEM_AUDIT["read_stems"](candidate)
    reference, reference_meta = STEM_AUDIT["read_stems"](baseline)
    source, source_digest = PARTIAL_AUDIT["source_headers"](headers)
    first_orth = defaultdict(list)
    all_orth = defaultdict(list)
    later_orth_types = defaultdict(list)
    orth_surfaces = defaultdict(list)
    with headers.open(encoding="utf-8") as input_headers:
        for raw in input_headers:
            row = json.loads(raw)
            if row["projection_error"] is not None or not row.get("headword"):
                continue
            spelling = legacy_lemma_spelling(row["headword"])
            first_orth[spelling].append(row["fields"])
            orth_index = 0
            for field in row["fields"]:
                if field["name"] == "orth":
                    token = field["projection"].split()[0].strip(",;:")
                    normalized = legacy_lemma_spelling(token)
                    all_orth[normalized].append(row["fields"])
                    orth_surfaces[projected_surface(token)].append(row["fields"])
                    if orth_index > 0:
                        later_orth_types[normalized].append(field.get("type"))
                    orth_index += 1
    split_lemmas = Counter()
    split_surfaces = set()
    split_digest = hashlib.sha256()
    with split.open("rb") as input_split:
        for line in input_split:
            split_digest.update(line)
            tokens = line.split(maxsplit=1)
            if tokens:
                surface = tokens[0].decode("utf-8", errors="replace")
                split_surfaces.add(surface)
                split_lemmas[legacy_lemma_spelling(surface)] += 1
    candidate_markers, _ = PARTIAL_AUDIT["marker_locations"](candidate)
    reference_markers, _ = PARTIAL_AUDIT["marker_locations"](baseline)
    classes = defaultdict(Counter)
    tag_changes = Counter()
    label_changes = Counter()
    tag_change_fields = defaultdict(Counter)
    for lemma in produced.keys() & reference.keys():
        left, right = produced[lemma], reference[lemma]
        if not left or not right or left & right:
            continue
        kind = STEM_AUDIT["spelling_difference"](left, right)
        if kind == "quantity_marks_only":
            continue
        report = classes[kind]
        report["lemma_groups"] += 1
        for tag in {line[:4] for line in left}:
            report["candidate_tag_" + tag] += 1
        report["candidate_multiple_lemma_markers"] += candidate_markers[lemma] > 1
        report["reference_multiple_lemma_markers"] += reference_markers[lemma] > 1
        entries = source.get(lemma, [])
        report["projected_key_matches_" + ("zero" if not entries else
                                           "one" if len(entries) == 1 else "multiple")] += 1
        orth_count = len(first_orth[lemma])
        report["projected_first_orth_matches_" + ("zero" if not orth_count else
                                                  "one" if orth_count == 1 else "multiple")] += 1
        report["key_miss_first_orth_match"] += not entries and bool(orth_count)
        if not entries:
            entries = first_orth[lemma]
        report["any_orth_match"] += bool(all_orth[lemma])
        types = later_orth_types[lemma]
        report["later_orth_match"] += bool(types)
        report["later_orth_untyped"] += any(value is None for value in types)
        report["later_orth_type_alt"] += any(value == "alt" for value in types)
        report["later_orth_other_type"] += any(value not in (None, "alt") for value in types)
        report["split_token_match"] += bool(split_lemmas[lemma])
        report["key_and_first_orth_miss_any_orth_match"] += (
            not source.get(lemma) and not orth_count and bool(all_orth[lemma]))
        report["no_header_orth_but_split_token_match"] += (
            not source.get(lemma) and not all_orth[lemma] and bool(split_lemmas[lemma]))
        if not entries:
            entries = all_orth[lemma]
        report["any_multiple_orth"] += any(
            sum(field["name"] == "orth" for field in fields) > 1 for fields in entries)
        for tag in ("gen", "itype"):
            report["any_" + tag] += any(
                field["name"] == tag for fields in entries for field in fields)
        candidate_adverbs = [line[4:].split()[0] for line in left if line.startswith(":wd:")]
        if candidate_adverbs:
            report["candidate_adverb_groups"] += 1
            report["adverb_stems_all_in_split"] += all(
                stem in split_surfaces for stem in candidate_adverbs)
            matching_headers = [fields for stem in candidate_adverbs
                                for fields in orth_surfaces[stem]]
            report["adverb_stem_header_orth_match"] += bool(matching_headers)
            report["adverb_stem_header_adv_pos"] += any(
                field["name"] == "pos" and field["projection"] == "Adv."
                for fields in matching_headers for field in fields)
            reference_adverbs = [line[4:].split()[0] for line in right if line.startswith(":wd:")]
            report["reference_adverb_header_orth_match"] += any(
                orth_surfaces[stem] for stem in reference_adverbs)
        if kind == "different_tags_or_labels":
            candidate_tags = tuple(sorted({line[:4] for line in left}))
            reference_tags = tuple(sorted({line[:4] for line in right}))
            if candidate_tags == reference_tags:
                report["same_tag_set_different_labels"] += 1
                label_changes["+".join(candidate_tags)] += 1
            else:
                report["different_tag_sets"] += 1
                pair = ("+".join(candidate_tags), "+".join(reference_tags))
                tag_changes[pair] += 1
                fields = tag_change_fields[pair]
                for name in ("gen", "itype"):
                    fields["any_" + name] += any(
                        field["name"] == name for record in entries for field in record)
                fields["any_adv_pos"] += any(
                    field["name"] == "pos" and field["projection"] == "Adv."
                    for record in entries for field in record)
    keys = ("lemma_groups", "candidate_multiple_lemma_markers",
            "reference_multiple_lemma_markers", "projected_key_matches_zero",
            "projected_key_matches_one", "projected_key_matches_multiple",
            "projected_first_orth_matches_zero", "projected_first_orth_matches_one",
            "projected_first_orth_matches_multiple", "key_miss_first_orth_match",
            "any_orth_match", "split_token_match",
            "key_and_first_orth_miss_any_orth_match",
            "no_header_orth_but_split_token_match",
            "later_orth_match", "later_orth_untyped",
            "later_orth_type_alt", "later_orth_other_type",
            "candidate_adverb_groups", "adverb_stems_all_in_split",
            "adverb_stem_header_orth_match", "adverb_stem_header_adv_pos",
            "reference_adverb_header_orth_match",
            "any_multiple_orth", "any_gen", "any_itype")
    return {"schema": 1, "scope": "aggregate triage; no normalized stem equivalence",
            "input_sha256": {"candidate": produced_meta["sha256"],
                             "reference": reference_meta["sha256"],
                             "headers": source_digest, "split": split_digest.hexdigest()},
            "non_quantity_disjoint": {
                name: {**{key: classes[name][key] for key in keys},
                       "candidate_tags": {tag: classes[name]["candidate_tag_" + tag]
                                          for tag in STEM_AUDIT["STEM_TAGS"]}}
                for name in ("beta_code_diacritics", "same_tags_and_labels",
                             "same_labels_different_multiplicity", "different_tags_or_labels")},
            "different_tags_or_labels": {
                "same_tag_set_different_labels": classes["different_tags_or_labels"]["same_tag_set_different_labels"],
                "different_tag_sets": classes["different_tags_or_labels"]["different_tag_sets"],
                "label_changes_by_tag": [
                    {"tags": tags, "lemma_groups": count}
                    for tags, count in sorted(label_changes.items())],
                "tag_set_changes": [
                    {"candidate_tags": left, "reference_tags": right, "lemma_groups": count,
                     "any_gen": tag_change_fields[(left, right)]["any_gen"],
                     "any_itype": tag_change_fields[(left, right)]["any_itype"],
                     "any_adv_pos": tag_change_fields[(left, right)]["any_adv_pos"]}
                    for (left, right), count in sorted(tag_changes.items())]}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--headers", type=Path, required=True)
    parser.add_argument("--split", type=Path, required=True)
    args = parser.parse_args()
    if len({path.resolve() for path in vars(args).values()}) != 4:
        parser.error("all four inputs must be different files")
    print(json.dumps(audit(args.candidate, args.baseline, args.headers, args.split), sort_keys=True))


if __name__ == "__main__":
    main()
