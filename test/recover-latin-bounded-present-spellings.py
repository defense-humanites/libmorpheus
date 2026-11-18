#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/recover-latin-bounded-present-spellings.py'
spec = importlib.util.spec_from_file_location('m', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
PAIRS = [('co_ni^zio', 'co_izio'), ('ef-fi^bio', 'ecfa^bio'),
         ('neglezo', 'neclezo'), ('are-zacio', 'arzacio'), ('traizio', 'transjizio')]


def fixture(head, alternate):
    row = {'id': 'synthetic', 'headword': head, 'projection_error': None,
           'full_alternates': [alternate],
           'fields': [{'name': 'itype', 'projection': 'xi, xum, 3'},
                      {'name': 'pos', 'projection': 'v. a.'}]}
    stem, tag = m.regular.parts(head, '3', present_only=True)[0]
    lemma = m.regular.letters(head.encode())
    raw = b':le:' + lemma + b'\n:vs:' + stem + b' ' + tag + b'\n:vs:old perfstem\n:vs:old pp4\n'
    return row, raw


def transform(raw, rows):
    return m.regular.transform(raw, m.selected_rows(rows), 'present-only')


class Recovery(unittest.TestCase):
    def test_five_rules_preserve_source_bytes_and_quantities(self):
        rules = set()
        for head, alternate in PAIRS:
            row, raw = fixture(head, alternate)
            rules.add(m.spelling_rule(head, alternate))
            after, counts = transform(raw, [row])
            stem, tag = m.regular.parts(alternate, '3', present_only=True)[0]
            self.assertEqual(counts['added_records'], 1)
            self.assertEqual(after, raw.replace(b':vs:old perfstem',
                b':vs:' + stem + b'\t' + tag + b' orth\n:vs:old perfstem'))
            self.assertEqual(transform(after, [row])[0], after)
            self.assertEqual(row['fields'][0]['projection'], 'xi, xum, 3')
        self.assertEqual(len(rules), 5)
        self.assertNotIn(None, rules)

    def test_reject_unbounded_edits_abbreviations_missing_boundaries_and_homographs(self):
        for pair in [('di-zerto', 'zorto'), ('efzibio', 'eczabio'), ('arefizio', 'arfizio'),
                     ('neglezo', 'neclexo'), ('zaglezo', 'zacmezo'), ('conizio', 'coizo'),
                     ('traizio', 'tranjizio'), ('traizio#2', 'transjizio')]:
            self.assertIsNone(m.spelling_rule(*pair))

    def test_strict_grammar_voice_projection_and_subclass_guards(self):
        row, raw = fixture(*PAIRS[0])
        for grammar in ['3', 'xi, xum and yum, 3', 'xi, xum, 4', 'xi or yi, 3']:
            changed = copy.deepcopy(row); changed['fields'][0]['projection'] = grammar
            self.assertEqual(transform(raw, [changed])[0], raw)
        for field, value in [('projection_error', 'entity')]:
            changed = copy.deepcopy(row); changed[field] = value
            self.assertEqual(transform(raw, [changed])[0], raw)
        changed = copy.deepcopy(row); changed['fields'][1]['projection'] = 'v. dep.'
        self.assertEqual(transform(raw, [changed])[0], raw)
        changed, raw = fixture('neglo', 'neclio')
        self.assertEqual(transform(raw, [changed])[0], raw)

    def test_unique_source_and_unflagged_matching_primary_are_required(self):
        row, raw = fixture(*PAIRS[2])
        for candidate, rows in [(raw * 2, [row]), (raw, [row, row]),
                                (raw.replace(b'conj3\n', b'conj3 orth\n'), [row]),
                                (raw.replace(b'neglez', b'other'), [row])]:
            self.assertEqual(transform(candidate, rows)[0], candidate)

    def test_present_families_use_public_abi_cells_and_subclasses(self):
        for stem, tag, indicative, subjunctive in [(b'aze^g', b'conj3', 'azego', 'azegam'),
                (b'azi_', b'conj3_io', 'aziio', 'aziiam')]:
            family = m.present_family(stem, tag)
            self.assertEqual(len(family), 13)
            self.assertEqual(len({r['form'] for r in family}), 13)
            self.assertEqual(family[0]['form'], indicative)
            self.assertEqual(family[6]['form'], subjunctive)
            self.assertEqual((family[3]['number'], family[6]['mood'], family[12]['mood']), (3, 8, 5))
            self.assertEqual((family[12]['person'], family[12]['number']), (0, 0))
        with self.assertRaises(ValueError): m.present_family(b'az', b'conj4')

    def test_private_family_witnesses_bind_source_header_and_exact_candidate(self):
        row, raw = fixture(*PAIRS[0])
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            p = Path(directory); candidate = p/'candidate'; headers = p/'headers'; source = p/'source'; lexica = p/'lexica'
            candidate.write_bytes(raw); headers.write_bytes(b'headers'); source.write_bytes(b'source'); lexica.mkdir()
            with patch.object(m.regular.alternates, 'source_alternates', return_value=([row], source, 'pinned')):
                report = m.prepare(candidate, headers, lexica, p/'out', 1, p/'witness')
            row = json.loads((p/'witness').read_text())
            self.assertEqual(row['candidate_sha256'], report['output_sha256'])
            self.assertEqual(row['source_sha256'], m.hashlib.sha256(b'source').hexdigest())
            self.assertEqual(row['headers_sha256'], m.hashlib.sha256(b'headers').hexdigest())
            self.assertEqual(report['expected_family_cells'], 13)
            self.assertEqual((p/'out').stat().st_mode & 0o777, 0o600)
            self.assertEqual((p/'witness').stat().st_mode & 0o777, 0o600)
            self.assertEqual(candidate.read_bytes(), raw)

    def test_wrong_counts_aliases_and_existing_outputs_fail_before_writing(self):
        row, raw = fixture(*PAIRS[2])
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            p = Path(directory); candidate = p/'candidate'; headers = p/'headers'; source = p/'source'; lexica = p/'lexica'
            candidate.write_bytes(raw); headers.write_bytes(b'headers'); source.write_bytes(b'source'); lexica.mkdir()
            with patch.object(m.regular.alternates, 'source_alternates', return_value=([row], source, 'pinned')):
                with self.assertRaises(ValueError): m.prepare(candidate, headers, lexica, p/'out', 2, p/'witness')
                self.assertFalse((p/'out').exists()); self.assertFalse((p/'witness').exists())
                with self.assertRaises(ValueError): m.prepare(candidate, headers, lexica, p/'out', 1, p/'out')
                (p/'witness').write_bytes(b'keep')
                with self.assertRaises(FileExistsError): m.prepare(candidate, headers, lexica, p/'out', 1, p/'witness')
                self.assertFalse((p/'out').exists()); self.assertEqual((p/'witness').read_bytes(), b'keep')


if __name__ == '__main__':
    unittest.main()
