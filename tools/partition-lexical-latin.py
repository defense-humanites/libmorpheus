#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Research-only partition of projected Lewis & Short header records.

The historical vtags selector is missing. This classifier uses TEI header
fields only, never the curated stem output, and records its own decisions.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


# See src/gkdict/conj1.l and src/gkdict/latvb.l. A final conjugation number
# or one of these infinitive forms is positive evidence for a verb. Isolated
# principal parts without a number remain unclassified by this rule.
VERBAL_ITYPE = re.compile(r"(?:^|,\s*)(?:[1-4]|a_re|e_re|e\^re|i_re|a_ri|i_ri)$")


def classify(record):
    if record.get("projection_error"):
        return "skipped", "projection-error"
    fields = record["fields"]
    parts_of_speech = [field["projection"] for field in fields if field["name"] == "pos"]
    types = [field["projection"] for field in fields if field["name"] == "itype"]
    if any(value.startswith("v.") for value in parts_of_speech):
        return "verbal", "verbal-pos"
    if any(VERBAL_ITYPE.search(value or "") for value in types):
        return "verbal", "conjugation-itype"
    if "P. a." in parts_of_speech:
        return "participial", "participial-pos"
    return "nominal", "no-verbal-header-evidence"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(headers, lemmata, output):
    if output.exists():
        raise ValueError(f"stage already exists: {output}")
    output.mkdir(parents=True)
    decisions = Counter()
    counts = Counter()
    with headers.open(encoding="utf-8") as records, lemmata.open(encoding="utf-8") as lines, \
         (output / "nominal.lemmata").open("w", encoding="utf-8") as nominal, \
         (output / "verbal.lemmata").open("w", encoding="utf-8") as verbal, \
         (output / "participial.lemmata").open("w", encoding="utf-8") as participial:
        streams = {"nominal": nominal, "verbal": verbal, "participial": participial}
        for row in records:
            record = json.loads(row)
            if record.get("schema") != 1:
                raise ValueError("unsupported lexical header schema")
            category, reason = classify(record)
            counts[category] += 1
            decisions[reason] += 1
            if category == "skipped":
                continue
            projected_line = next(lines, None)
            if projected_line is None:
                raise ValueError("candidate stream is shorter than projected header inventory")
            if not projected_line.startswith(record["headword"] + " \t"):
                raise ValueError("candidate stream and header inventory are out of order")
            streams[category].write(projected_line)
        if next(lines, None) is not None:
            raise ValueError("candidate stream is longer than projected header inventory")
    report = {"schema": 1,
              "status": "research-only; vtags not recovered or reproduced",
              "input_sha256": {"headers": sha256(headers), "lemmata": sha256(lemmata)},
              "categories": dict(sorted(counts.items())),
              "decision_reasons": dict(sorted(decisions.items())),
              "output_sha256": {kind: sha256(output / f"{kind}.lemmata")
                                for kind in ("nominal", "verbal", "participial")}}
    (output / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"categories": report["categories"], "decision_reasons": report["decision_reasons"]}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headers", type=Path, required=True)
    parser.add_argument("--lemmata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        run(args.headers, args.lemmata, args.output)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
