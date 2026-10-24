#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Repair existing are_vb derivatives from explicit source present spellings."""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("compound", REPO/"tools/recover-latin-compound-headwords.py")
compound = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compound)
review = compound.review
FIRST = re.compile(r"(?:^|,\s*)1$|^a_r[ei](?:,\s*1)?$")


def present_root(headword):
    headword = re.sub(r"#[1-9]$", "", headword)
    if headword.endswith("or"):
        return headword[:-2], True
    if headword.endswith("o"):
        return headword[:-1], False
    return None


def transform(candidate, rows, tier="all"):
    if tier not in {"all", "letters-only"}:
        raise ValueError("unsupported repair tier")
    roots = defaultdict(set)
    for row in rows:
        if row.get("projection_error") is not None:
            continue
        if not any(f["name"] == "itype" and FIRST.search(f["projection"] or "") for f in row["fields"]):
            continue
        root = present_root(row["headword"])
        if not root or not root[0]:
            continue
        # This is the literal lemma emitted by latvb, not a witness alias.
        lemma = row["headword"].translate(str.maketrans("", "", "_^-")).encode()
        roots[lemma].add((root[0].encode(), root[1]))
    output, counts = [], Counter()
    lemma = None
    pattern = re.compile(rb"(:de:)([^\s]+)([ \t]+)(are_vb)([^\r\n]*)(\r?\n)?$")
    for line in candidate.splitlines(keepends=True):
        if line.startswith(b":le:"):
            lemma = line[4:].strip()
        match = pattern.fullmatch(line)
        if match:
            counts["are_records"] += 1
            choices = roots[lemma]
            if len(choices) != 1:
                counts["withheld_missing_or_ambiguous_source"] += 1
            else:
                root, deponent = next(iter(choices))
                flags = match[5].split()
                if b"orth" in flags or (b"dep" in flags) != deponent:
                    counts["withheld_alternate_or_voice"] += 1
                elif root == match[2]:
                    counts["unchanged"] += 1
                elif tier == "letters-only" and root.translate(None,b"_^") == match[2].translate(None,b"_^"):
                    counts["withheld_quantity_only"] += 1
                else:
                    kind = "quantity_only" if root.translate(None,b"_^") == match[2].translate(None,b"_^") else "letters"
                    line = match[1] + root + match[3] + match[4] + match[5] + (match[6] or b"")
                    counts["repaired_records"] += 1
                    counts["repaired_"+kind] += 1
        output.append(line)
    return b"".join(output), dict(sorted(counts.items()))


def private_target(candidate, headers, lexica, output):
    target = output.resolve()
    inputs = [p.resolve() for p in (candidate, headers, lexica)]
    if target == REPO or REPO in target.parents or any(target == p or p in target.parents for p in inputs):
        raise ValueError("private output must be outside repository and inputs")
    return target


def source_rows(headers, lexica):
    entries, source, revision = review.load_entries(lexica)
    rows, seen = [], set()
    for line in headers.read_bytes().splitlines():
        row = json.loads(line)
        key = row.get("id")
        if (row.get("schema") != 1 or row.get("source") != review.SOURCE.name or
                key in seen or key not in entries or row.get("source_key") != entries[key].get("key")):
            raise ValueError("invalid source join")
        seen.add(key)
        entry = entries[key]
        base, _ = review.projection.project(entry, "Latin")
        if row.get("projection_error") is None:
            if base.get("projection_error") is not None:
                raise ValueError("source projection mismatch")
            repaired, _ = compound.repair(dict(base, id=key), entry)
            if row["headword"] not in {base["headword"], repaired["headword"]}:
                raise ValueError("headword differs from explicit source")
            # The first-sense trial may append fields; never accept other itypes.
            source_types = {f["projection"] for f in base["fields"] + review.initial_sense_fields(entry) if f["name"] == "itype"}
            if any(f["name"] == "itype" and f["projection"] not in source_types for f in row["fields"]):
                raise ValueError("conjugation differs from explicit source")
        rows.append(row)
    return rows, source, revision


def write_private(target, data):
    with os.fdopen(os.open(target, os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,"O_NOFOLLOW",0), 0o600), "wb") as stream:
        stream.write(data)


def prepare(candidate, headers, lexica, output, expected=None, tier="all"):
    target = private_target(candidate, headers, lexica, output)
    rows, source, revision = source_rows(headers, lexica)
    data, counts = transform(candidate.read_bytes(), rows, tier)
    if expected is not None and counts.get("repaired_records", 0) != expected:
        raise ValueError("unexpected repaired record count")
    report = {"schema": 1, "scope": "existing primary are_vb records; explicit source only",
              "source_revision": revision, "counts": counts, "tier": tier,
              "input_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (candidate, headers, source)},
              "output_sha256": hashlib.sha256(data).hexdigest()}
    write_private(target, data)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("candidate", "headers", "lexica", "private-output"):
        parser.add_argument("--"+name, type=Path, required=True)
    parser.add_argument("--expected", type=int)
    parser.add_argument("--tier", choices=["all", "letters-only"], default="all",
                        help="keep quantity-only differences in a separate trial")
    args = parser.parse_args()
    print(json.dumps(prepare(args.candidate, args.headers, args.lexica, args.private_output, args.expected, args.tier), sort_keys=True))


if __name__ == "__main__":
    main()
