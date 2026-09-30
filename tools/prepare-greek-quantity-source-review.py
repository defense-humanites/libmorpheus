#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Join a private long-quantity triage with pinned LSJ headers and pronunciations.

The output contains lexical records. Keep it outside the repository and do not
upload it as a CI artifact. Stdout contains only counts and input/output hashes.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import subprocess

from lxml import etree


REPO = Path(__file__).resolve().parents[1]
REVISION = "56061ca127f4a2844980baffc5f2b6d1332897b3"
SUBDIR = Path("CTS_XML_TEI/perseus/pdllex/grc/lsj")


def spelling(value):
    value = value.split()[0].strip(",;:")
    value = value.translate(str.maketrans("", "", "^_-"))
    if value.endswith("*"):
        value = value[:-1]
    return value[:1] + value[1:].replace("r)r(", "rr")


def pinned_files(lexica):
    revision = subprocess.check_output(
        ["git", "-C", str(lexica), "rev-parse", "HEAD"], text=True).strip()
    if revision != REVISION:
        raise ValueError("LSJ checkout differs from the pinned revision")
    files = sorted((lexica / SUBDIR).glob("grc.lsj.perseus-eng*.xml"),
                   key=lambda path: int(path.stem.rsplit("eng", 1)[1]))
    if len(files) != 27 or [int(p.stem.rsplit("eng", 1)[1]) for p in files] != list(range(1, 28)):
        raise ValueError("incomplete LSJ TEI edition")
    dirty = subprocess.check_output(
        ["git", "-C", str(lexica), "status", "--porcelain", "--", str(SUBDIR)],
        text=True)
    if dirty:
        raise ValueError("selected LSJ files differ from the pinned revision")
    return files


def prepare(triage, headers, lexica, output, expected=None):
    target = output.resolve()
    if target == REPO or REPO in target.parents or target in {triage.resolve(), headers.resolve()}:
        raise ValueError("private review must be outside the repository and differ from inputs")
    files = pinned_files(lexica)
    digests = {"triage": hashlib.sha256(), "headers": hashlib.sha256(),
               "LSJ": hashlib.sha256()}
    selected = {}
    with triage.open("rb") as source:
        for raw in source:
            digests["triage"].update(raw)
            row = json.loads(raw)
            if "_" not in row["candidate"].split()[0][4:] and \
                    "_" not in row["witness"].split()[0][4:]:
                continue
            lemma = row["lemma"]
            if lemma in selected:
                raise ValueError("duplicate long-quantity lemma")
            selected[lemma] = {"lemma": lemma, "candidate": row["candidate"],
                               "witness": row["witness"], "sources": []}
    if expected is not None and len(selected) != expected:
        raise ValueError("unexpected number of long-quantity groups")
    by_lemma = defaultdict(list)
    with headers.open("rb") as source:
        for raw in source:
            digests["headers"].update(raw)
            header = json.loads(raw)
            if header["projection_error"] is not None or not header.get("headword"):
                continue
            matches = set()
            if header["lemma"] in selected:
                matches.add(header["lemma"])
            for field in header["fields"]:
                if field["name"] == "orth" and field["projection"]:
                    candidate = spelling(field["projection"])
                    if candidate in selected:
                        matches.add(candidate)
            for lemma in matches:
                by_lemma[lemma].append(header)
    ids = {(header["source"], header["id"])
           for matches in by_lemma.values() for header in matches}
    pronunciations = defaultdict(list)
    for path in files:
        raw = path.read_bytes()
        digests["LSJ"].update(raw)
        parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True,
                                 huge_tree=True)
        root = etree.fromstring(raw, parser)
        for entry in root.xpath("//*[self::entryFree or self::entry]"):
            key = path.name, entry.get("id")
            if key not in ids:
                continue
            for pron in entry.iter("pron"):
                pronunciations[key].append({
                    "text": " ".join("".join(pron.itertext()).split()),
                    "direct": pron.getparent() is entry})
    counts = Counter()
    for lemma, row in selected.items():
        matches = by_lemma[lemma]
        if not matches:
            raise ValueError("long-quantity group has no projected LSJ source")
        for header in matches:
            key = header["source"], header["id"]
            row["sources"].append({"id": header["id"],
                                   "headword": header["headword"],
                                   "fields": header["fields"],
                                   "pron": pronunciations[key]})
        counts["source_count_" + str(len(matches))] += 1
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    digest = hashlib.sha256()
    with os.fdopen(os.open(target, flags, 0o600), "wb") as destination:
        for lemma in sorted(selected):
            raw = (json.dumps(selected[lemma], ensure_ascii=False, sort_keys=True) + "\n").encode()
            destination.write(raw)
            digest.update(raw)
    return {"schema": 1, "groups": len(selected),
            "source_counts": dict(sorted(counts.items())),
            "input_sha256": {name: value.hexdigest() for name, value in digests.items()},
            "private_output_sha256": digest.hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--triage", required=True, type=Path)
    parser.add_argument("--headers", required=True, type=Path)
    parser.add_argument("--lexica", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected", type=int)
    args = parser.parse_args()
    print(json.dumps(prepare(args.triage, args.headers, args.lexica,
                             args.output, args.expected), sort_keys=True))


if __name__ == "__main__":
    main()
