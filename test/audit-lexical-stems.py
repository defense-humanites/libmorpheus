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
            self.assertEqual(result["shared_lemma_outcomes"]["exact"], 1)
            self.assertEqual(result["shared_lemma_outcomes"]["partial_overlap"], 1)
            self.assertEqual(result["unmatched_stem_records_at_shared_lemmas"]["candidate_by_tag"][":no:"], 1)
            self.assertEqual(result["unmatched_stem_records_at_shared_lemmas"]["reference_by_tag"][":no:"], 1)

    def test_verb_derivation_tags_are_counted(self):
        with TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate"
            baseline = Path(directory) / "baseline"
            candidate.write_text(":le:amo\n:vs:am\tconj1\n:de:ama\tare_vb\n", encoding="utf-8")
            baseline.write_text(":le:amo\n:de:ama\tare_vb\n:vs:am\tconj1\n", encoding="utf-8")
            result = audit.compare(candidate, baseline)
            self.assertEqual(result["equal_record_multisets_at_common_lemmas"], 1)
            self.assertEqual(result["exact_shared_stem_records_with_multiplicity"], 2)

    def test_missing_and_disjoint_stems_are_distinguished(self):
        with TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate"
            baseline = Path(directory) / "baseline"
            candidate.write_text(":le:empty_left\n:le:empty_right\n:no:x\n"
                                 ":le:disjoint\n:de:a\n:de:b\n", encoding="utf-8")
            baseline.write_text(":le:empty_left\n:no:y\n:le:empty_right\n"
                                ":le:disjoint\n:de:c\n", encoding="utf-8")
            result = audit.compare(candidate, baseline)
            self.assertEqual(result["shared_lemma_outcomes"], {
                "candidate_without_stems": 1, "reference_without_stems": 1,
                "disjoint_stems": 1, "exact": 0, "partial_overlap": 0,
            })
            differences = result["unmatched_stem_records_at_shared_lemmas"]
            self.assertEqual(differences["candidate_by_tag"][":de:"], 2)
            self.assertEqual(differences["reference_by_tag"][":de:"], 1)

    def test_greek_spelling_probe_keeps_morphology_and_multiplicity(self):
        with TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate"
            baseline = Path(directory) / "baseline"
            candidate.write_text(":le:quantity\n:no:a_^ os_ou\n"
                                 ":le:diacritics\n:no:a)/ os_ou\n"
                                 ":le:stem\n:de:a) azw\n"
                                 ":le:labels\n:no:a os_ou\n"
                                 ":le:duplicate\n:no:a_^ os_ou\n:no:a_^ os_ou\n",
                                 encoding="utf-8")
            baseline.write_text(":le:quantity\n:no:a os_ou\n"
                                ":le:diacritics\n:no:a( os_ou\n"
                                ":le:stem\n:de:b) azw\n"
                                ":le:labels\n:no:b as_ou\n"
                                ":le:duplicate\n:no:a os_ou\n",
                                encoding="utf-8")
            result = audit.compare(candidate, baseline, greek_spelling=True)
            self.assertEqual(result["shared_lemma_outcomes"]["disjoint_stems"], 5)
            self.assertEqual(result["disjoint_greek_spelling_diagnostic"], {
                "quantity_marks_only": 1, "beta_code_diacritics": 1,
                "same_tags_and_labels": 1, "same_labels_different_multiplicity": 1,
                "different_tags_or_labels": 1,
            })
            self.assertNotIn("disjoint_greek_spelling_diagnostic",
                             audit.compare(candidate, baseline))


if __name__ == "__main__":
    unittest.main()
