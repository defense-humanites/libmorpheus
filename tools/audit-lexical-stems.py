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


STEM_TAGS = (":no:", ":aj:", ":wd:", ":vs:", ":de:", ":vb:")


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


def compare(candidate, baseline):
    produced, produced_meta = read_stems(candidate)
    reference, reference_meta = read_stems(baseline)
    common = produced.keys() & reference.keys()
    outcomes = Counter()
    candidate_excess = Counter()
    reference_excess = Counter()
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
        else:
            outcomes["partial_overlap"] += 1
    for name in ("exact", "candidate_without_stems", "reference_without_stems",
                 "disjoint_stems", "partial_overlap"):
        outcomes[name] += 0
    return {"schema": 2,
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--baseline", required=True, type=Path)
    args = parser.parse_args()
    if args.candidate.resolve() == args.baseline.resolve():
        parser.error("candidate and baseline must be different files")
    print(json.dumps(compare(args.candidate, args.baseline), sort_keys=True))


if __name__ == "__main__":
    main()
