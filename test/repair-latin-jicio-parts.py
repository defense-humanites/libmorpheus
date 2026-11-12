#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/repair-latin-jicio-parts.py'
spec = importlib.util.spec_from_file_location('parts', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def row(head='za_-i^ci^o#2', alts=None, itype='je_ci, jectum, 3'):
    return dict(headword=head, projection_error=None,
                fields=[dict(name='itype', projection=itype)], full_alternates=alts or ['za_ji^ci^o'])


class Parts(unittest.TestCase):
    raw = b':le:zaicio#2\n:vs:za_-i^c conj3_io\n:vs:za_-i^cje_c perfstem\n:vs:za_-i^cject pp4\n'

    def test_exact_repair_alternate_quantities_homograph_idempotence(self):
        data, counts = m.transform(self.raw, [row()])
        self.assertEqual(counts, {'added_records': 1, 'changed_lemma_blocks': 1, 'repaired_records': 2})
        self.assertIn(b':vs:za_-je_c\tperfstem\n', data)
        self.assertIn(b':vs:za_-ject\tpp4\n', data)
        self.assertIn(b':vs:za_ji^c\tconj3_io orth\n', data)
        self.assertEqual(m.transform(data, [row()])[0], data)
        self.assertEqual(m.transform(self.raw.replace(b'^', b''), [row()])[1]['repaired_records'], 2)

    def test_jact_variant_and_already_correct_parts(self):
        raw = self.raw.replace(b'ject', b'jact')
        data, counts = m.transform(raw, [row(itype='je_ci, jactum, 3')])
        self.assertIn(b'za_-jact\tpp4', data)
        self.assertEqual(counts['repaired_records'], 2)
        correct = self.raw.replace(b'i^cje_c', b'je_c').replace(b'i^cject', b'ject')
        self.assertNotIn('repaired_records', m.transform(correct, [row()])[1])

    def test_withhold_source_voice_incomplete_prefix_and_ambiguity(self):
        for source in [row(alts=['za-']), row(alts=['za_jicior']), row(alts=['otherjicio']),
                       row(itype='3'), row(head='za_-jicio#2'),
                       row(alts=['za_jicio', 'za_-jicio'])]:
            self.assertEqual(m.transform(self.raw, [source])[0], self.raw)
        self.assertEqual(m.transform(self.raw, [row(), row()])[0], self.raw)
        self.assertEqual(m.transform(self.raw * 2, [row()])[0], self.raw * 2)
        conflicting = row(); conflicting['fields'].append(dict(name='itype', projection='4'))
        self.assertEqual(m.transform(self.raw, [conflicting])[0], self.raw)

    def test_exact_candidate_required_and_unrelated_records_preserved(self):
        for raw in [self.raw.replace(b'conj3_io', b'conj3_io dep'), self.raw.replace(b'za_-i^cje_c', b'other'),
                    self.raw.replace(b'perfstem', b'perfstem orth'), self.raw + b':vs:other pp4\n']:
            self.assertEqual(m.transform(raw, [row()])[0], raw)
        raw = self.raw + b':vs:unrelated conj4\n'
        self.assertTrue(m.transform(raw, [row()])[0].endswith(b':vs:unrelated conj4\n'))

    def test_private_output_expected_count_and_no_overwrite(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            p = Path(directory); candidate=p/'candidate'; headers=p/'headers'; source=p/'source'; target=p/'out'
            candidate.write_bytes(self.raw); headers.write_text('synthetic'); source.write_text('synthetic')
            with patch.object(m.alternates, 'source_alternates', return_value=([row()], source, 'synthetic')):
                with self.assertRaises(ValueError): m.prepare(candidate, headers, p/'lexica', target, 3)
                self.assertFalse(target.exists())
                m.prepare(candidate, headers, p/'lexica', target, 2)
                self.assertEqual(target.stat().st_mode & 0o777, 0o600)
                with self.assertRaises(FileExistsError): m.prepare(candidate, headers, p/'lexica', target, 2)
                with self.assertRaises(ValueError): m.prepare(candidate, headers, p/'lexica', SCRIPT.parent/'forbidden', 2)


if __name__ == '__main__':
    unittest.main()
