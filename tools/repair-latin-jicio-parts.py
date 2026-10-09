#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stage exact duplicate-component repairs proved by complete -jicio alternates."""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import re

spec = importlib.util.spec_from_file_location("alternates", Path(__file__).with_name("recover-latin-full-alternates.py"))
alternates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alternates)
first = alternates.first
short = lambda value: value.replace(b"^", b"")
plain = lambda value: value.translate(str.maketrans("", "", "_^-"))


def proof(row):
    if row.get("projection_error") is not None:
        return None
    types = [f["projection"] for f in row["fields"] if f["name"] == "itype"]
    if types not in [["je_ci, jectum, 3"], ["je_ci, jactum, 3"]]:
        return None
    head = re.sub(r"#[1-9]$", "", row["headword"])
    match = re.fullmatch(r"([A-Za-z_^]+(?:-[A-Za-z_^]+)*-?)i[_^]?ci[_^]?o", head)
    if not match:
        return None
    prefix = match[1]
    compatible = []
    for alt in row.get("full_alternates", []):
        m = re.fullmatch(r"([A-Za-z_^]+(?:-[A-Za-z_^]+)*-?)ji[_^]?ci[_^]?o", alt)
        if m and plain(m[1]) == plain(prefix):
            compatible.append(re.sub(r"i[_^]?o$", "", alt).encode())
    compatible = set(compatible)
    if len(compatible) != 1:
        return None
    present = re.sub(r"i[_^]?o$", "", head).encode()
    perfect = (prefix + "je_c").encode()
    fourth = (prefix + ("ject" if types[0] == "je_ci, jectum, 3" else "jact")).encode()
    return present, perfect, fourth, next(iter(compatible))


def transform(candidate, rows):
    sources = defaultdict(list)
    for row in rows:
        parts = proof(row)
        if parts:
            lemma = row["headword"].translate(str.maketrans("", "", "_^-")).encode()
            sources[lemma].append(parts)
    pattern = re.compile(rb":vs:([^\s]+)[ \t]+(conj3_io|perfstem|pp4)([^\r\n]*)(?:\r?\n)?$")
    records = defaultdict(list)
    blocks = Counter()
    lemma = None
    for index, line in enumerate(candidate.splitlines(keepends=True)):
        if line.startswith(b":le:"):
            lemma = line[4:].strip()
            blocks[lemma] += 1
        m = pattern.fullmatch(line)
        if m:
            records[lemma].append((index, m[1], m[2], m[3].strip()))
    replacements = {}
    additions = {}
    counts = Counter()
    for lemma, choices in sources.items():
        if len(choices) != 1 or blocks[lemma] != 1:
            counts["withheld_ambiguity"] += 1
            continue
        present, perfect, fourth, alt = choices[0]
        primary = [r for r in records[lemma] if not r[3]]
        if sum(r[2] == b"conj3_io" and short(r[1]) == short(present) for r in primary) != 1:
            counts["withheld_present"] += 1
            continue
        selected = []
        for tag, good, ending in [(b"perfstem", perfect, b"je_c"), (b"pp4", fourth, fourth[-4:])]:
            part = [r for r in primary if r[2] == tag]
            bad = present + ending
            if len(part) != 1 or short(part[0][1]) not in {short(bad), short(good)}:
                break
            selected.append((part[0], good))
        if len(selected) != 2:
            counts["withheld_principal_parts"] += 1
            continue
        changed = False
        for (index, stem, tag, flags), good in selected:
            if short(stem) != short(good):
                replacements[index] = b":vs:" + good + b"\t" + tag + b"\n"
                counts["repaired_records"] += 1
                changed = True
        if not any(short(r[1]) == short(alt) and r[2:] == (b"conj3_io", b"orth") for r in records[lemma]):
            anchor = next(r[0] for r in primary if r[2] == b"conj3_io")
            additions[anchor] = b":vs:" + alt + b"\tconj3_io orth\n"
            counts["added_records"] += 1
            changed = True
        counts["changed_lemma_blocks"] += int(changed)
    output = []
    for index, line in enumerate(candidate.splitlines(keepends=True)):
        output.append(replacements.get(index, line))
        if index in additions:
            if not output[-1].endswith(b"\n"):
                output.append(b"\n")
            output.append(additions[index])
    return b"".join(output), dict(sorted(counts.items()))


def prepare(candidate, headers, lexica, output, expected=None):
    target = first.private_target(candidate, headers, lexica, output)
    rows, source, revision = alternates.source_alternates(headers, lexica)
    data, counts = transform(candidate.read_bytes(), rows)
    if expected is not None and counts.get("repaired_records", 0) != expected:
        raise ValueError("unexpected repaired record count")
    report = {"schema": 1, "scope": "exact duplicate components with same-article complete jicio proof",
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
