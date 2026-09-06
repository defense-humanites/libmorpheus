#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Isolate failing lemma records in a prepared lexical input; never build indexes.

Successful batches are discarded. Failed batches are bisected at :le: boundaries
until individual failing records are located. This is a diagnostic, not a full
corpus qualification: interactions between records may disappear on subdivision.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(args):
    if args.output.exists():
        raise ValueError("audit output already exists")
    stage, tool, input_path = args.stage.resolve(), args.tool.resolve(), args.input.resolve()
    data = input_path.read_bytes()
    lines = data.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.startswith(b":le:")]
    if not starts or any(line.strip() for line in lines[:starts[0]]):
        raise ValueError("input must start with a lemma (optional blank preamble)")
    starts[0] = 0  # retain the blank preamble byte for byte
    ends = starts[1:] + [len(lines)]
    records = [b"".join(lines[a:b]) for a, b in zip(starts, ends)]
    receipt = stage / "MORPHEUS-STEMLIB-TABLE-OUTPUTS.tsv"
    received = set()
    for row in receipt.read_text().splitlines():
        if not row or row.startswith("#"):
            continue
        name, expected = row.split("\t")
        if not name.startswith(args.language + "/") or ".." in Path(name).parts or name in received:
            raise ValueError("invalid table output receipt")
        received.add(name)
        if digest(stage / name) != expected:
            raise ValueError("table output checksum mismatch: " + name)
    if not received:
        raise ValueError("empty table output receipt")
    inputs = stage / "MORPHEUS-STEMLIB-INPUTS.tsv"
    input_count = 0
    for row in inputs.read_text().splitlines():
        if not row or row.startswith("#"):
            continue
        language, status, kind, name, expected = row.split("\t")
        if (language != args.language or status != "active" or
                Path(name).is_absolute() or ".." in Path(name).parts):
            raise ValueError("invalid table input receipt")
        if digest(stage / language / name) != expected:
            raise ValueError("table input checksum mismatch: " + name)
        input_count += 1
    if not input_count:
        raise ValueError("empty table input receipt")
    report = {"schema": 1, "diagnostic_only": True, "language": args.language,
              "producer": args.producer, "records": len(records), "invocations": 0,
              "sha256": {"input": digest(input_path), "tool": digest(tool),
                         "recipe": digest(Path(__file__)), "tables": digest(receipt),
                         "table_inputs": digest(inputs)},
              "failures": [], "batch_only_failures": []}
    env = dict(os.environ, MORPHLIB=str(stage), LC_ALL="C", LANG="C", TZ="UTC")
    options = ["-L"] if args.language == "Latin" else []
    # Explicit parent avoids platform /tmp restrictions and keeps all disposable
    # indexes away from the staged runtime tree.
    with tempfile.TemporaryDirectory(prefix="lexical-audit-", dir=args.output.resolve().parent) as temporary:
        work = Path(temporary)

        def probe(first, last):
            report["invocations"] += 1
            prepared = work / "input"
            prepared.write_bytes(b"".join(records[first:last]))
            output, sidecar = work / "output", work / "output.lindex"
            command = [str(tool), *options, str(prepared), str(output)]
            if args.producer == "do_conj":
                command.append(str(sidecar))
            result = subprocess.run(command, cwd=stage / args.language, env=env,
                                    capture_output=True, timeout=60)
            for path in [output, sidecar]:
                path.unlink(missing_ok=True)
            if result.returncode == 0:
                return False
            failure = {"first_line": starts[first] + 1, "last_line": ends[last - 1],
                       "exit_code": result.returncode,
                       "diagnostics": result.stderr.decode("utf-8", "replace")
                       .replace(str(work), "<audit>").replace(str(stage), "<stage>")}
            if last - first == 1:
                failure["record"] = first + 1
                failure["lemma"] = next(line[4:].strip().decode("utf-8", "replace")
                                        for line in records[first].splitlines() if line.startswith(b":le:"))
                report["failures"].append(failure)
            else:
                middle = (first + last) // 2
                left = probe(first, middle)
                right = probe(middle, last)
                if not left and not right:
                    report["batch_only_failures"].append(failure)
            return True

        failed = probe(0, len(records))
    # Exclusive creation protects an earlier audit and never emits a production receipt.
    with args.output.open("x") as output:
        json.dump(report, output, indent=2, sort_keys=True)
        output.write("\n")
    return int(failed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--tool", type=Path, required=True)
    parser.add_argument("--producer", choices=["indexnoms", "indexvbs", "do_conj"], required=True)
    parser.add_argument("--language", choices=["Greek", "Latin"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        raise SystemExit(audit(args))
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        parser.exit(2, f"lexical audit: {error}\n")
