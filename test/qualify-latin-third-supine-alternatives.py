#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Synthetic source bounds and byte-preserving insertion checks."""
from collections import Counter
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('trial',Path(__file__).resolve().parents[1]/'tools/qualify-latin-third-supine-alternatives.py')
trial=importlib.util.module_from_spec(spec);spec.loader.exec_module(trial)

def row(head,grammar):
    return {'headword':head,'fields':[{'name':'itype','projection':grammar}],'projection_error':None}

class Bounds(unittest.TestCase):
    def test_triple_literal_quantities(self):
        branch,expected=trial.recipe(row('bruo','brui, bru_tum, bruitum and bruutum, 3'))
        self.assertEqual(branch,'literal_triple_supines')
        self.assertEqual(sum(expected.values()),5)
        self.assertIn((b':vs:bru_t',b'pp4'),expected)
    def test_literal_contracted_triple(self):
        branch,expected=trial.recipe(row('ba^vo','ba^vi, bau_tum, bavatum and ba_tum, 3'))
        self.assertEqual(branch,'literal_triple_supines_vowel_contraction')
        self.assertEqual(sum(expected.values()),5)
        self.assertIn((b':vs:bau_t',b'pp4'),expected)
        self.assertIn((b':vs:bavat',b'pp4'),expected)
        self.assertIn((b':vs:ba_t',b'pp4'),expected)
    def test_unrelated_contraction_withheld(self):
        self.assertFalse(trial.recipe(row('bavo','bavi, bautum, bavatum and betum, 3'))[1])
    def test_short_supine_withheld(self):
        self.assertFalse(trial.recipe(row('bavo','bavi, utum, bavatum and batum, 3'))[1])
    def test_adjacent_fields(self):
        source=row('bruo','brui, brutum, bruitum and bruutum')
        source['fields'].append({'name':'itype','projection':'3'})
        self.assertEqual(sum(trial.recipe(source)[1].values()),5)
    def test_reduplicated_literal_homograph(self):
        branch,expected=trial.recipe(row('bati^o#1','bebe_ti, battum, and batitum, 3'))
        self.assertEqual(branch,'literal_dual_supines_reduplicated_perfect')
        self.assertIn((b':vs:bebe_t',b'perfstem'),expected)
        self.assertIn((b':vs:bat',b'conj3_io'),expected)
    def test_abbreviated_supine_withheld(self):
        self.assertFalse(trial.recipe(row('bruo','brui, tum, bruitum and bruutum, 3'))[1])
    def test_changing_perfect_withheld(self):
        self.assertFalse(trial.recipe(row('bruo','brai, brutum, bruitum and bruutum, 3'))[1])
    def test_changing_supine_withheld(self):
        self.assertFalse(trial.recipe(row('bruo','brui, brutum, bratium and bruutum, 3'))[1])
    def test_compound_withheld(self):
        self.assertFalse(trial.recipe(row('ab-bruo','brui, brutum, bruitum and bruutum, 3'))[1])
    def test_nonadjacent_fields_withheld(self):
        source=row('bruo','brui, brutum, bruitum and bruutum')
        source['fields'] += [{'name':'pos','projection':'v.'},{'name':'itype','projection':'3'}]
        self.assertFalse(trial.recipe(source)[1])
    def test_duplicate_supine_withheld(self):
        self.assertFalse(trial.recipe(row('bruo','brui, brutum, brutum and bruutum, 3'))[1])
    def test_projection_error_withheld(self):
        source=row('bruo','brui, brutum, bruitum and bruutum, 3');source['projection_error']='synthetic'
        self.assertFalse(trial.recipe(source)[1])
    def test_anchor_exactness(self):
        expected=trial.recipe(row('bruo','brui, brutum, bruitum and bruutum, 3'))[1]
        actual=Counter({(b':vs:bru',b'conj3'):1,(b':vs:bru',b'perfstem'):1,(b':vs:brut',b'pp4'):1})
        self.assertEqual(sum(trial.anchors(actual,expected).values()),2)
        actual[(b':vs:brut',b'pp4',b'orth')]=1
        with self.assertRaisesRegex(ValueError,'anchor scope'):trial.anchors(actual,expected)
    def test_insertion_keeps_unrelated_bytes_and_identity(self):
        before=b'# synthetic\n:le:bruo#1\n:vs:bru conj3\n\n:le:bruo#2\n:vs:other conj3\n'
        missing={b'bruo#1':Counter({(b':vs:brut',b'pp4'):1})}
        self.assertEqual(trial.append_missing(before,missing),
            b'# synthetic\n:le:bruo#1\n:vs:bru conj3\n\n:vs:brut pp4\n:le:bruo#2\n:vs:other conj3\n')
    def test_duplicate_block_rejected(self):
        with self.assertRaisesRegex(ValueError,'block identity'):
            trial.append_missing(b':le:bruo\n:vs:bru conj3\n:le:bruo\n:vs:bru perfstem\n',
                {b'bruo':Counter({(b':vs:brut',b'pp4'):1})})
    def test_missing_block_rejected(self):
        with self.assertRaisesRegex(ValueError,'block identity'):
            trial.append_missing(b':le:bruo\n:vs:bru conj3\n',
                {b'batio':Counter({(b':vs:bat',b'pp4'):1})})

if __name__=='__main__':unittest.main()
