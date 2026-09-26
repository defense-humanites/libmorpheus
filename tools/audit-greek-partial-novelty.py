#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Count genuinely additional Greek partial-overlap lines without disclosing them.

The candidate, original trial, TEI headers and curated witness stay private.
Only aggregate counts are printed; source-key matching is diagnostic.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import runpy


read_stems = runpy.run_path(str(Path(__file__).with_name("audit-lexical-stems.py")))["read_stems"]


def source_headers(path):
    headers = defaultdict(list)
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for raw in source:
            digest.update(raw)
            line = raw.decode("utf-8")
            row = json.loads(line)
            if row["projection_error"] is None and row["lemma"]:
                headers[row["lemma"]].append(row["fields"])
    return headers, digest.hexdigest()


def audit(candidate, original, baseline, headers):
    produced, produced_meta = read_stems(candidate)
    previous, previous_meta = read_stems(original)
    reference, reference_meta = read_stems(baseline)
    source, source_digest = source_headers(headers)
    counts = {"candidate": Counter(), "reference": Counter()}
    for lemma in produced.keys() & reference.keys():
        left, right = produced[lemma], reference[lemma]
        if not (left & right) or left == right:
            continue
        for side, excess, opposite in (("candidate", left - right, right),
                                       ("reference", right - left, left)):
            novel = {line: n for line, n in excess.items() if line not in opposite}
            if not novel:
                continue
            report = counts[side]
            report["lemma_groups"] += 1
            report["novel_records"] += sum(novel.values())
            report["records_in_original_candidate"] += sum(
                min(n, previous.get(lemma, {}).get(line, 0)) for line, n in novel.items())
            entries = source.get(lemma, [])
            report["projected_key_matches_" + ("zero" if not entries else
                                               "one" if len(entries) == 1 else "multiple")] += 1
            report["any_multiple_orth"] += any(
                sum(field["name"] == "orth" for field in fields) > 1 for fields in entries)
            for tag in ("gen", "itype"):
                report["any_" + tag] += any(
                    field["name"] == tag for fields in entries for field in fields)
    keys = ("lemma_groups", "novel_records", "records_in_original_candidate",
            "projected_key_matches_zero", "projected_key_matches_one",
            "projected_key_matches_multiple", "any_multiple_orth", "any_gen", "any_itype")
    return {"schema": 1, "scope": "aggregate diagnostic; projected key match is not provenance",
            "input_sha256": {"candidate": produced_meta["sha256"],
                             "original": previous_meta["sha256"],
                             "reference": reference_meta["sha256"],
                             "headers": source_digest},
            "partial_novelty": {side: {key: counts[side][key] for key in keys}
                                for side in ("candidate", "reference")}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--original-candidate", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--headers", type=Path, required=True)
    args = parser.parse_args()
    if len({path.resolve() for path in vars(args).values()}) != 4:
        parser.error("all four inputs must be different files")
    print(json.dumps(audit(args.candidate, args.original_candidate,
                           args.baseline, args.headers), sort_keys=True))


if __name__ == "__main__":
    main()
