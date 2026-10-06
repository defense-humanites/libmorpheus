#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/qualify-latin-present-stages.py'
spec = importlib.util.spec_from_file_location('qualification', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def reading(lemma=b'synthetic', person=1):
    return (b'form', lemma, 2, person, 1, 0, 0, 1, 1, 1, 0)


class Qualification(unittest.TestCase):
    def quote_fixture(self, parent):
        witness = parent / 'witness'
        row = {'schema': 1, 'form': 'azenitur', 'lemma': 'azego',
               'source_revision': '56061ca127f4a2844980baffc5f2b6d1332897b3',
               'source_sha256': 'ccbd2f79db1006edc607fe51227babab6872fbdaa4e925f4c1999a3b978041ee',
               'candidate_sha256': 'candidate', 'headers_sha256': 'headers'}
        witness.write_text(json.dumps(row)+'\n')
        expected = ((b'azenitur', b'azego', 2, 3, 1, 0, 0, 1, 4, 2, 0), b'')
        return witness, row, expected

    def test_source_quote_preserves_old_readings_and_requires_exact_direct_grammar(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory); witness, _, expected = self.quote_fixture(p)
            old = (reading(b'other'), b'')
            left, right = Mock(), Mock()
            left.rows.return_value = [old]; right.rows.return_value = [old, expected]
            with patch.object(m, 'NativeRows', side_effect=[left, right]):
                report = m.source_quote_control(witness, None, None, None, p/'out', {b'azego'}, 'candidate', 'headers')
            self.assertEqual(report['counts'], {'added_rows': 1, 'after_covered': 1,
                'before_covered': 0, 'direct_source_verb': 1, 'expected_readings': 1,
                'removed_rows': 0, 'retained_rows': 1, 'witnesses': 1})
            left.close.assert_called_once(); right.close.assert_called_once()
            self.assertEqual((p/'out').stat().st_mode & 0o777, 0o600)

    def test_source_quote_binding_rejects_wrong_candidate_header_or_source(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory); witness, row, _ = self.quote_fixture(p)
            for field in ('candidate_sha256', 'headers_sha256', 'source_sha256', 'source_revision'):
                changed = dict(row); changed[field] = 'wrong'; witness.write_text(json.dumps(changed)+'\n')
                with patch.object(m, 'NativeRows') as native:
                    with self.assertRaisesRegex(ValueError, 'bound'):
                        m.source_quote_control(witness, None, None, None, p/'out', {b'azego'}, 'candidate', 'headers')
                    native.assert_not_called()
                self.assertFalse((p/'out').exists())

    def test_source_quote_rejects_old_coverage_wrong_voice_and_preverb_lead(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory); witness, _, expected = self.quote_fixture(p)
            wrong_voice = (expected[0][:9]+(1, 0), b'')
            for old, new in [([expected], [expected]), ([], []),
                             ([], [wrong_voice]), ([], [(expected[0], b'ex')])]:
                left, right = Mock(), Mock(); left.rows.return_value = old; right.rows.return_value = new
                with patch.object(m, 'NativeRows', side_effect=[left, right]):
                    with self.assertRaisesRegex(ValueError, 'coverage'):
                        m.source_quote_control(witness, None, None, None, p/'out', {b'azego'}, 'candidate', 'headers')
                left.close.assert_called_once(); right.close.assert_called_once()
                self.assertFalse((p/'out').exists())

    def test_source_quote_removals_and_native_errors_fail_without_output(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory); witness, _, expected = self.quote_fixture(p)
            for error in (False, True):
                left, right = Mock(), Mock(); left.rows.return_value = [(reading(b'other'), b'')]
                right.rows.return_value = [expected]
                if error: right.rows.side_effect = ValueError('native reading analysis failed')
                with patch.object(m, 'NativeRows', side_effect=[left, right]):
                    with self.assertRaises(ValueError):
                        m.source_quote_control(witness, None, None, None, p/'out', {b'azego'}, 'candidate', 'headers')
                left.close.assert_called_once(); right.close.assert_called_once()
                self.assertFalse((p/'out').exists())

    def test_source_quote_identity_and_duplicate_witnesses_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory); witness, row, _ = self.quote_fixture(p)
            for records in ([dict(row, lemma='other')], [row, row]):
                witness.write_text(''.join(json.dumps(r)+'\n' for r in records))
                with self.assertRaisesRegex(ValueError, 'lemmas'):
                    m.source_quote_control(witness, None, None, None, p/'out', {b'azego'}, 'candidate', 'headers')

    def test_preserve_multiplicity_and_attribute_changes(self):
        row, changed = reading(), reading(person=2)
        result = m.compare_rows([(row, b'')] * 2, [(row, b''), (changed, b'')], {b'synthetic'})
        self.assertEqual(result, {'retained_rows': 1, 'removed_rows': 1,
                                  'added_rows': 1, 'direct_source_verb': 1})

    def test_prefix_other_and_ambiguous_provenance_stay_review_leads(self):
        row = reading()
        for rows, label in [([(row, b'ex')], 'native_preverb_review'),
                            ([(reading(b'other'), b'')], 'other_review'),
                            ([(row, b''), (row, b'ex')], 'ambiguous_provenance_review')]:
            result = m.compare_rows([], rows, {b'synthetic'})
            self.assertEqual(result[label], len(rows))
            self.assertNotIn('direct_source_verb', result)

    def test_insertions_keep_source_order_lemmas_and_unchanged_bytes(self):
        raw = b':le:synthetic#2\n:vs:primary conj3\n:vs:old perfstem\n'
        new = raw.replace(b':vs:old', b':vs:alternate\tconj3 orth\n:vs:old')
        self.assertEqual(m.additions(raw, new, 1), {b'synthetic#2'})
        for before, after, expected in [(raw, new, 2), (raw, new.replace(b'primary', b'changed'), 1),
                                        (raw, new.replace(b'conj3 orth', b'perfstem orth'), 1),
                                        (raw, new + b':le:other\n', 2)]:
            with self.assertRaises(ValueError):
                m.additions(before, after, expected)

    def test_private_no_overwrite_and_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'private'
            m.write_private(path, b'private')
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                m.write_private(path, b'changed')
            self.assertEqual(path.read_bytes(), b'private')

    def test_changed_counts_do_not_mask_native_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'difference.jsonl'
            with patch.object(m.listall, 'NativeAnalyzer'), patch.object(m.listall, 'audit',
                    return_value={'counts': {'error': 1}}):
                with self.assertRaisesRegex(ValueError, 'native errors'):
                    m.comparison(None, None, None, None, output)

    def test_reanalysis_counts_must_match_full_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'difference.jsonl'
            output.write_text(json.dumps({'form': 'synthetic', 'curated_count': 0, 'rebuilt_count': 1}) + '\n')
            with patch.object(m.listall, 'NativeAnalyzer'), patch.object(m.listall, 'audit',
                    return_value={'counts': {}}), patch.object(m, 'NativeRows') as native:
                native.return_value.rows.return_value = []
                with self.assertRaisesRegex(ValueError, 'reanalysis differs'):
                    m.comparison(None, None, None, None, output, {b'synthetic'})

    def test_private_stage_must_not_contain_inputs(self):
        repo = SCRIPT.parents[1]
        with self.assertRaisesRegex(ValueError, 'outside repository'):
            m.qualify(repo / 'forms', repo / 'library', repo / 'baseline',
                      repo / 'stage', repo / 'tools', repo / 'output')
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            with self.assertRaisesRegex(ValueError, 'outside repository'):
                m.qualify(parent / 'forms', parent / 'library', parent / 'baseline',
                          parent / 'stage', parent / 'tools', parent)


if __name__ == '__main__':
    unittest.main()
