#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/recover-latin-boundary-present.py'
spec = importlib.util.spec_from_file_location('m', SCRIPT); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def fixture(head='a_-ze^go', alternate='abze^go'):
    return {'id': 'n1', 'headword': head, 'projection_error': None,
            'fields': [{'name': 'itype', 'projection': 'xi, ctum, 3'}, {'name': 'pos', 'projection': 'v. a.'}],
            'full_alternates': [alternate]}


class Recovery(unittest.TestCase):
    def test_five_boundary_patterns(self):
        for head, alt in [('a_-ze^go', 'abze^go'), ('dis-ze^go', 'di_ze^go'), ('trans-ze^go', 'tra_ze^go'), ('ex-sze^go', 'exze^go'), ('transze^go', 'trans-sze^go')]:
            self.assertTrue(m.boundary_pair(head, alt))
        for head, alt in [('di_-ze^go', 'zogo'), ('trans-ze^go', 'trezego'), ('ex-sze^go', 'exzigo'), ('transzego', 'trans-sego')]:
            self.assertFalse(m.boundary_pair(head, alt))
    def test_preserve_alternate_quantity_present_only_and_idempotence(self):
        row = fixture(); raw = b':le:azego\n:vs:a_-zeg conj3\n:vs:old perfstem\n:vs:old pp4\n'
        data, counts = m.transform(raw, [row])
        self.assertEqual(counts['added_records'], 1)
        self.assertEqual(data, raw.replace(b':vs:a_-zeg conj3\n', b':vs:a_-zeg conj3\n:vs:abze^g\tconj3 orth\n'))
        self.assertEqual(m.transform(data, [row])[0], data)
        self.assertEqual(row['fields'][0]['projection'], 'xi, ctum, 3')
    def test_withhold_grammar_voice_abbreviation_and_subclass(self):
        row = fixture(); raw = b':le:azego\n:vs:a_-ze^g conj3\n'
        for change in ['grammar', 'voice', 'abbreviation', 'subclass']:
            altered = copy.deepcopy(row)
            if change == 'grammar': altered['fields'][0]['projection'] = '3'
            elif change == 'voice': altered['fields'][1]['projection'] = 'v. dep.'
            elif change == 'abbreviation': altered['full_alternates'] = ['ab-']
            else: altered['full_alternates'] = ['abzegio']
            self.assertEqual(m.transform(raw, [altered])[0], raw)
    def test_withhold_duplicates_flags_and_wrong_primary(self):
        row = fixture(); raw = b':le:azego\n:vs:a_-ze^g conj3\n'
        for candidate, rows in [(raw * 2, [row]), (raw, [row, row]), (raw.replace(b'conj3', b'conj3 orth'), [row]), (raw.replace(b'a_-ze^g', b'other'), [row])]:
            self.assertEqual(m.transform(candidate, rows)[0], candidate)
    def test_private_output_guards(self):
        row = fixture()
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            p = Path(directory); candidate = p/'candidate'; headers = p/'headers'; source = p/'source'; lexica = p/'lexica'; target = p/'out'
            candidate.write_bytes(b':le:azego\n:vs:a_-ze^g conj3\n'); headers.write_bytes(b'headers'); source.write_bytes(b'source'); lexica.mkdir()
            with patch.object(m.regular.alternates, 'source_alternates', return_value=([row], source, 'pinned')):
                with self.assertRaises(ValueError): m.prepare(candidate, headers, lexica, target, 2)
                self.assertFalse(target.exists()); m.prepare(candidate, headers, lexica, target, 1)
                self.assertEqual(target.stat().st_mode & 0o777, 0o600)
                with self.assertRaises(FileExistsError): m.prepare(candidate, headers, lexica, target, 1)


if __name__ == '__main__':
    unittest.main()
