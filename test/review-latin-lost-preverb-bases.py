#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

spec=importlib.util.spec_from_file_location('bases',Path(__file__).resolve().parents[1]/'tools/review-latin-lost-preverb-bases.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class Reader:
    def __init__(self,rows):self.rows=rows
    def analyses(self,form,require_untruncated=False):
        if not require_untruncated:raise AssertionError('must check native text')
        return self.rows


class BaseReview(unittest.TestCase):
    def test_only_literal_identifier_prefix_is_removed(self):
        self.assertEqual(m.literal_base('re-zzbase#2','re'),'zzbase#2')
        self.assertEqual(m.literal_base('re-zz-compound','re'),'zz-compound')
        for lemma,prefix in (('rezzbase','re'),('Re-zzbase','re'),('re-','re'),('re-zzbase','')):
            self.assertIsNone(m.literal_base(lemma,prefix))

    def test_decomposition_preserves_stored_notation_and_withholds_unknown_syntax(self):
        row={'stem':'zz-st_e^m','suffix':'','ending':'o'}
        self.assertEqual(m.decomposition_form(row),b'zzstemo')
        self.assertEqual(row['stem'],'zz-st_e^m')
        row['suffix']='SECRET FLAG';self.assertIsNone(m.decomposition_form(row))

    def test_base_peer_requires_exact_lemma_grammar_decomposition_and_direct_route(self):
        reading={'signature':['re-zzform','re-zzbase',2,1,1,0,0,1,4,1,0],
            'preverb':'re','raw_preverb':'re','stem':'zzstem','suffix':'','ending':'o'}
        row=SimpleNamespace(lemma=b'zzbase',preverb=b'',part_of_speech=2,person=1,number=1,gender=0,
            grammatical_case=0,tense=1,mood=4,voice=1,degree=0,stem=b'zzstem',suffix=b'',ending=b'o')
        self.assertEqual(m.peer_count(Reader([row]),b'zzstemo','zzbase',reading),1)
        row.preverb=b'ex';self.assertEqual(m.peer_count(Reader([row]),b'zzstemo','zzbase',reading),0)
        row.preverb=b'';row.tense=5;self.assertEqual(m.peer_count(Reader([row]),b'zzstemo','zzbase',reading),0)

    def test_public_dependency_summary_omits_native_identifiers_and_forms(self):
        reading={'signature':['re-zzform','re-zzbase',2,1,1,0,0,1,4,1,0],
            'preverb':'re','raw_preverb':'re','stem':'zzstem','suffix':'','ending':'o'}
        dossiers={'re-zzbase':{'definition_state':'no_definitions_in_either'},'zzbase':{'definition_state':'changed_definition_multisets'}}
        report,private=m.inspect([{'form':'re-zzform','readings':[reading]}],dossiers,
            {b'zzbase':m.Counter({b':vs:zzstem conj3':1})},{b'zzbase':m.Counter({b':vs:zzother conj3':1})},Reader([]),Reader([]),{})
        self.assertEqual(report['counts']['literal_preverb_base_identifier'],1)
        self.assertEqual(report['groups'][0]['base_complete_loss_state'],'changed_definition_multisets')
        for value in ('zzbase','zzform','zzstem'):self.assertNotIn(value,json.dumps(report))
        self.assertEqual(private[0]['base'],'zzbase')

    def test_receipt_rejection_precedes_source_native_and_output_access(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);f=root/'input';f.write_bytes(b'synthetic')
            args=SimpleNamespace(**{n:f for n in ('dossier','baseline_expanded','final_expanded','headers','tei')},output=root/'private')
            with self.assertRaisesRegex(ValueError,'receipt differs'):m.prepare(args)
            self.assertFalse(args.output.exists())


if __name__=='__main__':unittest.main()
