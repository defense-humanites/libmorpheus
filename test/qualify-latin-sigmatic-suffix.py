#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Synthetic checks for the sigmatic-repair replacement inventory."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('trial',Path(__file__).resolve().parents[1]/'tools/qualify-latin-sigmatic-suffix.py')
trial=importlib.util.module_from_spec(spec);spec.loader.exec_module(trial)
BEFORE=b':le:refulcio\n:vs:re^-fulc\tconj4\n:vs:re^-fulcs perfstem\n:vs:re^-fulct pp4\n:le:indulgeo\n:vs:indulg\tconj2\n:vs:ins perfstem\n:vs:int pp4\n'
AFTER=b':le:refulcio\n:vs:re^-fulc\tconj4\n:vs:re^-fuls perfstem\n:vs:re^-fult pp4\n:le:indulgeo\n:vs:indulg\tconj2\n:vs:induls perfstem\n:vs:indult pp4\n'


class Inventory(unittest.TestCase):
    def test_one_deletion_disregards_notation(self):
        self.assertTrue(trial.one_deletion(b'volvolv',b'volv'))
        self.assertTrue(trial.one_deletion(b'mansu^esu^e_v',b'mansu^e_v'))
        self.assertTrue(trial.one_deletion(b'volvo^lu_t',b'vo^lu_t'))
        self.assertFalse(trial.one_deletion(b'volv',b'volv'))
        self.assertFalse(trial.one_deletion(b'volvolv',b'volx'))
        self.assertFalse(trial.one_deletion(b'ab-cdef',b'acf'))

    def test_paired_replacements(self):
        gone,came=trial.replaced_records(BEFORE,AFTER)
        self.assertEqual(came,[(b'indulgeo',b'induls',b'perfstem',()),(b'indulgeo',b'indult',b'pp4',()),
                               (b'refulcio',b're^-fuls',b'perfstem',()),(b'refulcio',b're^-fult',b'pp4',())])
        self.assertEqual([s for _,s,_,_ in gone],[b'ins',b'int',b're^-fulcs',b're^-fulct'])

    def test_unpaired_or_foreign_changes_fail_closed(self):
        with self.assertRaises(ValueError):
            trial.replaced_records(BEFORE,AFTER+b':vs:extra pp4\n')
        with self.assertRaises(ValueError):
            trial.replaced_records(BEFORE,AFTER.replace(b're^-fult pp4',b're^-fult pp4 orth'))
        with self.assertRaises(ValueError):
            trial.replaced_records(BEFORE,AFTER.replace(b':vs:induls perfstem',b':vs:indulz perfstem'))
        with self.assertRaises(ValueError):
            trial.replaced_records(BEFORE,BEFORE.replace(b'indulg\tconj2',b'indulg\tconj3'))
        self.assertEqual(trial.replaced_records(BEFORE,BEFORE),([],[]))

    def test_family_cells_of_replacements_use_perfect_and_supine_tables(self):
        _,came=trial.replaced_records(BEFORE,AFTER)
        cells,classes=trial.prefix.family_cells(came)
        self.assertEqual(classes,{'perfstem':2,'pp4':2})
        self.assertIn(b'indulsit',{c[0] for c in cells})
        self.assertIn(b'refultum',{c[0] for c in cells})

    def test_defective_only_losses(self):
        import json,tempfile
        rows=[{'form':'subsit','curated_count':1,'rebuilt_count':0,'retained_rows':0,'added':[],
               'removed':[{'signature':['subsit','subsentio',2,3,1,0,0,5,4,1,0],'multiplicity':1}]},
              {'form':'other','curated_count':2,'rebuilt_count':1,'retained_rows':1,'added':[],
               'removed':[{'signature':['other','indulgeo',2,3,1,0,0,5,4,1,0],'multiplicity':1}]}]
        bad=rows+[{'form':'gone','curated_count':1,'rebuilt_count':0,'retained_rows':0,'added':[],
                   'removed':[{'signature':['gone','amo',2,3,1,0,0,1,4,1,0],'multiplicity':1}]}]
        with tempfile.TemporaryDirectory() as d:
            delta=Path(d)/'delta.jsonl'
            delta.write_text(''.join(json.dumps(r)+'\n' for r in rows))
            report=trial.defective_only_losses(delta,{b'subsentio',b'indulgeo'})
            self.assertEqual(report['counts'],{'forms':1,'readings':1})
            self.assertEqual(report['readings_by_tense'],{'5':1})
            delta.write_text(''.join(json.dumps(r)+'\n' for r in bad))
            with self.assertRaises(ValueError):
                trial.defective_only_losses(delta,{b'subsentio',b'indulgeo'})

    def test_pinned_counts(self):
        self.assertEqual(trial.EXPECTED_COUNTS,{'repaired_records':10,'repaired_lemma_blocks':6})


if __name__=='__main__':unittest.main()
