#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('supines',Path(__file__).resolve().parents[1]/'tools/qualify-latin-historical-source-supines.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
BUILD=Path(sys.argv.pop(1)).resolve()


class NativeSupines(unittest.TestCase):
    def test_second_supine_recovers_its_cells_and_preserves_existing_routes(self):
        row={'headword':'zz-zaro','fields':[{'name':'itype','projection':'zavi or z^i, zatum or z_tum, 3'}]}
        _,expected=m.review.source_expectations(row)
        selected=expected.copy();del selected[(b':vs:zz-z_t',b'pp4')]
        lemma=b'zzzaro';dossier={'source_header':row,'lemma':lemma.decode(),
            'after':[{'directive':b' '.join(t).decode(),'multiplicity':n} for t,n in selected.items()]}
        raw=m.payload(lemma,selected)
        self.assertEqual(m.expectations(dossier,raw),(lemma,selected,expected))
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);readers={}
            try:
                for name,records in (('before',selected),('after',expected)):
                    source=root/(name+'.stems');m.native.write_private(source,m.payload(lemma,records))
                    m.native.build_trial(BUILD/'stemlib-production/latin',source,BUILD,root/name)
                    readers[name]=m.direct.StrictRows(BUILD/('libmorpheus.dylib' if sys.platform=='darwin' else 'libmorpheus.so'),root/name)
                report=m.compare_family(lemma,m.family_cells(expected),readers['before'],readers['after'],root)
                self.assertEqual(report['source_cells']['covered_after'],12)
                self.assertEqual(report['sixteen_field_multisets']['removed_rows'],0)
                self.assertGreater(report['sixteen_field_multisets']['added_rows'],0)
                self.assertLess(report['source_cells']['covered_before'],12)
            finally:
                for reader in readers.values():reader.close()


if __name__=='__main__':unittest.main()
