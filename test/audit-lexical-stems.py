#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Validate record multiplicity and unrelated raw lines in stem comparison."""

import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "tools/audit-lexical-stems.py"
spec = importlib.util.spec_from_file_location("stem_audit", SCRIPT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class ComparisonTest(unittest.TestCase):
    def test_record_multisets_and_lemma_scope(self):
        with TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate"
            baseline = Path(directory) / "baseline"
            candidate.write_text("raw header\n:le:alpha\n:no:x\n:no:x\n"
                                 ":le:beta\n:aj:y\n", encoding="utf-8")
            baseline.write_text("raw header\n:le:alpha\n:no:x\n:no:z\n"
                                ":le:beta\n:aj:y\n:le:gamma\n:no:q\n", encoding="utf-8")
            result = audit.compare(candidate, baseline)
            self.assertEqual(result["common_lemmas"], 2)
            self.assertEqual(result["equal_record_multisets_at_common_lemmas"], 1)
            self.assertEqual(result["exact_shared_stem_records_with_multiplicity"], 2)
            self.assertEqual(result["reference_only_lemmas"], 1)
            self.assertEqual(result["candidate_only_lemmas"], 0)

    def test_verb_derivation_tags_are_counted(self):
        with TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate"
            baseline = Path(directory) / "baseline"
            candidate.write_text(":le:amo\n:vs:am\tconj1\n:de:ama\tare_vb\n", encoding="utf-8")
            baseline.write_text(":le:amo\n:de:ama\tare_vb\n:vs:am\tconj1\n", encoding="utf-8")
            result = audit.compare(candidate, baseline)
            self.assertEqual(result["equal_record_multisets_at_common_lemmas"], 1)
            self.assertEqual(result["exact_shared_stem_records_with_multiplicity"], 2)


if __name__ == "__main__":
    unittest.main()
