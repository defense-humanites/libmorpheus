#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Record narrow, private decisions for the Greek entry-level review.

The source and the decision ledger contain lexicon-derived spellings. Keep
both outside the repository; stdout contains aggregate counts and hashes only.
"""

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def stem_lines(blocks):
    return [line for block in blocks for line in block]


def without_marker(line, marker):
    # Restrict the comparison to the stem token, never tags or morphological
    # labels. The colon prefix is also preserved.
    token = line.split(maxsplit=1)[0]
    if token[:4] not in (":no:", ":aj:", ":wd:"):
        raise ValueError("unexpected stem record tag")
    return token[:4] + token[4:].replace(marker, "") + line[len(token):]


def disposition(row):
    candidate = stem_lines(row["candidate_blocks"])
    witness = stem_lines(row["witness_blocks"])
    if (row["category"] == "same_tags_and_labels" and
            any("-" in line.split(maxsplit=1)[0] for line in candidate) and
            sorted(without_marker(line, "-") for line in candidate) == sorted(witness)):
        return ("stem_separator_only", "indexstems strips the stem separator "
                "before storing the stem; preserve both source records")
    if (row["category"] == "beta_code_diacritics" and
            any("+" in line.split(maxsplit=1)[0] for line in candidate) and
            sorted(without_marker(line, "+") for line in candidate) == sorted(witness)):
        return ("diaeresis_needs_analysis", "the lookup key loses diaeresis, "
                "but the marked stem can retain it; compare analyzer behavior")
    return ("manual_review", "inspect source entry, importer rule and analyzer behavior")


def arbitrate(source, output):
    target = output.resolve()
    if target == REPO or REPO in target.parents:
        raise ValueError("decision ledger must be outside the repository")
    if target == source.resolve():
        raise ValueError("decision ledger must differ from its input")
    rows = []
    digest = hashlib.sha256()
    with source.open("rb") as data:
        for raw in data:
            digest.update(raw)
            row = json.loads(raw)
            decision, reason = disposition(row)
            rows.append({"lemma": row["lemma"], "category": row["category"],
                         "disposition": decision, "reason": reason})
    if len({row["lemma"] for row in rows}) != len(rows):
        raise ValueError("duplicate lemma in private review")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(target, flags, 0o600)
    written = hashlib.sha256()
    with os.fdopen(fd, "wb") as ledger:
        for row in rows:
            raw = (json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n").encode()
            ledger.write(raw)
            written.update(raw)
    return {"schema": 1, "input_sha256": digest.hexdigest(),
            "ledger_sha256": written.hexdigest(), "groups": len(rows),
            "by_disposition": dict(sorted(Counter(row["disposition"] for row in rows).items()))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(arbitrate(args.review, args.output), sort_keys=True))


if __name__ == "__main__":
    main()
