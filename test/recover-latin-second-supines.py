#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT=Path(__file__).resolve().parents[1]/"tools/recover-latin-second-supines.py"
spec=importlib.util.spec_from_file_location("supines",SCRIPT)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def row(head,parts):
    return dict(headword=head,projection_error=None,fields=[dict(name="itype",projection=parts)])


class Supines(unittest.TestCase):
    def test_explicit_suffixes_prefix_newlines_and_idempotence(self):
        raw=b":le:zatendo\n:vs:za-tend conj3\n:vs:za-tend perfstem\n:vs:za-tent pp4"
        rows=[row("za-tendo","di, tum and sum, 3")]
        data,counts=m.transform(raw,rows)
        self.assertEqual(data,raw+b"\n:vs:za-tens pp4\n")
        self.assertEqual(counts["added_records"],1)
        self.assertEqual(m.transform(data,rows)[0],data)

    def test_full_parts_preserve_source_quantities(self):
        raw=b":le:zatendo#2\n:vs:za-tend conj3\n:vs:za-te^tend perfstem\n:vs:za-tens pp4\r\n"
        data,counts=m.transform(raw,[row("za-tendo#2","te^tendi, tensum and tentum, 3")])
        self.assertEqual(data,raw+b":vs:za-tent pp4\n")
        self.assertEqual(counts["added_records"],1)

    def test_exact_broken_c_s_branch_and_two_explicit_supines(self):
        raw=b":le:zafurcio\n:vs:za-furc conj4\n:vs:za-furcs perfstem\n:vs:za-furcs pp4\n"
        rows=[row("za-furci^o","si, sum and tum, 4")]
        data,counts=m.transform(raw,rows)
        self.assertEqual(data,b":le:zafurcio\n:vs:za-furc conj4\n:vs:za-furs perfstem\n:vs:za-furs pp4\n:vs:za-furct pp4\n")
        self.assertEqual(counts["repaired_records"],2)
        self.assertEqual(m.transform(data,rows)[0],data)

    def test_no_missing_parts_alias_voice_or_ambiguous_block(self):
        raw=b":le:zatendo\n:vs:za-tend conj3\n:vs:za-tend perfstem\n:vs:za-tent pp4\n"
        source=row("za-tendo","di, tum and sum, 3")
        for candidate in [raw.replace(b"conj3",b"conj3 dep"),raw.replace(b"za-tent",b"other"),raw*2]:
            self.assertEqual(m.transform(candidate,[source])[0],candidate)
        self.assertEqual(m.transform(raw,[source,source])[0],raw)
        for head,parts in [("othero","di, tum and sum, 3"),("za-tendor","di, tum and sum, 3"),("za-tendo","di, tum, 3")]:
            self.assertEqual(m.transform(raw,[row(head,parts)])[0],raw)

    def test_expected_count_private_target_and_no_overwrite(self):
        record=row("za-tendo","di, tum and sum, 3")
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            root=Path(directory);candidate=root/"candidate";headers=root/"headers";source=root/"source";target=root/"output"
            candidate.write_bytes(b":le:zatendo\n:vs:za-tend conj3\n:vs:za-tend perfstem\n:vs:za-tent pp4\n")
            headers.write_text("synthetic");source.write_text("synthetic")
            with patch.object(m.first,"source_rows",return_value=([record],source,"synthetic")):
                with self.assertRaises(ValueError):m.prepare(candidate,headers,root/"lexica",target,2)
                self.assertFalse(target.exists())
                m.prepare(candidate,headers,root/"lexica",target,1)
                self.assertEqual(target.stat().st_mode & 0o777,0o600)
                with self.assertRaises(FileExistsError):m.prepare(candidate,headers,root/"lexica",target,1)
                with self.assertRaises(ValueError):m.prepare(candidate,headers,root/"lexica",SCRIPT.parent/"forbidden",1)


if __name__=="__main__":
    unittest.main()
