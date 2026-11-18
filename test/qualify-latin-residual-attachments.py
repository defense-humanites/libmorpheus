#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Synthetic checks for the residual-attachment replacement inventory."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('trial',Path(__file__).resolve().parents[1]/'tools/qualify-latin-residual-attachments.py')
trial=importlib.util.module_from_spec(spec);spec.loader.exec_module(trial)
BEFORE=(b':le:eximo\n:vs:ex-i^m\tconj3\n:vs:e_m perfstem\n:vs:empt pp4\n'
        b':le:congruo\n:vs:congru^\tconj3\n:vs:congru^u^ perfstem\n'
        b':le:sileo\n:vs:si^l\tconj3\n:vs:si^lu^ perfstem\n'
        b':le:illabor\n:vs:illa_b\tconj3\n:vs:illa_bps pp4\n')
AFTER=(b':le:eximo\n:vs:ex-i^m\tconj3\n:vs:ex-e_m perfstem\n:vs:ex-empt pp4\n'
       b':le:congruo\n:vs:congru^\tconj3\n:vs:congru^ perfstem\n'
       b':le:sileo\n:vs:si^l\tconj2\n:vs:si^lu^ perfstem\n'
       b':le:illabor\n:vs:illa_b\tconj3\n:vs:illa_ps pp4\n')


class Inventory(unittest.TestCase):
    def test_paired_replacements_including_the_reclassed_present(self):
        gone,came=trial.replaced_records(BEFORE,AFTER)
        self.assertEqual(came,[(b'congruo',b'congru^',b'perfstem',()),(b'eximo',b'ex-e_m',b'perfstem',()),
                               (b'eximo',b'ex-empt',b'pp4',()),(b'illabor',b'illa_ps',b'pp4',()),(b'sileo',b'si^l',b'conj2',())])
        self.assertEqual([s for _,s,_,_ in gone],[b'congru^u^',b'e_m',b'empt',b'illa_bps',b'si^l'])

    def test_unpaired_or_foreign_changes_fail_closed(self):
        with self.assertRaises(ValueError):
            trial.replaced_records(BEFORE,AFTER+b':vs:extra pp4\n')
        with self.assertRaises(ValueError):
            trial.replaced_records(BEFORE,AFTER.replace(b'ex-empt pp4',b'ex-empt pp4 orth'))
        with self.assertRaises(ValueError):
            trial.replaced_records(BEFORE,AFTER.replace(b':vs:ex-e_m perfstem',b':vs:ax-e_n perfstem'))
        with self.assertRaises(ValueError):
            trial.replaced_records(BEFORE,AFTER.replace(b'si^l\tconj2',b'si^l\tconj4'))
        with self.assertRaises(ValueError):
            trial.replaced_records(BEFORE,AFTER.replace(b'si^l\tconj2',b'si^le\tconj2'))
        self.assertEqual(trial.replaced_records(BEFORE,BEFORE),([],[]))

    def test_family_cells_cover_present_perfect_and_supine_tables(self):
        gone,came=trial.replaced_records(BEFORE,AFTER)
        cells,classes=trial.prefix.family_cells(came)
        self.assertEqual(classes,{'conj2':1,'perfstem':2,'pp4':2})
        forms={c[0] for c in cells}
        self.assertTrue({b'silet',b'exemit',b'congruit',b'exemptum',b'illapsum'}<=forms)
        defective,_=trial.prefix.family_cells(gone)
        self.assertTrue({b'silit',b'congruuit',b'illabpsum'}<=({c[0] for c in defective}))

    def test_defective_only_losses_accept_reclassed_present_readings(self):
        rows=[{'form':'silis','curated_count':1,'rebuilt_count':0,'retained_rows':0,'added':[],
               'removed':[{'signature':['silis','sileo',2,2,1,0,0,1,4,1,0],'multiplicity':1}]},
              {'form':'exemit','curated_count':1,'rebuilt_count':0,'retained_rows':0,'added':[],
               'removed':[{'signature':['exemit','de_-eximo',2,3,1,0,0,5,4,1,0],'multiplicity':1}]}]
        bad=rows+[{'form':'exemis','curated_count':1,'rebuilt_count':0,'retained_rows':0,'added':[],
                   'removed':[{'signature':['exemis','eximo',2,2,1,0,0,1,4,1,0],'multiplicity':1}]}]
        with tempfile.TemporaryDirectory() as d:
            delta=Path(d)/'delta.jsonl'
            delta.write_text(''.join(json.dumps(r)+'\n' for r in rows))
            report=trial.defective_only_losses(delta,{b'sileo',b'eximo'},{b'sileo'})
            self.assertEqual(report['counts'],{'forms':2,'readings':2})
            self.assertEqual(report['readings_by_tense'],{'1':1,'5':1})
            with self.assertRaises(ValueError):
                trial.defective_only_losses(delta,{b'sileo',b'eximo'})
            delta.write_text(''.join(json.dumps(r)+'\n' for r in bad))
            with self.assertRaises(ValueError):
                trial.defective_only_losses(delta,{b'sileo',b'eximo'},{b'sileo'})

    def test_pinned_counts(self):
        self.assertEqual(trial.EXPECTED_COUNTS,{'repaired_records':32,'repaired_lemma_blocks':24})


if __name__=='__main__':unittest.main()
