#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check aggregate-only classification of disjoint Greek stem groups."""

import json
from pathlib import Path
import runpy
from tempfile import TemporaryDirectory
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "tools/audit-greek-disjoint-triage.py"
audit = runpy.run_path(str(SCRIPT))["audit"]


class DisjointTriageTest(unittest.TestCase):
    def test_non_quantity_groups_and_tag_change(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            candidate, baseline, headers = (root / name for name in
                                            ("candidate", "baseline", "headers"))
            candidate.write_text(":le:quantity\n:no:a^ os_ou\n"
                                 ":le:stem\n:no:abc os_ou\n"
                                 ":le:tag\n:no:abc os_ou\n"
                                 ":le:labels\n:no:abc os_ou\n"
                                 ":le:diacritics\n:no:a)/ os_ou\n"
                                 ":le:multiplicity\n:no:abc os_ou\n:no:abc os_ou\n",
                                 encoding="utf-8")
            baseline.write_text(":le:quantity\n:no:a os_ou\n"
                                ":le:stem\n:le:stem\n:no:xyz os_ou\n"
                                ":le:tag\n:aj:abc os_ou\n"
                                ":le:labels\n:no:xyz as_ou\n"
                                ":le:diacritics\n:no:a( os_ou\n"
                                ":le:multiplicity\n:no:xyz os_ou\n", encoding="utf-8")
            headers.write_text("".join(json.dumps(row) + "\n" for row in (
                {"lemma": "source_key", "headword": "ste^m", "projection_error": None,
                 "fields": [{"name": "orth"}, {"name": "orth"}, {"name": "gen"}]},
                {"lemma": "tag", "headword": "tag", "projection_error": None,
                 "fields": [{"name": "orth"}, {"name": "itype"}]},
                {"lemma": "multiplicity", "headword": "multiplicity", "projection_error": None,
                 "fields": [{"name": "orth"}]},
            )), encoding="utf-8")
            result = audit(candidate, baseline, headers)
            groups = result["non_quantity_disjoint"]
            self.assertEqual(sum(row["lemma_groups"] for row in groups.values()), 5)
            self.assertEqual(groups["same_tags_and_labels"]["reference_multiple_lemma_markers"], 1)
            self.assertEqual(groups["same_tags_and_labels"]["projected_key_matches_zero"], 1)
            self.assertEqual(groups["same_tags_and_labels"]["key_miss_first_orth_match"], 1)
            self.assertEqual(groups["same_tags_and_labels"]["any_multiple_orth"], 1)
            self.assertEqual(groups["same_labels_different_multiplicity"]["lemma_groups"], 1)
            self.assertEqual(groups["beta_code_diacritics"]["lemma_groups"], 1)
            self.assertEqual(result["different_tags_or_labels"], {
                "same_tag_set_different_labels": 1, "different_tag_sets": 1,
                "tag_set_changes": [{"candidate_tags": ":no:", "reference_tags": ":aj:",
                                     "lemma_groups": 1}],
            })


if __name__ == "__main__":
    unittest.main()
