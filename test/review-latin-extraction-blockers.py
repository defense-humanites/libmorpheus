#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

spec = importlib.util.spec_from_file_location('blockers', Path(__file__).resolve().parents[1] /
                                           'tools/review-latin-extraction-blockers.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def header():
    return {'id': 'synthetic', 'headword': 'zzsourceo', 'fields': [
        {'name': 'pos', 'projection': 'v.'}, {'name': 'itype', 'projection': '3'},
        {'name': 'gen', 'projection': 'synthetic'}, {'name': 'itype', 'projection': 'zzperf, zzsup, 3'}]}


def traces(text):
    return [{'filter': f, 'stdout': text, 'stderr': ''} for f in m.review.FILTERS]


def case():
    return {'lemma': 'zzsourceo', 'lost_readings': 7, 'review_decision': 'historical_extraction_review',
        'articles': [{'header': header(), 'partition': 'verbal', 'headword_identity': 'same_literal_lemma',
            'replay_state': 'emits_no_definitions', 'candidate_has_headword_definitions': False,
            'final_has_headword_definitions': False, 'filter_traces': traces('zzsourceo <itype>3</itype>'),
            'grammar_profile': {'itype_shape': 'multiple_itypes', 'first_orth_extent': 'full',
                'headword_shape': 'active_present', 'first_sense_signal': 'no_first_sense_verbal_signal'}}]}


class ExtractionBlockers(unittest.TestCase):
    def test_isolation_preserves_order_other_fields_and_original_values(self):
        original = header()
        variants = m.isolated_headers(original)
        self.assertEqual([p for p, _ in variants], [1, 3])
        for p, variant in variants:
            self.assertEqual(variant['fields'], [f for i, f in enumerate(original['fields']) if f['name'] != 'itype' or i == p])
        variants[0][1]['fields'][0]['projection'] = 'changed'
        self.assertEqual(original['fields'][0]['projection'], 'v.')
        self.assertEqual(m.isolated_headers(dict(original, fields=[])), [])
        self.assertEqual(m.isolated_headers(dict(original, fields=original['fields'][:2])), [])

    def test_shape_categories_publish_no_literal_field(self):
        for value, expected in [('', 'empty'), ('3', 'bare_conjugation_digit'),
                ('zzperf, zzsup, 3', 'principal_parts_with_conjugation_digit'),
                ('zze^re', 'infinitive_spelling'), ('zzpart', 'other_field_structure')]:
            self.assertEqual(m.field_shape(value), expected)

    def test_stage_retention_counts_exact_occurrences_not_substrings(self):
        h = header()
        h['fields'] = [{'name': 'itype', 'projection': '3'}] * 2
        profiles = m.stage_profiles(h, traces('zzsourceo <itype>3</itype><itype>13</itype>'))
        self.assertEqual(profiles[0]['source_itype_occurrences_retained'], 1)
        self.assertEqual(profiles[0]['output_itype_occurrences'], 2)
        self.assertTrue(profiles[0]['headword_prefix_preserved'])
        self.assertEqual(profiles[0]['output_itype_shapes'], {'bare_conjugation_digit': 1, 'other_field_structure': 1})

    def test_stages_ignore_echo_and_count_only_bound_definitions(self):
        text = ':le:zzsourceo\nprivate ECHO\n:vs:zzstem conj3\n:vs:zzstem conj3\n:de:zzbase are_vb\n'
        stages = m.stage_profiles(header(), traces(text))
        self.assertEqual(stages[-1]['emitted_stem_directives'], {':de:': 1, ':vs:': 2})
        self.assertFalse(stages[-1]['headword_prefix_preserved'])
        with self.assertRaisesRegex(ValueError, 'filter sequence'):
            m.stage_profiles(header(), traces(text)[::-1])

    def test_isolated_replay_is_measured_with_other_lemma_kept_private(self):
        c = case()
        def render(h):
            return str(len(h['fields'])) + h['fields'][-1]['projection']
        def replay(text):
            if text.startswith('4'):
                return {}, c['articles'][0]['filter_traces']
            emitted = b':le:zzsourceo\n:vs:zzstem conj3\n' if text.endswith('synthetic') else b':le:zzother\n:vs:zzstem conj3\n'
            return m.review.replay_definitions(emitted), traces(emitted.decode())
        result = m.inspect_case(c, replay, render)
        self.assertEqual([t['replay_state'] for t in result['isolated_source_fields']],
                         ['emits_missing_lemma', 'emits_only_other_lemmas'])
        report = m.summarize([result])
        self.assertEqual(report['counts'], {'lemmas': 1, 'lost_readings': 7, 'isolated_field_trials': 2})
        for token in ('zzsourceo', 'zzother', 'zzstem', 'zzperf', 'zzsup', 'synthetic'):
            self.assertNotIn(token, json.dumps(report))

    def test_original_replay_drift_aborts(self):
        with self.assertRaisesRegex(ValueError, 'replay differs'):
            m.inspect_case(case(), lambda _: ({}, traces('changed')), lambda _: 'synthetic')

    def test_selection_rejects_duplicates_and_scope_inconsistency(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'review'
            c = case()
            path.write_text(json.dumps(c) + '\n')
            self.assertEqual(m.select_cases(path), [c])
            path.write_text((json.dumps(c) + '\n') * 2)
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                m.select_cases(path)
            c['articles'][0]['final_has_headword_definitions'] = True
            path.write_text(json.dumps(c) + '\n')
            with self.assertRaisesRegex(ValueError, 'scope differs'):
                m.select_cases(path)

    def test_receipt_mismatch_aborts_before_reading_source(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'review'; path.write_text('private synthetic')
            with self.assertRaisesRegex(ValueError, 'receipt differs'):
                m.prepare(SimpleNamespace(review_dossier=path, expected_review_sha256='wrong'))


if __name__ == '__main__':
    unittest.main()
