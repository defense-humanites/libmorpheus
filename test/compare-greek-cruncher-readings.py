#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check recognition transitions, reading multisets, and private output."""

import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "tools/compare-greek-cruncher-readings.py"
spec = importlib.util.spec_from_file_location("cruncher_readings", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def record(display, lemma, grammar):
    head = display if display == lemma else display + "," + lemma
    return "<NL>N " + head + "  " + grammar + "</NL>"


class ComparisonTest(unittest.TestCase):
    def test_cells_preserve_lemma_grammar_and_duplicate_readings(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            root = Path(directory)
            forms, left, right = [root / name for name in ("forms", "left", "right")]
            forms.write_text("a\nb\nc\nd\ne\nf\ng\n")
            one = record("lemma", "lemma", "masc nom sg")
            other = record("lemma", "lemma", "masc acc sg")
            left.write_text("a\n" + one + "\nc\n" + one + "\nd\n" + one +
                            "\ne\n" + one + "\nf\n" + one + one + "\n")
            right.write_text("a\n" + record("le_mma", "lemma", "masc nom sg") +
                             "\nb\n" + one + "\nd\n" + other + "\ne\n" +
                             one + "\nf\n" + one + "\n")
            output = root / "differences.jsonl"
            report = module.compare(forms, left, right, output)
            self.assertEqual(report["counts"], {
                "distinct_forms": 7, "left_recognized": 5, "right_recognized": 5,
                "left_reading_rows": 6, "right_reading_rows": 5,
                "shared_display_changed": 1, "gained": 1, "lost": 1,
                "shared_readings_changed": 2, "identical": 1, "absent_both": 1})
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            self.assertEqual(len(output.read_text().splitlines()), 5)
            with self.assertRaises(FileExistsError):
                module.compare(forms, left, right, output)
            with self.assertRaises(ValueError):
                module.compare(forms, left, right, SCRIPT.parent / "forbidden.jsonl")

    def test_order_is_irrelevant_within_a_surface_but_headers_are_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            forms, left, right = [root / name for name in ("forms", "left", "right")]
            forms.write_text("a\nb\n")
            x = record("a", "a", "nom sg")
            y = record("a", "b", "acc sg")
            left.write_text("a\n" + x + y + "\n")
            right.write_text("a\n" + y + x + "\n")
            self.assertEqual(module.compare(forms, left, right)["counts"]["identical"], 1)
            right.write_text("b\n" + x + "\na\n" + y + "\n")
            with self.assertRaises(ValueError):
                module.compare(forms, left, right)

    def test_rejects_duplicate_forms_and_malformed_or_unsupported_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            forms, left, right = [root / name for name in ("forms", "left", "right")]
            forms.write_text("a\na\n")
            left.write_text("")
            right.write_text("")
            with self.assertRaises(ValueError):
                module.compare(forms, left, right)
            forms.write_text("a\n")
            for invalid in ("a\n", "a\n<NL>X a  pres</NL>\n",
                            "a\n<NL>N a</NL>\n", "a\n\n"):
                left.write_text(invalid)
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    module.compare(forms, left, right)

    def test_homograph_verbs_and_participles_are_not_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            forms, left, right = [root / name for name in ("forms", "left", "right")]
            forms.write_text("a\n")
            noun = record("a", "a", "nom sg")
            left.write_text("a\n" + noun + "<NL>V b  pres ind act</NL>\n")
            right.write_text("a\n" + noun + "<NL>P b  pres part act</NL>\n")
            report = module.compare(forms, left, right)
            self.assertEqual(report["counts"]["shared_readings_changed"], 1)
            self.assertEqual(report["counts"]["left_reading_rows"], 2)


if __name__ == "__main__":
    unittest.main()
