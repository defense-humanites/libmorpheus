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
PARTS = re.compile(r"([A-Za-z_^]+i),\s*([A-Za-z_^]+(?:um|us)),\s*([23])")


def transform(candidate, rows, proof_tier="exact-present"):
    if proof_tier not in {"exact-present", "source-allomorphs"}:
        raise ValueError("unsupported proof tier")
    proofs = defaultdict(set)
    plain = lambda text: text.translate(str.maketrans("", "", "_^"))
    consonants = lambda text: re.sub("[aeiouy]", "", plain(text))
    primary = defaultdict(set)
    lemma = None
    for line in candidate.splitlines():
        if line.startswith(b":le:"):
            lemma = line[4:].strip()
        match = re.fullmatch(rb":vs:([^\s]+)[ \t]+(conj[23])", line)
        if match:
            primary[lemma].add((match[1], match[2]))
    for row in rows:
        if row.get("projection_error") is not None:
            continue
        head = re.sub(r"#[1-9]$", "", row["headword"])
        if not head.endswith("o"):
            continue
        present = head[:-1]
        before, separator, component = present.rpartition("-")
        prefix = before + "-" if separator else ""
        component = component if separator else present
        lemma = row["headword"].translate(str.maketrans("", "", "_^-")).encode()
        for field in row["fields"]:
            if field["name"] != "itype":
                continue
            match = PARTS.fullmatch(field["projection"] or "")
            if not match:
                continue
            root = component
            conjugation = match[3]
            if conjugation == "2":
                if proof_tier == "exact-present":
                    continue
                root = re.sub(r"e[_^]?$", "", component)
                if root == component:
                    continue
            perfect, fourth = match[1][:-1], match[2][:-2]
            # The complete perfect component spells the present component.
            # Only the historical s/d,q trim bug is recognized. Replacement
            # parts must be explicit; no suppletion, alias or voice is inferred.
            if not perfect.startswith("s") or not root.endswith(("d", "q")):
                continue
            if proof_tier == "exact-present":
                if plain(perfect) != plain(root):
                    continue
            else:
                # All replacement letters are explicit source parts. These
                # relations identify a complete component, rather than a short
                # suffix; never use them to construct an unattested allomorph.
                same_consonants = consonants(perfect) == consonants(root)
                reduplicated = plain(root).startswith("sp") and plain(perfect) == "spo" + plain(root)[1:]
                if len(plain(perfect)) < 3 or not (same_consonants or reduplicated):
                    continue
                if ((prefix + root).encode(), ("conj" + conjugation).encode()) not in primary[lemma]:
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


def prepare(candidate, headers, lexica, output, expected=None, proof_tier="exact-present"):
    target = first.private_target(candidate, headers, lexica, output)
    rows, source, revision = first.source_rows(headers, lexica)
    data, counts = transform(candidate.read_bytes(), rows, proof_tier)
    if expected is not None and counts.get("repaired_records",0) != expected:
        raise ValueError("unexpected repaired record count")
    report = {"schema":1, "scope":"explicit principal parts; exact duplicated-fragment proof", "proof_tier":proof_tier,
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
    parser.add_argument("--proof-tier", choices=["exact-present", "source-allomorphs"], default="exact-present",
                        help="separately qualify explicit vowel-changing/reduplicated components")
    args = parser.parse_args()
    print(json.dumps(prepare(args.candidate,args.headers,args.lexica,args.private_output,args.expected,args.proof_tier),sort_keys=True))


if __name__ == "__main__":
    main()
