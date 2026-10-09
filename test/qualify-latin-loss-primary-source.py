#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import argparse
from collections import Counter
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

spec=importlib.util.spec_from_file_location('tool',Path(__file__).resolve().parents[1]/'tools/qualify-latin-loss-primary-source.py')
tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)


def header(head,grammar):
    return {'headword':head,'projection_error':None,'fields':[{'name':'itype','projection':grammar}]}


class PrimarySource(unittest.TestCase):
    def test_first_active_root_and_homograph_are_literal(self):
        row=header('zzza_-xio#2','a_vi, a_tum, 1')
        branch,records=tool.source_recipe(row)
        self.assertEqual(branch,'regular_first_active_primary')
        self.assertEqual(records,Counter({(b':de:zzza_-xi',b'are_vb'):1}))
        self.assertEqual(tool.review.source_key(row),b'zzzaxio#2')

    def test_deponent_requires_both_source_voice_conditions(self):
        self.assertEqual(tool.source_recipe(header('zzzaxamor','a_tus, 1'))[1],
                         Counter({(b':de:zzzaxam',b'are_vb',b'dep'):1}))
        for row in (header('zzzaxamo','a_tus, 1'),header('zzzaxamor','a_vi, a_tum, 1')):
            self.assertFalse(tool.source_recipe(row)[1])

    def test_compound_uses_only_explicit_boundary(self):
        row=header('zzza_-maxo','ma_xi, ma_xum, 3')
        _,records=tool.source_recipe(row)
        self.assertEqual(records,Counter({(b':vs:zzza_-max',b'conj3'):1,
            (b':vs:zzza_-ma_x',b'perfstem'):1,(b':vs:zzza_-ma_x',b'pp4'):1}))
        for head,g in [('zzzamaxo','ma_xi, ma_xum, 3'),('zzza-maxo','na_xi, ma_xum, 3'),
                       ('zzza-amo','a_xi, a_xum, 3'),('zzza-maxo','ma_xi or maxi, ma_xum, 3'),
                       ('zzza-maxi^o','ma_xi, ma_xum, 3'),('zzza-maxio','ma_xi, ma_xum, 3'),
                       ('zzza-maxo','mi_xi, ma_xum, 3'),('zzza-maxo','ma_xi, mum, 3')]:
            self.assertFalse(tool.source_recipe(header(head,g))[1])

    def test_fourth_perfect_does_not_create_supine(self):
        _,records=tool.source_recipe(header('zzzmi^o','i_vi, 4'))
        self.assertEqual(records,Counter({(b':vs:zzzm',b'conj4'):1,(b':vs:zzzmi_v',b'perfstem'):1}))
        self.assertFalse(any(b'pp4' in tokens for tokens in records))
        for head in ('i^o','zzzmio','zzzmi^or'):
            self.assertFalse(tool.source_recipe(header(head,'i_vi, 4'))[1])

    def test_projection_and_nonadjacent_grammar_withheld(self):
        row=header('zzzamo','a_vi, a_tum, 1');row['projection_error']='unsupported'
        self.assertFalse(tool.source_recipe(row)[1])
        row=header('zzzamo','a_vi');row['fields'] += [dict(name='pos',projection='v.'),dict(name='itype',projection='a_tum, 1')]
        self.assertFalse(tool.source_recipe(row)[1])
        self.assertFalse(tool.source_recipe(header('zzzamo#22','a_re'))[1])

    def test_family_codes_and_input_notation_are_separate(self):
        _,records=tool.source_recipe(header('zzza_-xio#2','a_vi, a_tum, 1'))
        cells=tool.family_cells(records)
        self.assertEqual(len(cells),6)
        self.assertEqual(cells[0],(b'zzzaxio',(2,1,1,0,0,1,4,1,0),b'zzza_-xi'))
        self.assertEqual(cells[3][1][1:3],(1,3))
        with self.assertRaisesRegex(ValueError,'duplicate'):
            tool.family_cells(Counter({(b':de:zzzax',b'are_vb'):2}))

    def test_orth_is_withheld_without_accepting_other_flags(self):
        records=Counter({(b':de:zzzax',b'are_vb'):1,(b':de:zzzay',b'are_vb',b'orth'):1,
                         (b':de:zzzaz',b'are_vb',b'not_in_comp'):1})
        self.assertEqual(sum(tool.primary(records).values()),2)
        self.assertIn((b':de:zzzaz',b'are_vb',b'not_in_comp'),tool.primary(records))

    def test_native_comparison_includes_decomposition_and_direct_identity(self):
        signature=(2,1,1,0,0,1,4,1,0)
        def row(**kwargs):
            values=dict(zip(('part_of_speech','person','number','gender','grammatical_case','tense','mood','voice','degree'),signature))
            values.update(workword=b'zzzaxo',lemma=b'zzzaxo',preverb=b'',raw_preverb=b'',stem=b'zzzax',suffix=b'',ending=b'o')
            values.update(kwargs);return SimpleNamespace(**values)
        class Reader:
            def __init__(self,rows):self.data=rows
            def analyses(self,word,require_untruncated):
                assert require_untruncated;return self.data
        cells=[(b'zzzaxo',signature,b'zzzax')]
        reference=Reader([row(),row()])
        actual=Reader([row(),row(suffix=b'x'),row(preverb=b'z'),row(lemma=b'zzzaxo#2')])
        counts,_=tool.check_cells(actual,b'zzzaxo',cells,reference)
        self.assertEqual(counts['matching_direct_readings'],1)
        self.assertEqual(counts['missing_reference_readings'],1)

    def test_input_receipt_checked_before_private_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);source=p/'source';source.write_bytes(b'invalid')
            args=argparse.Namespace(**{n:source for n in ('report','candidate','diagnostic','headers','tei')},output=p/'output')
            with self.assertRaisesRegex(ValueError,'input receipt'):
                tool.prepare(args)
            self.assertFalse(args.output.exists())


if __name__=='__main__':unittest.main()
