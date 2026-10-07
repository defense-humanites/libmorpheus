#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exercise the replay with real native indexes and synthetic source notices."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/qualify-latin-present-stages.py'
spec = importlib.util.spec_from_file_location('qualification', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
global_spec = importlib.util.spec_from_file_location('global_readings', SCRIPT.with_name('audit-latin-global-readings.py'))
g = importlib.util.module_from_spec(global_spec)
global_spec.loader.exec_module(g)
BUILD = Path(sys.argv.pop(1)).resolve()
BASELINE = BUILD / 'stemlib-production/latin'
LIBRARY = BUILD / ('libmorpheus.dylib' if sys.platform == 'darwin' else 'libmorpheus.so')


class NativeQualification(unittest.TestCase):
    def test_global_comparison_detects_equal_count_lemma_change_with_real_api(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, lemma in [('before','zzbefore'),('after','zzafter')]:
                source=root/(name+'.stems')
                source.write_text(':le:'+lemma+'\n:vs:zzstemz conj3\n')
                m.build_trial(BASELINE,source,BUILD,root/name)
            forms=root/'forms'; forms.write_bytes(b'zzstemzo\n')
            left=m.NativeRows(LIBRARY,root/'before')
            try:
                right=m.NativeRows(LIBRARY,root/'after')
                try:
                    report=g.audit(forms,left,right,root/'private',g.source_lemmas(root/'after.stems'))
                finally: right.close()
            finally: left.close()
            self.assertEqual(report['changed_analysis_counts'],0)
            self.assertEqual(report['changed_grammatical_multisets'],1)
            self.assertEqual(report['changed_multisets_at_equal_counts'],1)
            self.assertEqual(report['global_eleven_field_multisets']['removed_rows'],1)
            self.assertEqual(report['global_eleven_field_multisets']['added_rows'],1)

    def witness(self, lemma, candidate):
        return {'schema': 1, 'lemma': lemma,
                'source_revision': '56061ca127f4a2844980baffc5f2b6d1332897b3',
                'source_sha256': 'ccbd2f79db1006edc607fe51227babab6872fbdaa4e925f4c1999a3b978041ee',
                'candidate_sha256': m.digest(candidate), 'headers_sha256': 'synthetic-headers'}

    def test_native_quote_covers_new_and_preexisting_direct_passive_readings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'source'
            source.write_bytes(b':le:zzlemma\n:vs:zzalternz conj3 orth\n')
            m.build_trial(BASELINE, source, BUILD, root/'trial')
            row = dict(self.witness('zzlemma', source), form='zzalternzitur')
            witness = root/'witness'; witness.write_text(json.dumps(row)+'\n')
            for name, before, covered in [('new', BASELINE, 0), ('existing', root/'trial', 1)]:
                report = m.source_quote_control(witness, LIBRARY, before, root/'trial', root/name,
                                                {b'zzlemma'}, m.digest(source), 'synthetic-headers')
                self.assertEqual(report['counts']['before_covered'], covered)
                self.assertEqual(report['counts']['after_covered'], 1)
                self.assertEqual(report['counts']['removed_rows'], 0)

    def test_native_active_families_cover_both_class_three_subclasses(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'source'
            source.write_bytes(b':le:zzlemmaa\n:vs:zzalternz conj3 orth\n:le:zzlemmab\n:vs:zzalternb conj3_io orth\n')
            m.build_trial(BASELINE, source, BUILD, root/'trial')
            records = []
            for io, lemma, stem in [(False, 'zzlemmaa', 'zzalternz'), (True, 'zzlemmab', 'zzalternb')]:
                forms = []
                for mood, endings in [(4, ['io' if io else 'o', 'is', 'it', 'imus', 'itis', 'iunt' if io else 'unt']),
                                      (8, ['iam', 'ias', 'iat', 'iamus', 'iatis', 'iant'] if io else ['am', 'as', 'at', 'amus', 'atis', 'ant'])]:
                    for i, suffix in enumerate(endings):
                        forms.append({'form': stem+suffix, 'person': i % 3 + 1, 'number': 1 if i < 3 else 3, 'mood': mood})
                forms.append({'form': stem+'ere', 'person': 0, 'number': 0, 'mood': 5})
                records.append(dict(self.witness(lemma, source), forms=forms))
            witness = root/'witness'; witness.write_text(''.join(json.dumps(row)+'\n' for row in records))
            report = m.source_family_control(witness, LIBRARY, BASELINE, root/'trial', root/'output',
                                              {b'zzlemmaa', b'zzlemmab'}, m.digest(source), 'synthetic-headers')
            self.assertEqual(report['counts']['before_covered'], 0)
            self.assertEqual(report['counts']['after_covered'], 26)
            self.assertEqual(report['counts']['removed_rows'], 0)

    def test_controlled_source_replays_exact_indexes_and_abi_readings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hashes = m.build_trial(BASELINE, BASELINE / 'Latin/stemsrc/vbs.latin', BUILD, root / 'trial')
            self.assertEqual(hashes, {name: m.digest(BASELINE / 'Latin/steminds' / name) for name in hashes})
            self.assertFalse(list((root / 'trial').glob('MORPHEUS-*')))
            forms = root / 'forms'
            forms.write_bytes(b'amo\namat\nest\n')
            result = m.comparison(forms, LIBRARY, BASELINE, root / 'trial', root / 'difference.jsonl', {b'amo'})
            self.assertEqual(result['changed_analysis_counts'], 0)
            native = m.NativeRows(LIBRARY, BASELINE)
            try:
                self.assertTrue(any(row[1] == b'amo' for row, _ in native.rows(b'amat')))
            finally:
                native.close()

    def test_staged_insertions_and_all_five_comparisons(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root / 'stages'
            stage.mkdir()
            letters = 'bcdfghklmnpqrsz'
            def block(letter, extra=False):
                return (f':le:zzlemma{letter}\n:vs:zzroot{letter} conj3\n' +
                        (f':vs:zzalternate{letter}\tconj3 orth\n' if extra else ''))
            inputs = {'cited-future-imperative': ''.join(block(c) for c in letters).encode(),
                      'boundary-present': ''.join(block(c, i < 11) for i, c in enumerate(letters)).encode(),
                      'vowel-present': ''.join(block(c, True) for c in letters).encode()}
            for name, data in inputs.items():
                (stage / ('verbal-letters-only-' + name + '.stems')).write_bytes(data)
            (stage / 'verbal-all-vowel-present.stems').write_bytes(inputs['vowel-present'])
            forms = root / 'forms'
            forms.write_bytes(b'zzrootbo\nzzalternatebo\nzzalternatezo\nest\n')
            with contextlib.redirect_stdout(io.StringIO()):
                report = m.qualify(forms, LIBRARY, BASELINE, stage, BUILD, root / 'output', 4,
                                   include_global_readings=True)
            for name in ('boundary-step', 'vowel-step'):
                rows = report['comparisons'][name]['changed_form_eleven_field_multisets']
                self.assertGreater(rows['direct_source_verb'], 0)
                self.assertEqual(rows['removed_rows'], 0)
            for name in ('boundary-control', 'vowel-control'):
                self.assertEqual(report['comparisons'][name]['changed_analysis_counts'], 0)
            self.assertEqual(len(report['comparisons']), 5)
            global_control=report['global_comparisons']['final-global-control']
            self.assertEqual(global_control['changed_grammatical_multisets'],0)
            global_delta=report['global_comparisons']['baseline-to-final-global']
            self.assertEqual(global_delta['counts']['absent_curated__recognized_rebuilt'],3)
            self.assertEqual(global_delta['global_eleven_field_multisets']['removed_rows'],0)
            self.assertEqual((root / 'output').stat().st_mode & 0o777, 0o700)
            self.assertEqual((root / 'output/report.json').stat().st_mode & 0o777, 0o600)


if __name__ == '__main__':
    unittest.main()
