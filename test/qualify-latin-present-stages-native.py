#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exercise the replay with real native indexes and synthetic source notices."""
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/qualify-latin-present-stages.py'
spec = importlib.util.spec_from_file_location('qualification', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
BUILD = Path(sys.argv.pop(1)).resolve()
BASELINE = BUILD / 'stemlib-production/latin'
LIBRARY = BUILD / ('libmorpheus.dylib' if sys.platform == 'darwin' else 'libmorpheus.so')


class NativeQualification(unittest.TestCase):
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
                report = m.qualify(forms, LIBRARY, BASELINE, stage, BUILD, root / 'output', 4)
            for name in ('boundary-step', 'vowel-step'):
                rows = report['comparisons'][name]['changed_form_eleven_field_multisets']
                self.assertGreater(rows['direct_source_verb'], 0)
                self.assertEqual(rows['removed_rows'], 0)
            for name in ('boundary-control', 'vowel-control'):
                self.assertEqual(report['comparisons'][name]['changed_analysis_counts'], 0)
            self.assertEqual(len(report['comparisons']), 5)
            self.assertEqual((root / 'output').stat().st_mode & 0o777, 0o700)
            self.assertEqual((root / 'output/report.json').stat().st_mode & 0o777, 0o600)


if __name__ == '__main__':
    unittest.main()
