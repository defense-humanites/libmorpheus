#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
from collections import Counter
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from lxml import etree

spec = importlib.util.spec_from_file_location('source_present', Path(__file__).resolve().parents[1] /
                                           'tools/qualify-latin-isolated-source-present.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def trial():
    return {'lemma': 'zzsourcezo#2', 'source_field_shape': 'bare_conjugation_digit',
        'source_field_position': 1, 'header': {'id': 'synthetic', 'headword': 'zzsourcezo#2',
            'fields': [{'name': 'itype', 'projection': 'zzpast'}, {'name': 'itype', 'projection': '1'}]}}


def entries(extent='full'):
    return {'synthetic': etree.fromstring(('<entryFree><orth extent="'+extent+'">zzsourcezo</orth></entryFree>').encode())}


class SourcePresent(unittest.TestCase):
    def test_selects_source_digit_not_expanded_class_and_preserves_homograph(self):
        t = trial()
        other = dict(t, source_field_shape='other_field_structure')
        index, selected = m.select_source_trial([other, t], entries(), 1)
        self.assertEqual(index, 2)
        self.assertEqual(selected['digit'], 1)
        self.assertEqual(selected['lemma'], 'zzsourcezo#2')
        self.assertEqual(selected['header'], t['header'])
        self.assertNotIn('digit', t)
        self.assertEqual(len(m.terminal.source_present_family(selected)), 13)

    def test_conflicting_terminal_digit_and_duplicate_bare_fields_abort(self):
        for value in ('zzpast, zzsup, 3', '1'):
            t = trial(); t['header']['fields'][0]['projection'] = value
            with self.assertRaisesRegex(ValueError, 'ambiguous or conflicts'):
                m.select_source_trial([t], entries(), 1)

    def test_nonunique_successful_digits_and_unsupported_class_abort(self):
        t = trial()
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            m.select_source_trial([t, t], entries(), 1)
        t['header']['fields'][1]['projection'] = '2'
        with self.assertRaisesRegex(ValueError, 'unsupported source family'):
            m.select_source_trial([t], entries(), 2)
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            m.select_source_trial([], entries(), 1)

    def test_full_literal_identity_and_expected_digit_are_required(self):
        t = trial()
        with self.assertRaisesRegex(ValueError, 'full literal'):
            m.select_source_trial([t], entries('partial'), 1)
        t['lemma'] = 'zzother'
        with self.assertRaisesRegex(ValueError, 'full literal'):
            m.select_source_trial([t], entries(), 1)
        with self.assertRaisesRegex(ValueError, 'ambiguous or conflicts'):
            m.select_source_trial([trial()], entries(), 3)

    def test_changed_route_review_resolves_shared_grammar_and_keeps_literals_private(self):
        def row(preverb):
            return SimpleNamespace(workword=b'zzform', lemma=b'zzsourcezo', part_of_speech=2,
                person=1, number=1, gender=0, grammatical_case=0, tense=1, mood=4, voice=1,
                degree=0, preverb=preverb, raw_preverb=preverb, stem=b'zzstem', suffix=b'', ending=b'o')
        derived, direct = row(b'zzprefix'), row(b'')
        old = SimpleNamespace(analyses=lambda *a, **k: [derived])
        new = SimpleNamespace(analyses=lambda *a, **k: [derived, direct])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'delta'
            path.write_text(json.dumps({'form': 'zzform', 'removed': [],
                'added': m.global_readings.serialized(Counter({m.loss.signature(direct): 1}))})+'\n')
            private = io.StringIO()
            result = m.changed_route_review(path, old, new, b'zzsourcezo', private)
            self.assertEqual(result['counts'], {'changed_forms_reviewed': 1, 'removed_rows': 0, 'added_rows': 1})
            self.assertEqual(result['added_profiles'][0]['provenance'], 'direct')
            self.assertEqual(result['added_profiles'][0]['lemma_relation'], 'selected_source_lemma')
            self.assertNotIn('zz', json.dumps(result))
            self.assertIn('zz', private.getvalue())
            path.write_text(json.dumps({'form': 'zzform', 'removed': [], 'added': []})+'\n')
            with self.assertRaisesRegex(ValueError, 'reanalysis differs'):
                m.changed_route_review(path, old, new, b'zzsourcezo', io.StringIO())

    def test_global_reading_wrapper_enforces_per_analysis_truncation_guard(self):
        obj = object.__new__(m.StrictRows)
        called = []
        obj.analyses = lambda word, **kw: called.append((word, kw)) or []
        self.assertEqual(obj.rows(b'zzform'), [])
        self.assertEqual(called, [(b'zzform', {'require_untruncated': True})])

    def test_receipt_mismatch_aborts_before_source_read(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input'; path.write_text('synthetic')
            with self.assertRaisesRegex(ValueError, 'input receipt differs'):
                m.prepare(SimpleNamespace(blocker_dossier=path, expected_blocker_sha256='wrong',
                    forms=path, expected_forms_sha256='wrong'))


if __name__ == '__main__':
    unittest.main()
