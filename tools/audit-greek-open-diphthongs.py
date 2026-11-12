#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Locate bare LSJ quantity when other repeated letters close diphthongs.

This deliberately narrow positional diagnostic writes individual records only
to a private file. It does not infer a complete replacement stem record.
"""

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "greek_quantity_long", Path(__file__).with_name("arbitrate-greek-quantity-long.py"))
LONG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LONG)


def free_vowels(value, vowel):
    token = value.split()[0]
    positions = []
    letter_index = -1
    for i, char in enumerate(token):
        if not char.isascii() or not char.isalpha():
            continue
        letter_index += 1
        if char.lower() != vowel:
            continue
        preceding = token[i - 1].lower() if i else ""
        following = token[i + 1] if i + 1 < len(token) else ""
        # Mirror is_diphth in the Greek library: the second i/u of a
        # contiguous diphthong is excluded, except with diaeresis (+).
        diphthong = bool(preceding) and following != "+" and (
            (vowel == "i" and preceding in "aeou") or
            (vowel == "u" and preceding in "aeoh"))
        if not diphthong:
            positions.append(letter_index)
    return positions


def locate(row):
    if LONG.decision(row) != "manual_review" or len(row["sources"]) != 1:
        return None
    witness, marks = LONG.letters_and_longs(row["witness"].split()[0][4:])
    candidate, candidate_marks = LONG.letters_and_longs(row["candidate"].split()[0][4:])
    if witness != candidate or len(marks) != 1 or candidate_marks:
        return None
    marked, vowel = marks[0]
    source = row["sources"][0]
    headword, _ = LONG.letters_and_longs(source["headword"].split()[0])
    if not headword.startswith(witness) or headword.count(vowel) < 2:
        return None
    positions = free_vowels(source["headword"], vowel)
    if len(positions) != 1 or positions[0] >= len(witness) or not any(
            pron["direct"] and pron["text"] == f"[{vowel}_]"
            for pron in source["pron"]):
        return None
    return {"lemma": row["lemma"], "source_id": source["id"],
            "vowel": vowel, "witness_position": marked,
            "source_position": positions[0],
            "disposition": "retain_witness_position" if marked == positions[0]
                           else "different_witness_position"}


def audit(source, private_output=None):
    if private_output is not None:
        target = private_output.resolve()
        if target == REPO or REPO in target.parents or target == source.resolve():
            raise ValueError("private review must be outside the repository")
    digest = hashlib.sha256()
    output_digest = hashlib.sha256()
    counts = Counter()
    output = None
    try:
        if private_output is not None:
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            output = os.fdopen(os.open(target, flags, 0o600), "wb")
        with source.open("rb") as handle:
            for raw in handle:
                digest.update(raw)
                item = locate(json.loads(raw))
                if item is None:
                    continue
                counts[item["disposition"]] += 1
                if output is not None:
                    encoded = (json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n").encode()
                    output.write(encoded)
                    output_digest.update(encoded)
    finally:
        if output is not None:
            output.close()
    return {"schema": 1, "scope": "positional diphthong diagnostic only",
            "input_sha256": digest.hexdigest(), "counts": dict(sorted(counts.items())),
            "private_output_sha256": output_digest.hexdigest() if private_output else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-review", required=True, type=Path)
    parser.add_argument("--private-output", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.source_review, args.private_output), sort_keys=True))


if __name__ == "__main__":
    main()
