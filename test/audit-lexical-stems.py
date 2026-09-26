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
                                 ":le:reference_quantity\n:no:a os_ou\n"
                                 ":le:both_quantified\n:no:a^_ os_ou\n"
                                 ":le:diacritics\n:no:a)/ os_ou\n"
                                 ":le:stem\n:de:a) azw\n"
                                 ":le:labels\n:no:a os_ou\n"
                                 ":le:duplicate\n:no:a_^ os_ou\n:no:a_^ os_ou\n",
                                 encoding="utf-8")
            baseline.write_text(":le:quantity\n:no:a os_ou\n"
                                ":le:reference_quantity\n:no:a_ os_ou\n"
                                ":le:both_quantified\n:no:a__ os_ou\n"
                                ":le:diacritics\n:no:a( os_ou\n"
                                ":le:stem\n:de:b) azw\n"
                                ":le:labels\n:no:b as_ou\n"
                                ":le:duplicate\n:no:a os_ou\n",
                                encoding="utf-8")
            result = audit.compare(candidate, baseline, greek_spelling=True)
            self.assertEqual(result["shared_lemma_outcomes"]["disjoint_stems"], 7)
            self.assertEqual(result["disjoint_greek_spelling_diagnostic"], {
                "quantity_marks_only": 3, "beta_code_diacritics": 1,
                "same_tags_and_labels": 1, "same_labels_different_multiplicity": 1,
                "different_tags_or_labels": 1,
            })
            self.assertEqual(result["quantity_only_difference_direction"], {
                "lemma_mark_presence": {"candidate_only": 1, "reference_only": 1,
                                        "both": 1, "neither": 0},
                "stem_mark_counts": {"candidate_short": 2, "candidate_long": 2,
                                     "reference_short": 0, "reference_long": 3},
            })
            self.assertNotIn("disjoint_greek_spelling_diagnostic",
                             audit.compare(candidate, baseline))

    def test_partial_overlap_classifies_only_unmatched_records(self):
        with TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate"
            baseline = Path(directory) / "baseline"
            examples = {
                "candidate_extra": ([":no:common", ":no:extra"], [":no:common"]),
                "reference_extra": ([":no:common"], [":no:common", ":no:extra"]),
                "candidate_duplicate": ([":no:common", ":no:common"], [":no:common"]),
                "reference_duplicate": ([":no:common"], [":no:common", ":no:common"]),
                "quantity": ([":no:common", ":no:a^ os_ou"],
                             [":no:common", ":no:a os_ou"]),
                "diacritics": ([":no:common", ":no:a)/ os_ou"],
                               [":no:common", ":no:a( os_ou"]),
                "stem": ([":no:common", ":no:a os_ou"],
                         [":no:common", ":no:b os_ou"]),
                "multiplicity": ([":no:common", ":no:a os_ou", ":no:a os_ou"],
                                 [":no:common", ":no:b os_ou"]),
                "labels": ([":no:common", ":no:a os_ou"],
                           [":no:common", ":no:b as_ou"]),
            }
            for path, index in ((candidate, 0), (baseline, 1)):
                path.write_text("".join(":le:" + lemma + "\n" +
                                        "\n".join(records[index]) + "\n"
                                        for lemma, records in examples.items()), encoding="utf-8")
            result = audit.compare(candidate, baseline, greek_spelling=True)
            self.assertEqual(result["shared_lemma_outcomes"]["partial_overlap"], 9)
            self.assertEqual(result["partial_greek_residual_diagnostic"], {
                "candidate_extra_only": 2, "reference_extra_only": 2,
                "quantity_marks_only": 1, "beta_code_diacritics": 1,
                "same_tags_and_labels": 1, "same_labels_different_multiplicity": 1,
                "different_tags_or_labels": 1,
            })
            for side, novel in (("candidate", 7), ("reference", 6)):
                residual = result["partial_greek_residual_records"][side]
                self.assertEqual(residual["new_line"], novel)
                self.assertEqual(residual["duplicate_shared_line"], 1)
                self.assertEqual(residual["by_tag"][":no:"], novel + 1)
            self.assertNotIn("partial_greek_residual_diagnostic",
                             audit.compare(candidate, baseline))

    def test_alternative_reports_exact_gains_and_losses(self):
        with TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate"
            alternate = Path(directory) / "alternate"
            baseline = Path(directory) / "baseline"
            candidate.write_text(":le:alpha\n:no:x\n:le:beta\n:no:q\n"
                                 ":le:gamma\n:no:z\n", encoding="utf-8")
            alternate.write_text(":le:alpha\n:no:q\n:le:beta\n:no:y\n"
                                 ":le:gamma\n:no:z\n:le:delta\n:no:q\n", encoding="utf-8")
            baseline.write_text(":le:alpha\n:no:x\n:le:beta\n:no:y\n"
                                ":le:gamma\n:no:z\n:le:delta\n:no:w\n", encoding="utf-8")
            result = audit.compare_variants(candidate, alternate, baseline)
            self.assertEqual(result["reference_lemmas_in_either_candidate"], 4)
            self.assertEqual(result["exact_transitions"], {
                "both_exact": 1, "original_only_exact": 1,
                "alternate_only_exact": 1, "neither_exact": 1,
            })


if __name__ == "__main__":
    unittest.main()
