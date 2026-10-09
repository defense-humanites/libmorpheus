#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check generated Greek surfaces against their own expected analyzer lemmas.

Input generation TSV uses LEMMA headers followed by surface, lemma and nine
comma-separated integer grammatical fields. Only quantity marks are stripped
for lookup. An unrelated homograph does not satisfy an expected lemma.
All individual forms and lemmas stay private; only counts and hashes print.
"""

import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import re


SCRIPT = Path(__file__).resolve().parent / "compare-greek-cruncher-readings.py"
spec = importlib.util.spec_from_file_location("reading_comparison", SCRIPT)
comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)


def read_generated(path):
    expected = {}
    lemmas = set()
    current = None
    rows = 0
    for line in path.read_text(encoding="ascii").splitlines():
        if line.startswith("LEMMA\t"):
            current = line[6:]
            if (not current or current in lemmas or
                    any(ord(c) < 33 or ord(c) > 126 for c in current)):
                raise ValueError("invalid or duplicate generation lemma header")
            lemmas.add(current)
            continue
        fields = line.split("\t")
        if (current is None or len(fields) != 3 or fields[1] != current or
                not re.fullmatch(r"-?\d+(?:,-?\d+){8}", fields[2])):
            raise ValueError("invalid generated row or lemma relationship")
        surface = fields[0].translate(str.maketrans("", "", "_^"))
        if not surface or any(ord(c) < 33 or ord(c) > 126 for c in surface):
            raise ValueError("invalid generated surface")
        expected.setdefault(surface, set()).add(current)
        rows += 1
    if not lemmas or not rows:
        raise ValueError("empty generation output")
    return expected, lemmas, rows


def audit(generated, forms_path, analysis):
    expected, lemmas, rows = read_generated(generated)
    forms = comparison.read_forms(forms_path)
    if set(expected) - set(forms):
        raise ValueError("query wordlist omits generated surfaces")
    readings = comparison.read_output(analysis, forms)
    counts = Counter(generated_rows=rows, generation_lemmas=len(lemmas),
                     generated_surfaces=len(expected), query_surfaces=len(forms),
                     expected_lemma_pairs=sum(map(len, expected.values())),
                     matched_lemma_pairs=0, missing_lemma_pairs=0,
                     absent_generated_surfaces=0, homograph_only_surfaces=0,
                     partially_covered_surfaces=0)
    covered_lemmas = set()
    for surface, targets in expected.items():
        found = {r[2] for r in readings.get(surface, [])}
        matched = targets & found
        covered_lemmas.update(matched)
        counts["matched_lemma_pairs"] += len(matched)
        counts["missing_lemma_pairs"] += len(targets - found)
        if not found:
            counts["absent_generated_surfaces"] += 1
        elif not matched:
            counts["homograph_only_surfaces"] += 1
        elif targets - found:
            counts["partially_covered_surfaces"] += 1
    counts["lemmas_without_covered_surface"] = len(lemmas - covered_lemmas)
    return {"schema": 1, "mode": "generated surfaces; quantity stripped; exact lemma match",
            "counts": dict(sorted(counts.items())),
            "generated_sha256": comparison.digest(generated),
            "forms_sha256": comparison.digest(forms_path),
            "analysis_sha256": comparison.digest(analysis)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated", required=True, type=Path)
    parser.add_argument("--forms", required=True, type=Path)
    parser.add_argument("--analysis", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.generated, args.forms, args.analysis), sort_keys=True))


if __name__ == "__main__":
    main()
