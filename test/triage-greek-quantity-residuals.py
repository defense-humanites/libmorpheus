#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify that quantity triage reads stem tokens, not paradigm labels."""

import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "tools/triage-greek-quantity-residuals.py"
spec = importlib.util.spec_from_file_location("quantity_triage", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class QuantityTriageTest(unittest.TestCase):
    def test_stem_only_and_position_categories(self):
        self.assertEqual(module.category(":no:stem os_ou", ":no:ste_m os_ou"),
                         "candidate_unmarked")
        self.assertEqual(module.category(":no:ste_m os_ou", ":no:stem os_ou"),
                         "witness_unmarked")
        self.assertEqual(module.category(":no:ste_m os_ou", ":no:st_em os_ou"),
                         "different_positions")
        self.assertEqual(module.category(":no:ste_m os_ou", ":no:ste__m os_ou"),
                         "same_positions_different_marks_or_multiplicity")

    def test_private_output_and_quantity_only_filter(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            left = Path(directory) / "left"
            right = Path(directory) / "right"
            output = Path(directory) / "private.jsonl"
            left.write_text(":le:a\n:no:stem os_ou\n:le:b\n:no:ste_m os_ou\n")
            right.write_text(":le:a\n:no:ste_m os_ou\n:le:b\n:aj:st_em os_h_on\n")
            report = module.triage(left, right, output)
            self.assertEqual(report["by_category"], {"candidate_unmarked": 1})
            self.assertEqual(report["by_candidate_tag"], {":no:": 1})
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            self.assertEqual(len(output.read_text().splitlines()), 1)
            with self.assertRaises(FileExistsError):
                module.triage(left, right, output)
            with self.assertRaises(ValueError):
                module.triage(left, right, SCRIPT.parent / "forbidden.jsonl")


if __name__ == "__main__":
    unittest.main()
