#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('candidate',Path(__file__).resolve().parents[1]/'tools/qualify-latin-historical-source-candidate.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class CandidateTrial(unittest.TestCase):
    def fixture(self):
        row={'headword':'zz-zaro','fields':[{'name':'itype','projection':'zavi or z^i, zatum or z_tum, 3'}]}
        before=[b':vs:zz-zar conj3',b':vs:zz-zav perfstem',b':vs:zz-obsolete perfstem']
        dossier={'source_header':row,'lemma':'zzzaro','before':[{'directive':r.decode(),'multiplicity':1} for r in before]}
        data=b'synthetic echo\r\n:le:zzzaro\n'+b'\n'.join(before)+b'\nprivate echo\n:le:zzother\n:vs:zzother conj1\r\n'
        return dossier,data

    def test_only_selected_block_changes_and_other_bytes_are_retained(self):
        dossier,data=self.fixture();lemma,expected,result,classes=m.replace_selected(data,dossier)
        self.assertEqual(lemma,b'zzzaro');self.assertEqual(sum(expected.values()),5)
        self.assertTrue(result.startswith(b'synthetic echo\r\n:le:zzzaro\n'))
        self.assertTrue(result.endswith(b'private echo\n:le:zzother\n:vs:zzother conj1\r\n'))
        self.assertEqual(classes,{'removed':{'perfect':1},'added':{'perfect':1,'supine':2}})

    def test_duplicate_block_and_changed_selected_records_are_rejected(self):
        dossier,data=self.fixture()
        for altered in (data+b':le:zzzaro\n',data.replace(b'zz-obsolete',b'zz-unreceived'),data.replace(b'conj3',b'conj2')):
            with self.assertRaises(ValueError):m.replace_selected(altered,dossier)

    def test_source_boundaries_and_identity_remain_literal(self):
        dossier,data=self.fixture();dossier['lemma']='zzother'
        with self.assertRaises(ValueError):m.replace_selected(data,dossier)
        dossier,data=self.fixture();dossier['source_header']['headword']='zzzaro'
        with self.assertRaises(ValueError):m.replace_selected(data,dossier)

    def test_candidate_receipt_rejection_precedes_native_or_output_access(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);f=root/'synthetic';f.write_bytes(b'synthetic')
            with self.assertRaisesRegex(ValueError,'receipt differs'):
                m.prepare(SimpleNamespace(candidate=f,review=f,forms=f,output=root/'out'))
            self.assertFalse((root/'out').exists())

    def test_original_rows_are_pinned_per_runtime_and_reported_for_an_unqualified_one(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);table=root/m.RUNTIME_TABLE;table.parent.mkdir(parents=True)
            table.write_bytes(b'synthetic ending table')
            digest=m.native.digest(table)
            # A runtime nobody qualified yet: measured, never refused.
            self.assertNotIn(digest,m.ORIGINAL_ROWS)
            self.assertEqual(m.original_rows(root,7),{'runtime_ending_table_sha256':digest,
                'analysis_rows':7,'qualified_analysis_rows':None})
            self.assertFalse(m.original_rows_differ(root,7))
            # A qualified runtime: its count is exact.
            m.ORIGINAL_ROWS[digest]=7
            try:
                self.assertFalse(m.original_rows_differ(root,7));self.assertTrue(m.original_rows_differ(root,8))
                self.assertEqual(m.original_rows(root,8)['qualified_analysis_rows'],7)
            finally:del m.ORIGINAL_ROWS[digest]
        self.assertEqual(m.ORIGINAL_ROWS,{'62b662c86b1844f3c2b7cc02b4f7cf12535536c92c049aeb2f16766da30e751c':2100530})


if __name__=='__main__':unittest.main()
