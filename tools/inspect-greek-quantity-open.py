#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prepare a private positional dossier for unresolved Greek long marks.

The source review contains lexicon-derived records. Print only aggregates and
digests; never commit or publish the optional entry-level output.
"""

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re


REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "greek_quantity_long", Path(__file__).with_name("arbitrate-greek-quantity-long.py"))
LONG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LONG)
CONTEXTUAL = re.compile(r"\[([a-z]+)_([a-z]*)\]")


def positions(value):
    spelling, longs = LONG.letters_and_longs(value.split()[0])
    return {"spelling": spelling, "long": sorted({index for index, _ in longs}),
            "short": sorted(LONG.short_positions(value.split()[0]))}


def dossier(row):
    witness = positions(row["witness"].split()[0][4:])
    candidate = positions(row["candidate"].split()[0][4:])
    sources = []
    for source in row["sources"]:
        orths = [positions(source["headword"])]
        for field in source.get("fields", []):
            if field["name"] == "orth":
                orth = positions(field["projection"])
                if orth not in orths:
                    orths.append(orth)
        sources.append({"id": source["id"], "orthographies": orths,
                        "pronunciations": source.get("pron", [])})
    return {"lemma": row["lemma"], "candidate": candidate, "witness": witness,
            "sources": sources}


def inspect(source, private_output=None):
    if private_output is not None:
        target = private_output.resolve()
        if target == REPO or REPO in target.parents or target == source.resolve():
            raise ValueError("private dossier must be outside the repository and differ from input")
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
                if LONG.decision(row) != "manual_review":
                    continue
                item = dossier(row)
                counts["manual_review"] += 1
                counts["multiple_sources"] += len(item["sources"]) > 1
                counts["alternate_orthographies"] += any(
                    len(entry["orthographies"]) > 1 for entry in item["sources"])
                counts["explicit_long_in_orthography"] += any(
                    orth["long"] for entry in item["sources"]
                    for orth in entry["orthographies"])
                counts["explicit_short_in_orthography"] += any(
                    orth["short"] for entry in item["sources"]
                    for orth in entry["orthographies"])
                counts["contextual_direct_pron"] += any(
                    pron["direct"] and (match := CONTEXTUAL.fullmatch(pron["text"]))
                    and len(match.group(1) + match.group(2)) > 1
                    for entry in item["sources"] for pron in entry["pronunciations"])
                if output is not None:
                    result = (json.dumps(item, sort_keys=True, ensure_ascii=False) + "\n").encode()
                    output.write(result)
                    output_digest.update(result)
    finally:
        if output is not None:
            output.close()
    return {"schema": 1, "scope": "positional review, no lexical decision",
            "input_sha256": digest.hexdigest(), "counts": dict(sorted(counts.items())),
            "private_output_sha256": output_digest.hexdigest() if private_output else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-review", required=True, type=Path)
    parser.add_argument("--private-output", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.source_review, args.private_output), sort_keys=True))


if __name__ == "__main__":
    main()
