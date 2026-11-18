#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Validate the pinned historical LISTALL archive and stage private literal forms."""

import argparse
from collections import Counter
import hashlib
import io
import json
import os
from pathlib import Path
import zipfile

REPO = Path(__file__).resolve().parents[1]
URL = "https://downloads.sourceforge.net/project/wwwords/Whitaker/listall.zip"
ARCHIVE_SHA256 = "ea0b45df1271870b51befa882798c81cae158e8f6ebfbd748f76fbeeb692191d"
MEMBER_SHA256 = "6b557b50fc333cddb17082a6eb71fb87029d095738672a3cd308f7161073769b"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inspect(payload, archive_sha256=ARCHIVE_SHA256, member_sha256=MEMBER_SHA256):
    if len(payload) > 8_000_000 or digest(payload) != archive_sha256:
        raise ValueError("LISTALL archive differs from pinned bytes")
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = archive.infolist()
        if (len(members) != 1 or members[0].filename != "listall" or
                members[0].file_size > 16_000_000 or members[0].flag_bits & 1):
            raise ValueError("unexpected LISTALL archive member")
        raw = archive.read(members[0])
    if digest(raw) != member_sha256:
        raise ValueError("LISTALL member differs from pinned bytes")
    forms = raw.splitlines()
    if not forms or any(not w or any(b < 33 or b > 126 for b in w) for w in forms):
        raise ValueError("LISTALL forms must be nonempty literal ASCII tokens")
    counts = Counter(forms)
    distinct = b"".join(word + b"\n" for word in sorted(counts))
    report = {
        "schema": 1, "source_url": URL,
        "scope": "historical external probe; no spelling normalization",
        "archive_sha256": digest(payload), "member_sha256": digest(raw),
        "distinct_sha256": digest(distinct), "input_bytes": len(raw),
        "input_lines": len(forms), "distinct_forms": len(counts),
        "duplicate_lines": len(forms) - len(counts),
        "crlf_lines": raw.count(b"\r\n"),
        "sorted_literal_input": forms == sorted(forms),
        "maximum_token_bytes": max(map(len, forms)),
    }
    return raw, distinct, report


def prepare(archive, output):
    output = output.resolve()
    archive = archive.resolve()
    if output == REPO or REPO in output.parents or output == archive or output in archive.parents:
        raise ValueError("private stage must be outside repository and archive")
    raw, distinct, report = inspect(archive.read_bytes())
    output.mkdir(mode=0o700)  # refuse an existing stage before any write
    for name, data in {
        "LISTALL.original.txt": raw,
        "LISTALL.distinct-literal.txt": distinct,
        "report.json": (json.dumps(report, sort_keys=True, indent=2) + "\n").encode(),
    }.items():
        with os.fdopen(os.open(output / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as stream:
            stream.write(data)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.archive, args.output), sort_keys=True))


if __name__ == "__main__":
    main()
