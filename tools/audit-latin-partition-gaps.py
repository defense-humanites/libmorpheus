#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit the research Latin partition against curated lemma inventories.

The witnesses are used only for this aggregate diagnostic, never to select
the partition. Input headers contain lexicon-derived data; print no entries.
"""

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import runpy


PARTITION = runpy.run_path(str(Path(__file__).with_name("partition-lexical-latin.py")))


def lemmas(path):
    with path.open(encoding="utf-8", errors="replace") as source:
        return {raw[4:].strip() for raw in source if raw.startswith(":le:")}


def field_profile(fields):
    names = {field["name"] for field in fields}
    if names == {"orth"}:
        return "orth_only"
    if names == {"orth", "itype"}:
        return "orth_and_itype_only"
    return "other"


def audit(headers, nominal_baseline, verbal_baseline):
    nominal = lemmas(nominal_baseline)
    verbal = lemmas(verbal_baseline)
    table = defaultdict(Counter)
    profiles = defaultdict(Counter)
    with headers.open(encoding="utf-8") as source:
        for raw in source:
            record = json.loads(raw)
            if record.get("schema") != 1:
                raise ValueError("unsupported lexical header schema")
            category, _ = PARTITION["classify"](record)
            if category == "skipped":
                continue
            lemma = record["lemma"]
            in_nominal = lemma in nominal
            in_verbal = lemma in verbal
            inventory = ("both" if in_nominal and in_verbal else
                         "nominal_only" if in_nominal else
                         "verbal_only" if in_verbal else "neither")
            table[category][inventory] += 1
            if category == "nominal" and inventory in ("nominal_only", "verbal_only"):
                profiles[inventory][field_profile(record["fields"])] += 1
    return {"schema": 1, "units": "projected source entries; not unique lemmas",
            "partition_by_inventory": {kind: dict(sorted(counts.items()))
                                       for kind, counts in sorted(table.items())},
            "nominal_field_profiles": {kind: dict(sorted(counts.items()))
                                       for kind, counts in sorted(profiles.items())}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headers", type=Path, required=True)
    parser.add_argument("--nominal-baseline", type=Path, required=True)
    parser.add_argument("--verbal-baseline", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.headers, args.nominal_baseline, args.verbal_baseline),
                     sort_keys=True))


if __name__ == "__main__":
    main()
