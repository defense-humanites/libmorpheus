#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Apply the historical Greek nominal entity constraints byte for byte."""

from pathlib import Path
import re


def _lines(data: bytes):
    """Split only on LF, like Perl's default input record separator."""
    records = data.split(b"\n")
    for record in records[:-1]:
        yield record + b"\n"
    if records[-1]:
        yield records[-1]


def apply_constraints(entity_path: Path, nominal_paths: list[Path]) -> bytes:
    """Return the nominal stream produced historically by addconstraints.pl.

    The transformation deliberately operates on bytes with C-locale regular
    expression semantics.  This preserves the inherited script's ordering,
    substitutions, and synthetic plural/dual notices without requiring Perl.
    """
    entity_types = {}
    for line in _lines(entity_path.read_bytes()):
        fields = re.split(rb"\s+", line)
        entity_types[fields[0]] = fields[1] if len(fields) >= 2 else b""

    output = bytearray()
    current_lemma = b""
    for path in nominal_paths:
        for original in _lines(path.read_bytes()):
            line = original
            match = re.search(rb":le:(.+)", line)
            if match:
                current_lemma = re.sub(rb"\s+$", b"", match.group(1))

            if (line.startswith(b":no:") and
                    b"person" in entity_types.get(current_lemma, b"") and
                    b"pers_name" not in line):
                line = re.sub(rb"(.+)", rb"\1 pers_name", line, count=1)

            if b"pers_name" in line and not re.search(rb"\bsg", line):
                line = line.replace(b"pers_name", b"pers_name sg")

            output.extend(line)
            if re.search(rb":no.+pers_name", line):
                plural = line.replace(b"pers_name", b"is_group", 1)
                plural = re.sub(rb"\bsg\b", b"pl", plural, count=1)
                output.extend(b":le:" + current_lemma + b"-pl\n")
                output.extend(plural + b"\n" + current_lemma + b"\n")

                dual = re.sub(rb"\bsg\b", b"dual", line, count=1)
                output.extend(b":le:" + current_lemma + b"-pl\n")
                output.extend(dual + b"\n" + current_lemma + b"\n")
    return bytes(output)
