#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exercise private Greek partial-overlap provenance counters."""

import json
from pathlib import Path
import runpy
from tempfile import TemporaryDirectory
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "tools/audit-greek-partial-novelty.py"
audit = runpy.run_path(str(SCRIPT))["audit"]


class PartialNoveltyTest(unittest.TestCase):
    def test_novel_lines_are_distinct_from_duplicate_shared_lines(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            candidate, original, baseline, headers = (
                root / name for name in ("candidate", "original", "baseline", "headers"))
            candidate.write_text(":le:alpha\n:no:common\n:no:new\n"
                                 ":le:beta\n:no:common\n"
                                 ":le:gamma\n:no:common\n:no:common\n"
                                 ":le:delta\n:no:alone\n", encoding="utf-8")
            original.write_text(":le:alpha\n:no:common\n:no:new\n"
                                ":le:beta\n:no:common\n:no:old\n", encoding="utf-8")
            baseline.write_text(":le:alpha\n:no:common\n"
                                ":le:beta\n:no:common\n:le:beta\n:no:old\n"
                                ":le:gamma\n:no:common\n", encoding="utf-8")
            headers.write_text("".join(json.dumps(row) + "\n" for row in (
                {"lemma": "alpha", "projection_error": None,
                 "fields": [{"name": "orth"}, {"name": "orth"}, {"name": "gen"}]},
                {"lemma": "beta", "projection_error": None,
                 "fields": [{"name": "orth"}, {"name": "itype"}]},
                {"lemma": None, "projection_error": "unsupported-key", "fields": []},
            )), encoding="utf-8")
            result = audit(candidate, original, baseline, headers)["partial_novelty"]
            self.assertEqual(result["candidate"], {
                "lemma_groups": 1, "novel_records": 1, "records_in_original_candidate": 1,
                "candidate_multiple_lemma_markers": 0, "reference_multiple_lemma_markers": 0,
                "novel_lines_in_later_marker": 0, "novel_lines_only_in_first_marker": 1,
                "projected_key_matches_zero": 0, "projected_key_matches_one": 1,
                "projected_key_matches_multiple": 0, "any_multiple_orth": 1,
                "any_gen": 1, "any_itype": 0,
            })
            self.assertEqual(result["reference"], {
                "lemma_groups": 1, "novel_records": 1, "records_in_original_candidate": 1,
                "candidate_multiple_lemma_markers": 0, "reference_multiple_lemma_markers": 1,
                "novel_lines_in_later_marker": 1, "novel_lines_only_in_first_marker": 0,
                "projected_key_matches_zero": 0, "projected_key_matches_one": 1,
                "projected_key_matches_multiple": 0, "any_multiple_orth": 0,
                "any_gen": 0, "any_itype": 1,
            })


if __name__ == "__main__":
    unittest.main()
