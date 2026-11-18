#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Transfer reviewed corrections only to identical records under the same lemma."""

import argparse
import hashlib
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def transform(candidate, original, corrections, language, source_path):
    if Path(source_path).is_absolute() or ".." in Path(source_path).parts:
        raise ValueError("invalid correction source path")
    source_lines = original.splitlines()
    lemma = None
    locations = {}
    for number, line in enumerate(source_lines, 1):
        if line.startswith(b":le:"):
            lemma = line[4:].strip()
        locations[number] = lemma
    mapping = {}
    selected = 0
    seen = set()
    for row in corrections.decode().splitlines():
        if not row or row.startswith("#"):
            continue
        fields = row.split("\t", 4)
        if len(fields) != 5:
            raise ValueError("invalid correction row")
        lang, name, text_number, expected, replacement_json = fields
        if lang != language or name != source_path:
            continue
        number = int(text_number)
        if number in seen or number < 1 or number > len(source_lines):
            raise ValueError("invalid or duplicate correction line")
        seen.add(number)
        line = source_lines[number - 1]
        replacement = json.loads(replacement_json)
        if digest(line) != expected or not locations[number]:
            raise ValueError("reviewed source record mismatch")
        if not isinstance(replacement, str) or "\n" in replacement or "\r" in replacement:
            raise ValueError("invalid correction replacement")
        if line.startswith(b":le:") or not line.startswith(b":"):
            raise ValueError("correction must select a lexical record")
        key = (locations[number], expected)
        replacement = replacement.encode()
        if key in mapping and mapping[key] != replacement:
            raise ValueError("conflicting reviewed record corrections")
        mapping[key] = replacement
        selected += 1
    if not selected:
        raise ValueError("no reviewed corrections for selected source")
    output = []
    lemma = None
    applied = 0
    for line in candidate.splitlines(keepends=True):
        record = line.rstrip(b"\r\n")
        if record.startswith(b":le:"):
            lemma = record[4:].strip()
        key = (lemma, digest(record))
        if key in mapping:
            line = mapping[key] + line[len(record):]
            applied += 1
        output.append(line)
    data = b"".join(output)
    return data, {"schema": 1, "scope": "existing reviewed records; exact lemma and bytes",
                  "selected_source_corrections": selected, "applied_records": applied,
                  "input_sha256": {"candidate": digest(candidate), "original": digest(original),
                                   "corrections": digest(corrections)},
                  "output_sha256": digest(data)}


def prepare(candidate, original, corrections, language, source_path, output, expected=None):
    target = output.resolve()
    inputs = [p.resolve() for p in (candidate, original, corrections)]
    if target == REPO or REPO in target.parents or target in inputs:
        raise ValueError("private output must be outside repository and inputs")
    data, report = transform(*(p.read_bytes() for p in (candidate, original, corrections)),
                             language, source_path)
    if expected is not None and report["applied_records"] != expected:
        raise ValueError("unexpected applied correction count")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    with os.fdopen(os.open(target, flags, 0o600), "wb") as stream:
        stream.write(data)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["candidate", "original", "corrections", "private-output"]:
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--language", required=True, choices=["Greek", "Latin"])
    parser.add_argument("--source-path", required=True)
    parser.add_argument("--expected", type=int)
    args = parser.parse_args()
    print(json.dumps(prepare(args.candidate, args.original, args.corrections, args.language,
                             args.source_path, args.private_output, args.expected), sort_keys=True))


if __name__ == "__main__":
    main()
