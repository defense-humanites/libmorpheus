#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('probe', Path(__file__).resolve().parents[1] /
                                           'tools/probe-latin-historical-filter-portability.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class PortabilityControl(unittest.TestCase):
    def test_failure_summary_excludes_private_text_and_addresses(self):
        stderr=(b'ERROR: AddressSanitizer: global-buffer-overflow on address 0xdeadbeef\n'
                b'#1 0x123 in set_lemma /private/SECRET/latvb.l:211:4\n'
                b'#2 0xabc in SECRET /private/SECRET/input:999\n'
                b'private article SECRET and stem SECRET\n')
        result=m.failure_summary('filter',1,stderr)
        self.assertEqual(result['categories'],['global-buffer-overflow'])
        self.assertEqual(result['functions'],['set_lemma'])
        self.assertEqual(result['lexer_or_generated_source_lines'],[211])
        self.assertNotIn('SECRET',str(result)); self.assertNotIn('0x',str(result))

    def test_unknown_error_text_is_not_forwarded(self):
        result=m.failure_summary('SECRET',-6,b'AddressSanitizer: SECRET\nruntime error: SECRET')
        self.assertEqual(result['operation'],'unknown')
        self.assertEqual(result['categories'],['undefined-behavior'])
        self.assertNotIn('SECRET',str(result))

    def test_failed_process_preserves_private_logs_and_raises_typed_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            r=Path(directory)
            with patch.object(m.subprocess,'run',return_value=SimpleNamespace(
                    returncode=1,stdout=b'SECRET',stderr=b'AddressSanitizer: SEGV\nSECRET')):
                with self.assertRaises(m.DiagnosticProcessError) as failure:
                    m.run_private(['synthetic'],r,'filter',b'SECRET')
            self.assertEqual(failure.exception.summary['categories'],['SEGV'])
            self.assertNotIn('SECRET',str(failure.exception))
            self.assertEqual((r/'filter.stdout').read_bytes(),b'SECRET')
            self.assertEqual((r/'filter.stderr').stat().st_mode & 0o777,0o600)

    def test_source_receipt_precedes_patch(self):
        with self.assertRaisesRegex(ValueError, 'lexer receipt'):
            m.diagnostic_source(b'synthetic changed lexer')

    def test_counts_multiplicity_and_equal_count_substitution(self):
        before = b':le:zzlemma#2\n:vs:zzstem conj1\n:vs:zzstem conj1\n'
        after = b':le:zzlemma#2\n:vs:zzstem conj1\n:vs:zzother conj1\n'
        metrics, _, _ = m.compare(before, after)
        self.assertEqual(metrics['before_rows'], 2)
        self.assertEqual(metrics['after_rows'], 2)
        self.assertEqual(metrics['retained_rows'], 1)
        self.assertEqual(metrics['removed_rows'], 1)
        self.assertEqual(metrics['added_rows'], 1)
        self.assertEqual(metrics['changed_lemma_multisets'], 1)

    def test_homographs_are_separate_and_echo_is_excluded(self):
        before = b'synthetic echo\n:le:zzlemma#1\n:vs:zzstem conj1\n'
        after = b'different echo\n:le:zzlemma#2\n:vs:zzstem conj1\n'
        metrics, _, _ = m.compare(before, after)
        self.assertEqual(metrics['union_lemmas'], 2)
        self.assertEqual(metrics['retained_rows'], 0)
        same, _, _ = m.compare(before, before.replace(b'synthetic echo', b'other echo'))
        self.assertEqual(same['unchanged_lemma_multisets'], 1)
        self.assertEqual(same['changed_lemma_multisets'], 0)

    def test_unbound_or_empty_directives_are_rejected(self):
        for data in (b':vs:zzstem conj1\n', b':le:\n', b':le:zzlemma\n:vs:\n'):
            with self.assertRaises(ValueError): m.definitions(data)

    def test_private_write_is_exclusive_and_restrictive(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'private'
            m.write_private(p, b'synthetic')
            self.assertEqual(p.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError): m.write_private(p, b'changed')

    def test_reference_receipt_precedes_output_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            r = Path(directory); p = r / 'synthetic'; p.write_bytes(b'synthetic')
            args = SimpleNamespace(lexer=p, input=p, reference=p, output=r/'output',
                                   expected_reference_sha256='wrong')
            with self.assertRaisesRegex(ValueError, 'reference receipt'): m.prepare(args)
            self.assertFalse(args.output.exists())


if __name__ == '__main__':
    unittest.main()
