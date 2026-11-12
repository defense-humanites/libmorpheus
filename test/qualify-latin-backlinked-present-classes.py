#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Synthetic checks for the prefix alternate family inventory."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('trial',Path(__file__).resolve().parents[1]/'tools/qualify-latin-backlinked-present-classes.py')
trial=importlib.util.module_from_spec(spec);spec.loader.exec_module(trial)
BEFORE=b':le:bado\n:vs:bad\tconj3\n:vs:bas perfstem\n:vs:bas pp4\n:le:other\n:de:oth\tare_vb dep\n'
AFTER=(b':le:bado\n:vs:bad\tconj3\n:vs:cad\tconj3 orth\n:vs:bas perfstem\n:vs:cas perfstem orth\n'
       b':vs:bas pp4\n:vs:cas pp4 orth\n:le:other\n:de:oth\tare_vb dep\n:de:ath\tare_vb dep orth\n')


class Inventory(unittest.TestCase):
    def test_added_records_are_exact_orth_additions(self):
        records=trial.added_records(BEFORE,AFTER)
        self.assertEqual(records,[(b'bado',b'cad',b'conj3',()),(b'bado',b'cas',b'perfstem',()),
                                  (b'bado',b'cas',b'pp4',()),(b'other',b'ath',b'are_vb',(b'dep',))])

    def test_removed_or_unflagged_additions_fail_closed(self):
        with self.assertRaises(ValueError):
            trial.added_records(AFTER,BEFORE)
        with self.assertRaises(ValueError):
            trial.added_records(BEFORE,BEFORE+b':vs:cad\tconj3\n')
        with self.assertRaises(ValueError):
            trial.added_records(BEFORE,BEFORE+b':vs:cad\tconj3 orth\n'*2)

    def test_family_cells_follow_stem_class_and_voice(self):
        cells,classes=trial.family_cells(trial.added_records(BEFORE,AFTER))
        self.assertEqual(classes,{'conj3':1,'perfstem':1,'pp4':1,'are_vb_dep':1})
        self.assertEqual(len(cells),6+6+6+6)
        forms={c[0] for c in cells}
        self.assertTrue({b'cadit',b'casit',b'casum',b'athatur'}<=forms)
        self.assertNotIn(b'athat',forms)
        present=[c for c in cells if c[0]==b'cadit'][0]
        self.assertEqual(present[1:],((2,3,1,0,0,1,4,1,0),b'bado',b'cad',b'conj3'))
        passive=[c for c in cells if c[0]==b'athatur'][0]
        self.assertEqual(passive[1],(2,3,1,0,0,1,4,2,0))

    def test_unsupported_classes_are_counted_not_guessed(self):
        cells,classes=trial.family_cells([(b'x',b'y',b'irreg_pp1',()),(b'x',b'y',b'perfstem',(b'dep',))])
        self.assertEqual(cells,[])
        self.assertEqual(classes,{'unsupported_irreg_pp1':1,'unsupported_perfstem':1})

    def test_displacement_review_explains_enclitic_fallbacks(self):
        import json, tempfile
        class Row:
            def __init__(self,sig,preverb=b''):self.sig=sig;self.preverb=preverb
        class Reader:
            def __init__(self,table):self.table=table
            def analyses(self,form,require_untruncated=False):return self.table.get(form,[])
        sig=lambda r:r.sig
        original=trial.supines.direct.loss.signature
        trial.supines.direct.loss.signature=sig
        try:
            fallback=(b'bada_s',b'ba-do',2,2,1,0,0,1,8,1,0);direct=(b'badandum',b'bado',2,0,1,0,0,0,0,0,0)
            text=lambda signature:[v.decode() if isinstance(v,bytes) else v for v in signature]
            table={b'badandum':[Row(direct)],b'badan':[Row(fallback),Row(direct)],b'cane':[Row(direct)],b'ca':[],
                   b'dadum':[Row(direct,b'da')]}
            with tempfile.TemporaryDirectory() as directory:
                delta=Path(directory)/'delta.jsonl'
                rows=[{'form':'badandum','removed':[{'signature':text(fallback),'multiplicity':1}],'added':[]},
                      {'form':'cane','removed':[{'signature':text(fallback),'multiplicity':2}],'added':[]},
                      {'form':'dadum','removed':[{'signature':text(fallback),'multiplicity':1}],'added':[]},
                      {'form':'quiet','removed':[],'added':[{'signature':text(direct),'multiplicity':1}]}]
                delta.write_text(''.join(json.dumps(r)+'\n' for r in rows))
                report=trial.displacement_review(delta,Reader(table))
            self.assertEqual(report['counts'],{'forms_with_removed_readings':3,'removed_readings':4,
                'removed_readings_on_forms_without_direct_after_analysis':1,
                'removed_readings_reproduced_on_enclitic_stripped_input_after':1,'removed_readings_unexplained':2})
            self.assertEqual(report['reproduced_by_enclitic'],{'dum':1})
        finally:
            trial.supines.direct.loss.signature=original

    def test_notation_is_removed_only_from_analysis_inputs(self):
        cells,_=trial.family_cells([(b'l',b'con-pri^m',b'conj3',())])
        self.assertEqual(cells[0][0],b'conprimo')
        self.assertEqual(cells[0][3],b'con-pri^m')


if __name__=='__main__':unittest.main()
