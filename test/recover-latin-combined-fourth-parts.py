#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
SCRIPT=Path(__file__).resolve().parents[1]/'tools/recover-latin-combined-fourth-parts.py'
spec=importlib.util.spec_from_file_location('m',SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def row(tier='with-supine'):
    return dict(headword='za_vi^o#2',projection_error=None,full_alternates=['zauvi^o'],fields=[
        dict(name='orth',projection='za_vi^o',type=None),dict(name='orth',projection='zauvi^o',type='alt'),
        *[dict(name='itype',projection=t,type=None) for t in m.TIERS[tier]],dict(name='pos',projection='v. a.',type=None)])

class Recovery(unittest.TestCase):
    def test_supine_both_perfects_complete_alternate_and_idempotence(self):
        source=row();lemma,raw,records,n=m.proof(source,'with-supine')
        data,counts=m.transform(raw,[source])
        self.assertEqual(data,raw+records)
        self.assertEqual(n,8);self.assertEqual(counts,{'added_stem_records':8,'recovered_headers':1})
        self.assertIn(b':le:zavio#2\n',records);self.assertIn(b':vs:za_vu^ perfstem\n',records)
        self.assertIn(b':vs:zauvi_t pp4 orth\n',records)
        self.assertEqual(m.transform(data,[source])[0],data)
    def test_perfect_only_never_invents_supine_or_moves_source_fields(self):
        source=row('perfect-only');before=copy.deepcopy(source)
        lemma,raw,records,n=m.proof(source,'perfect-only')
        self.assertEqual(n,6);self.assertNotIn(b'pp4',records)
        self.assertIn(b'<itype>i_vi, or u^i, 4</itype>',raw)
        self.assertEqual(source,before)
        self.assertEqual(m.transform(raw,[source],'perfect-only')[0],raw+records)
    def test_exact_header_source_uniqueness_existing_block_and_flags(self):
        source=row();lemma,raw,records,n=m.proof(source,'with-supine')
        for candidate,rows in [(raw*2,[source]),(raw,[source,source]),(b'altered\n',[source]),(raw+b':le:'+lemma+b'\n',[source])]:
            self.assertEqual(m.transform(candidate,rows)[0],candidate)
        for change in ['voice','grammar','adjacency','alternate','notation','extra']:
            altered=copy.deepcopy(source)
            if change=='voice':altered['fields'][-1]['projection']='v. dep.'
            if change=='grammar':altered['fields'][2]['projection']='i_vi'
            if change=='adjacency':altered['fields'].insert(3,dict(name='pos',projection='v. a.'))
            if change=='alternate':altered['full_alternates']=['zauvior']
            if change=='notation':altered['full_alternates']=['za_vi_o']
            if change=='extra':altered['fields'].append(dict(name='gen',projection='n.'))
            self.assertIsNone(m.proof(altered,'with-supine'))
        with self.assertRaises(ValueError):m.transform(raw,[source],'unknown')
    def test_private_output_expected_count_and_no_overwrite(self):
        source=row();lemma,raw,records,n=m.proof(source,'with-supine')
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            p=Path(directory);candidate=p/'candidate';headers=p/'headers';xml=p/'source';target=p/'out'
            candidate.write_bytes(raw);headers.write_text('synthetic');xml.write_text('synthetic')
            with patch.object(m.alternates,'source_alternates',return_value=([source],xml,'synthetic')):
                with self.assertRaises(ValueError):m.prepare(candidate,headers,p/'lexica',target,2)
                self.assertFalse(target.exists());m.prepare(candidate,headers,p/'lexica',target,1)
                self.assertEqual(target.stat().st_mode&0o777,0o600)
                with self.assertRaises(FileExistsError):m.prepare(candidate,headers,p/'lexica',target,1)
                with self.assertRaises(ValueError):m.prepare(candidate,headers,p/'lexica',SCRIPT.parent/'forbidden',1)
if __name__=='__main__':unittest.main()
