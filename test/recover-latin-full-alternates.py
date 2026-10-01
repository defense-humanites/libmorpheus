#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1]/"tools/recover-latin-full-alternates.py"
spec = importlib.util.spec_from_file_location("alts", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def row(head="za-be^o#2", alts=None, itype="a_vi, a_tum, 1"):
    return dict(headword=head,projection_error=None,fields=[dict(name="itype",projection=itype)],full_alternates=alts or ["za-boe^o"])


class Alternates(unittest.TestCase):
    def test_same_article_root_quantities_homograph_and_idempotence(self):
        raw=b":le:zabeo#2\n:de:za-be\tare_vb\r\n"
        expected=raw+b":de:za-boe^\tare_vb orth\n"
        data,counts=m.transform(raw,[row()])
        self.assertEqual(data,expected)
        self.assertEqual(counts["added_records"],1)
        self.assertEqual(m.transform(data,[row()])[0],data)

    def test_no_abbreviations_voice_or_quantity_transfer(self):
        raw=b":le:zabeo#2\n:de:za-be^\tare_vb\n"
        for alts in [["za-"],["za-boe^or"],["za-be_o"]]:
            self.assertEqual(m.transform(raw,[row(alts=alts)])[0],raw)
        self.assertEqual(m.transform(raw,[row(itype="2")])[0],raw)
        conflicting=row();conflicting["fields"].append(dict(name="itype",projection="2"))
        self.assertEqual(m.transform(raw,[conflicting])[0],raw)
        self.assertEqual(m.transform(raw,[row(),row()])[0],raw)
        self.assertEqual(m.transform(raw*2,[row()])[0],raw*2)
        self.assertEqual(m.transform(raw.replace(b"za-be^",b"other"),[row()])[0],raw.replace(b"za-be^",b"other"))

    def test_deponent_and_missing_final_newline(self):
        raw=b":le:zabeor\n:de:zabe\tare_vb dep"
        data,counts=m.transform(raw,[row("zabeor",["zaboeor"],"a_ri")])
        self.assertEqual(data,raw+b"\n:de:zaboe\tare_vb dep orth\n")
        self.assertEqual(counts["added_records"],1)

    def test_source_orthography_validation_private_output_and_no_overwrite(self):
        entry=m.first.review.etree.fromstring(b'<entryFree id="synthetic" key="zabeo"><orth extent="full">zabeo</orth><orth extent="full" type="alt">zaboeo</orth><itype>1</itype></entryFree>')
        record,_=m.first.review.projection.project(entry,"Latin")
        record.update(id="synthetic",source=m.first.review.SOURCE.name)
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            root=Path(directory);candidate=root/"candidate";headers=root/"headers";source=root/"source";target=root/"output"
            candidate.write_bytes(b":le:zabeo\n:de:zabe\tare_vb\n");headers.write_text("synthetic");source.write_text("synthetic")
            with patch.object(m.first,"source_rows",return_value=([record],source,"synthetic")), patch.object(m.first.review,"load_entries",return_value=({"synthetic":entry},source,"synthetic")):
                with self.assertRaises(ValueError):m.prepare(candidate,headers,root/"lexica",target,2)
                self.assertFalse(target.exists())
                m.prepare(candidate,headers,root/"lexica",target,1)
                self.assertEqual(target.stat().st_mode & 0o777,0o600)
                with self.assertRaises(FileExistsError):m.prepare(candidate,headers,root/"lexica",target,1)
                with self.assertRaises(ValueError):m.prepare(candidate,headers,root/"lexica",SCRIPT.parent/"forbidden",1)
                record["fields"][1]["projection"]="different"
                with self.assertRaises(ValueError):m.prepare(candidate,headers,root/"lexica",root/"bad")
                self.assertFalse((root/"bad").exists())


if __name__ == "__main__":
    unittest.main()
