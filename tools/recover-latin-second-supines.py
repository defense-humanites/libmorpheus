#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Qualify narrowly explicit dual-supine headers against existing stems."""
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
PARTS = re.compile(r"([A-Za-z_^]+i), ([A-Za-z_^]+um) and ([A-Za-z_^]+um), ([34])")


def proof(row):
    if row.get("projection_error") is not None:
        return None
    head = re.sub(r"#[1-9]$", "", row["headword"])
    if not head.endswith("o"):
        return None
    types = [f["projection"] for f in row["fields"] if f["name"] == "itype"]
    matches = [PARTS.fullmatch(t or "") for t in types]
    matches = [m for m in matches if m]
    if len(matches) != 1 or any(re.search(r"(?:^|,\s*)[1-4]$", t or "") and not PARTS.fullmatch(t or "") for t in types):
        return None
    m = matches[0]
    perfect, one, two, conjugation = m[1][:-1], m[2][:-2], m[3][:-2], m[4]
    plain = lambda text: text.translate(str.maketrans("", "", "_^"))
    present = head[:-1]
    prefix, separator, component = present.rpartition("-")
    prefix = prefix + "-" if separator else ""
    component = component if separator else present
    if conjugation == "3" and plain(component) == "tend":
        if perfect == "d" and {one, two} == {"t", "s"}:
            base = prefix + component[:-1]
            result = (present, "conj3", base + perfect, base + perfect, base + one, base + one, base + two)
        elif plain(perfect) == "tetend" and {plain(one), plain(two)} == {"tent", "tens"}:
            result = (present, "conj3", prefix + perfect, prefix + perfect, prefix + one, prefix + one, prefix + two)
        else:
            return None
    elif conjugation == "4" and perfect == "s" and {one, two} == {"s", "t"}:
        stem = re.sub(r"i[_^]?$", "", present)
        if stem == present or not stem.endswith("c"):
            return None
        # The exact historical si,sum,4 rule trims c before s; the generic
        # combined-field branch incorrectly retains it. The t part retains c.
        correct = lambda part: stem[:-1] + "s" if part == "s" else stem + "t"
        result = (stem, "conj4", stem + "s", correct("s"), stem + one, correct(one), correct(two))
    else:
        return None
    return tuple(x.encode() for x in result)


def transform(candidate, rows):
    sources = defaultdict(list)
    for row in rows:
        p = proof(row)
        if p:
            lemma = row["headword"].translate(str.maketrans("", "", "_^-")).encode()
            sources[lemma].append(p)
    inventory = defaultdict(lambda: defaultdict(set))
    blocks = Counter();lemma = None
    pattern = re.compile(rb"(:vs:)([^\s]+)([ \t]+)(conj[34]|perfstem|pp4)(\r?\n)?$")
    for line in candidate.splitlines(keepends=True):
        if line.startswith(b":le:"):
            lemma = line[4:].strip();blocks[lemma] += 1
        match = pattern.fullmatch(line)
        if match:
            inventory[lemma][match[4]].add(match[2])
    plans = {};counts = Counter()
    for lemma, choices in sources.items():
        if len(choices) != 1 or blocks[lemma] != 1:
            counts["withheld_ambiguous_source_or_block"] += 1;continue
        present, tag, old_perf, perf, old_one, one, two = choices[0]
        inv = inventory[lemma]
        if (inv[tag] != {present} or len(inv[b"perfstem"]) != 1 or
                not inv[b"perfstem"].issubset({old_perf, perf}) or
                not inv[b"pp4"].intersection({old_one, one}) or
                not inv[b"pp4"].issubset({old_one, one, two}) or
                (old_one != one and {old_one, one}.issubset(inv[b"pp4"]))):
            counts["withheld_unmatched_stems"] += 1;continue
        plans[lemma] = (old_perf, perf, old_one, one, two)
    output = [];lemma = None;changed = set()
    for line in candidate.splitlines(keepends=True):
        if line.startswith(b":le:"):
            lemma = line[4:].strip()
        match = pattern.fullmatch(line)
        if match and lemma in plans:
            old_perf, perf, old_one, one, two = plans[lemma]
            new = match[2]
            if match[4] == b"perfstem" and new == old_perf:
                new = perf
            elif match[4] == b"pp4" and new == old_one:
                new = one
            if new != match[2]:
                line = match[1] + new + match[3] + match[4] + (match[5] or b"")
                counts["repaired_records"] += 1;changed.add(lemma)
            output.append(line)
            if match[4] == b"pp4" and new == one and two not in inventory[lemma][b"pp4"]:
                if not line.endswith(b"\n"):
                    output.append(b"\n")
                output.append(b":vs:" + two + b" pp4\n")
                inventory[lemma][b"pp4"].add(two)
                counts["added_records"] += 1;changed.add(lemma)
        else:
            output.append(line)
    counts["changed_lemma_blocks"] = len(changed)
    return b"".join(output), dict(sorted(counts.items()))


def prepare(candidate, headers, lexica, output, expected=None):
    target = first.private_target(candidate, headers, lexica, output)
    rows, source, revision = first.source_rows(headers, lexica)
    data, counts = transform(candidate.read_bytes(), rows)
    if expected is not None and counts.get("changed_lemma_blocks", 0) != expected:
        raise ValueError("unexpected changed block count")
    report = {"schema":1,"scope":"explicit -tendo and conjugation-4 c/s,t dual supines; exact stem proof",
              "source_revision":revision,"counts":counts,
              "input_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (candidate,headers,source)},
              "output_sha256":hashlib.sha256(data).hexdigest()}
    first.write_private(target, data)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("candidate","headers","lexica","private-output"):
        parser.add_argument("--"+name,type=Path,required=True)
    parser.add_argument("--expected",type=int)
    args=parser.parse_args()
    print(json.dumps(prepare(args.candidate,args.headers,args.lexica,args.private_output,args.expected),sort_keys=True))


if __name__ == "__main__":
    main()
