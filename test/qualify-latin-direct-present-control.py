#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

spec = importlib.util.spec_from_file_location('direct', Path(__file__).resolve().parents[1] /
                                           'tools/qualify-latin-direct-present-control.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class DirectControl(unittest.TestCase):
    def test_one_flag_preserves_unselected_bytes_and_homographs(self):
        data = b'# synthetic\n:le:zzsourcezo#1\n:vs:zzother conj1 are_vb\n:le:zzsourcezo#2\n:vs:zzsourcez conj1 are_vb\n'
        result = m.restricted_payload(data, b'zzsourcezo#2')
        self.assertEqual(result, data.replace(b':vs:zzsourcez conj1 are_vb\n', b':vs:zzsourcez conj1 are_vb not_in_comp\n'))

    def test_line_endings_and_missing_terminal_newline_are_preserved(self):
        for ending in (b'\n', b'\r\n', b''):
            data = b':le:zzsourcezo\n:vs:zzsourcez conj1 are_vb' + ending
            self.assertEqual(m.restricted_payload(data, b'zzsourcezo'), b':le:zzsourcezo\n:vs:zzsourcez conj1 are_vb not_in_comp'+ending)

    def test_multiple_or_absent_present_directives_abort(self):
        for data in (b':le:zzsourcezo\n', b':le:zzsourcezo\n:vs:zzsourcez conj1 are_vb\n:vs:zzother conj1 are_vb\n'):
            with self.assertRaisesRegex(ValueError, 'exactly one'):
                m.restricted_payload(data, b'zzsourcezo')

    def test_other_stem_classes_or_existing_flags_abort(self):
        for directive in (b':de:zzsourcez are_vb', b':vs:zzsourcez conj3', b':vs:zzsourcez conj1', b':vs:zzsourcez conj1 are_vb orth', b':vs:zzsourcez conj1 are_vb not_in_comp'):
            with self.assertRaisesRegex(ValueError, 'qualified class'):
                m.restricted_payload(b':le:zzsourcezo\n'+directive+b'\n', b'zzsourcezo')

    def test_global_reader_requires_truncation_guard(self):
        obj = object.__new__(m.StrictRows); calls = []
        obj.analyses = lambda word, **kw: calls.append(kw) or []
        self.assertEqual(obj.rows(b'zzform'), []); self.assertEqual(calls, [{'require_untruncated': True}])

    def test_family_detects_decomposition_drift_even_at_equal_grammar(self):
        def row(stem):
            return SimpleNamespace(workword=b'zzform', lemma=b'zzsourcezo', part_of_speech=2, person=1,
                number=1, gender=0, grammatical_case=0, tense=1, mood=4, voice=1, degree=0,
                preverb=b'', raw_preverb=b'', stem=stem, suffix=b'', ending=b'o')
        cell = {'form':'zzform','lemma':'zzsourcezo','person':1,'number':1,'mood':4,'voice':1}
        left = SimpleNamespace(analyses=lambda *a, **k:[row(b'zzstem')])
        right = SimpleNamespace(analyses=lambda *a, **k:[row(b'zzother')])
        with self.assertRaisesRegex(ValueError, 'multiset'):
            m.family_control([cell], left, right)
        self.assertEqual(m.family_control([cell], left, left), {'cells_unchanged':1,'expected_readings':1})

    def test_unchanged_family_still_requires_source_expectation(self):
        empty = SimpleNamespace(analyses=lambda *a, **k:[])
        cell = {'form':'zzform','lemma':'zzsourcezo','person':1,'number':1,'mood':4,'voice':1}
        with self.assertRaisesRegex(ValueError, 'expectation missing'):
            m.family_control([cell], empty, empty)

    def test_receipt_failure_precedes_native_build(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'input'; path.write_text('synthetic')
            args=SimpleNamespace(**{n:path for n in ('source','family','forms','candidate_source')},
                **{'expected_'+n+'_sha256':'wrong' for n in ('source','family','forms','candidate_source')})
            with self.assertRaisesRegex(ValueError, 'receipt differs'): m.prepare(args)


if __name__ == '__main__':
    unittest.main()
