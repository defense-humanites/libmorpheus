#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Remove a proven duplicated present fragment from explicit principal parts."""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import re

spec = importlib.util.spec_from_file_location("first",Path(__file__).resolve().with_name("repair-latin-first-conjugation.py"))
first = importlib.util.module_from_spec(spec)
spec.loader.exec_module(first)
PARTS = re.compile(r"([A-Za-z_^]+i),\s*([A-Za-z_^]+(?:um|us)),\s*3")


def transform(candidate, rows):
    proofs = defaultdict(set)
    plain = lambda text: text.translate(str.maketrans("", "", "_^"))
    for row in rows:
        if row.get("projection_error") is not None:
            continue
        head = re.sub(r"#[1-9]$", "", row["headword"])
        if not head.endswith("o"):
            continue
        present = head[:-1]
        before, separator, root = present.rpartition("-")
        prefix = before + "-" if separator else ""
        root = root if separator else present
        lemma = row["headword"].translate(str.maketrans("", "", "_^-")).encode()
        for field in row["fields"]:
            if field["name"] != "itype":
                continue
            match = PARTS.fullmatch(field["projection"] or "")
            if not match:
                continue
            perfect, fourth = match[1][:-1], match[2][:-2]
            # The complete perfect component spells the present component.
            # Only the historical s/d,q trim bug is recognized; no other
            # ablaut, suppletion, spelling alias or voice is reconstructed.
            if not perfect.startswith("s") or not root.endswith(("d", "q")) or plain(perfect) != plain(root):
                continue
            for part, tag in [(perfect,b"perfstem"),(fourth,b"pp4")]:
                proofs[(lemma,tag)].add(((prefix+root[:-1]+part).encode(),(prefix+part).encode()))
    output, counts = [], Counter()
    lemma = None
    pattern = re.compile(rb"(:vs:)([^\s]+)([ \t]+)(perfstem|pp4)(\r?\n)?$")
    for line in candidate.splitlines(keepends=True):
        if line.startswith(b":le:"):
            lemma = line[4:].strip()
        match = pattern.fullmatch(line)
        if match:
            choices = proofs[(lemma,match[4])]
            if len(choices) > 1:
                counts["withheld_ambiguous_source"] += 1
            elif choices:
                old, new = next(iter(choices))
                if match[2] == old:
                    line = match[1]+new+match[3]+match[4]+(match[5] or b"")
                    counts["repaired_records"] += 1
                elif match[2] == new:
                    counts["already_correct"] += 1
                else:
                    counts["withheld_unmatched_record"] += 1
        output.append(line)
    return b"".join(output), dict(sorted(counts.items()))


def prepare(candidate, headers, lexica, output, expected=None):
    target = first.private_target(candidate, headers, lexica, output)
    rows, source, revision = first.source_rows(headers, lexica)
    data, counts = transform(candidate.read_bytes(), rows)
    if expected is not None and counts.get("repaired_records",0) != expected:
        raise ValueError("unexpected repaired record count")
    report = {"schema":1, "scope":"explicit conjugation-3 parts; exact duplicated-fragment proof",
              "source_revision":revision, "counts":counts,
              "input_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (candidate,headers,source)},
              "output_sha256":hashlib.sha256(data).hexdigest()}
    first.write_private(target,data)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("candidate","headers","lexica","private-output"):
        parser.add_argument("--"+name,type=Path,required=True)
    parser.add_argument("--expected",type=int)
    args = parser.parse_args()
    print(json.dumps(prepare(args.candidate,args.headers,args.lexica,args.private_output,args.expected),sort_keys=True))


if __name__ == "__main__":
    main()
