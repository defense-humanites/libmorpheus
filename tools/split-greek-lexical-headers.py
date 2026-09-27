#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reproduce the historical Greek header split for projected, quant-free input.

Equivalent to ``sed 's/-//' | setquant | splitlems`` when the input contains
no <quant> field. The result contains lexicon-derived material: keep it private.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re


REPO = Path(__file__).resolve().parents[1]
HEADER = re.compile(rb"[A-Za-z\^_\-]+[#1-9]*")
RULES = (
    re.compile(rb"\t[a-z\*]"),
    re.compile(rb"</gen>\t<orth>[^<]+</orth>"),
    re.compile(rb"</pos>\t<orth>[^<]+</orth>"),
    re.compile(rb"</itype>\t<orth>[^<]+</orth>"),
    re.compile(rb"</gen>\t<itype>"),
)


def split_line(raw, lemma):
    """Apply flex's longest-match rules, including its default one-byte ECHO."""
    line = raw.replace(b"-", b"", 1)
    result = bytearray()
    i = 0
    while i < len(line):
        if i == 0:
            match = HEADER.match(line)
            if match:
                lemma = match.group()
                result.extend(lemma)
                i = match.end()
                continue
        matches = (rule.match(line, i) for rule in RULES)
        match = max((item for item in matches if item),
                    key=lambda item: item.end(), default=None)
        if match is None:
            result.extend(line[i:i + 1])
            i += 1
            continue
        lexeme = match.group()
        if match.re is RULES[0]:
            result.extend(b"\n" + lexeme[1:])
        elif match.re is RULES[4]:
            result.extend(b"</gen>\n" + lemma + b"\t<itype>")
        else:
            label, orth = lexeme.split(b"\t<orth>")
            result.extend(label + b"\n" + orth[:-7] + b"\t")
        i = match.end()
    return bytes(result), lemma


def split(source, output):
    target = output.resolve()
    if target == REPO or REPO in target.parents:
        raise ValueError("output must be outside the repository")
    if target == source.resolve():
        raise ValueError("output must differ from input")
    # setquant is the identity only for this projected subset.
    with source.open("rb") as stream:
        if any(b"<quant>" in raw for raw in stream):
            raise ValueError("input has <quant> fields; use the historical setquant lexer")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(target, flags, 0o600)
    digest = hashlib.sha256()
    rows = 0
    lemma = b""
    with source.open("rb") as stream, os.fdopen(fd, "wb") as result:
        for raw in stream:
            produced, lemma = split_line(raw, lemma)
            result.write(produced)
            digest.update(produced)
            rows += produced.count(b"\n")
    return {"split_rows": rows, "split_sha256": digest.hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(split(args.input, args.output), sort_keys=True))


if __name__ == "__main__":
    main()
