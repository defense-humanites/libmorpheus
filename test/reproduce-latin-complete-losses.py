#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

spec=importlib.util.spec_from_file_location('loss',Path(__file__).resolve().parents[1]/'tools/reproduce-latin-complete-losses.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class ReproductionReceipts(unittest.TestCase):
    def test_source_receipt_rejection_precedes_native_build_and_output_access(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);f=root/'input';f.write_bytes(b'synthetic')
            with self.assertRaisesRegex(ValueError,'receipt differs'):
                m.prepare(SimpleNamespace(candidate=f,forms=f,output=root/'private'))
            self.assertFalse((root/'private').exists())


if __name__=='__main__':unittest.main()
