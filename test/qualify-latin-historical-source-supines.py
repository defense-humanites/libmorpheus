#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

spec=importlib.util.spec_from_file_location('supines',Path(__file__).resolve().parents[1]/'tools/qualify-latin-historical-source-supines.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class SupineTrial(unittest.TestCase):
    def fixture(self):
        row={'headword':'zz-zaro','fields':[{'name':'itype','projection':'zavi or z^i, zatum or z_tum, 3'}]}
        _,expected=m.review.source_expectations(row)
        selected=expected.copy();del selected[(b':vs:zz-z_t',b'pp4')]
        dossier={'source_header':row,'lemma':'zzzaro','after':[{'directive':b' '.join(t).decode(),'multiplicity':n} for t,n in selected.items()]}
        return dossier,m.payload(b'zzzaro',selected),expected

    def test_raw_delta_must_be_exact_one_supine_insertion(self):
        dossier,raw,expected=self.fixture()
        lemma,before,after=m.expectations(dossier,raw)
        self.assertEqual(after,expected);self.assertEqual(sum((after-before).values()),1)
        for data in (raw+b':vs:zz-extra pp4\n',raw.replace(b'conj3',b'conj2'),raw.replace(b'perfstem',b'pp4')):
            with self.assertRaises(ValueError):m.expectations(dossier,data)

    def test_source_join_and_recipe_must_remain_literal(self):
        dossier,raw,_=self.fixture();dossier['lemma']='zzother'
        with self.assertRaises(ValueError):m.expectations(dossier,raw)
        dossier,raw,_=self.fixture();dossier['source_header']['headword']='zzzaro'
        with self.assertRaises(ValueError):m.expectations(dossier,raw)

    def test_analysis_notation_does_not_rewrite_source_stems(self):
        _,_,expected=self.fixture();before=expected.copy();cells=m.family_cells(expected)
        self.assertEqual(expected,before);self.assertEqual(len(cells),12)
        self.assertEqual(len({f for f,_ in cells}),10)
        self.assertTrue(all(not set(b'_^-' ) & set(f) for f,_ in cells))
        self.assertIn((b':vs:zz-z_t',b'pp4'),expected)

    def test_receipt_rejection_precedes_native_build_and_private_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'input';source.write_bytes(b'synthetic')
            with self.assertRaisesRegex(ValueError,'receipt differs'):
                m.prepare(SimpleNamespace(review=source,diagnostic=source,output=root/'private'))
            self.assertFalse((root/'private').exists())


if __name__=='__main__':unittest.main()
