#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the deliberately narrow Greek source-quantity decision rule."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "tools/arbitrate-greek-quantity-long.py"
spec = importlib.util.spec_from_file_location("long_quantity", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def row(stem=":no:pi_t os_ou", headword="pi/tos", pron="[i_]", direct=True):
    return {"lemma": "pi/tos", "candidate": ":no:pit os_ou", "witness": stem,
            "sources": [{"id": "n1", "headword": headword,
                         "pron": [{"text": pron, "direct": direct}]}]}


class GreekLongQuantityTest(unittest.TestCase):
    def test_source_must_name_a_unique_vowel_in_the_headword(self):
        accepted = "retain_witness_long_from_unique_direct_pron"
        self.assertEqual(module.decision(row()), accepted)
        self.assertEqual(module.decision(row(headword="pi/tios")), "manual_review")
        self.assertEqual(module.decision(row(pron="[i_]", direct=False)), "manual_review")
        self.assertEqual(module.decision(row(pron="[u_]")), "manual_review")
        self.assertEqual(module.decision(row(stem=":no:pi__t os_ou")), "manual_review")
        self.assertEqual(module.decision(row(headword="ti/pus")), "manual_review")
        repeated = row()
        repeated["sources"].append(dict(repeated["sources"][0], id="n2"))
        self.assertEqual(module.decision(repeated), "manual_review")
        context = row(stem=":no:pi_t os_ou", headword="pi/tios", pron="[pi_]")
        self.assertEqual(module.decision(context),
                         "retain_witness_long_from_unique_pron_context")
        context["sources"][0]["pron"][0]["text"] = "[i_]"
        self.assertEqual(module.decision(context), "manual_review")

        alternate = row(headword="pi/s", pron="[pi_]")
        alternate["sources"][0]["fields"] = [
            {"name": "orth", "projection": "pi/s"},
            {"name": "orth", "projection": "pi/tos"}]
        self.assertEqual(module.decision(alternate),
                         "retain_witness_long_from_alternate_orth_pron_context")
        alternate["sources"][0]["fields"].append(
            {"name": "orth", "projection": "pi/ti_tos"})
        self.assertEqual(module.decision(alternate),
                         "retain_witness_long_from_alternate_orth_pron_context")
        alternate["sources"][0]["fields"].append(
            {"name": "orth", "projection": "pi/tospi"})
        self.assertEqual(module.decision(alternate), "manual_review")
        alternate["sources"][0]["fields"].pop()
        alternate["sources"].append(dict(alternate["sources"][0], id="n2"))
        self.assertEqual(module.decision(alternate), "manual_review")

        itype = {"lemma": "sta/c", "candidate": ":no:sta_ c_kos masc",
                 "witness": ":no:sta c_kos masc",
                 "sources": [{"id": "n3", "headword": "sta/c", "pron": [],
                              "fields": [{"name": "itype", "projection": "a_kos"}]}]}
        self.assertEqual(module.decision(itype), "retain_candidate_long_from_itype")
        itype["sources"][0]["fields"][0]["projection"] = "akos"
        self.assertEqual(module.decision(itype), "manual_review")

    def test_aggregate_and_private_ledger(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            source = Path(directory) / "review.jsonl"
            output = Path(directory) / "decisions.jsonl"
            source.write_text("\n".join(json.dumps(item) for item in
                                        (row(), row(pron="[u_]"))) + "\n")
            result = module.arbitrate(source, output)
            self.assertEqual(result["by_disposition"], {
                "manual_review": 1, "retain_witness_long_from_unique_direct_pron": 1})
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            self.assertEqual(len(output.read_text().splitlines()), 2)
            with self.assertRaises(FileExistsError):
                module.arbitrate(source, output)
            with self.assertRaises(ValueError):
                module.arbitrate(source, SCRIPT.parent / "forbidden.jsonl")


if __name__ == "__main__":
    unittest.main()
