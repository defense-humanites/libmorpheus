#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Select unambiguous source-backed Greek long marks for private review.

The input and optional ledger contain lexicon-derived records. Only counts
and digests are printed. This does not rewrite a stemlib or judge paradigms.
"""

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def letters_and_longs(value):
    letters = []
    longs = []
    for character in value:
        if character.isascii() and character.isalpha():
            letters.append(character.lower())
        elif character == "_" and letters:
            longs.append((len(letters) - 1, letters[-1]))
    return "".join(letters), longs


def decision(row):
    candidate, candidate_longs = letters_and_longs(row["candidate"].split()[0][4:])
    witness, witness_longs = letters_and_longs(row["witness"].split()[0][4:])
    if candidate != witness:
        raise ValueError("candidate and witness stem spellings differ beyond quantity")
    if candidate_longs or len(witness_longs) != 1:
        return "manual_review"
    if len(row["sources"]) != 1:
        return "manual_review"
    source = row["sources"][0]
    headword, _ = letters_and_longs(source["headword"].split()[0])
    position, vowel = witness_longs[0]
    if (not headword.startswith(witness) or position >= len(headword) or
            headword.count(vowel) != 1):
        return "manual_review"
    if not any(pron["direct"] and pron["text"] == f"[{vowel}_]"
               for pron in source["pron"]):
        return "manual_review"
    return "retain_witness_long_from_unique_direct_pron"


def arbitrate(source, private_output=None):
    if private_output is not None:
        target = private_output.resolve()
        if target == REPO or REPO in target.parents or target == source.resolve():
            raise ValueError("private ledger must be outside the repository and differ from input")
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
                row = json.loads(raw)
                disposition = decision(row)
                counts[disposition] += 1
                if output is not None:
                    result = (json.dumps({"lemma": row["lemma"], "disposition": disposition,
                                          "source_ids": [s["id"] for s in row["sources"]]},
                                         sort_keys=True, ensure_ascii=False) + "\n").encode()
                    output.write(result)
                    output_digest.update(result)
    finally:
        if output is not None:
            output.close()
    return {"schema": 1, "scope": "source quantity notation only; no paradigm decision",
            "input_sha256": digest.hexdigest(), "by_disposition": dict(sorted(counts.items())),
            "private_output_sha256": output_digest.hexdigest() if private_output else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-review", required=True, type=Path)
    parser.add_argument("--private-output", type=Path)
    args = parser.parse_args()
    print(json.dumps(arbitrate(args.source_review, args.private_output), sort_keys=True))


if __name__ == "__main__":
    main()
