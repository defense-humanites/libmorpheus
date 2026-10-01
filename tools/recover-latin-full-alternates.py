#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stage complete same-article spellings for existing first-conjugation roots."""
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
COMPLETE = re.compile(r"[A-Za-z_^]+(?:-[A-Za-z_^]+)*(?:o|or)")


def transform(candidate, rows):
    sources = defaultdict(list)
    for row in rows:
        if row.get("projection_error") is not None:
            continue
        types = [f["projection"] or "" for f in row["fields"] if f["name"] == "itype"]
        if (not any(first.FIRST.search(t) for t in types) or
                any(re.search(r"(?:^|,\s*)[234]$", t) for t in types)):
            continue
        root = first.present_root(row["headword"])
        if root:
            lemma = row["headword"].translate(str.maketrans("", "", "_^-")).encode()
            sources[lemma].append((root, row.get("full_alternates", [])))
    records = defaultdict(set)
    blocks = Counter()
    lemma = None
    pattern = re.compile(rb":de:([^\s]+)[ \t]+are_vb( dep)?( orth)?(?:\r?\n)?$")
    for line in candidate.splitlines(keepends=True):
        if line.startswith(b":le:"):
            lemma = line[4:].strip()
            blocks[lemma] += 1
        match = pattern.fullmatch(line)
        if match:
            records[lemma].add((match[1].replace(b"^", b""), bool(match[2]), bool(match[3])))
    additions, counts = {}, Counter()
    for lemma, choices in sources.items():
        if len(choices) != 1 or blocks[lemma] != 1:
            counts["withheld_source_or_block_ambiguity"] += 1
            continue
        (root, dep), alternates = choices[0]
        primary = (root.encode().replace(b"^", b""), dep, False)
        if primary not in records[lemma]:
            counts["withheld_unmatched_primary"] += 1
            continue
        for alt in alternates:
            if not COMPLETE.fullmatch(alt):
                counts["withheld_incomplete_alternate"] += 1
                continue
            alt_root, alt_dep = first.present_root(alt)
            if alt_dep != dep:
                counts["withheld_voice_difference"] += 1
                continue
            if alt_root.translate(str.maketrans("", "", "_^")) == root.translate(str.maketrans("", "", "_^")):
                counts["withheld_quantity_only"] += 1
                continue
            key = (alt_root.encode().replace(b"^", b""), dep, True)
            if key in records[lemma]:
                counts["already_present"] += 1
                continue
            records[lemma].add(key)
            additions.setdefault(lemma, []).append(b":de:" + alt_root.encode() + b"\tare_vb" + (b" dep" if dep else b"") + b" orth\n")
            counts["added_records"] += 1
    counts["changed_lemma_blocks"] = len(additions)
    output = []
    lemma = None
    for line in candidate.splitlines(keepends=True):
        output.append(line)
        if line.startswith(b":le:"):
            lemma = line[4:].strip()
        match = pattern.fullmatch(line)
        if match and not match[3] and lemma in additions:
            if not line.endswith(b"\n"):
                output.append(b"\n")
            output.extend(additions.pop(lemma))
    return b"".join(output), dict(sorted(counts.items()))


def prepare(candidate, headers, lexica, output, expected=None):
    target = first.private_target(candidate, headers, lexica, output)
    rows, source, revision = first.source_rows(headers, lexica)
    entries, _, _ = first.review.load_entries(lexica)
    for row in rows:
        if row.get("projection_error") is not None:
            continue
        entry = entries[row["id"]]
        base, _ = first.review.projection.project(entry, "Latin")
        orths = lambda r: [f for f in r["fields"] if f["name"] == "orth"]
        if orths(row) != orths(base):
            raise ValueError("orthographies differ from pinned source")
        alternates = []
        for node in entry.findall("orth")[1:]:
            if node.get("extent") != "full" or node.get("type") not in {None, "alt"}:
                continue
            raw = " ".join("".join(node.itertext()).split())
            projected = first.review.projection.normalize(raw, "Latin")
            if projected is None:
                continue
            if " " in projected:
                if not first.compound.COMPOUND.fullmatch(projected):
                    continue
                projected = projected.replace(" ", "")
            alternates.append(projected)
        row["full_alternates"] = alternates
    data, counts = transform(candidate.read_bytes(), rows)
    if expected is not None and counts.get("added_records", 0) != expected:
        raise ValueError("unexpected added alternate count")
    report = {"schema": 1, "scope": "same-article complete orthographies; existing primary are_vb only",
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
