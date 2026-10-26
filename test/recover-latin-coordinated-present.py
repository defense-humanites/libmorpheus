#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from lxml import etree

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/recover-latin-coordinated-present.py'
spec = importlib.util.spec_from_file_location('m', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
RAW = b':le:azego\n:vs:a_-ze^g conj3\n:vs:old perfstem\n:vs:old pp4\n'


def fixture(body='<quote lang="la">azenitur</quote>'):
    row = {'id': 'n1', 'source_key': 'azego', 'headword': 'a_-ze^go',
           'projection_error': None, 'full_alternates': ['a_-ze^no'],
           'fields': [{'name': 'itype', 'projection': 'xi, xum and yum, 3'},
                      {'name': 'pos', 'projection': 'v. a.'}]}
    entry = etree.fromstring(('<entryFree id="n1" key="azego">'+body+'</entryFree>').encode())
    return row, {'n1': entry}


class Recovery(unittest.TestCase):
    def test_quote_backed_present_preserves_bytes_quantities_and_other_parts(self):
        row, entries = fixture()
        data, counts = m.transform(RAW, [row], entries)
        self.assertEqual(counts['added_records'], 1)
        self.assertEqual(data, RAW.replace(b':vs:a_-ze^g conj3\n',
            b':vs:a_-ze^g conj3\n:vs:a_-ze^n\tconj3 orth\n'))
        self.assertEqual(m.transform(data, [row], entries)[0], data)
        self.assertEqual(row['fields'][0]['projection'], 'xi, xum and yum, 3')

    def test_only_explicit_latin_quote_tokens_count(self):
        for body in ['<quote lang="la"><hi>ĂZĒNITUR</hi>,</quote>',
                     '<sense><cit><quote lang="la">azenitur.</quote></cit></sense>']:
            row, entries = fixture(body)
            self.assertEqual(m.transform(RAW, [row], entries)[1]['added_records'], 1)
        for body in ['<sense>azenitur</sense>', '<quote lang="en">azenitur</quote>',
                     '<quote lang="la">azegitur</quote>', '<quote lang="la">azexit</quote>',
                     '<quote lang="la">preazenitur</quote>', '<quote lang="la">αazenitur</quote>']:
            row, entries = fixture(body)
            self.assertEqual(m.transform(RAW, [row], entries)[0], RAW)

    def test_entities_in_quote_are_withheld(self):
        row, entries = fixture()
        parser = etree.XMLParser(resolve_entities=False)
        entries['n1'] = etree.fromstring(b'<!DOCTYPE entryFree [<!ENTITY x "azenitur">]><entryFree><quote lang="la">&x;</quote></entryFree>', parser)
        self.assertEqual(m.transform(RAW, [row], entries)[0], RAW)

    def test_no_general_edit_rule_or_subclass_transfer(self):
        row, entries = fixture()
        for alternate in ['ze^no', 'abze^no', 'a_-ze^nio', 'a_-ze^go', 'a_-ye^no']:
            other = copy.deepcopy(row); other['full_alternates'] = [alternate]
            self.assertEqual(m.transform(RAW, [other], entries)[0], RAW)
        for grammar in ['xi, xum, 3', 'xi, xum or yum, 3', 'xi, xum and yum, 2', '3']:
            other = copy.deepcopy(row); other['fields'][0]['projection'] = grammar
            self.assertEqual(m.transform(RAW, [other], entries)[0], RAW)
        other = copy.deepcopy(row); other['fields'][1]['projection'] = 'v. dep.'
        self.assertEqual(m.transform(RAW, [other], entries)[0], RAW)
        other = copy.deepcopy(row); other['projection_error'] = 'entity'
        self.assertEqual(m.transform(RAW, [other], entries)[0], RAW)

    def test_source_block_and_primary_ambiguity_are_withheld(self):
        row, entries = fixture()
        for candidate, rows in [(RAW * 2, [row]), (RAW, [row, row]),
                                (RAW.replace(b'conj3\n', b'conj3 orth\n'), [row]),
                                (RAW.replace(b'a_-ze^g', b'other'), [row])]:
            self.assertEqual(m.transform(candidate, rows, entries)[0], candidate)
        with self.assertRaisesRegex(ValueError, 'missing source'):
            m.transform(RAW, [row], {})

    def test_private_witness_is_bound_to_candidate_and_source(self):
        row, entries = fixture()
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            p = Path(directory); candidate = p/'candidate'; headers = p/'headers'; source = p/'source'; lexica = p/'lexica'
            candidate.write_bytes(RAW); headers.write_bytes(b'headers'); source.write_bytes(b'source'); lexica.mkdir()
            with patch.object(m.regular.alternates, 'source_alternates', return_value=([row], source, 'pinned')), patch.object(m.first.review, 'load_entries', return_value=(entries, source, 'pinned')):
                report = m.prepare(candidate, headers, lexica, p/'out', 1, p/'witness')
                witness = json.loads((p/'witness').read_text())
                self.assertEqual(witness['candidate_sha256'], report['output_sha256'])
                self.assertEqual(witness['source_sha256'], m.hashlib.sha256(b'source').hexdigest())
                self.assertEqual((witness['form'], witness['lemma']), ('azenitur', 'azego'))
                self.assertEqual((p/'out').stat().st_mode & 0o777, 0o600)
                self.assertEqual((p/'witness').stat().st_mode & 0o777, 0o600)
                self.assertEqual(candidate.read_bytes(), RAW)

    def test_expected_count_output_alias_and_no_overwrite_guards(self):
        row, entries = fixture()
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            p = Path(directory); candidate = p/'candidate'; headers = p/'headers'; source = p/'source'; lexica = p/'lexica'
            candidate.write_bytes(RAW); headers.write_bytes(b'headers'); source.write_bytes(b'source'); lexica.mkdir()
            with patch.object(m.regular.alternates, 'source_alternates', return_value=([row], source, 'pinned')), patch.object(m.first.review, 'load_entries', return_value=(entries, source, 'pinned')):
                with self.assertRaises(ValueError): m.prepare(candidate, headers, lexica, p/'out', 2, p/'witness')
                self.assertFalse((p/'out').exists()); self.assertFalse((p/'witness').exists())
                with self.assertRaises(ValueError): m.prepare(candidate, headers, lexica, p/'out', 1, p/'out')
                (p/'witness').write_bytes(b'keep')
                with self.assertRaises(FileExistsError): m.prepare(candidate, headers, lexica, p/'out', 1, p/'witness')
                self.assertFalse((p/'out').exists()); self.assertEqual((p/'witness').read_bytes(), b'keep')
                with self.assertRaises(ValueError): m.prepare(candidate, headers, lexica, p/'out', 1, SCRIPT.parent/'forbidden')


if __name__ == '__main__':
    unittest.main()
