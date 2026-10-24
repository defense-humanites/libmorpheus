#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from lxml import etree

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/recover-latin-backlinked-present.py'
spec = importlib.util.spec_from_file_location('m', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixture():
    row = {'id': 'n1', 'source_key': 'azego', 'headword': 'a_-ze^go', 'projection_error': None,
           'fields': [{'name': 'itype', 'projection': 'xi, ctum, 3'}, {'name': 'pos', 'projection': 'v. a.'}],
           'full_alternates': ['abze^go']}
    entry = etree.fromstring(b'<entryFree id="n2" key="abzego"><orth extent="full">ab-ze^go</orth>, v. azego.</entryFree>')
    return row, {'n2': entry}


RAW = b':le:azego\n:vs:a_-ze^g conj3\n:vs:old perfstem\n:vs:old pp4\n'


class Recovery(unittest.TestCase):
    def test_bidirectional_present_only_preserves_source_and_is_idempotent(self):
        row, entries = fixture()
        data, counts = m.transform(RAW, [row], entries)
        self.assertEqual(counts['added_records'], 1)
        self.assertEqual(data, RAW.replace(b':vs:a_-ze^g conj3\n', b':vs:a_-ze^g conj3\n:vs:abze^g\tconj3 orth\n'))
        self.assertEqual(m.transform(data, [row], entries)[0], data)
        self.assertEqual(row['fields'][0]['projection'], 'xi, ctum, 3')

    def test_plain_reference_with_only_compatible_fields_and_initial_qualifier(self):
        row, _ = fixture()
        for extra, tail in [('', 'azego.'), ('<itype>e^re</itype>, ', 'azego.'),
                            ('<itype>3</itype>, <pos>v. a.</pos>, ', 'azego.'),
                            ('', 'azego <sense><hi rend="ital">init.</hi></sense>')]:
            entry = etree.fromstring(('<entryFree id="n2"><orth extent="full">abzego</orth>, '+extra+'v. '+tail+'</entryFree>').encode())
            self.assertEqual(m.transform(RAW, [row], {'n2': entry})[1]['added_records'], 1)

    def test_embedded_ambiguous_or_wrong_target_reference_is_withheld(self):
        row, entries = fixture()
        for xml in [
            '<orth extent="full">abzego</orth>, v. other.',
            '<orth extent="full">abzego</orth>, sometimes v. azego.',
            '<orth extent="full">abzego</orth><sense>v. azego.</sense>',
            '<orth extent="full">abzego</orth><quote>v. azego.</quote>',
            '<orth extent="full">abzego</orth>, <itype>2</itype>, v. azego.',
            '<orth extent="full">abzego</orth>, <pos>v. dep.</pos>, v. azego.',
            '<orth extent="full">abzego</orth>, v. azego, and other.',
            '<orth extent="full">abzego</orth><orth extent="full">other</orth>, v. azego.',
            '<orth extent="full" type="alt">abzego</orth>, v. azego.']:
            entry = etree.fromstring(('<entryFree id="n2">'+xml+'</entryFree>').encode())
            self.assertEqual(m.transform(RAW, [row], {'n2': entry})[0], RAW)
        duplicate = copy.deepcopy(entries['n2']); duplicate.set('id', 'n3')
        self.assertEqual(m.transform(RAW, [row], dict(entries, n3=duplicate))[0], RAW)

    def test_no_cross_article_paradigm_without_same_article_full_alternate(self):
        row, entries = fixture()
        for change in ('absent', 'voice', 'grammar', 'shortened', 'subclass', 'homograph'):
            other = copy.deepcopy(row)
            if change == 'absent': other['full_alternates'] = []
            elif change == 'voice': other['fields'][1]['projection'] = 'v. dep.'
            elif change == 'grammar': other['fields'][0]['projection'] = '3'
            elif change == 'shortened': other['full_alternates'] = ['zego']
            elif change == 'subclass': other['full_alternates'] = ['abzegio']
            else: other['source_key'] = 'azego2'
            self.assertEqual(m.transform(RAW, [other], entries)[0], RAW)
        for candidate, rows in [(RAW*2,[row]), (RAW,[row,row]),
                                (RAW.replace(b'conj3\n',b'conj3 orth\n'),[row]),
                                (RAW.replace(b'a_-ze^g',b'other'),[row])]:
            self.assertEqual(m.transform(candidate, rows, entries)[0], candidate)

    def test_private_source_and_output_guards(self):
        row, entries = fixture()
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            p = Path(directory); candidate = p/'candidate'; headers = p/'headers'; source = p/'source'; lexica = p/'lexica'; target = p/'out'
            candidate.write_bytes(RAW); headers.write_bytes(b'headers'); source.write_bytes(b'source'); lexica.mkdir()
            with patch.object(m.regular.alternates, 'source_alternates', return_value=([row],source,'pinned')), patch.object(m.first.review,'load_entries',return_value=(entries,source,'pinned')):
                with self.assertRaises(ValueError): m.prepare(candidate,headers,lexica,target,2)
                self.assertFalse(target.exists())
                m.prepare(candidate,headers,lexica,target,1)
                self.assertEqual(target.stat().st_mode & 0o777,0o600)
                with self.assertRaises(FileExistsError): m.prepare(candidate,headers,lexica,target,1)
                with self.assertRaises(ValueError): m.prepare(candidate,headers,lexica,SCRIPT.parent/'forbidden',1)
            with patch.object(m.regular.alternates, 'source_alternates', return_value=([row],source,'pinned')), patch.object(m.first.review,'load_entries',return_value=(entries,source,'changed')):
                with self.assertRaises(ValueError): m.prepare(candidate,headers,lexica,p/'invalid',1)
                self.assertFalse((p/'invalid').exists())


if __name__ == '__main__':
    unittest.main()
