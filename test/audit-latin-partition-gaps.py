#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check that the Latin gap audit counts entries without changing selection."""

import json
from pathlib import Path
import runpy
from tempfile import TemporaryDirectory
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "tools/audit-latin-partition-gaps.py"
audit = runpy.run_path(str(SCRIPT))["audit"]


class PartitionGapTest(unittest.TestCase):
    def test_exclusive_witness_profiles_and_repeated_entries(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            headers = root / "headers"
            nominal = root / "nominal"
            verbal = root / "verbal"
            nominal.write_text(":le:noun\n:no:stem\n", encoding="utf-8")
            verbal.write_text(":le:verb\n:de:stem\n", encoding="utf-8")
            rows = [
                ("noun", [("orth", "noun")]),
                ("verb", [("orth", "verb")]),
                ("verb", [("orth", "verb"), ("itype", "principal parts")]),
                ("verb", [("orth", "verb"), ("pos", "v. a.")]),
                ("unknown", [("orth", "unknown")]),
            ]
            with headers.open("w", encoding="utf-8") as result:
                for lemma, fields in rows:
                    result.write(json.dumps({
                        "schema": 1, "lemma": lemma, "projection_error": None,
                        "fields": [{"name": key, "projection": value}
                                   for key, value in fields]}) + "\n")
            report = audit(headers, nominal, verbal)
            self.assertEqual(report["partition_by_inventory"], {
                "nominal": {"neither": 1, "nominal_only": 1, "verbal_only": 2},
                "verbal": {"verbal_only": 1}})
            self.assertEqual(report["nominal_field_profiles"], {
                "nominal_only": {"orth_only": 1},
                "verbal_only": {"orth_and_itype_only": 1, "orth_only": 1}})


if __name__ == "__main__":
    unittest.main()
