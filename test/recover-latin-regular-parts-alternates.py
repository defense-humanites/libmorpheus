#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
SCRIPT=Path(__file__).resolve().parents[1]/'tools/recover-latin-regular-parts-alternates.py'
spec=importlib.util.spec_from_file_location('m',SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def row(head='za_-prendo#2',field='di, sum, 3',alts=None):
    return dict(headword=head,projection_error=None,fields=[dict(name='itype',projection=field)],full_alternates=alts or ['za_praendo'])

class Alternates(unittest.TestCase):
    raw=b':le:zaprendo#2\n:vs:za_-prend conj3\n:vs:za_-prend perfstem\n:vs:za_-prens pp4\n'
    def test_three_source_parts_prefixes_homograph_and_idempotence(self):
        data,counts=m.transform(self.raw,[row()])
        self.assertEqual(counts,{'added_records':3,'changed_lemma_blocks':1})
        self.assertTrue(data.endswith(b':vs:za_praend\tconj3 orth\n:vs:za_praend\tperfstem orth\n:vs:za_praens\tpp4 orth\n'))
        self.assertEqual(m.transform(data,[row()])[0],data)
    def test_fourth_quantities_and_missing_final_newline(self):
        raw=b':le:zavio\n:vs:za_v conj4\n:vs:za_vi_v perfstem\n:vs:za_vi_t pp4'
        source=row('za_vi^o','i_vi, i_tum, 4',['zauv_i^o'])
        data,counts=m.transform(raw,[source])
        self.assertEqual(counts['added_records'],3)
        self.assertIn(b'pp4\n:vs:zauv_\tconj4 orth\n',data)
        self.assertIn(b':vs:zauv_i_t\tpp4 orth\n',data)
    def test_withhold_missing_conflicting_and_flagged_primary_parts(self):
        for raw in [self.raw.replace(b'za_-prens',b'wrong'),self.raw.replace(b'perfstem',b'perfstem orth'),self.raw+b':vs:other pp4\n',self.raw*2]:
            self.assertEqual(m.transform(raw,[row()])[0],raw)
        source=row();source['fields'].append(dict(name='itype',projection='4'))
        self.assertEqual(m.transform(self.raw,[source])[0],self.raw)
        self.assertEqual(m.transform(self.raw,[row(),row()])[0],self.raw)
    def test_withhold_voice_abbreviations_and_notation_only(self):
        for source in [row(alts=['za_praendor']),row(alts=['za-']),row(alts=['za_prendo']),row(field='3'),row(head='za_prendor#2')]:
            self.assertEqual(m.transform(self.raw,[source])[0],self.raw)
        self.assertIsNone(m.parts('zavi^o','i_vi, 4'))
    def test_private_output_expected_count_and_no_overwrite(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            p=Path(directory);candidate=p/'candidate';headers=p/'headers';source=p/'source';target=p/'out'
            candidate.write_bytes(self.raw);headers.write_text('synthetic');source.write_text('synthetic')
            with patch.object(m.alternates,'source_alternates',return_value=([row()],source,'synthetic')):
                with self.assertRaises(ValueError):m.prepare(candidate,headers,p/'lexica',target,4)
                self.assertFalse(target.exists());m.prepare(candidate,headers,p/'lexica',target,3)
                self.assertEqual(target.stat().st_mode&0o777,0o600)
                with self.assertRaises(FileExistsError):m.prepare(candidate,headers,p/'lexica',target,3)
                with self.assertRaises(ValueError):m.prepare(candidate,headers,p/'lexica',SCRIPT.parent/'forbidden',3)
if __name__=='__main__':unittest.main()
