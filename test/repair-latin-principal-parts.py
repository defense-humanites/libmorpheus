#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1]/"tools/repair-latin-principal-parts.py"
spec = importlib.util.spec_from_file_location("parts",SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def row(head="za-scendo#2", itype="scendi, scensum, 3"):
    return dict(headword=head,projection_error=None,fields=[dict(name="itype",projection=itype)])


class Parts(unittest.TestCase):
    def test_exact_fragment_proof_preserves_prefix_and_newlines(self):
        raw=b":le:zascendo#2\n:vs:za-scend\tconj3\n:vs:za-scenscend perfstem\r\n:vs:za-scenscens pp4"
        data,counts=m.transform(raw,[row()])
        self.assertEqual(data,b":le:zascendo#2\n:vs:za-scend\tconj3\n:vs:za-scend perfstem\r\n:vs:za-scens pp4")
        self.assertEqual(counts["repaired_records"],2)

    def test_no_guessed_parts_aliases_or_alternate_records(self):
        raw=b":le:zascendo#2\n:vs:za-scenscend perfstem orth\n:vs:unrelated perfstem\n"
        data,counts=m.transform(raw,[row()])
        self.assertEqual(data,raw)
        self.assertEqual(counts.get("repaired_records",0),0)
        plain=b":le:zascendo#2\n:vs:za-scenscend perfstem\n"
        for source in [row(itype="feci, factum, 3"),row(itype="scendi, scensum, 2"),row(head="za-scendor#2"),row(head="othero")]:
            self.assertEqual(m.transform(plain,[source])[0],plain)

    def test_already_correct_and_ambiguous_source(self):
        raw=b":le:zascendo#2\n:vs:za-scend perfstem\n"
        self.assertEqual(m.transform(raw,[row()])[1]["already_correct"],1)
        source=row(itype="sce_ndi, scensum, 3")
        self.assertEqual(m.transform(raw,[row(),source])[1]["withheld_ambiguous_source"],1)

    def test_explicit_allomorphs_require_separate_tier_and_primary(self):
        raw=b":le:zasido\n:vs:za-si_\tconj3\n:vs:za-si_se_d perfstem\n"
        # A mismatching present record cannot establish the component boundary.
        self.assertEqual(m.transform(raw,[row("za-si_do","se_di, sessum, 3")],"source-allomorphs")[0],raw)
        raw=raw.replace(b"za-si_\t",b"za-si_d\t")
        source=row("za-si_do","se_di, sessum, 3")
        self.assertEqual(m.transform(raw,[source])[0],raw)
        fixed,counts=m.transform(raw,[source],"source-allomorphs")
        self.assertEqual(fixed,raw.replace(b"za-si_se_d",b"za-se_d"))
        self.assertEqual(counts["repaired_records"],1)
        self.assertEqual(m.transform(raw,[row("za-si_do","si, sum, 3")],"source-allomorphs")[0],raw)

    def test_reduplication_second_conjugation_and_withheld_voice(self):
        raw=b":le:zaspandeo\n:vs:za-spand conj2\n:vs:za-spanspo^pand perfstem\n:vs:za-spanspans pp4\n"
        source=row("za-spande^o","spo^pandi, spansum, 2")
        fixed,counts=m.transform(raw,[source],"source-allomorphs")
        self.assertEqual(fixed,raw.replace(b"za-spanspo^pand",b"za-spo^pand").replace(b"za-spanspans",b"za-spans"))
        self.assertEqual(counts["repaired_records"],2)
        for withheld in [raw.replace(b"conj2",b"conj3"),raw.replace(b"conj2",b"conj2 orth"),raw.replace(b"conj2",b"conj2 dep")]:
            self.assertEqual(m.transform(withheld,[source],"source-allomorphs")[0],withheld)
        self.assertEqual(m.transform(raw,[row("za-spande^or","spo^pandi, spansum, 2")],"source-allomorphs")[0],raw)
        with self.assertRaises(ValueError):m.transform(raw,[source],"unknown")


if __name__ == "__main__":
    unittest.main()
