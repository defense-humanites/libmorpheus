#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the private Greek long-quantity source join."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "tools/prepare-greek-quantity-source-review.py"
spec = importlib.util.spec_from_file_location("quantity_sources", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SourceJoinTest(unittest.TestCase):
    def test_long_groups_and_direct_or_nested_pron(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            root = Path(directory)
            triage, headers, xml, output = (root / name for name in
                                            ("triage.jsonl", "headers.jsonl",
                                             "grc.lsj.perseus-eng1.xml", "review.jsonl"))
            triage.write_text("".join(json.dumps(row) + "\n" for row in (
                {"lemma": "pi/tios", "candidate": ":no:pitios os_ou",
                 "witness": ":no:pi_tios os_ou"},
                {"lemma": "a/b", "candidate": ":no:ab os_ou",
                 "witness": ":no:a^b os_ou"},
                {"lemma": "gamma", "candidate": ":no:ga_^mma os_ou",
                 "witness": ":no:ga_mma os_ou"})), encoding="utf-8")
            headers.write_text(json.dumps({
                "lemma": "other", "headword": "pi/ti^os", "projection_error": None,
                "source": xml.name, "id": "n1", "fields": [
                    {"name": "orth", "projection": "pi/ti^os"},
                    {"name": "orth", "projection": "pi/tios"}]}) + "\n", encoding="utf-8")
            xml.write_text("<root><entryFree id='n1'><orth>pi/ti^os</orth>"
                           "<pron>[i_]</pron><sense><pron>[ti_]</pron></sense>"
                           "</entryFree></root>", encoding="utf-8")
            with patch.object(module, "pinned_files", return_value=[xml]):
                result = module.prepare(triage, headers, root, output, expected=1)
                self.assertEqual(result["groups"], 1)
                self.assertEqual(result["source_counts"], {"source_count_1": 1})
                row = json.loads(output.read_text(encoding="utf-8"))
                self.assertEqual(row["sources"][0]["pron"], [
                    {"text": "[i_]", "direct": True},
                    {"text": "[ti_]", "direct": False}])
                self.assertEqual(output.stat().st_mode & 0o777, 0o600)
                with self.assertRaises(FileExistsError):
                    module.prepare(triage, headers, root, output)
                with self.assertRaises(ValueError):
                    module.prepare(triage, headers, root, SCRIPT.parent / "forbidden.jsonl")
                with self.assertRaises(ValueError):
                    module.prepare(triage, headers, root, root / "other.jsonl", expected=2)


if __name__ == "__main__":
    unittest.main()
