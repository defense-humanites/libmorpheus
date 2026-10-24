#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/recover-latin-vowel-present.py'
spec = importlib.util.spec_from_file_location('m', SCRIPT); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def fixture():
    return {'id': 'n1', 'headword': 'za_-pe^rgo#2', 'projection_error': None,
            'fields': [{'name': 'itype', 'projection': 'xi, ctum, 3'}, {'name': 'pos', 'projection': 'v. a.'}],
            'full_alternates': ['za_pa^r-go']}


class Recovery(unittest.TestCase):
    def test_single_internal_vowel_and_preserved_prefix(self):
        self.assertTrue(m.vowel_pair('za_-pe^rgo#2', 'za_pa^r-go'))
        self.assertTrue(m.vowel_pair('zapargo', 'zapergo'))
        for head, alt in [('zapergo', 'zepergo'), ('zapergo', 'zaparco'), ('zapergo', 'pargo'), ('zapergo', 'zapirgo'), ('zapealgo', 'zapeargo'), ('zepa-rgo', 'zapa-rgo')]:
            self.assertFalse(m.vowel_pair(head, alt))
    def test_preserve_homograph_quantity_and_other_parts(self):
        row = fixture(); raw = b':le:zapergo#1\n:vs:za_-perg conj3\n:le:zapergo#2\n:vs:za_-perg conj3\n:vs:old perfstem\n'
        data, counts = m.transform(raw, [row])
        self.assertEqual(counts['added_records'], 1)
        self.assertEqual(data, raw.replace(b':le:zapergo#2\n:vs:za_-perg conj3\n', b':le:zapergo#2\n:vs:za_-perg conj3\n:vs:za_pa^r-g\tconj3 orth\n'))
        self.assertEqual(m.transform(data, [row])[0], data)
        self.assertEqual(data.count(b'perfstem'), 1); self.assertNotIn(b'pp4', data)
    def test_reject_voice_grammar_and_incomplete_alternate(self):
        row = fixture(); raw = b':le:zapergo#2\n:vs:za_-perg conj3\n'
        for change in ['voice', 'grammar', 'alternate']:
            changed = copy.deepcopy(row)
            if change == 'voice': changed['fields'][1]['projection'] = 'v. dep.'
            elif change == 'grammar': changed['fields'][0]['projection'] = 'xi, ctum, 4'
            else: changed['full_alternates'] = ['-pargo']
            self.assertEqual(m.transform(raw, [changed])[0], raw)
    def test_withhold_ambiguous_or_flagged_canonical(self):
        row = fixture(); raw = b':le:zapergo#2\n:vs:za_-perg conj3\n'
        for data, rows in [(raw * 2, [row]), (raw, [row, row]), (raw.replace(b'conj3', b'conj3 dep'), [row]), (raw.replace(b'za_-perg', b'other'), [row])]:
            self.assertEqual(m.transform(data, rows)[0], data)
    def test_private_output_guards(self):
        row = fixture()
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            p = Path(directory); candidate = p/'candidate'; headers = p/'headers'; source = p/'source'; lexica = p/'lexica'; target = p/'out'
            candidate.write_bytes(b':le:zapergo#2\n:vs:za_-perg conj3\n'); headers.write_bytes(b'headers'); source.write_bytes(b'source'); lexica.mkdir()
            with patch.object(m.boundary.regular.alternates, 'source_alternates', return_value=([row], source, 'pinned')):
                with self.assertRaises(ValueError): m.prepare(candidate, headers, lexica, target, 2)
                self.assertFalse(target.exists()); m.prepare(candidate, headers, lexica, target, 1)
                self.assertEqual(target.stat().st_mode & 0o777, 0o600)
                with self.assertRaises(FileExistsError): m.prepare(candidate, headers, lexica, target, 1)


if __name__ == '__main__':
    unittest.main()
