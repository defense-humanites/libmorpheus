#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Guard the narrow review decisions against loss of lexical distinctions."""

import importlib.util
from pathlib import Path
import tempfile
import unittest
import json


SCRIPT = Path(__file__).resolve().parents[1] / "tools/arbitrate-greek-lexical-review.py"
spec = importlib.util.spec_from_file_location("greek_arbitration", SCRIPT)
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


def row(category, candidate, witness, lemma="sample"):
    return {"lemma": lemma, "category": category,
            "candidate_blocks": [[candidate]], "witness_blocks": [[witness]]}


class ArbitrationTest(unittest.TestCase):
    def test_stem_separator_only_preserves_labels(self):
        plain = row("same_tags_and_labels", ":no:para-log os_ou masc",
                    ":no:paralog os_ou masc")
        self.assertEqual(review.disposition(plain)[0], "stem_separator_only")
        changed = row("same_tags_and_labels", ":no:para-log os_ou masc",
                      ":no:paralog os_ou fem")
        self.assertEqual(review.disposition(changed)[0], "manual_review")

    def test_diaeresis_is_still_pending(self):
        plain = row("beta_code_diacritics", ":wd:boi+sti/ adverb",
                    ":wd:boisti/ adverb")
        self.assertEqual(review.disposition(plain)[0], "diaeresis_needs_analysis")
        changed = row("beta_code_diacritics", ":wd:boi+sti/ adverb",
                      ":wd:boisti/ adverb language")
        self.assertEqual(review.disposition(changed)[0], "manual_review")

    def test_quantity_difference_cannot_be_silently_dropped(self):
        changed = row("same_tags_and_labels", ":aj:xortaio-bam wn_on",
                      ":aj:xortaioba_m wn_on")
        self.assertEqual(review.disposition(changed)[0], "manual_review")

    def test_private_ledger_and_repository_boundary(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            source = Path(directory) / "review.jsonl"
            output = Path(directory) / "decisions.jsonl"
            source.write_text(json.dumps(row("same_tags_and_labels",
                                            ":no:para-log os_ou masc",
                                            ":no:paralog os_ou masc")) + "\n")
            report = review.arbitrate(source, output)
            self.assertEqual(report["by_disposition"], {"stem_separator_only": 1})
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                review.arbitrate(source, output)
            with self.assertRaises(ValueError):
                review.arbitrate(source, SCRIPT.parent / "forbidden.jsonl")


if __name__ == "__main__":
    unittest.main()
