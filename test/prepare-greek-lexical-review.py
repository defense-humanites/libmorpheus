#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check private residual selection and output safeguards."""

import json
import os
from pathlib import Path
import runpy
from tempfile import TemporaryDirectory
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "tools/prepare-greek-lexical-review.py"
prepare = runpy.run_path(str(SCRIPT))["prepare"]


class PrivateReviewTest(unittest.TestCase):
    def test_selects_distinct_residuals_and_refuses_public_output(self):
        with TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            root = Path(directory)
            candidate, original, baseline, headers, split, output = (
                root / name for name in ("candidate", "original", "baseline",
                                        "headers", "split", "review.jsonl"))
            candidate.write_text(":le:alpha\n:no:common\n:no:novel\n"
                                 ":le:beta\n:wd:surface adverb\n"
                                 ":le:quantity\n:no:a^ os_ou\n"
                                 ":le:duplicate\n:no:common\n:no:common\n", encoding="utf-8")
            original.write_text(":le:alpha\n:no:common\n:no:novel\n"
                                ":le:beta\n:wd:surface adverb\n", encoding="utf-8")
            baseline.write_text(":le:alpha\n:no:common\n"
                                ":le:beta\n:wd:sur/face adverb\n"
                                ":le:quantity\n:no:a os_ou\n"
                                ":le:duplicate\n:no:common\n", encoding="utf-8")
            headers.write_text("".join(json.dumps(row) + "\n" for row in (
                {"lemma": "alpha", "headword": "alpha", "projection_error": None,
                 "fields": [{"name": "orth", "projection": "alpha"}]},
                {"lemma": "source_beta", "headword": "surface", "projection_error": None,
                 "fields": [{"name": "orth", "projection": "surface"},
                            {"name": "pos", "projection": "Adv."}]},
            )), encoding="utf-8")
            split.write_text("alpha\t<gen>x</gen>\nsurface\t<pos>Adv.</pos>\n",
                             encoding="utf-8")
            report = prepare(candidate, baseline, headers, split, output, original)
            self.assertEqual(report["by_category"], {
                "beta_code_diacritics": 1, "partial_distinct_line": 1})
            self.assertEqual(os.stat(output).st_mode & 0o777, 0o600)
            rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["lemma"] for row in rows], ["alpha", "beta"])
            self.assertIn("adverb_stem_orth", rows[1]["source_headers"][0]["match"])
            with self.assertRaises(FileExistsError):
                prepare(candidate, baseline, headers, split, output)
            with self.assertRaises(ValueError):
                prepare(candidate, baseline, headers, split, SCRIPT.parent / "review.jsonl")


if __name__ == "__main__":
    unittest.main()
