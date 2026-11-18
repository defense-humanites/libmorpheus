#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check conservative positional exclusion of diphthong second letters."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "tools/audit-greek-open-diphthongs.py"
spec = importlib.util.spec_from_file_location("open_diphthongs", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def row(lemma, headword, position):
    bare = module.LONG.letters_and_longs(headword)[0]
    stem = bare[:position + 1] + "_" + bare[position + 1:]
    return {"lemma": lemma, "candidate": f":no:{bare} os_ou",
            "witness": f":no:{stem} os_ou",
            "sources": [{"id": "n1", "headword": headword,
                         "pron": [{"text": "[i_]", "direct": True}]}]}


class DiphthongTest(unittest.TestCase):
    def test_only_a_single_free_vowel_is_located(self):
        retain = row("foini/k", "foini/k", 4)
        move = row("oi)nopi/phs", "oi)nopi/phs", 1)
        self.assertEqual(module.locate(retain)["disposition"], "retain_witness_position")
        self.assertEqual(module.locate(move)["source_position"], 5)
        self.assertEqual(module.locate(move)["disposition"], "different_witness_position")
        self.assertIsNone(module.locate(row("dia/pi", "dia/pi", 1)))
        self.assertIsNone(module.locate(row("a)i+/pi", "a)i+/pi", 3)))
        self.assertEqual(module.free_vowels("u(lhourgo/s", "u"), [0])
        self.assertEqual(module.free_vowels("mono/u_los", "u"), [4])

    def test_private_output_and_counts(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            root = Path(directory)
            source, output = root / "source.jsonl", root / "review.jsonl"
            source.write_text("".join(json.dumps(r) + "\n" for r in (
                row("foini/k", "foini/k", 4),
                row("oi)nopi/phs", "oi)nopi/phs", 1))), encoding="utf-8")
            report = module.audit(source, output)
            self.assertEqual(report["counts"], {
                "retain_witness_position": 1, "different_witness_position": 1})
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                module.audit(source, output)
            with self.assertRaises(ValueError):
                module.audit(source, SCRIPT.parent / "forbidden.jsonl")


if __name__ == "__main__":
    unittest.main()
