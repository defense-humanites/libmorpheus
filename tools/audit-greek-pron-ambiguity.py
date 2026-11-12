#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Count bare long-vowel pron evidence in the pinned LSJ TEI edition.

Only aggregate counts and a combined input digest are printed. This audit
does not infer which repeated vowel a bare pronunciation marks.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess

from lxml import etree


REVISION = "56061ca127f4a2844980baffc5f2b6d1332897b3"
SUBDIR = Path("CTS_XML_TEI/perseus/pdllex/grc/lsj")
BARE_LONG = re.compile(r"\[([aehiouw])_\]")


def count_tree(root):
    counts = Counter()
    for entry in root.xpath("//*[self::entryFree or self::entry]"):
        orth = entry.find("orth")
        if orth is None:
            continue
        spelling = "".join(orth.itertext())
        letters = re.sub(r"[^A-Za-z]", "", spelling).lower()
        for pron in entry.findall("pron"):
            match = BARE_LONG.fullmatch("".join(pron.itertext()).strip())
            if match is None:
                continue
            vowel = match.group(1)
            if letters.count(vowel) < 2:
                continue
            counts["repeated_vowel_bare_long_pron"] += 1
            if re.search(vowel + r"_", spelling, flags=re.IGNORECASE):
                counts["same_vowel_already_long_in_first_orth"] += 1
            if re.search(vowel + r"\^", spelling, flags=re.IGNORECASE):
                counts["same_vowel_short_in_first_orth"] += 1
    return counts


def audit(lexica):
    revision = subprocess.check_output(
        ["git", "-C", str(lexica), "rev-parse", "HEAD"], text=True).strip()
    if revision != REVISION:
        raise ValueError("LSJ checkout differs from the pinned revision")
    directory = lexica / SUBDIR
    files = sorted(directory.glob("grc.lsj.perseus-eng*.xml"),
                   key=lambda path: int(path.stem.rsplit("eng", 1)[1]))
    if len(files) != 27 or [int(path.stem.rsplit("eng", 1)[1]) for path in files] != list(range(1, 28)):
        raise ValueError("incomplete LSJ TEI edition")
    dirty = subprocess.check_output(
        ["git", "-C", str(lexica), "status", "--porcelain", "--", str(SUBDIR)],
        text=True)
    if dirty:
        raise ValueError("selected LSJ files differ from the pinned revision")
    counts = Counter()
    digest = hashlib.sha256()
    for path in files:
        raw = path.read_bytes()
        digest.update(raw)
        parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True)
        counts.update(count_tree(etree.fromstring(raw, parser)))
    return {"schema": 1, "revision": revision, "files": len(files),
            "input_sha256": digest.hexdigest(),
            "counts": {name: counts[name] for name in (
                "repeated_vowel_bare_long_pron", "same_vowel_already_long_in_first_orth",
                "same_vowel_short_in_first_orth")}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lexica", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.lexica), sort_keys=True))


if __name__ == "__main__":
    main()
