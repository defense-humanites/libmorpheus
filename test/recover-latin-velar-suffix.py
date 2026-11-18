#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from lxml import etree

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/recover-latin-velar-suffix.py'
spec = importlib.util.spec_from_file_location('m', SCRIPT); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def fixture():
    entry = etree.fromstring(b'<entryFree id="n1" key="zatingo2" n="2"><orth extent="full">za^-tingo</orth> (<orth type="alt" extent="full">-tinguo</orth>), <itype>e^re</itype><sense><hi rend="ital">v. a., to</hi> definition</sense></entryFree>')
    row, _ = m.first.review.projection.project(entry, 'Latin'); row['id'] = 'n1'
    return row, entry


class Recovery(unittest.TestCase):
    def test_expand_explicit_suffix_preserve_prefix_quantity_homograph_and_parts(self):
        row, entry = fixture(); lemma, stem, alt = m.proof(row, entry)
        self.assertEqual(lemma, b'zatingo#2')
        raw=b':le:zatingo#1\n:vs:za^-ting conj3\n:le:zatingo#2\n:vs:za^-ting conj3\n:vs:unrelated perfstem\n'
        data, counts = m.transform(raw, [row], {'n1': entry})
        self.assertEqual(counts['added_records'], 1)
        self.assertEqual(data,raw.replace(b':le:zatingo#2\n:vs:za^-ting conj3\n',b':le:zatingo#2\n:vs:za^-ting conj3\n:vs:za^-tingu\tconj3 orth\n'))
        self.assertEqual(m.transform(data, [row], {'n1': entry})[0], data)
        self.assertEqual(data.count(b'perfstem'),1); self.assertNotIn(b'pp4',data)
    def test_reject_bare_alternate_other_grammar_voice_and_quantities(self):
        row, entry = fixture()
        for change in ['bare','grammar','voice','quantity']:
            altered=copy.deepcopy(entry)
            if change=='bare': altered[1].text='tinguo'
            elif change=='grammar': altered[2].text='e_re'
            elif change=='voice': altered[3][0].text='v. dep.'
            else: altered[1].text='-ti_nguo'
            source,_=m.first.review.projection.project(altered,'Latin'); source['id']='n1'
            self.assertIsNone(m.proof(source,altered))
    def test_withhold_wrong_block_flags_duplicates_and_source_fields(self):
        row, entry=fixture();raw=b':le:zatingo#2\n:vs:za^-ting conj3\n'
        for data,rows in [(raw.replace(b'#2',b'#1'),[row]),(raw.replace(b'conj3',b'conj3 dep'),[row]),(raw*2,[row]),(raw,[row,row]),(raw.replace(b'za^-ting',b'other'),[row])]:
            self.assertEqual(m.transform(data,rows,{'n1':entry})[0],data)
        altered=copy.deepcopy(row); altered['fields'][1]['projection']='-tungo'
        self.assertIsNone(m.proof(altered,entry))
    def test_private_output_expected_count_and_no_overwrite(self):
        row,entry=fixture();raw=b':le:zatingo#2\n:vs:za^-ting conj3\n'
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            p=Path(directory);candidate=p/'candidate';headers=p/'headers';source=p/'source';lexica=p/'lexica';target=p/'out'
            candidate.write_bytes(raw);headers.write_bytes(b'headers');source.write_bytes(b'source');lexica.mkdir()
            with patch.object(m.first,'source_rows',return_value=([row],source,'pinned')),patch.object(m.first.review,'load_entries',return_value=({'n1':entry},source,'pinned')):
                with self.assertRaises(ValueError):m.prepare(candidate,headers,lexica,target,2)
                self.assertFalse(target.exists());m.prepare(candidate,headers,lexica,target,1)
                self.assertEqual(target.stat().st_mode&0o777,0o600)
                with self.assertRaises(FileExistsError):m.prepare(candidate,headers,lexica,target,1)


if __name__=='__main__':unittest.main()
