#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Synthetic checks for the anchor-repair replacement inventory."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('trial',Path(__file__).resolve().parents[1]/'tools/qualify-latin-anchor-duplication.py')
trial=importlib.util.module_from_spec(spec);spec.loader.exec_module(trial)
BEFORE=b':le:volvo\n:vs:volv\tconj3\n:vs:volvolv perfstem\n:vs:volvo^lu_t pp4\n:le:mansuesco\n:vs:mansu^esc\tconj3\n:vs:mansu^esu^e_v perfstem\n:vs:mansu^esu^e_t pp4\n'
AFTER=b':le:volvo\n:vs:volv\tconj3\n:vs:volv perfstem\n:vs:vo^lu_t pp4\n:le:mansuesco\n:vs:mansu^esc\tconj3\n:vs:mansu^e_v perfstem\n:vs:mansu^e_t pp4\n'


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
        self.assertEqual(came,[(b'mansuesco',b'mansu^e_t',b'pp4',()),(b'mansuesco',b'mansu^e_v',b'perfstem',()),
                               (b'volvo',b'vo^lu_t',b'pp4',()),(b'volvo',b'volv',b'perfstem',())])
        self.assertEqual([s for _,s,_,_ in gone],[b'mansu^esu^e_t',b'mansu^esu^e_v',b'volvo^lu_t',b'volvolv'])

    def test_unpaired_or_foreign_changes_fail_closed(self):
        with self.assertRaises(ValueError):
            trial.replaced_records(BEFORE,AFTER+b':vs:extra pp4\n')
        with self.assertRaises(ValueError):
            trial.replaced_records(BEFORE,AFTER.replace(b'vo^lu_t pp4',b'vo^lu_t pp4 orth'))
        with self.assertRaises(ValueError):
            trial.replaced_records(BEFORE,AFTER.replace(b':vs:volv perfstem',b':vs:vols perfstem'))
        with self.assertRaises(ValueError):
            trial.replaced_records(BEFORE,BEFORE.replace(b'volv\tconj3',b'volv\tconj3_io'))
        self.assertEqual(trial.replaced_records(BEFORE,BEFORE),([],[]))

    def test_family_cells_of_replacements_use_perfect_and_supine_tables(self):
        _,came=trial.replaced_records(BEFORE,AFTER)
        cells,classes=trial.prefix.family_cells(came)
        self.assertEqual(classes,{'perfstem':2,'pp4':2})
        self.assertIn(b'volvit',{c[0] for c in cells})
        self.assertIn(b'volutum',{c[0] for c in cells})
        self.assertIn(b'mansuevit',{c[0] for c in cells})

    def test_pinned_counts(self):
        self.assertEqual(trial.EXPECTED_COUNTS,{'repaired_records':44,'repaired_lemma_blocks':25})


if __name__=='__main__':unittest.main()
