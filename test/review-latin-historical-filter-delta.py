#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('review',Path(__file__).resolve().parents[1]/
                                         'tools/review-latin-historical-filter-delta.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class SourceReview(unittest.TestCase):
    def test_grammar_shape_publishes_only_structure_and_receipt(self):
        row={'fields':[{'name':'itype','projection':'zz_vi or zz^i, zz_tum, 3'},
                       {'name':'pos','projection':'SECRET'}]}
        shape=m.source_grammar_shape(row)
        self.assertEqual(shape['terminal_conjugation_digit'],3)
        self.assertEqual(shape['principal_part_like_tokens'],3)
        self.assertEqual(shape['tokens_with_quantity_marks'],3)
        self.assertEqual(shape['comma_separated_segments'],3)
        self.assertNotIn('zz',json.dumps(shape));self.assertNotIn('SECRET',json.dumps(shape))
        row['fields'][0]['projection']='SECRET 99'
        self.assertIsNone(m.source_grammar_shape(row)['terminal_conjugation_digit'])

    def test_isolated_replay_measures_only_the_selected_literal_lemma(self):
        calls=[]
        def run(command,target,name,data):
            calls.append(name)
            return (b':le:zzselected#2\n:vs:zzstem perfstem\n:le:zzother\n:vs:zzother conj4\n'
                    if name=='replay-latvb' else b'zzsynthetic <itype>i_vi, or i^i, i_tum, 4</itype>\n')
        with patch.object(m,'sibling',return_value=SimpleNamespace(render=lambda row:'synthetic header\n')):
            with patch.object(m.probe,'run_private',side_effect=run):
                records,branches=m.isolated_replay({},b'zzselected#2',Path('/filters'),Path('/diagnostic'),Path('/private'))
        self.assertEqual(calls,['replay-combitype','replay-splitlat','replay-conj1','replay-latvb'])
        self.assertEqual(records,m.Counter({(b':vs:zzstem',b'perfstem'):1}))
        self.assertEqual(branches,1)

    def test_unrecognized_backend_grammar_is_not_counted_as_a_known_branch(self):
        with patch.object(m,'sibling',return_value=SimpleNamespace(render=lambda row:'synthetic\n')):
            with patch.object(m.probe,'run_private',return_value=b'synthetic echo'):
                records,branches=m.isolated_replay({},b'zzselected',Path('/filters'),Path('/diagnostic'),Path('/private'))
        self.assertFalse(records);self.assertEqual(branches,0)

    def test_adjacent_source_fields_and_bare_quantity_remain_literal(self):
        row={'headword':'zzzo','fields':[{'name':'itype','projection':'i_vi and ii, i_tum'},
                                        {'name':'itype','projection':'4'}]}
        branch,expected=m.source_expectations(row)
        self.assertEqual(branch,'alternative_perfect_with_supine')
        self.assertIn((b':vs:zzzi',b'perfstem'),expected)
        self.assertNotIn((b':vs:zzzi^',b'perfstem'),expected)
        row['fields'].insert(1,{'name':'pos','projection':'synthetic'})
        self.assertEqual(m.source_expectations(row),('unclassified',m.Counter()))

    def test_quantity_pair_diagnostic_is_not_identity_substitution(self):
        missing=m.Counter({(b':vs:zzzi',b'perfstem'):1})
        extra=m.Counter({(b':vs:zzzi^',b'perfstem'):1})
        self.assertEqual(m.quantity_only_pairs(missing,extra),1)
        self.assertNotEqual(missing,extra)
        self.assertEqual(m.quantity_only_pairs(missing,m.Counter({(b':vs:zzother',b'perfstem'):1})),0)

    def test_classes_never_publish_unknown_tokens(self):
        self.assertEqual(m.classify(b':vs:zzstem perfstem SECRET'),'perfect')
        self.assertEqual(m.classify(b':vs:zzstem pp4'),'supine')
        self.assertEqual(m.classify(b':vs:zzstem SECRET'),'unclassified')
        self.assertEqual(m.classify(b':vs:zzstem conj4 perfstem'),'conflicting')

    def test_literal_join_preserves_case_and_homograph(self):
        self.assertEqual(m.source_key({'headword':'Zz_^zo#2'}),b'Zzzo#2')
        self.assertIsNone(m.source_key({'headword':'zzzo phrase'}))
        self.assertIsNone(m.source_key({'headword':'zzzo','projection_error':'synthetic'}))

    def test_alternative_perfect_recipe_preserves_source_quantity(self):
        row={'headword':'zz_i^o#2','fields':[{'name':'itype','projection':'i_vi, or i^i, i_tum, 4'}]}
        branch,expected=m.source_expectations(row)
        self.assertEqual(branch,'alternative_perfect_with_supine')
        self.assertEqual(sum(expected.values()),4)
        self.assertIn((b':vs:zz_i_v',b'perfstem'),expected)
        self.assertIn((b':vs:zz_i^',b'perfstem'),expected)
        self.assertIn((b':vs:zz_i_t',b'pp4'),expected)
        row['fields'][0]['projection']='i_vi, or i^i, 4'
        self.assertEqual(sum(m.source_expectations(row)[1].values()),3)

    def test_unclassified_and_duplicate_grammar_is_not_approved(self):
        row={'headword':'zzzo','fields':[{'name':'itype','projection':'synthetic grammar'}]}
        self.assertEqual(m.source_expectations(row),('unclassified',m.Counter()))
        row['fields']=[{'name':'itype','projection':'i_vi, or i^i, 4'}]*2
        self.assertEqual(m.source_expectations(row),('unclassified',m.Counter()))

    def test_delta_must_match_actual_raw_multisets(self):
        left=m.probe.definitions(b':le:zzzo\n:vs:zzold perfstem\n')
        right=m.probe.definitions(b':le:zzzo\n:vs:zznew perfstem\n')
        rows=[{'change':label,'lemma':'zzzo','directive':line,'multiplicity':1} for label,line in
              (('removed',':vs:zzold perfstem'),('added',':vs:zznew perfstem'))]
        payload='\n'.join(json.dumps(r) for r in rows).encode()
        m.validate_delta(payload,left,right)
        with self.assertRaises(ValueError):m.validate_delta(payload+b'\n'+json.dumps(rows[0]).encode(),left,right)
        rows[1]['directive']=':vs:zzother perfstem'
        with self.assertRaises(ValueError):m.validate_delta('\n'.join(json.dumps(r) for r in rows).encode(),left,right)

    def test_receipt_rejection_precedes_source_access_and_output(self):
        with tempfile.TemporaryDirectory() as directory:
            r=Path(directory);f=r/'input';f.write_bytes(b'synthetic')
            args=SimpleNamespace(**{n:f for n in m.RECEIPTS},output=r/'output')
            with self.assertRaisesRegex(ValueError,'receipt differs'):m.prepare(args)
            self.assertFalse(args.output.exists())


if __name__=='__main__':unittest.main()
