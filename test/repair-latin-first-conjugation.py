#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1]/"tools/repair-latin-first-conjugation.py"
spec = importlib.util.spec_from_file_location("first",SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def row(head, itype="a_vi, a_tum, 1"):
    return dict(headword=head, projection_error=None, fields=[dict(name="itype",projection=itype)])


class Derivatives(unittest.TestCase):
    def test_source_quantities_homographs_and_deponents(self):
        raw=b":le:zabeo#2\n:de:zab\tare_vb\r\n:le:zabior\n:de:zab\tare_vb dep\n:le:zabo\n:de:zab\tare_vb\n"
        data, report=m.transform(raw,[row("za-be^o#2"),row("zabi^or","a_ri"),row("zabo")])
        self.assertEqual(data,b":le:zabeo#2\n:de:za-be^\tare_vb\r\n:le:zabior\n:de:zabi^\tare_vb dep\n:le:zabo\n:de:zab\tare_vb\n")
        self.assertEqual(report["repaired_records"],2)
        self.assertEqual(report["unchanged"],1)

    def test_no_alias_voice_or_ambiguous_inheritance(self):
        raw=b":le:zabeo\n:de:zab\tare_vb\n:de:zab\tare_vb orth\n:le:other\n:de:oth\tare_vb\n"
        data, report=m.transform(raw,[row("zabeo"),row("za_beo")])
        self.assertEqual(data,raw)
        self.assertEqual(report.get("repaired_records",0),0)
        for source in [row("zabeo","2"),row("zabeor","1")]:
            self.assertEqual(m.transform(raw,[source])[0],raw)

    def test_non_derivatives_and_missing_final_newline(self):
        raw=b":le:zabeo\n:vs:zab conj2\n:de:zab\tare_vb"
        data,report=m.transform(raw,[row("zabeo","1")])
        self.assertEqual(data,b":le:zabeo\n:vs:zab conj2\n:de:zabe\tare_vb")
        self.assertEqual(report["repaired_records"],1)

    def test_quantity_only_repairs_are_separately_selectable(self):
        raw=b":le:zabio\n:de:zabi\tare_vb\n:le:zabeo\n:de:zab\tare_vb\n"
        rows=[row("zabi^o"),row("zabe^o")]
        all_data,all_counts=m.transform(raw,rows)
        letters,counts=m.transform(raw,rows,"letters-only")
        self.assertEqual(all_counts["repaired_quantity_only"],1)
        self.assertEqual(all_counts["repaired_letters"],1)
        self.assertEqual(counts["withheld_quantity_only"],1)
        self.assertEqual(letters,b":le:zabio\n:de:zabi\tare_vb\n:le:zabeo\n:de:zabe^\tare_vb\n")
        self.assertNotEqual(all_data,letters)
        with self.assertRaises(ValueError):m.transform(raw,rows,"unknown")

    def test_source_validation_private_output_and_no_overwrite(self):
        entry=m.review.etree.fromstring(b'<entryFree id="synthetic" key="zabeo"><orth extent="full">zabeo</orth><itype>1</itype></entryFree>')
        record,_=m.review.projection.project(entry,"Latin")
        record.update(id="synthetic",source=m.review.SOURCE.name)
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            root=Path(directory);candidate=root/"candidate";headers=root/"headers";source=root/"source"
            candidate.write_bytes(b":le:zabeo\n:de:zab\tare_vb\n")
            headers.write_text(json.dumps(record)+"\n");source.write_text("synthetic")
            with patch.object(m.review,"load_entries",return_value=({"synthetic":entry},source,"synthetic")):
                with self.assertRaises(ValueError):m.prepare(candidate,headers,root/"lexica",root/"bad",2)
                self.assertFalse((root/"bad").exists())
                m.prepare(candidate,headers,root/"lexica",root/"output",1)
                self.assertEqual((root/"output").stat().st_mode & 0o777,0o600)
                with self.assertRaises(FileExistsError):m.prepare(candidate,headers,root/"lexica",root/"output",1)
                with self.assertRaises(ValueError):m.prepare(candidate,headers,root/"lexica",SCRIPT.parent/"forbidden",1)
                record["fields"][1]["projection"]="different"
                headers.write_text(json.dumps(record)+"\n")
                with self.assertRaises(ValueError):m.prepare(candidate,headers,root/"lexica",root/"stale",1)
                self.assertFalse((root/"stale").exists())


if __name__ == "__main__":
    unittest.main()
