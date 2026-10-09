#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Synthetic attribution, multiplicity, identity and quantity regressions."""
from collections import Counter
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

spec=importlib.util.spec_from_file_location('review',Path(__file__).resolve().parents[1]/'tools/review-latin-third-supine-recoveries.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def row(lemma=b'bavo',stem=b'ba_t',preverb=b'',word=b'batum',raw_preverb=b''):
    return SimpleNamespace(workword=word,lemma=lemma,part_of_speech=2,person=0,number=1,
        gender=8,grammatical_case=16,tense=0,mood=9,voice=0,degree=0,
        stem=stem,suffix=b'',ending=b'um',preverb=preverb,raw_preverb=raw_preverb)


def record(before,after):
    left=Counter(map(m.loss.signature,before));right=Counter(map(m.loss.signature,after))
    return {'form':'batum','curated_count':len(before),'rebuilt_count':len(after),
        'retained_rows':sum((left&right).values()),'added':m.serialized(right-left),
        'removed':m.serialized(left-right)}


class Reader:
    def __init__(self,rows):self.rows=rows
    def analyses(self,form,require_untruncated=False):
        if not require_untruncated:raise AssertionError('complete native reads required')
        return self.rows


class Attribution(unittest.TestCase):
    def test_complete_loss_recovered(self):
        added=row();counts,cases,_,_=m.compare(record([], [added]),[],[added],[added],{b'bavo':{}})
        self.assertEqual(counts['historical_readings_restored__complete_form_loss'],1)
        self.assertEqual(cases[(b'bavo','sixteen_fields')],1)
    def test_recognized_form_excluded_from_complete_dossier(self):
        kept=row(lemma=b'other');added=row()
        counts,cases,_,_=m.compare(record([kept],[kept,added]),[kept],[kept,added],[kept,added],{b'bavo':{}})
        self.assertEqual(counts['historical_readings_restored__still_recognized_form_loss'],1)
        self.assertFalse(cases)
    def test_addition_without_old_loss(self):
        added=row();counts,_,_,_=m.compare(record([],[added]),[],[added],[],{b'bavo':{}})
        self.assertEqual(counts['additions_beyond_historical_removed_multiset'],1)
        self.assertEqual(counts['historical_removed_readings_restored'],0)
    def test_duplicate_multiplicity_is_not_one(self):
        added=row();counts,_,pairs,_=m.compare(record([],[added,added]),[],[added,added],[added],{b'bavo':{}})
        self.assertEqual(counts['added_sixteen_field_readings'],2)
        self.assertEqual(counts['historical_removed_readings_restored'],1)
        self.assertEqual(pairs[0][1],2)
    def test_quantity_difference_does_not_prove_sixteen_fields(self):
        historical=row(stem=b'ba^t');added=row(stem=b'ba_t')
        counts,_,_,_=m.compare(record([],[added]),[],[added],[historical],{b'bavo':{}})
        self.assertEqual(counts['selected_old_complete_loss_readings_restored_eleven_fields'],1)
        self.assertEqual(counts['selected_old_complete_loss_readings_restored_sixteen_fields'],0)
    def test_retained_derivation_change_rejected_at_equal_grammar(self):
        old=row(stem=b'ba^t');new=row(stem=b'ba_t')
        with self.assertRaisesRegex(ValueError,'retained derivation'):
            m.compare(record([old],[new]),[old],[new],[old],{b'bavo':{}})
    def test_qualified_ledger_mismatch_rejected(self):
        added=row();evidence=record([],[added]);evidence['added'][0]['multiplicity']=2
        with self.assertRaisesRegex(ValueError,'qualified multiset'):
            m.compare(evidence,[],[added],[added],{b'bavo':{}})
    def test_homograph_identity_kept(self):
        added=row(lemma=b'bavo#2');historical=row(lemma=b'bavo#1')
        counts,_,_,_=m.compare(record([],[added]),[],[added],[historical],{b'bavo#2':{}})
        self.assertEqual(counts['historical_removed_readings_restored'],0)
    def test_native_identifier_literal_boundary(self):
        self.assertEqual(m.bases.literal_base('ab-bavo#2','ab'),'bavo#2')
        self.assertIsNone(m.bases.literal_base('abbavo','ab'))
        self.assertIsNone(m.bases.literal_base('ad-bavo','ab'))
    def test_exact_native_base_peer(self):
        native=row(lemma=b'ab-bavo#2',preverb=b'ab',raw_preverb=b'ab')
        direct=row(lemma=b'bavo#2');empty=Reader([])
        readers={'baseline':empty,'original':empty,'trial':Reader([direct]),'reference':Reader([direct])}
        group,base,details=m.inspect_dependency(native,readers,{b'bavo#2':{}})
        self.assertEqual(base,'bavo#2')
        self.assertEqual(group,('selected_source_base','after_direct_peer_only',True,False))
        self.assertEqual(details['exact_direct_peers']['trial'],1)
    def test_wrong_quantity_and_homograph_peers_withheld(self):
        native=row(lemma=b'ab-bavo#2',preverb=b'ab',raw_preverb=b'ab')
        wrong=Reader([row(lemma=b'bavo#1'),row(lemma=b'bavo#2',stem=b'ba^t')])
        group,_,_=m.inspect_dependency(native,{name:wrong for name in ('baseline','original','trial','reference')},{b'bavo#2':{}})
        self.assertEqual(group,('selected_source_base','no_direct_peer',False,False))
    def test_native_peer_cannot_count_as_direct(self):
        native=row(lemma=b'ab-bavo',preverb=b'ab')
        indirect=Reader([row(preverb=b'zz')])
        group,_,_=m.inspect_dependency(native,{name:indirect for name in ('baseline','original','trial','reference')},{b'bavo':{}})
        self.assertFalse(group[2])
    def test_unclassified_identifier_is_not_normalized(self):
        native=row(lemma=b'abbavo',preverb=b'ab')
        group,base,_=m.inspect_dependency(native,{name:Reader([row()]) for name in ('baseline','original','trial','reference')},{b'bavo':{}})
        self.assertIsNone(base)
        self.assertEqual(group[0],'unclassified_identifier')
    def test_published_receipts_bind_exact_bytes(self):
        root=Path(__file__).resolve().parents[1]
        self.assertEqual(m.native.digest(root/'docs/qualification/latin-third-supine-alternatives-60b3eb4.json'),m.QUALIFICATION_SHA)
        self.assertEqual(m.native.digest(root/'docs/qualification/latin-loss-source-review-8462af2.json'),m.trial.primary.REPORT_SHA)
    def test_invalid_signature_length_rejected(self):
        with self.assertRaisesRegex(ValueError,'signature scope'):
            m.deserialized([{'signature':['synthetic'],'multiplicity':1}])
    def test_invalid_multiplicity_rejected(self):
        for count in (0,-1,True,1.5):
            with self.assertRaisesRegex(ValueError,'signature scope'):
                m.deserialized([{'signature':[0]*11,'multiplicity':count}])
    def test_unjoined_case_does_not_have_a_header_receipt(self):
        evidence=[];cases=[{'source_partition':'no_article_join'}]
        for head,grammar,count in [('bavo','bavi, bautum, bavatum and batum, 3',77),
                                   ('bati^o#2','bebeti, battum, and batitum, 3',42)]:
            source={'headword':head,'projection_error':None,'fields':[{'name':'itype','projection':grammar}]}
            key=m.trial.review.probe.digest(json.dumps(source,sort_keys=True).encode())
            cases.append({'source_header_sha256':key,'source_partition':'verbal','literal_headword_identity':True,'readings':{'direct':count}})
            evidence.append({'source_header':source,'lemma':m.trial.review.source_key(source).decode()})
        selected,_=m.source_cases(evidence,{'changed_definition_source_review':{'anonymous_cases':cases}})
        self.assertEqual(sum(c['old_complete_loss_readings'] for c in selected.values()),119)
    def test_filter_preserves_original_quantity_and_case_bytes(self):
        lines=[b'BA_TTUM\n',b'abbattum\n',b'unrelated\n']
        self.assertEqual(m.filtered_forms(lines,{b'batt'}),lines[:2])
    def test_replay_bounds_do_not_accept_other_directives(self):
        with self.assertRaisesRegex(ValueError,'directive scope'):
            m.replay_needles([{'missing':[[':vs:bat','perfstem']]}])
        with self.assertRaisesRegex(ValueError,'alternative count'):
            m.replay_needles([{'missing':[[':vs:bat','pp4']]}])


if __name__=='__main__':unittest.main()
