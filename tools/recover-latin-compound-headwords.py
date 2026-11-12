#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stage explicit full Latin compound spellings lost at the first space."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("recovery", REPO / "tools/recover-latin-initial-sense.py")
recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)
review = recovery.review
COMPOUND = re.compile(r"[A-Za-z_^]+(?: *- *[A-Za-z_^]+)+")


def repair(row, entry):
    if row.get("projection_error") is not None:
        return row, "unprojected"
    orth = entry.find("orth")
    field = next((f for f in row["fields"] if f["name"] == "orth"), None)
    if orth is None or field is None:
        return row, "no_orthography"
    if any(isinstance(n, review.etree._Entity) for n in orth.iter()):
        return row, "unsupported_orthography"
    raw = " ".join("".join(orth.itertext()).split())
    projected = review.projection.normalize(raw, "Latin")
    if field["value"] != raw or field["projection"] != projected:
        raise ValueError("first orthography differs from pinned source")
    if (orth.get("extent") != "full" or projected is None or
            " " not in projected or not COMPOUND.fullmatch(projected)):
        return row, "unchanged"
    headword = projected.replace(" ", "")
    lemma = headword.translate(str.maketrans("", "", "_^-")).replace("#", "")
    # A homograph number belongs only to the same complete spelling. A short
    # source key must not number a different, fully spelled compound lemma.
    key = re.fullmatch(r"(.+?)([1-9])?", row["source_key"])
    if key and key.group(2) and key.group(1) == lemma:
        headword += "#" + key.group(2)
        lemma += "#" + key.group(2)
    return dict(row, headword=headword, lemma=lemma,
                compound_recovery={"scope": "explicit first full orthography",
                                   "original_header_sha256": hashlib.sha256(
                                       recovery.render(row).encode()).hexdigest()}), "recovered"


def stage(headers, lemmata, lexica, output, expected=None):
    target = output.resolve()
    inputs = [p.resolve() for p in (headers, lemmata, lexica)]
    if target == REPO or REPO in target.parents or any(target == p or target in p.parents or p in target.parents for p in inputs):
        raise ValueError("private stage must be outside repository and inputs")
    entries, source, revision = review.load_entries(lexica)
    lines = iter(lemmata.read_text().splitlines(keepends=True))
    rows, candidates, counts, seen = [], [], Counter(), set()
    for raw in headers.read_bytes().splitlines():
        row = json.loads(raw)
        key = row.get("id")
        if (row.get("schema") != 1 or row.get("source") != review.SOURCE.name or
                key in seen or key not in entries or row.get("source_key") != entries[key].get("key")):
            raise ValueError("invalid source join")
        seen.add(key)
        if row.get("projection_error") is None:
            line = next(lines, None)
            if line is None or line.rstrip("\r\n") != recovery.render(row).rstrip("\n"):
                raise ValueError("projected header stream mismatch")
            updated, kind = repair(row, entries[key])
            candidates.append(recovery.render(updated) if updated is not row else line)
            row = updated
        else:
            kind = "unprojected"
        counts[kind] += 1
        rows.append(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    if next(lines, None) is not None:
        raise ValueError("projected stream is longer than header inventory")
    if expected is not None and counts["recovered"] != expected:
        raise ValueError("unexpected recovered compound count")
    payloads = {"Latin.headers.jsonl": "".join(rows).encode(), "Latin.lemmata": "".join(candidates).encode()}
    report = {"schema": 1, "scope": "source-only full compounds; separate unqualified trial",
              "source_revision": revision, "source_rows": len(rows), "by_reason": dict(counts),
              "input_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (headers, lemmata, source)},
              "output_sha256": {k: hashlib.sha256(v).hexdigest() for k, v in payloads.items()}}
    payloads["report.json"] = (json.dumps(report, sort_keys=True, indent=2) + "\n").encode()
    target.mkdir(mode=0o700)
    for name, data in payloads.items():
        with os.fdopen(os.open(target / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as stream:
            stream.write(data)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("headers", "lemmata", "lexica", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--expected", type=int)
    args = parser.parse_args()
    print(json.dumps(stage(args.headers, args.lemmata, args.lexica, args.output, args.expected), sort_keys=True))


if __name__ == "__main__":
    main()
