#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Triage non-quantity Greek stem differences with aggregate counts only.

Inputs may contain lexicon-derived records. Never print lemma, stem, header
text or a per-entry digest; this report is not a stem equivalence decision.
"""

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import runpy


STEM_AUDIT = runpy.run_path(str(Path(__file__).with_name("audit-lexical-stems.py")))
PARTIAL_AUDIT = runpy.run_path(str(Path(__file__).with_name("audit-greek-partial-novelty.py")))


def audit(candidate, baseline, headers):
    produced, produced_meta = STEM_AUDIT["read_stems"](candidate)
    reference, reference_meta = STEM_AUDIT["read_stems"](baseline)
    source, source_digest = PARTIAL_AUDIT["source_headers"](headers)
    first_orth = defaultdict(list)
    with headers.open(encoding="utf-8") as input_headers:
        for raw in input_headers:
            row = json.loads(raw)
            if row["projection_error"] is not None or not row.get("headword"):
                continue
            spelling = row["headword"].translate(str.maketrans("", "", "^_-"))
            if spelling.endswith("*"):
                spelling = spelling[:-1]
            # Equivalent to zap_rr_breath after the first character, for
            # this specific Beta Code sequence in the legacy stripmeta.c.
            spelling = spelling[:1] + spelling[1:].replace("r)r(", "rr")
            first_orth[spelling].append(row["fields"])
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
            "any_multiple_orth", "any_gen", "any_itype")
    return {"schema": 1, "scope": "aggregate triage; no normalized stem equivalence",
            "input_sha256": {"candidate": produced_meta["sha256"],
                             "reference": reference_meta["sha256"],
                             "headers": source_digest},
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
    args = parser.parse_args()
    if len({path.resolve() for path in vars(args).values()}) != 3:
        parser.error("all three inputs must be different files")
    print(json.dumps(audit(args.candidate, args.baseline, args.headers), sort_keys=True))


if __name__ == "__main__":
    main()
