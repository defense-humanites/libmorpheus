#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prepare a private, entry-level Greek residual review outside the repository.

The JSONL output contains lexicon-derived spellings and stems. Never upload it
as a CI artifact, commit it, or print its rows to a public log.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import runpy


REPO = Path(__file__).resolve().parents[1]
STEMS = runpy.run_path(str(Path(__file__).with_name("audit-lexical-stems.py")))
TRIAGE = runpy.run_path(str(Path(__file__).with_name("audit-greek-disjoint-triage.py")))
STEM_TAGS = tuple(STEMS["STEM_TAGS"])


def selected_groups(candidate, baseline):
    left, _ = STEMS["read_stems"](candidate)
    right, _ = STEMS["read_stems"](baseline)
    selected = {}
    for lemma in left.keys() & right.keys():
        produced, witness = left[lemma], right[lemma]
        if not produced or not witness or produced == witness:
            continue
        shared = produced & witness
        if not shared:
            kind = STEMS["spelling_difference"](produced, witness)
            if kind != "quantity_marks_only":
                selected[lemma] = kind
        elif any(line not in witness for line in produced - witness) or any(
                line not in produced for line in witness - produced):
            selected[lemma] = "partial_distinct_line"
    return selected, left, right


def read_blocks(path, selected):
    blocks = defaultdict(list)
    current = None
    with path.open(encoding="utf-8", errors="replace") as source:
        for raw in source:
            line = raw.rstrip("\r\n")
            if line.startswith(":le:"):
                current = line[4:].strip() if line[4:].strip() in selected else None
                if current is not None:
                    blocks[current].append([])
            elif current is not None and line.startswith(STEM_TAGS):
                blocks[current][-1].append(line)
    return blocks


def context(headers, split, selected, candidate):
    by_lemma = defaultdict(list)
    by_split = defaultdict(list)
    adverb_stems = {lemma: {line[4:].split()[0] for line in candidate[lemma]
                            if line.startswith(":wd:")}
                    for lemma in selected}
    surface_to_lemmas = defaultdict(set)
    for lemma, stems in adverb_stems.items():
        for stem in stems:
            surface_to_lemmas[stem].add(lemma)
    with headers.open(encoding="utf-8") as source:
        for raw in source:
            row = json.loads(raw)
            if row["projection_error"] is not None:
                continue
            matches = defaultdict(set)
            if row["lemma"] in selected:
                matches[row["lemma"]].add("source_key")
            if row.get("headword"):
                lemma = TRIAGE["legacy_lemma_spelling"](row["headword"])
                if lemma in selected:
                    matches[lemma].add("first_orth")
            for field in row["fields"]:
                if field["name"] != "orth":
                    continue
                token = field["projection"].split()[0].strip(",;:")
                lemma = TRIAGE["legacy_lemma_spelling"](token)
                if lemma in selected:
                    matches[lemma].add("any_orth")
                for linked in surface_to_lemmas[TRIAGE["projected_surface"](token)]:
                    matches[linked].add("adverb_stem_orth")
            for lemma, reasons in matches.items():
                by_lemma[lemma].append({"match": sorted(reasons), "header": row})
    with split.open(encoding="utf-8", errors="replace") as source:
        for raw in source:
            line = raw.rstrip("\r\n")
            token = line.split(maxsplit=1)
            if not token:
                continue
            lemma = TRIAGE["legacy_lemma_spelling"](token[0])
            matched = {lemma} if lemma in selected else set()
            matched.update(surface_to_lemmas[token[0]])
            for target in matched:
                by_split[target].append(line)
    return by_lemma, by_split


def prepare(candidate, baseline, headers, split, output, original=None):
    target = output.resolve()
    if target == REPO or REPO in target.parents:
        raise ValueError("review output must be outside the repository")
    inputs = [candidate, baseline, headers, split] + ([original] if original else [])
    if target in {path.resolve() for path in inputs}:
        raise ValueError("review output must differ from every input")
    selected, left, right = selected_groups(candidate, baseline)
    candidate_blocks = read_blocks(candidate, selected)
    witness_blocks = read_blocks(baseline, selected)
    original_blocks = read_blocks(original, selected) if original else {}
    source_headers, split_rows = context(headers, split, selected, left)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(target, flags, 0o600)
    digest = hashlib.sha256()
    with os.fdopen(fd, "wb") as result:
        for lemma in sorted(selected):
            row = {"category": selected[lemma], "lemma": lemma,
                   "candidate_blocks": candidate_blocks[lemma],
                   "witness_blocks": witness_blocks[lemma],
                   "source_headers": source_headers[lemma], "split_rows": split_rows[lemma]}
            if original:
                row["original_candidate_blocks"] = original_blocks[lemma]
            raw = (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
            result.write(raw)
            digest.update(raw)
    return {"schema": 1, "scope": "private review file; never publish rows",
            "review_groups": len(selected),
            "by_category": dict(sorted(Counter(selected.values()).items())),
            "output_sha256": digest.hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--headers", type=Path, required=True)
    parser.add_argument("--split", type=Path, required=True)
    parser.add_argument("--original-candidate", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = prepare(args.candidate, args.baseline, args.headers, args.split,
                     args.output, args.original_candidate)
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
