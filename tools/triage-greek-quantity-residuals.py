#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Triage exact Greek quantity residuals without publishing lexical records."""

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import runpy


REPO = Path(__file__).resolve().parents[1]
STEMS = runpy.run_path(str(Path(__file__).with_name("audit-lexical-stems.py")))


def marks(line):
    token = line.split(maxsplit=1)[0]
    if token[:4] not in STEMS["STEM_TAGS"]:
        raise ValueError("unexpected stem record tag")
    position = 0
    found = []
    for character in token[4:]:
        if character in "^_":
            found.append((position - 1, character))
        else:
            position += 1
    return found


def category(candidate, witness):
    left, right = marks(candidate), marks(witness)
    if not left:
        return "candidate_unmarked"
    if not right:
        return "witness_unmarked"
    left_positions = {position for position, _ in left}
    right_positions = {position for position, _ in right}
    if left_positions == right_positions:
        return "same_positions_different_marks_or_multiplicity"
    if left_positions & right_positions:
        return "overlapping_positions"
    return "different_positions"


def triage(candidate, witness, private_output=None):
    if private_output is not None:
        target = private_output.resolve()
        if target == REPO or REPO in target.parents or target in {candidate.resolve(), witness.resolve()}:
            raise ValueError("private review must differ from inputs and be outside the repository")
    left, left_meta = STEMS["read_stems"](candidate)
    right, right_meta = STEMS["read_stems"](witness)
    counts = Counter()
    by_tag = Counter()
    written = hashlib.sha256()
    output = None
    try:
        if private_output is not None:
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            output = os.fdopen(os.open(target, flags, 0o600), "wb")
        for lemma in sorted(left.keys() & right.keys()):
            produced, reference = left[lemma], right[lemma]
            if (not produced or not reference or produced & reference or
                    STEMS["spelling_difference"](produced, reference) != "quantity_marks_only"):
                continue
            if sum(produced.values()) != 1 or sum(reference.values()) != 1:
                counts["multiple_records_needing_review"] += 1
                continue
            one = next(iter(produced))
            other = next(iter(reference))
            kind = category(one, other)
            counts[kind] += 1
            by_tag[one[:4]] += 1
            if output is not None:
                raw = (json.dumps({"lemma": lemma, "category": kind,
                                   "candidate": one, "witness": other},
                                  ensure_ascii=False, sort_keys=True) + "\n").encode()
                output.write(raw)
                written.update(raw)
    finally:
        if output is not None:
            output.close()
    return {"schema": 1, "scope": "quantity marks in stem tokens only",
            "input_sha256": {"candidate": left_meta["sha256"],
                             "witness": right_meta["sha256"]},
            "by_category": dict(sorted(counts.items())),
            "by_candidate_tag": dict(sorted(by_tag.items())),
            "private_output_sha256": written.hexdigest() if private_output else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--witness", required=True, type=Path)
    parser.add_argument("--private-output", type=Path)
    args = parser.parse_args()
    print(json.dumps(triage(args.candidate, args.witness, args.private_output), sort_keys=True))


if __name__ == "__main__":
    main()
