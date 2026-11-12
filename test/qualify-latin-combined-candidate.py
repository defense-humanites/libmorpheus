#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Synthetic checks for the combined-candidate record inventory."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('trial',Path(__file__).resolve().parents[1]/'tools/qualify-latin-combined-candidate.py')
trial=importlib.util.module_from_spec(spec);spec.loader.exec_module(trial)
BEFORE=(b':le:a\n:vs:a\tconj1\n:vs:aKayser perfstem\n:le:b\n:vs:b\tconj3\n:vs:bu^ perfstem\n:vs:b/ityp pp4\n'
        b':le:c\n:vs:co^qu\tconj3\n:vs:co^qx perfstem\n:vs:co^qct pp4\n')
AFTER=(b':le:a\n:de:a\tare_vb\n:de:ad\tare_vb orth\n:le:b\n:vs:b\tconj3\n:vs:bu^ perfstem\n'
       b':le:c\n:vs:co^qu\tconj3\n:vs:co^x perfstem\n:vs:co^ct pp4\n:vs:co^x\tconj3 orth\n')


class Inventory(unittest.TestCase):
    def test_delta_and_removed_classes(self):
        gone,came=trial.record_delta(BEFORE,AFTER)
        self.assertEqual(trial.classify_removed(gone),{'attribution_stem':1,'leaked_tag_stem':1,'reclassed_conj1_present':1,
                                                        'replaced_perfstem':1,'replaced_pp4':1})
        self.assertEqual([(l,s,k) for l,s,k,_ in came],[(b'a',b'a',b'are_vb'),(b'a',b'ad',b'are_vb'),(b'c',b'co^ct',b'pp4'),
                                                         (b'c',b'co^x',b'conj3'),(b'c',b'co^x',b'perfstem')])
        self.assertEqual(trial.record_delta(BEFORE,BEFORE),([],[]))

    def test_added_record_cells(self):
        _,came=trial.record_delta(BEFORE,AFTER)
        cells,classes=trial.prefix.family_cells(came)
        self.assertEqual(classes,{'are_vb':2,'pp4':1,'conj3':1,'perfstem':1})
        self.assertIn(b'adat',{c[0] for c in cells}); self.assertIn(b'coxit',{c[0] for c in cells})

    def test_pinned_sequence(self):
        self.assertEqual([name for name,_ in trial.combine.STAGES],list(trial.STAGE_SHA))
        self.assertEqual(trial.STAGE_SHA['quoted-presents'],trial.COMBINED_SHA)


if __name__=='__main__':unittest.main()
