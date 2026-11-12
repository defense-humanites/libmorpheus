#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Synthetic checks for the labiovelar replacement inventory."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('trial',Path(__file__).resolve().parents[1]/'tools/qualify-latin-velar-short-suffix.py')
trial=importlib.util.module_from_spec(spec);spec.loader.exec_module(trial)
BEFORE=b':le:bacoquo\n:vs:ba-co^qu\tconj3\n:vs:ba-co^qx perfstem\n:vs:ba-co^qct pp4\n:le:stinguo\n:vs:stingu\tconj3\n:vs:stingx perfstem\n:vs:stingct pp4\n'
AFTER=b':le:bacoquo\n:vs:ba-co^qu\tconj3\n:vs:ba-co^x perfstem\n:vs:ba-co^ct pp4\n:le:stinguo\n:vs:stingu\tconj3\n:vs:stinx perfstem\n:vs:stinct pp4\n'


class Inventory(unittest.TestCase):
    def test_paired_replacements(self):
        gone,came=trial.replaced_records(BEFORE,AFTER)
        self.assertEqual(came,[(b'bacoquo',b'ba-co^ct',b'pp4',()),(b'bacoquo',b'ba-co^x',b'perfstem',()),
                               (b'stinguo',b'stinct',b'pp4',()),(b'stinguo',b'stinx',b'perfstem',())])
        self.assertEqual([s for _,s,_,_ in gone],[b'ba-co^qct',b'ba-co^qx',b'stingct',b'stingx'])

    def test_unpaired_or_foreign_changes_fail_closed(self):
        with self.assertRaises(ValueError):
            trial.replaced_records(BEFORE,AFTER+b':vs:extra pp4\n')
        with self.assertRaises(ValueError):
            trial.replaced_records(BEFORE,AFTER.replace(b'ba-co^ct pp4',b'ba-co^ct pp4 orth'))
        with self.assertRaises(ValueError):
            trial.replaced_records(BEFORE,AFTER.replace(b':vs:stinx perfstem',b':vs:stinxx perfstem'))
        with self.assertRaises(ValueError):
            trial.replaced_records(BEFORE,BEFORE.replace(b'ba-co^qu\tconj3',b'ba-co^qu\tconj3_io'))
        self.assertEqual(trial.replaced_records(BEFORE,BEFORE),([],[]))

    def test_family_cells_of_replacements_use_perfect_and_supine_tables(self):
        _,came=trial.replaced_records(BEFORE,AFTER)
        cells,classes=trial.prefix.family_cells(came)
        self.assertEqual(classes,{'perfstem':2,'pp4':2})
        self.assertEqual(len(cells),24)
        self.assertIn(b'bacoxit',{c[0] for c in cells})
        self.assertIn(b'stinctum',{c[0] for c in cells})


if __name__=='__main__':unittest.main()
