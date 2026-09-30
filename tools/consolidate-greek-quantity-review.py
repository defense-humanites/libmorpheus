#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Validate explicit private reviews against the Greek source-review queue.

This binds each individual judgment to an exact source-review row. It does
not infer new lexical decisions or edit stem records. Only aggregate counts
and hashes are printed; the consolidated ledger must remain private.
"""

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "quantity_arbitrator", REPO / "tools/arbitrate-greek-quantity-long.py")
arbitrator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(arbitrator)


def read_rows(path):
    rows = {}
    for raw in path.read_bytes().splitlines(keepends=True):
        row = json.loads(raw)
        lemma = row["lemma"]
        if lemma in rows:
            raise ValueError("duplicate lemma in input")
        rows[lemma] = (row, hashlib.sha256(raw).hexdigest())
    return rows


def validate(row, row_digest, review):
    if review.get("source_row_sha256") != row_digest:
        raise ValueError("review does not match exact source row")
    if review.get("source_ids") != [s["id"] for s in row["sources"]]:
        raise ValueError("review source IDs do not match")
    if not isinstance(review.get("evidence"), str) or not review["evidence"].strip():
        raise ValueError("review requires an explicit evidence note")
    position = review.get("long_position")
    if type(position) is not int:
        raise ValueError("long position must be an integer")
    candidate, candidate_longs = arbitrator.letters_and_longs(
        row["candidate"].split()[0][4:])
    witness, witness_longs = arbitrator.letters_and_longs(
        row["witness"].split()[0][4:])
    if candidate != witness or not 0 <= position < len(witness):
        raise ValueError("invalid stem spelling or position")
    if witness[position] not in "aiu":
        raise ValueError("long position must name a dichronon")
    disposition = review.get("disposition")
    mark = (position, witness[position])
    if disposition == "retain_witness_position":
        if witness_longs != [mark]:
            raise ValueError("retained position must equal the sole witness mark")
    elif disposition == "relocate_witness_long":
        if (len(witness_longs) != 1 or witness_longs[0] == mark or
                witness_longs[0][1] != mark[1]):
            raise ValueError("relocation must move one mark to another same-vowel position")
    elif disposition == "deduplicate_witness_long":
        if (len(witness_longs) < 2 or set(witness_longs) != {mark} or
                candidate_longs != [mark]):
            raise ValueError("deduplication must match the single candidate mark")
    else:
        raise ValueError("unsupported individual disposition")
    return disposition


def consolidate(source, reviews_path, private_output=None, expected=None):
    sources = read_rows(source)
    reviews = read_rows(reviews_path)
    if expected is not None and len(sources) != expected:
        raise ValueError("unexpected number of source rows")
    if set(reviews) - set(sources):
        raise ValueError("review lemma is absent from source queue")
    counts = Counter()
    output_rows = []
    for lemma, (row, row_digest) in sources.items():
        disposition = arbitrator.decision(row)
        result = {"lemma": lemma, "disposition": disposition,
                  "source_ids": [s["id"] for s in row["sources"]]}
        if lemma in reviews:
            if disposition != "manual_review":
                raise ValueError("individual review may only address the manual queue")
            review = reviews[lemma][0]
            disposition = validate(row, row_digest, review)
            result.update(disposition=disposition, long_position=review["long_position"],
                          evidence=review["evidence"], source_row_sha256=row_digest,
                          provisional=True,
                          position_resolved=disposition != "deduplicate_witness_long")
        counts[disposition] += 1
        output_rows.append(result)
    payload = b"".join((json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n").encode()
                       for row in output_rows)
    if private_output is not None:
        target = private_output.resolve()
        if target == REPO or REPO in target.parents or target in {
                source.resolve(), reviews_path.resolve()}:
            raise ValueError("private ledger must be outside repository and inputs")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        with os.fdopen(os.open(target, flags, 0o600), "wb") as output:
            output.write(payload)
    return {"schema": 1, "scope": "explicit provisional review; no stem replacement",
            "source_rows": len(sources), "individual_reviews": len(reviews),
            "by_disposition": dict(sorted(counts.items())),
            "individual_positions_resolved": sum(
                r.get("position_resolved", False) for r in output_rows),
            "multiplicity_only": counts["deduplicate_witness_long"],
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "reviews_sha256": hashlib.sha256(reviews_path.read_bytes()).hexdigest(),
            "ledger_sha256": hashlib.sha256(payload).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-review", required=True, type=Path)
    parser.add_argument("--reviews", required=True, type=Path)
    parser.add_argument("--private-output", type=Path)
    parser.add_argument("--expected", type=int)
    args = parser.parse_args()
    print(json.dumps(consolidate(args.source_review, args.reviews, args.private_output,
                                 args.expected), sort_keys=True))


if __name__ == "__main__":
    main()
