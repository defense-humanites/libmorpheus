#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare cruncher XML outputs for a fixed private Greek wordlist.

Run cruncher with -T on both sides and record the same options externally.
Unrecognized inputs are absent from stdout. This tool compares the multisets
of (reading kind, lemma, grammatical fields), separately from displayed form.
Only aggregate counts and input digests are printed. Per-form differences
may be written to a new owner-only JSONL outside the repository.
"""

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re


REPO = Path(__file__).resolve().parents[1]
READING = re.compile(r"<NL>([NVP]) ([^<>]+)</NL>")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_forms(path):
    forms = path.read_text(encoding="ascii").splitlines()
    if not forms or any(not form or any(ord(c) < 33 or ord(c) > 126
                                       for c in form) for form in forms):
        raise ValueError("forms must be nonempty literal ASCII tokens")
    if len(forms) != len(set(forms)):
        raise ValueError("forms must be unique")
    return forms


def read_output(path, forms):
    lines = path.read_text(encoding="ascii").splitlines()
    if len(lines) % 2:
        raise ValueError("cruncher output must have header/reading pairs")
    order = {form: i for i, form in enumerate(forms)}
    result = {}
    previous = -1
    for offset in range(0, len(lines), 2):
        form, line = lines[offset:offset + 2]
        if form not in order or order[form] <= previous:
            raise ValueError("output headers must follow the supplied unique forms")
        previous = order[form]
        matches = list(READING.finditer(line))
        if not matches or "".join(match.group(0) for match in matches) != line:
            raise ValueError("unsupported or malformed XML reading line")
        readings = []
        for match in matches:
            kind = match.group(1)
            fields = match.group(2).split("  ", 1)
            if len(fields) != 2 or not fields[1]:
                raise ValueError("reading must contain grammatical fields")
            head, grammar = fields
            if head.count(",") > 1:
                raise ValueError("unsupported headword fields")
            if "," in head:
                display, lemma = head.split(",")
            else:
                display = lemma = head
            if not display or not lemma:
                raise ValueError("empty displayed form or lemma")
            readings.append((kind, display, lemma, grammar))
        result[form] = readings
    return result


def signatures(readings):
    return Counter((kind, lemma, grammar) for kind, _, lemma, grammar in readings)


def compare(forms_path, left_path, right_path, private_output=None):
    forms = read_forms(forms_path)
    left = read_output(left_path, forms)
    right = read_output(right_path, forms)
    counts = Counter(distinct_forms=len(forms), left_recognized=len(left),
                     right_recognized=len(right),
                     left_reading_rows=sum(map(len, left.values())),
                     right_reading_rows=sum(map(len, right.values())))
    differences = []
    for form in forms:
        a, b = left.get(form, []), right.get(form, [])
        if not a and not b:
            cell = "absent_both"
        elif not a:
            cell = "gained"
        elif not b:
            cell = "lost"
        elif signatures(a) != signatures(b):
            cell = "shared_readings_changed"
        elif Counter(a) != Counter(b):
            cell = "shared_display_changed"
        else:
            cell = "identical"
        counts[cell] += 1
        if cell not in ("identical", "absent_both"):
            differences.append({"form": form, "cell": cell,
                                "left": a, "right": b})
    if private_output is not None:
        target = private_output.resolve()
        if target == REPO or REPO in target.parents or target in {
                forms_path.resolve(), left_path.resolve(), right_path.resolve()}:
            raise ValueError("private output must be outside repository and inputs")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        with os.fdopen(os.open(target, flags, 0o600), "w") as output:
            for row in differences:
                output.write(json.dumps(row, sort_keys=True) + "\n")
    return {"schema": 1, "mode": "literal forms; N/V/P XML reading multisets",
            "forms_sha256": digest(forms_path), "left_sha256": digest(left_path),
            "right_sha256": digest(right_path), "counts": dict(sorted(counts.items()))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--forms", required=True, type=Path)
    parser.add_argument("--left", required=True, type=Path)
    parser.add_argument("--right", required=True, type=Path)
    parser.add_argument("--private-output", type=Path)
    args = parser.parse_args()
    print(json.dumps(compare(args.forms, args.left, args.right,
                             args.private_output), sort_keys=True))


if __name__ == "__main__":
    main()
