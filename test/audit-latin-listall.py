#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check literal differential cells and the private-output boundary."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "tools/audit-latin-listall.py"
spec = importlib.util.spec_from_file_location("latin_listall", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Analyzer:
    def __init__(self, answers):
        self.answers = answers
        self.calls = []

    def analyze(self, word):
        self.calls.append(word)
        return self.answers[word]


class ListallTest(unittest.TestCase):
    def test_literal_cells_errors_duplicates_and_private_output(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            forms = Path(directory) / "forms.txt"
            output = Path(directory) / "private.jsonl"
            forms.write_bytes(b"est\namat\nignotum\nerrat\nest\n\n")
            left = Analyzer({b"est": (0, 2), b"amat": (0, 0),
                             b"ignotum": (0, 0), b"errat": (6, 0)})
            right = Analyzer({b"est": (0, 3), b"amat": (0, 1),
                              b"ignotum": (0, 0), b"errat": (0, 1)})
            report = module.audit(forms, left, right, output)
            self.assertEqual(report["counts"], {
                "input_lines": 6, "blank_lines": 1, "duplicate_lines": 1,
                "distinct_forms": 4, "recognized_curated__recognized_rebuilt": 1,
                "absent_curated__recognized_rebuilt": 1,
                "absent_curated__absent_rebuilt": 1, "error": 1})
            self.assertEqual(report["status_pairs"], {"0,0": 3, "6,0": 1})
            self.assertEqual(left.calls, [b"est", b"amat", b"ignotum", b"errat"])
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            self.assertEqual(len([json.loads(s) for s in output.read_text().splitlines()]), 4)
            with self.assertRaises(FileExistsError):
                module.audit(forms, left, right, output)

    def test_rejects_private_output_inside_repository_and_nonascii_input(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            forms = Path(directory) / "forms.txt"
            forms.write_bytes(b"amo\ncaf\xc3\xa9\n")
            analyzer = Analyzer({b"amo": (0, 1)})
            with self.assertRaises(ValueError):
                module.audit(forms, analyzer, analyzer, SCRIPT.parent / "forbidden.jsonl")
            with self.assertRaisesRegex(ValueError, "input line 2"):
                module.audit(forms, analyzer, analyzer)


if __name__ == "__main__":
    unittest.main()
