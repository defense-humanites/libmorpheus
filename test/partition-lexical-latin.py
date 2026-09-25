#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check independent header signals and alignment with projected rows."""

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "tools/partition-lexical-latin.py"
spec = importlib.util.spec_from_file_location("partition_latin", SCRIPT)
partition = importlib.util.module_from_spec(spec)
spec.loader.exec_module(partition)


def record(lemma, headword, fields, error=None):
    return {"schema": 1, "lemma": lemma, "headword": headword,
            "fields": [{"name": name, "projection": value} for name, value in fields],
            "projection_error": error}


class PartitionTest(unittest.TestCase):
    def test_signals_do_not_depend_on_reference_lemmas(self):
        samples = [
            (record("amo", "a^mo", [("pos", "v. a.")]), "verbal"),
            (record("curro", "curro", [("itype", "cu^curri, 3")]), "verbal"),
            (record("bonus", "bonus", [("itype", "a, um")]), "nominal"),
            (record("amatus", "ama_tus", [("pos", "P. a.")]), "participial"),
        ]
        for entry, expected in samples:
            self.assertEqual(partition.classify(entry)[0], expected)

    def test_input_alignment_is_fail_closed(self):
        with TemporaryDirectory() as directory:
            directory = Path(directory)
            headers = directory / "headers"
            lemmata = directory / "lemmata"
            headers.write_text(json.dumps(record("amo", "a^mo", [("pos", "v. a.")])) + "\n", encoding="utf-8")
            lemmata.write_text("bonus \t<itype>a, um</itype>\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "out of order"):
                partition.run(headers, lemmata, directory / "output")


if __name__ == "__main__":
    unittest.main()
