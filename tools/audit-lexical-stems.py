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


STEM_TAGS = (":no:", ":aj:", ":wd:")


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
    equal = sum(produced[key] == reference[key] for key in common)
    intersecting = sum(sum((produced[key] & reference[key]).values()) for key in common)
    return {"schema": 1,
            "scope": "diagnostic; compare exact records, not analyzer behavior",
            "candidate": produced_meta, "reference": reference_meta,
            "common_lemmas": len(common),
            "equal_record_multisets_at_common_lemmas": equal,
            "exact_shared_stem_records_with_multiplicity": intersecting,
            "candidate_only_lemmas": len(produced.keys() - reference.keys()),
            "reference_only_lemmas": len(reference.keys() - produced.keys())}


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
