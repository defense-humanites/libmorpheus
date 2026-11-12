#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
from pathlib import Path
import unittest
import tempfile
from unittest.mock import patch
from lxml import etree

spec = importlib.util.spec_from_file_location('m', Path(__file__).resolve().parents[1] / 'tools/recover-latin-cited-present.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def fixture():
    entry = etree.fromstring(b'<entryFree id="n1" key="zaverto"><orth extent="full">za-verto</orth><orth type="alt" extent="full">zavorto</orth><itype>ti, sum, 3</itype><pos>v. a.</pos><sense><quote lang="la">zavortunt</quote></sense></entryFree>')
    row, _ = m.first.review.projection.project(entry, 'Latin')
    row['id'] = 'n1'; row['full_alternates'] = ['zavorto']
    return row, entry


class Recovery(unittest.TestCase):
    def test_present_only_and_idempotence(self):
        row, entry = fixture()
        raw = b':le:zaverto\n:vs:za-vert conj3\n:vs:za-vert perfstem\n:vs:za-vers pp4\n'
        data, counts = m.transform(raw, [row], {'n1': entry})
        self.assertEqual(counts['added_records'], 1)
        self.assertEqual(data, raw.replace(b':vs:za-vert conj3\n', b':vs:za-vert conj3\n:vs:zavort\tconj3 orth\n'))
        self.assertEqual(m.transform(data, [row], {'n1': entry})[0], data)
        self.assertEqual(row['fields'][2]['projection'], 'ti, sum, 3')
    def test_whole_word_language_and_compound_boundary(self):
        row, entry = fixture()
        for word, lang in [('nezavortunt', 'la'), ('zavortunt', 'en'), ('zavortum', 'la')]:
            changed = copy.deepcopy(entry); changed.find('.//quote').text = word; changed.find('.//quote').set('lang', lang)
            self.assertEqual(m.cited_alternates(row, changed), [])
        bare = copy.deepcopy(row); bare['full_alternates'] = ['vorto']
        self.assertEqual(m.cited_alternates(bare, entry), [])
    def test_grammar_voice_and_subclass(self):
        row, entry = fixture()
        for value in ['ti, sum, 4', '3', 'ti, sum, 3, extra']:
            changed = copy.deepcopy(row); changed['fields'][2]['projection'] = value
            self.assertEqual(m.cited_alternates(changed, entry), [])
        changed = copy.deepcopy(row); changed['fields'][3]['projection'] = 'v. dep.'
        self.assertEqual(m.cited_alternates(changed, entry), [])
        changed = copy.deepcopy(row); changed['full_alternates'] = ['zavorio']
        self.assertEqual(m.cited_alternates(changed, entry), [])
    def test_ambiguous_or_flagged_primary(self):
        row, entry = fixture(); raw = b':le:zaverto\n:vs:za-vert conj3\n'
        for candidate, rows in [(raw * 2, [row]), (raw, [row, row]), (raw.replace(b'conj3', b'conj3 dep'), [row]), (raw.replace(b'za-vert', b'other'), [row])]:
            self.assertEqual(m.transform(candidate, rows, {'n1': entry})[0], candidate)
    def test_separate_future_imperative_evidence_tier(self):
        row, entry = fixture()
        for word in ['zavorte', 'zavortite', 'zavortet']:
            entry.find('.//quote').text = word
            self.assertEqual(m.cited_alternates(row, entry), [])
            self.assertEqual(m.cited_alternates(row, entry, 'future-imperative'), ['zavorto'])
        changed = copy.deepcopy(row); changed['headword'] = 'zaverio'; changed['full_alternates'] = ['zavorio']
        for word in ['zavoriet', 'zavorite']:
            entry.find('.//quote').text = word
            self.assertEqual(m.cited_alternates(changed, entry, 'future-imperative'), ['zavorio'])
        entry.find('.//quote').text = 'zavortebat'
        self.assertEqual(m.cited_alternates(row, entry, 'future-imperative'), [])
    def test_private_output_and_expected_count(self):
        row, entry = fixture()
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2]) as directory:
            p = Path(directory); candidate = p/'candidate'; headers = p/'headers'; source = p/'source'; lexica = p/'lexica'; target = p/'out'
            candidate.write_bytes(b':le:zaverto\n:vs:za-vert conj3\n'); headers.write_bytes(b'headers'); source.write_bytes(b'source'); lexica.mkdir()
            with patch.object(m.regular.alternates, 'source_alternates', return_value=([row], source, 'pinned')), patch.object(m.first.review, 'load_entries', return_value=({'n1': entry}, source, 'pinned')):
                with self.assertRaises(ValueError): m.prepare(candidate, headers, lexica, target, 2)
                self.assertFalse(target.exists())
                m.prepare(candidate, headers, lexica, target, 1)
                self.assertEqual(target.stat().st_mode & 0o777, 0o600)
                with self.assertRaises(FileExistsError): m.prepare(candidate, headers, lexica, target, 1)


if __name__ == '__main__':
    unittest.main()
