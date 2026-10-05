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

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/audit-latin-remaining-presents.py'
spec = importlib.util.spec_from_file_location('audit', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixture():
    row = {'id': 'n1', 'headword': 'za_-pe^rgo#2', 'projection_error': None,
           'fields': [{'name': 'itype', 'projection': 'xi, ctum, 3'},
                      {'name': 'pos', 'projection': 'v. a.'}],
           'full_alternates': ['za_pa^r-go', 'pe^rgo']}
    entry = etree.fromstring(b'<entryFree id="n1"><orth extent="full">synthetic</orth><sense><quote lang="la">synthetic quotation</quote></sense></entryFree>')
    candidate = b':le:zapergo#2\n:vs:za_-perg conj3\n:vs:old perfstem\n'
    return candidate, row, {'n1': entry}


class Audit(unittest.TestCase):
    def test_remaining_variants_share_article_and_keep_private_evidence(self):
        candidate, row, entries = fixture()
        before = copy.deepcopy(row)
        dossiers, report = m.inventory(candidate, [row], entries)
        self.assertEqual(report['variants'], 2)
        self.assertEqual(report['articles'], 1)
        self.assertEqual(report['spelling_shapes'], {'deletion': 1, 'single_substitution': 1})
        self.assertEqual(report['delimiter_reviews'], {'first_delimited_segment_not_retained': 1,
                                                      'first_delimited_segment_retained': 1})
        self.assertEqual(report['quotation_reviews'], {'has_latin_quote': 2})
        self.assertEqual(row, before)
        self.assertTrue(all(r['candidate_lemma'] == 'zapergo#2' for r in dossiers))
        self.assertTrue(any(r['proposed_present'] == 'za_pa^r-g' for r in dossiers))
        self.assertTrue(all(r['latin_quotes'] == ['synthetic quotation'] for r in dossiers))
        self.assertNotIn('synthetic', json.dumps(report))

    def test_existing_orthographic_records_are_removed_from_inventory(self):
        candidate, row, entries = fixture()
        candidate += b':vs:za_par-g conj3 orth\n'
        dossiers, report = m.inventory(candidate, [row], entries)
        self.assertEqual(report['variants'], 1)
        self.assertEqual(dossiers[0]['alternate'], 'pe^rgo')

    def test_grammar_voice_subclass_and_incomplete_spellings_are_withheld(self):
        candidate, row, entries = fixture()
        for change in ('grammar', 'voice', 'subclass', 'incomplete'):
            changed = copy.deepcopy(row)
            if change == 'grammar': changed['fields'][0]['projection'] = '3'
            elif change == 'voice': changed['fields'][1]['projection'] = 'v. dep.'
            elif change == 'subclass': changed['full_alternates'] = ['zapargio']
            else: changed['full_alternates'] = ['-pargo']
            self.assertEqual(m.inventory(candidate, [changed], entries)[1]['variants'], 0)

    def test_ambiguous_blocks_flags_and_unmatched_primary_are_withheld(self):
        candidate, row, entries = fixture()
        for changed in (candidate * 2, candidate.replace(b'conj3', b'conj3 dep'),
                        candidate.replace(b'za_-perg', b'other')):
            self.assertEqual(m.inventory(changed, [row], entries)[1]['variants'], 0)
        duplicate = dict(copy.deepcopy(row), id='n2')
        self.assertEqual(m.inventory(candidate, [row, duplicate], dict(entries, n2=entries['n1']))[1]['variants'], 0)
        with self.assertRaises(ValueError): m.inventory(candidate, [row, row], entries)
        with self.assertRaises(ValueError): m.inventory(candidate, [row], {})

    def test_private_outputs_counts_and_unchanged_inputs(self):
        candidate_bytes, row, entries = fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate, headers, source, lexica, output = [root / name for name in ('candidate', 'headers', 'source', 'lexica', 'output')]
            candidate.write_bytes(candidate_bytes); headers.write_bytes(b'headers'); source.write_bytes(b'source'); lexica.mkdir()
            with patch.object(m.regular.alternates, 'source_alternates', return_value=([row], source, 'pinned')), \
                    patch.object(m.first.review, 'load_entries', return_value=(entries, source, 'pinned')):
                for expected, articles in ((3, 1), (2, 2)):
                    with self.assertRaises(ValueError): m.prepare(candidate, headers, lexica, output, expected, articles)
                    self.assertFalse(output.exists())
                report = m.prepare(candidate, headers, lexica, output, 2, 1)
                self.assertEqual(output.stat().st_mode & 0o777, 0o600)
                self.assertEqual(candidate.read_bytes(), candidate_bytes)
                self.assertNotIn('synthetic quotation', json.dumps(report))
                self.assertEqual(len(output.read_text().splitlines()), 2)
                with self.assertRaises(FileExistsError): m.prepare(candidate, headers, lexica, output, 2, 1)
                with self.assertRaises(ValueError): m.prepare(candidate, headers, lexica, SCRIPT.parent / 'private', 2, 1)

    def test_source_change_rejected_before_output(self):
        _, row, entries = fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(m.regular.alternates, 'source_alternates', return_value=([row], root / 'source', 'pinned')), \
                    patch.object(m.first.review, 'load_entries', return_value=(entries, root / 'other', 'pinned')):
                with self.assertRaisesRegex(ValueError, 'source changed'):
                    m.prepare(root / 'candidate', root / 'headers', root / 'lexica', root / 'output')
                self.assertFalse((root / 'output').exists())

    def test_private_spelling_shapes_ignore_notation_and_keep_homographs(self):
        for head, alternate, shape in [('za_-pargo#2', 'zapargo', 'notation_only'),
                                       ('zapargo', 'zapp argo'.replace(' ', ''), 'insertion'),
                                       ('zapargo', 'zagro', 'multiple_letter_change')]:
            self.assertEqual(m.spelling_shape(head, alternate)['shape'], shape)

    def test_diagnostic_proposal_cannot_change_existing_records(self):
        raw = b':le:synthetic\n:vs:root conj3\n'
        with self.assertRaises(ValueError): m.inserted_records(raw, raw.replace(b'root', b'changed'))
        with self.assertRaises(ValueError): m.inserted_records(raw, raw + b':vs:extra perfstem orth\n')
        self.assertEqual(m.inserted_records(raw, raw + b':vs:extra conj3 orth\n'), [(b'synthetic', b'extra', b'conj3')])


if __name__ == '__main__':
    unittest.main()
