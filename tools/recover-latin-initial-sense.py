#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stage a source-only Latin first-sense verbal-header recovery experiment.

The current projection remains the baseline. Only nominal-trial records
with an explicit direct first-sense verbal POS or styled verbal label are
augmented. No curated inventory chooses a record. This does not reconstruct
historical vtags, supply cross-reference paradigms or change public stems.
"""

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "latin_source_review", REPO / "tools/prepare-latin-partition-review.py")
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


def augment(row, entry):
    if review.partition.classify(row)[0] != "nominal":
        return row, "unchanged"
    extra = review.initial_sense_fields(entry)
    kind = review.signal(extra)
    if kind not in {"first_sense_verbal_pos", "first_sense_italic_verbal_label"}:
        return row, "no_explicit_verbal_label"
    if any(field["projection"] is None for field in extra):
        return row, "withheld_unsupported_field"
    fields = [dict(field, name="pos" if field["name"] == "italic_verbal_label"
                   else field["name"], type=None) for field in extra]
    result = dict(row, fields=row["fields"] + fields,
                  source_recovery={"mode": kind, "location": "first-sense/direct-child"})
    if review.partition.classify(result)[0] != "verbal":
        raise ValueError("recovered verbal label does not select verbal trial")
    return result, kind


def render(row):
    first = next(i for i, field in enumerate(row["fields"]) if field["name"] == "orth")
    fragments = []
    for i, field in enumerate(row["fields"]):
        if i == first:
            continue
        name = field["name"]
        tag = "<orth type=alt>" if name == "orth" and field.get("type") == "alt" else f"<{name}>"
        value = field["projection"].replace("&", "&amp;").replace("<", "&lt;")
        fragments.append(f"{tag}{value}</{name}>")
    return row["headword"] + " \t" + "\t".join(fragments) + "\n"


def recover(headers, lemmata, lexica, output, expected=None):
    target = output.resolve()
    if (target.exists() or target == REPO or REPO in target.parents or
            target == lexica.resolve() or lexica.resolve() in target.parents):
        raise ValueError("recovery stage must be new and outside source checkouts")
    entries, source, revision = review.load_entries(lexica)
    lines = iter(lemmata.read_text().splitlines(keepends=True))
    header_rows, candidate_rows, counts, seen = [], [], Counter(), set()
    for raw in headers.read_bytes().splitlines(keepends=True):
        row = json.loads(raw)
        if row.get("schema") != 1:
            raise ValueError("unsupported lexical header schema")
        key = row["id"]
        if key in seen or row["source"] != review.SOURCE.name or key not in entries:
            raise ValueError("invalid or duplicate source join")
        seen.add(key)
        entry = entries[key]
        if row["source_key"] != entry.get("key"):
            raise ValueError("source key mismatch")
        if row.get("projection_error") is None:
            line = next(lines, None)
            if line is None or not line.startswith(row["headword"] + " \t"):
                raise ValueError("projected stream does not match header order")
            # Check the entire old header before augmenting it, not just its headword.
            if line.rstrip("\r\n") != render(row).rstrip("\n"):
                raise ValueError("projected header fields differ from supplied stream")
            updated, kind = augment(row, entry)
            counts[kind] += 1
            if updated is not row:
                updated["source_recovery"]["header_row_sha256"] = hashlib.sha256(raw).hexdigest()
                candidate_rows.append(render(updated))
            else:
                candidate_rows.append(line)
            row = updated
        else:
            counts["unprojected"] += 1
        header_rows.append(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
    if next(lines, None) is not None:
        raise ValueError("projected stream is longer than header inventory")
    restored = counts["first_sense_verbal_pos"] + counts["first_sense_italic_verbal_label"]
    if expected is not None and restored != expected:
        raise ValueError("unexpected recovered record count")
    payloads = {"Latin.headers.jsonl": "".join(header_rows).encode(),
                "Latin.lemmata": "".join(candidate_rows).encode()}
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()
    report = {"schema": 1, "status": "source recovery trial; not historical vtags",
              "source_revision": revision, "source_rows": len(header_rows),
              "recovered_records": restored, "by_reason": dict(sorted(counts.items())),
              "input_sha256": {"headers": digest(headers), "lemmata": digest(lemmata),
                               "Latin_TEI": digest(source)},
              "output_sha256": {name: hashlib.sha256(data).hexdigest()
                                for name, data in payloads.items()}}
    # All joins and old candidate rows are validated before creating the stage.
    target.mkdir(parents=True, mode=0o700)
    payloads["report.json"] = (json.dumps(report, sort_keys=True, indent=2) + "\n").encode()
    for name, payload in payloads.items():
        with os.fdopen(os.open(target / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as f:
            f.write(payload)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headers", required=True, type=Path)
    parser.add_argument("--lemmata", required=True, type=Path)
    parser.add_argument("--lexica", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected", type=int)
    args = parser.parse_args()
    print(json.dumps(recover(args.headers, args.lemmata, args.lexica, args.output,
                             args.expected), sort_keys=True))


if __name__ == "__main__":
    main()
