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

spec = importlib.util.spec_from_file_location('isolated', Path(__file__).resolve().parents[1] /
                                           'tools/probe-latin-isolated-fields.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixture():
    header = {'id': 'synthetic', 'headword': 'zzsourcezo', 'fields': [
        {'name': 'itype', 'projection': '1'}, {'name': 'pos', 'projection': 'v.'},
        {'name': 'itype', 'projection': 'zzpart'}]}
    traces = lambda text: [{'filter': f, 'stdout': text, 'stderr': ''} for f in m.review.FILTERS]
    def render(h):
        return 'original' if len(h['fields']) == 3 else h['fields'][0]['projection'] if h['fields'][0]['name'] == 'itype' else h['fields'][1]['projection']
    def replay(text):
        result = 'zzsourcezo <itype>zzmerged, 1</itype>' if text == 'original' else ':le:zzsourcezo\n:de:zzsourcez are_vb\n'
        return m.review.replay_definitions(result.encode()), traces(result)
    _, original = replay(render(header))
    saved = []
    for p, h in m.blockers.isolated_headers(header):
        records, ts = replay(render(h))
        saved.append({'source_field_position': p, 'header': h, 'filter_traces': ts,
            'source_field_shape': m.blockers.field_shape(header['fields'][p]['projection']),
            'replay_state': m.review.replay_state('zzsourcezo', records),
            'replayed_definitions': {k.decode(): [{'line': l.decode(), 'multiplicity': n}
                for l, n in sorted(v.items())] for k, v in records.items()},
            'stages': m.blockers.stage_profiles(h, ts)})
    case = {'lemma': 'zzsourcezo', 'lost_readings': 3, 'original_header': header,
        'original_stages': m.blockers.stage_profiles(header, original), 'isolated_source_fields': saved}
    return case, header, replay, render


class IsolatedFields(unittest.TestCase):
    def revalidate(self, cases, headers=None, replay=None):
        _, h, default_replay, render = fixture()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'review'
            path.write_text(''.join(json.dumps(c) + '\n' for c in cases))
            return m.revalidate_cases(path, headers or {'synthetic': h}, replay or default_replay, render)

    def test_two_successful_fields_can_belong_to_one_lemma(self):
        c, _, _, _ = fixture()
        cases, trials = self.revalidate([c])
        self.assertEqual(len(cases), 1)
        self.assertEqual(len(trials), 2)
        self.assertEqual(len({t['lemma'] for t in trials}), 1)
        self.assertEqual([t['source_field_position'] for t in trials], [0, 2])
        self.assertTrue(all(t['counterfactual_definitions'] == {b'zzsourcezo': Counter({b':de:zzsourcez are_vb': 1})} for t in trials))

    def test_duplicate_and_changed_original_headers_abort(self):
        c, h, _, _ = fixture()
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.revalidate([c, c])
        with self.assertRaisesRegex(ValueError, 'original header differs'):
            self.revalidate([c], {'synthetic': dict(h, headword='zzotherzo')})

    def test_original_replay_drift_aborts(self):
        c, _, _, _ = fixture()
        with self.assertRaisesRegex(ValueError, 'original replay differs'):
            self.revalidate([c], replay=lambda _: ({}, [{'filter': f, 'stdout': 'changed', 'stderr': ''} for f in m.review.FILTERS]))

    def test_variant_and_transcript_drift_abort(self):
        for key, value in [('source_field_position', 99), ('header', {}),
                           ('filter_traces', []), ('source_field_shape', 'empty'),
                           ('replayed_definitions', {}), ('replay_state', 'emits_no_definitions')]:
            c, _, _, _ = fixture()
            c['isolated_source_fields'][0][key] = value
            with self.assertRaises(ValueError):
                self.revalidate([c])

    def test_missing_variant_aborts(self):
        c, _, _, _ = fixture()
        c['isolated_source_fields'].pop()
        with self.assertRaisesRegex(ValueError, 'trial inventory differs'):
            self.revalidate([c])

    def test_receipt_mismatch_precedes_source_reads(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'review'; path.write_text('private synthetic')
            with self.assertRaisesRegex(ValueError, 'input receipt differs'):
                m.prepare(SimpleNamespace(blocker_dossier=path, expected_blocker_sha256='wrong',
                    loss_dossier=path, expected_loss_sha256='wrong', candidate_source=path,
                    expected_candidate_sha256='wrong', candidate=Path(directory), expected_expanded_sha256='wrong',
                    baseline=Path(directory), expected_baseline_expanded_sha256='wrong'))

    def test_native_public_controls_exclude_literal_headword_and_routes(self):
        def row():
            return SimpleNamespace(workword=b'zzsourcezo', lemma=b'zzsourcezo', part_of_speech=2,
                person=1, number=1, gender=0, grammatical_case=0, tense=1, mood=4, voice=1,
                degree=0, preverb=b'', raw_preverb=b'', stem=b'zzsourcez', suffix=b'', ending=b'o')
        empty = SimpleNamespace(analyses=lambda *a, **k: [])
        supplied = SimpleNamespace(analyses=lambda *a, **k: [row()])
        signature = m.loss.signature(row())
        private = io.StringIO()
        result = m.probe_root({'lemma': 'zzsourcezo', 'header': {'headword': 'zzsourcezo'}},
            {b'zzsourcezo': Counter({signature: 1})}, supplied, empty, supplied, private)
        self.assertEqual(result['lost_reading_control']['counts']['recovered_exact_readings'], 1)
        self.assertEqual(result['source_headword_route_control']['counts']['added_direct_rows'], 1)
        self.assertNotIn('zzsource', json.dumps(result))
        self.assertIn('zzsource', private.getvalue())


if __name__ == '__main__':
    unittest.main()
