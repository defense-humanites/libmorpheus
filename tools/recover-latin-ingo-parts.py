#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Recover an unhandled explicit -ingo/inxi two-supine header privately."""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import re

spec = importlib.util.spec_from_file_location("first", Path(__file__).resolve().with_name("repair-latin-first-conjugation.py"))
first = importlib.util.module_from_spec(spec)
spec.loader.exec_module(first)


def transform(candidate, rows):
    proofs = defaultdict(set)
    for row in rows:
        if row.get("projection_error") is not None:
            continue
        head = row["headword"]
        match = re.fullmatch(r"([A-Za-z_^]+(?:-[A-Za-z_^]+)*)ingo(#[1-9])?", head)
        types = [f["projection"] for f in row["fields"] if f["name"] == "itype"]
        orths = [f for f in row["fields"] if f["name"] == "orth"]
        if (not match or len(orths) != 1 or len(types) != 1 or
                types[0] not in {"inxi, inctum and ictum, 3", "inxi, ictum and inctum, 3"}):
            continue
        lemma = head.translate(str.maketrans("", "", "_^-")).encode()
        base = match[1].encode()
        # Both supines, the perfect suffix and conjugation are explicit.
        # This narrowly matched present spelling supplies their common base.
        records = (b":le:" + lemma + b"\n:vs:" + base + b"ing\tconj3\n:vs:" +
                   base + b"inx perfstem\n:vs:" + base + b"inct pp4\n:vs:" + base + b"ict pp4\n")
        raw = first.compound.recovery.render(row).encode()
        proofs[raw].add((lemma, records))
    counts = Counter()
    additions = {}
    lemmas = {line[4:].strip() for line in candidate.splitlines() if line.startswith(b":le:")}
    for raw, choices in proofs.items():
        if len(choices) != 1:
            counts["withheld_ambiguous_source"] += 1
            continue
        lemma, records = next(iter(choices))
        if lemma in lemmas:
            counts["withheld_existing_lemma"] += 1
            continue
        if candidate.splitlines(keepends=True).count(raw) != 1:
            counts["withheld_missing_or_duplicate_header"] += 1
            continue
        additions[raw] = records
        counts["recovered_headers"] += 1
        counts["added_stem_records"] += 4
    output = b"".join(line + additions.get(line, b"") for line in candidate.splitlines(keepends=True))
    return output, dict(sorted(counts.items()))


def prepare(candidate, headers, lexica, output, expected=None):
    target = first.private_target(candidate, headers, lexica, output)
    rows, source, revision = first.source_rows(headers, lexica)
    data, counts = transform(candidate.read_bytes(), rows)
    if expected is not None and counts.get("recovered_headers", 0) != expected:
        raise ValueError("unexpected recovered header count")
    report = {"schema": 1, "scope": "unhandled explicit -ingo/inxi two-supine headers only",
              "source_revision": revision, "counts": counts,
              "input_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (candidate, headers, source)},
              "output_sha256": hashlib.sha256(data).hexdigest()}
    first.write_private(target, data)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("candidate", "headers", "lexica", "private-output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--expected", type=int)
    args = parser.parse_args()
    print(json.dumps(prepare(args.candidate, args.headers, args.lexica, args.private_output, args.expected), sort_keys=True))


if __name__ == "__main__":
    main()
