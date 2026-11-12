#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Synthetic checks for the tag-leak deletion inventory."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('trial',Path(__file__).resolve().parents[1]/'tools/qualify-latin-itype-tag-leak.py')
trial=importlib.util.module_from_spec(spec);spec.loader.exec_module(trial)
BEFORE=b':le:basileo\n:vs:ba^si^l\tconj3\n:vs:ba^si^lu^ perfstem\n:vs:ba^si^l/ityp pp4\n'
AFTER=b':le:basileo\n:vs:ba^si^l\tconj3\n:vs:ba^si^lu^ perfstem\n'


class Inventory(unittest.TestCase):
    def test_only_leaked_supines_are_removed(self):
        gone,came=trial.replaced_records(BEFORE,AFTER)
        self.assertEqual(gone,[(b'basileo',b'ba^si^l/ityp',b'pp4',())]);self.assertEqual(came,[])
        self.assertEqual(trial.replaced_records(BEFORE,BEFORE),([],[]))

    def test_fail_closed_on_additions_or_other_removals(self):
        with self.assertRaises(ValueError):
            trial.replaced_records(BEFORE,AFTER+b':vs:extra pp4\n')
        with self.assertRaises(ValueError):
            trial.replaced_records(BEFORE,AFTER.replace(b':vs:ba^si^lu^ perfstem\n',b''))
        with self.assertRaises(ValueError):
            trial.replaced_records(BEFORE.replace(b'/ityp pp4',b'/ityp pp4 orth'),AFTER)

    def test_leaked_cells_carry_the_slash(self):
        gone,_=trial.replaced_records(BEFORE,AFTER)
        cells,classes=trial.prefix.family_cells(gone)
        self.assertEqual(classes,{'pp4':1})
        self.assertTrue(all(b'/' in c[0] for c in cells))


if __name__=='__main__':unittest.main()
