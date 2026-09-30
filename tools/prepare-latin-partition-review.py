#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Locate source evidence omitted by the Latin initial-header projection.

Curated inventories select a private diagnostic dossier of verbal-only
witness lemmas classified nominal. They never select replacement stems.
Only direct grammatical fields of the first sense contribute source signals;
quoted or later-sense grammatical labels are not inherited as header fields.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import subprocess

from lxml import etree


REPO = Path(__file__).resolve().parents[1]
SOURCE = Path("CTS_XML_TEI/perseus/pdllex/lat/ls/lat.ls.perseus-eng1.xml")
REVISION = "56061ca127f4a2844980baffc5f2b6d1332897b3"


def sibling(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "tools" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


partition = sibling("partition-lexical-latin")
projection = sibling("reconstruct-lexical-exports")


def initial_sense_fields(entry):
    first = entry.find("sense")
    if first is None:
        return []
    fields = []
    for child in first:
        raw = " ".join("".join(child.itertext()).split())
        italic_label = (child.tag == "hi" and child.get("rend") == "ital" and
                        re.match(r"v\. (?:a\.|n\.|dep\.|freq\.|inch\.)", raw))
        if child.tag not in {"itype", "pos", "gen", "quant"} and not italic_label:
            continue
        if any(isinstance(n, etree._Entity) for n in child.iter()):
            value = None
        else:
            value = projection.normalize(raw, "Latin")
        fields.append({"name": "italic_verbal_label" if italic_label else child.tag,
                       "value": raw, "projection": value,
                       "location": "first-sense/direct-child"})
    return fields


def signal(fields):
    valid = [f for f in fields if f["projection"] is not None]
    if any(f["name"] == "pos" and f["projection"].startswith("v.") for f in valid):
        return "first_sense_verbal_pos"
    types = [f["projection"] for f in valid if f["name"] == "itype"]
    if any(partition.VERBAL_ITYPE.search(value) for value in types):
        return "first_sense_conjugation_itype"
    if any(value in partition.HISTORICAL_VERB_TYPES for value in types):
        return "first_sense_historical_itype"
    if any(f["name"] == "italic_verbal_label" for f in valid):
        return "first_sense_italic_verbal_label"
    return "no_first_sense_verbal_signal"


def analyze(headers, entries, nominal, verbal):
    table = defaultdict(Counter)
    dossier = []
    seen = set()
    for raw in headers.read_bytes().splitlines(keepends=True):
        row = json.loads(raw)
        if row.get("schema") != 1:
            raise ValueError("unsupported lexical header schema")
        source_id = row["id"]
        if source_id in seen:
            raise ValueError("duplicate source entry ID")
        seen.add(source_id)
        if row["source"] != SOURCE.name or source_id not in entries:
            raise ValueError("header does not join the selected Latin source")
        entry = entries[source_id]
        if row["source_key"] != entry.get("key"):
            raise ValueError("source key mismatch")
        if partition.classify(row)[0] != "nominal":
            continue
        lemma = row["lemma"]
        inventory = ("both" if lemma in nominal and lemma in verbal else
                     "verbal_only" if lemma in verbal else
                     "nominal_only" if lemma in nominal else "neither")
        fields = initial_sense_fields(entry)
        kind = signal(fields)
        table[inventory][kind] += 1
        if inventory == "verbal_only":
            dossier.append({"lemma": lemma, "source_id": source_id,
                            "source_key": row["source_key"], "source": row["source"],
                            "header_row_sha256": hashlib.sha256(raw).hexdigest(),
                            "projected_fields": row["fields"],
                            "first_sense_fields": fields, "source_signal": kind,
                            "references": [{"text": " ".join("".join(n.itertext()).split()),
                                            "attributes": dict(n.attrib),
                                            "direct": n.getparent() is entry}
                                           for n in entry.iter("ref")],
                            "scope": "source-evidence dossier; no partition decision"})
    return dict(table), dossier


def prepare(headers, lexica, nominal_path, verbal_path, private_output=None, expected=None):
    revision = subprocess.check_output(
        ["git", "-C", str(lexica), "rev-parse", "HEAD"], text=True).strip()
    if revision != REVISION:
        raise ValueError("Latin source checkout differs from pinned revision")
    if subprocess.check_output(["git", "-C", str(lexica), "status", "--porcelain", "--",
                                str(SOURCE)], text=True):
        raise ValueError("selected Latin source differs from pinned revision")
    source = lexica / SOURCE
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True,
                             huge_tree=True)
    tree = etree.parse(str(source), parser)
    entries = {}
    for entry in tree.iter("entryFree"):
        key = entry.get("id")
        if not key or key in entries:
            raise ValueError("invalid or duplicate Latin source entry ID")
        entries[key] = entry
    def lemmas(path):
        return {line[4:].strip() for line in path.read_text().splitlines()
                if line.startswith(":le:")}
    table, rows = analyze(headers, entries, lemmas(nominal_path), lemmas(verbal_path))
    if expected is not None and len(rows) != expected:
        raise ValueError("unexpected private dossier size")
    payload = b"".join((json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n").encode()
                       for row in rows)
    if private_output is not None:
        target = private_output.resolve()
        if target == REPO or REPO in target.parents or target in {
                p.resolve() for p in [headers, source, nominal_path, verbal_path]}:
            raise ValueError("private dossier must be outside repository and inputs")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        with os.fdopen(os.open(target, flags, 0o600), "wb") as output:
            output.write(payload)
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()
    return {"schema": 1, "scope": "first-sense source evidence; no partition change",
            "source_revision": revision, "dossier_entries": len(rows),
            "nominal_by_inventory_and_source_signal": {
                k: dict(sorted(v.items())) for k, v in sorted(table.items())},
            "input_sha256": {"headers": digest(headers), "Latin_TEI": digest(source),
                             "nominal": digest(nominal_path), "verbal": digest(verbal_path)},
            "dossier_sha256": hashlib.sha256(payload).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headers", required=True, type=Path)
    parser.add_argument("--lexica", required=True, type=Path)
    parser.add_argument("--nominal-baseline", required=True, type=Path)
    parser.add_argument("--verbal-baseline", required=True, type=Path)
    parser.add_argument("--private-output", type=Path)
    parser.add_argument("--expected", type=int)
    args = parser.parse_args()
    print(json.dumps(prepare(args.headers, args.lexica, args.nominal_baseline,
                             args.verbal_baseline, args.private_output, args.expected),
                     sort_keys=True))


if __name__ == "__main__":
    main()
