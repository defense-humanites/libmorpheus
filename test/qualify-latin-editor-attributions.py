#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Synthetic checks for the editor-attribution replacement inventory."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('trial',Path(__file__).resolve().parents[1]/'tools/qualify-latin-editor-attributions.py')
trial=importlib.util.module_from_spec(spec);spec.loader.exec_module(trial)
BEFORE=(b':le:barrodo\n:vs:bar-ro_d\tconj3\n:vs:bar-ro_dKayser perfstem\n'
        b':le:battrecto\n:vs:bat-trect\tconj1\n:vs:bat-trectRitschl perfstem\n:le:other\n:vs:oth\tconj3\n')
AFTER=(b':le:barrodo\n:vs:bar-ro_d\tconj3\n:vs:bar-ro_s perfstem\n:vs:bar-ro_s pp4\n'
       b':le:battrecto\n:de:bat-trect\tare_vb\n:le:other\n:vs:oth\tconj3\n')


class Inventory(unittest.TestCase):
    def test_partition_of_removed_records(self):
        gone,came,junk,reclassed=trial.replaced_records(BEFORE,AFTER)
        self.assertEqual([s for _,s,_,_ in junk],[b'bar-ro_dKayser',b'bat-trectRitschl'])
        self.assertEqual(reclassed,[(b'battrecto',b'bat-trect',b'conj1',())])
        self.assertEqual(came,[(b'barrodo',b'bar-ro_s',b'perfstem',()),(b'barrodo',b'bar-ro_s',b'pp4',()),
                               (b'battrecto',b'bat-trect',b'are_vb',())])
        self.assertEqual(len(gone),3)

    def test_fail_closed_on_unexpected_shapes(self):
        with self.assertRaises(ValueError):
            trial.replaced_records(BEFORE,AFTER.replace(b'bar-ro_s pp4',b'bar-Ro_s pp4'))
        with self.assertRaises(ValueError):
            trial.replaced_records(BEFORE.replace(b'bar-ro_dKayser perfstem',b'bar-ro_dKayser pp4'),AFTER)
        with self.assertRaises(ValueError):
            trial.replaced_records(BEFORE,AFTER.replace(b':de:bat-trect\tare_vb',b':de:bat-trecta\tare_vb'))
        with self.assertRaises(ValueError):
            trial.replaced_records(BEFORE,AFTER+b':le:extra\n:vs:ext\tconj3\n')
        self.assertEqual(trial.replaced_records(BEFORE,BEFORE),([],[],[],[]))

    def test_family_cells_of_added_and_reclassed_records(self):
        _,came,_,reclassed=trial.replaced_records(BEFORE,AFTER)
        cells,classes=trial.prefix.family_cells(came)
        self.assertEqual(classes,{'perfstem':1,'pp4':1,'are_vb':1})
        self.assertIn(b'battrectat',{c[0] for c in cells})
        old,_=trial.prefix.family_cells(reclassed)
        self.assertEqual({c[0] for c in old},{b'battrecto',b'battrectas',b'battrectat',b'battrectamus',b'battrectatis',b'battrectant'})


if __name__=='__main__':unittest.main()
