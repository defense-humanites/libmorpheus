#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare staged colon-tagged stem records with a curated witness.

Print counts and digests only. The input files may contain lexicon-derived data
and must remain outside release archives and published CI artifacts.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re


STEM_TAGS = (":no:", ":aj:", ":wd:", ":vs:", ":de:", ":vb:")
GREEK_DIACRITICS = r"\/=()+|'_^"


def stem_signature(line, removed="", retain_stem=True):
    """Keep the stem tag and morphology labels byte-for-byte for a diagnostic."""
    payload = line[4:]
    stem = re.match(r"\S*", payload).group()
    labels = payload[len(stem):]
    if retain_stem:
        stem = stem.translate(str.maketrans("", "", removed))
    else:
        stem = ""
    return line[:4] + stem + labels


def diagnostic_group(group, removed="", retain_stem=True):
    transformed = Counter()
    for line, count in group.items():
        transformed[stem_signature(line, removed, retain_stem)] += count
    return transformed


def quantity_marks(group):
    counts = Counter()
    for line, multiplicity in group.items():
        stem = re.match(r"\S*", line[4:]).group()
        for mark in "^_":
            counts[mark] += stem.count(mark) * multiplicity
    return counts


def spelling_difference(left, right):
    """Classify unmatched multisets without treating normalized stems as equal."""
    if not left:
        return "reference_extra_only"
    if not right:
        return "candidate_extra_only"
    if diagnostic_group(left, "^_") == diagnostic_group(right, "^_"):
        return "quantity_marks_only"
    if diagnostic_group(left, GREEK_DIACRITICS) == diagnostic_group(right, GREEK_DIACRITICS):
        return "beta_code_diacritics"
    if diagnostic_group(left, retain_stem=False) == diagnostic_group(right, retain_stem=False):
        return "same_tags_and_labels"
    if (set(diagnostic_group(left, retain_stem=False)) ==
            set(diagnostic_group(right, retain_stem=False))):
        return "same_labels_different_multiplicity"
    return "different_tags_or_labels"


def read_stems(path):
    groups = defaultdict(Counter)
    entries = 0
    orphan = 0
    unexpected = Counter()
    current = None
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for raw in source:
            digest.update(raw)
            line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
            if line.startswith(":le:"):
                current = line[4:].strip()
                if not current:
                    raise ValueError(f"empty lemma in {path}")
                groups[current]
                entries += 1
            elif line.startswith(STEM_TAGS):
                if current is None:
                    orphan += 1
                else:
                    groups[current][line] += 1
            elif line.startswith(":"):
                unexpected[line[:4]] += 1
    return groups, {"sha256": digest.hexdigest(), "lemma_markers": entries,
                    "unique_lemmas": len(groups), "orphan_stem_records": orphan,
                    "unexpected_colon_tags": dict(sorted(unexpected.items())),
                    "stem_records": sum(sum(group.values()) for group in groups.values())}


def compare(candidate, baseline, greek_spelling=False):
    produced, produced_meta = read_stems(candidate)
    reference, reference_meta = read_stems(baseline)
    common = produced.keys() & reference.keys()
    outcomes = Counter()
    candidate_excess = Counter()
    reference_excess = Counter()
    spelling = Counter()
    partial_spelling = Counter()
    partial_residual_tags = {"candidate": Counter(), "reference": Counter()}
    partial_residual_origin = {"candidate": Counter(), "reference": Counter()}
    quantity_presence = Counter()
    quantity_totals = Counter()
    intersecting = 0
    for key in common:
        left, right = produced[key], reference[key]
        shared = left & right
        intersecting += sum(shared.values())
        for line, count in (left - right).items():
            candidate_excess[line[:4]] += count
        for line, count in (right - left).items():
            reference_excess[line[:4]] += count
        if left == right:
            outcomes["exact"] += 1
        elif not left:
            outcomes["candidate_without_stems"] += 1
        elif not right:
            outcomes["reference_without_stems"] += 1
        elif not shared:
            outcomes["disjoint_stems"] += 1
            if greek_spelling:
                classification = spelling_difference(left, right)
                spelling[classification] += 1
                if classification == "quantity_marks_only":
                    left_marks, right_marks = quantity_marks(left), quantity_marks(right)
                    presence = ("both" if sum(left_marks.values()) and sum(right_marks.values()) else
                                "candidate_only" if sum(left_marks.values()) else
                                "reference_only" if sum(right_marks.values()) else "neither")
                    quantity_presence[presence] += 1
                    for mark, label in (("^", "short"), ("_", "long")):
                        quantity_totals[f"candidate_{label}"] += left_marks[mark]
                        quantity_totals[f"reference_{label}"] += right_marks[mark]
        else:
            outcomes["partial_overlap"] += 1
            if greek_spelling:
                partial_spelling[spelling_difference(left - right, right - left)] += 1
                for side, residual, other in (
                        ("candidate", left - right, right),
                        ("reference", right - left, left)):
                    for line, count in residual.items():
                        partial_residual_tags[side][line[:4]] += count
                        kind = "duplicate_shared_line" if line in other else "new_line"
                        partial_residual_origin[side][kind] += count
    for name in ("exact", "candidate_without_stems", "reference_without_stems",
                 "disjoint_stems", "partial_overlap"):
        outcomes[name] += 0
    report = {"schema": 5,
            "scope": "diagnostic; compare exact records, not analyzer behavior",
            "candidate": produced_meta, "reference": reference_meta,
            "common_lemmas": len(common),
            "equal_record_multisets_at_common_lemmas": outcomes["exact"],
            "exact_shared_stem_records_with_multiplicity": intersecting,
            "candidate_only_lemmas": len(produced.keys() - reference.keys()),
            "reference_only_lemmas": len(reference.keys() - produced.keys()),
            "shared_lemma_outcomes": dict(sorted(outcomes.items())),
            "unmatched_stem_records_at_shared_lemmas": {
                "candidate_by_tag": {tag: candidate_excess[tag] for tag in STEM_TAGS},
                "reference_by_tag": {tag: reference_excess[tag] for tag in STEM_TAGS},
            }}
    if greek_spelling:
        report["disjoint_greek_spelling_diagnostic"] = {
            name: spelling[name] for name in ("quantity_marks_only", "beta_code_diacritics",
                                            "same_tags_and_labels", "same_labels_different_multiplicity",
                                            "different_tags_or_labels")}
        report["partial_greek_residual_diagnostic"] = {
            name: partial_spelling[name] for name in
            ("candidate_extra_only", "reference_extra_only", "quantity_marks_only",
             "beta_code_diacritics", "same_tags_and_labels",
             "same_labels_different_multiplicity", "different_tags_or_labels")}
        report["partial_greek_residual_records"] = {
            side: {"by_tag": {tag: partial_residual_tags[side][tag] for tag in STEM_TAGS},
                   "duplicate_shared_line": partial_residual_origin[side]["duplicate_shared_line"],
                   "new_line": partial_residual_origin[side]["new_line"]}
            for side in ("candidate", "reference")}
        report["quantity_only_difference_direction"] = {
            "lemma_mark_presence": {name: quantity_presence[name] for name in
                                    ("candidate_only", "reference_only", "both", "neither")},
            "stem_mark_counts": {name: quantity_totals[name] for name in
                                 ("candidate_short", "candidate_long", "reference_short", "reference_long")},
        }
    return report


def compare_variants(candidate, alternate, baseline):
    original, original_meta = read_stems(candidate)
    variant, variant_meta = read_stems(alternate)
    reference, reference_meta = read_stems(baseline)
    compared = reference.keys() & (original.keys() | variant.keys())
    transitions = Counter()
    for key in compared:
        was_exact = key in original and original[key] == reference[key]
        now_exact = key in variant and variant[key] == reference[key]
        if was_exact and now_exact:
            transitions["both_exact"] += 1
        elif was_exact:
            transitions["original_only_exact"] += 1
        elif now_exact:
            transitions["alternate_only_exact"] += 1
        else:
            transitions["neither_exact"] += 1
    return {"schema": 1,
            "scope": "diagnostic exact-multiset transition; no lexical equivalence inferred",
            "input_sha256": {"original": original_meta["sha256"],
                             "alternate": variant_meta["sha256"],
                             "reference": reference_meta["sha256"]},
            "reference_lemmas_in_either_candidate": len(compared),
            "exact_transitions": {name: transitions[name] for name in
                                  ("both_exact", "original_only_exact",
                                   "alternate_only_exact", "neither_exact")}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--greek-spelling-diagnostic", action="store_true",
                        help="count spelling-only signatures at disjoint Greek lemmes; never equate them")
    parser.add_argument("--alternate-candidate", type=Path,
                        help="compare exact-match gains and losses for an isolated alternative")
    args = parser.parse_args()
    paths = [args.candidate, args.baseline]
    if args.alternate_candidate:
        paths.append(args.alternate_candidate)
    if len({path.resolve() for path in paths}) != len(paths):
        parser.error("candidate, alternate and baseline must be different files")
    if args.alternate_candidate and args.greek_spelling_diagnostic:
        parser.error("Greek spelling diagnostics cannot be combined with an alternate candidate")
    report = (compare_variants(args.candidate, args.alternate_candidate, args.baseline)
              if args.alternate_candidate else
              compare(args.candidate, args.baseline, args.greek_spelling_diagnostic))
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
