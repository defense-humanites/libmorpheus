#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1]/"tools/recover-latin-ingo-parts.py"
spec = importlib.util.spec_from_file_location("ingo", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def row(head="za-lingo#2", itype="inxi, inctum and ictum, 3"):
    return dict(headword=head, projection_error=None, fields=[dict(name="orth", projection=head), dict(name="itype", projection=itype)])


class Recovery(unittest.TestCase):
    def test_explicit_parts_prefix_homograph_and_existing_records(self):
        source=row();raw=m.first.compound.recovery.render(source).encode()
        data,counts=m.transform(b"other\n"+raw,[source])
        self.assertEqual(data,b"other\n"+raw+b":le:zalingo#2\n:vs:za-ling\tconj3\n:vs:za-linx perfstem\n:vs:za-linct pp4\n:vs:za-lict pp4\n")
        self.assertEqual(counts,{"recovered_headers":1,"added_stem_records":4})
        self.assertEqual(m.transform(data,[source])[0],data)
        self.assertEqual(m.transform(raw*2,[source])[0],raw*2)

    def test_no_alternates_voice_guesses_or_unrelated_headers(self):
        for source in [row(head="za-lingor"),row(head="za-lungo"),row(itype="inxi, ictum, 3"),row(itype="inxi, inctum and ictum, 4")]:
            raw=m.first.compound.recovery.render(source).encode()
            self.assertEqual(m.transform(raw,[source])[0],raw)
        source=row();source["fields"].append(dict(name="orth",projection="za-lungo",type="alt"))
        raw=m.first.compound.recovery.render(source).encode()
        self.assertEqual(m.transform(raw,[source])[0],raw)
        self.assertEqual(m.transform(b"different\n",[row()])[0],b"different\n")

    def test_private_output_expected_count_and_no_overwrite(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            root=Path(directory);candidate=root/"candidate";headers=root/"headers";source=root/"source";target=root/"output"
            record=row();candidate.write_bytes(m.first.compound.recovery.render(record).encode());headers.write_text("synthetic");source.write_text("synthetic")
            with patch.object(m.first,"source_rows",return_value=([record],source,"synthetic")):
                with self.assertRaises(ValueError):m.prepare(candidate,headers,root/"lexica",target,2)
                self.assertFalse(target.exists())
                m.prepare(candidate,headers,root/"lexica",target,1)
                self.assertEqual(target.stat().st_mode & 0o777,0o600)
                with self.assertRaises(FileExistsError):m.prepare(candidate,headers,root/"lexica",target,1)
                with self.assertRaises(ValueError):m.prepare(candidate,headers,root/"lexica",SCRIPT.parent/"forbidden",1)


if __name__ == "__main__":
    unittest.main()
