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


def audit(candidate, baseline, headers, split):
    produced, produced_meta = STEM_AUDIT["read_stems"](candidate)
    reference, reference_meta = STEM_AUDIT["read_stems"](baseline)
    source, source_digest = PARTIAL_AUDIT["source_headers"](headers)
    first_orth = defaultdict(list)
    all_orth = defaultdict(list)
    with headers.open(encoding="utf-8") as input_headers:
        for raw in input_headers:
            row = json.loads(raw)
            if row["projection_error"] is not None or not row.get("headword"):
                continue
            spelling = legacy_lemma_spelling(row["headword"])
            first_orth[spelling].append(row["fields"])
            for field in row["fields"]:
                if field["name"] == "orth":
                    token = field["projection"].split()[0].strip(",;:")
                    all_orth[legacy_lemma_spelling(token)].append(row["fields"])
    split_lemmas = Counter()
    split_digest = hashlib.sha256()
    with split.open("rb") as input_split:
        for line in input_split:
            split_digest.update(line)
            tokens = line.split(maxsplit=1)
            if tokens:
                split_lemmas[legacy_lemma_spelling(tokens[0].decode("utf-8", errors="replace"))] += 1
    candidate_markers, _ = PARTIAL_AUDIT["marker_locations"](candidate)
    reference_markers, _ = PARTIAL_AUDIT["marker_locations"](baseline)
    classes = defaultdict(Counter)
    tag_changes = Counter()
    for lemma in produced.keys() & reference.keys():
        left, right = produced[lemma], reference[lemma]
        if not left or not right or left & right:
            continue
        kind = STEM_AUDIT["spelling_difference"](left, right)
        if kind == "quantity_marks_only":
            continue
        report = classes[kind]
        report["lemma_groups"] += 1
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
        if kind == "different_tags_or_labels":
            candidate_tags = tuple(sorted({line[:4] for line in left}))
            reference_tags = tuple(sorted({line[:4] for line in right}))
            if candidate_tags == reference_tags:
                report["same_tag_set_different_labels"] += 1
            else:
                report["different_tag_sets"] += 1
                tag_changes[("+".join(candidate_tags), "+".join(reference_tags))] += 1
    keys = ("lemma_groups", "candidate_multiple_lemma_markers",
            "reference_multiple_lemma_markers", "projected_key_matches_zero",
            "projected_key_matches_one", "projected_key_matches_multiple",
            "projected_first_orth_matches_zero", "projected_first_orth_matches_one",
            "projected_first_orth_matches_multiple", "key_miss_first_orth_match",
            "any_orth_match", "split_token_match",
            "key_and_first_orth_miss_any_orth_match",
            "no_header_orth_but_split_token_match",
            "any_multiple_orth", "any_gen", "any_itype")
    return {"schema": 1, "scope": "aggregate triage; no normalized stem equivalence",
            "input_sha256": {"candidate": produced_meta["sha256"],
                             "reference": reference_meta["sha256"],
                             "headers": source_digest, "split": split_digest.hexdigest()},
            "non_quantity_disjoint": {
                name: {key: classes[name][key] for key in keys}
                for name in ("beta_code_diacritics", "same_tags_and_labels",
                             "same_labels_different_multiplicity", "different_tags_or_labels")},
            "different_tags_or_labels": {
                "same_tag_set_different_labels": classes["different_tags_or_labels"]["same_tag_set_different_labels"],
                "different_tag_sets": classes["different_tags_or_labels"]["different_tag_sets"],
                "tag_set_changes": [
                    {"candidate_tags": left, "reference_tags": right, "lemma_groups": count}
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
