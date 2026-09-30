#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Expected lemma coverage must not be masked by unrelated homographs."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools/audit-greek-generated-coverage.py"
spec = importlib.util.spec_from_file_location("coverage", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
GRAMMAR = "0,0,0,0,0,0,0,0,0"


class CoverageTest(unittest.TestCase):
    def test_exact_lemma_pairs_distinguish_absence_and_homographs(self):
        with tempfile.TemporaryDirectory() as directory:
            generated, forms, analysis = [Path(directory) / n for n in ("g", "f", "a")]
            generated.write_text("LEMMA\tx\n" + "a_\tx\t" + GRAMMAR + "\n" +
                                 "b\tx\t" + GRAMMAR + "\n" +
                                 "c\tx\t" + GRAMMAR + "\n" +
                                 "LEMMA\ty\na^\ty\t" + GRAMMAR + "\n")
            forms.write_text("a\nb\nc\nd\n")
            analysis.write_text("a\n<NL>N a,x  nom sg</NL>\nb\n<NL>N b,z  nom sg</NL>\n")
            counts = m.audit(generated, forms, analysis)["counts"]
            self.assertEqual(counts["expected_lemma_pairs"], 4)
            self.assertEqual(counts["matched_lemma_pairs"], 1)
            self.assertEqual(counts["missing_lemma_pairs"], 3)
            self.assertEqual(counts["homograph_only_surfaces"], 1)
            self.assertEqual(counts["absent_generated_surfaces"], 1)
            self.assertEqual(counts["partially_covered_surfaces"], 1)
            self.assertEqual(counts["lemmas_without_covered_surface"], 1)
            forms.write_text("a\nb\n")
            with self.assertRaisesRegex(ValueError, "omits"):
                m.audit(generated, forms, analysis)

    def test_quantity_only_normalization_preserves_case_and_accents(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "g"
            path.write_text("LEMMA\tx\nA_/\tx\t" + GRAMMAR + "\n")
            expected, lemmas, rows = m.read_generated(path)
            self.assertEqual(expected, {"A/": {"x"}})
            self.assertEqual((lemmas, rows), ({"x"}, 1))

    def test_rejects_malformed_and_mismatched_generation_records(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "g"
            for data in ("", "LEMMA\tx\n", "LEMMA\tx\nLEMMA\tx\n",
                         "a\tx\t" + GRAMMAR + "\n",
                         "LEMMA\tx\na\ty\t" + GRAMMAR + "\n",
                         "LEMMA\tx\na\tx\t0,0\n",
                         "LEMMA\tx\na b\tx\t" + GRAMMAR + "\n"):
                path.write_text(data)
                with self.subTest(data=data), self.assertRaises(ValueError):
                    m.read_generated(path)


if __name__ == "__main__":
    unittest.main()
