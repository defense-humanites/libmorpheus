#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the private unresolved-quantity dossier and its output boundary."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "tools/inspect-greek-quantity-open.py"
spec = importlib.util.spec_from_file_location("quantity_open", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class QuantityOpenTest(unittest.TestCase):
    def test_positional_dossier_only_for_manual_cases(self):
        unresolved = {"lemma": "pi/tios", "candidate": ":no:pitios os_ou",
                      "witness": ":no:pi_tios os_ou", "sources": [{
                          "id": "n1", "headword": "pi/ti^osi",
                          "fields": [{"name": "orth", "projection": "pi/ti_osi"}],
                          "pron": [{"text": "[i_]", "direct": True}]}]}
        resolved = {"lemma": "pi/tos", "candidate": ":no:pit os_ou",
                    "witness": ":no:pi_t os_ou", "sources": [{
                        "id": "n2", "headword": "pi/tos",
                        "pron": [{"text": "[i_]", "direct": True}]}]}
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            source = Path(directory) / "source.jsonl"
            output = Path(directory) / "dossier.jsonl"
            source.write_text("".join(json.dumps(row) + "\n" for row in
                                      (unresolved, resolved)), encoding="utf-8")
            result = module.inspect(source, output)
            self.assertEqual(result["counts"], {
                "alternate_orthographies": 1, "contextual_direct_pron": 0,
                "explicit_long_in_orthography": 1,
                "explicit_short_in_orthography": 1,
                "manual_review": 1, "multiple_sources": 0})
            item = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(item["witness"]["long"], [1])
            self.assertEqual(item["sources"][0]["orthographies"][0]["short"], [3])
            self.assertEqual(item["sources"][0]["orthographies"][1]["long"], [3])
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                module.inspect(source, output)
            with self.assertRaises(ValueError):
                module.inspect(source, SCRIPT.parent / "forbidden.jsonl")


if __name__ == "__main__":
    unittest.main()
