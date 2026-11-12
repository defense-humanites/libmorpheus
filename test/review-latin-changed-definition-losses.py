#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from lxml import etree

spec=importlib.util.spec_from_file_location('changed',Path(__file__).resolve().parents[1]/'tools/review-latin-changed-definition-losses.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
normalize=lambda text,language:text


class ChangedDefinitionReview(unittest.TestCase):
    def test_whole_full_orthographies_and_quantity_leads_remain_distinct(self):
        entry=etree.fromstring(b'<entry><orth extent="full">zzform</orth><orth extent="full">zz_fo^rm</orth><orth>zzignored</orth><orth extent="full">zzform phrase</orth></entry>')
        leads=m.surface_leads(entry,{b'zzform',b'zzignored'},normalize)
        self.assertEqual(leads[('full_orthography','literal')],{b'zzform'})
        self.assertEqual(leads[('full_orthography','notation_removed_lead')],{b'zzform'})
        self.assertEqual(len(leads),2)

    def test_citation_language_and_token_boundaries_are_required(self):
        entry=etree.fromstring(b'<entry><quote lang="lat">zzform zzformextra Zzform</quote><quote lang="grc">zzgreek</quote><quote lang="lat"><foreign lang="grc">zzgreek</foreign></quote><quote>zzunknown</quote><ref>zzform phrase</ref><ref>zzreference</ref></entry>')
        leads=m.surface_leads(entry,{b'zzform',b'zzgreek',b'zzunknown',b'zzreference'},normalize)
        self.assertEqual(leads[('latin_citation','literal')],{b'zzform'})
        self.assertEqual(leads[('whole_reference','literal')],{b'zzreference'})
        self.assertEqual(len(leads),2)

    def test_inherited_language_excludes_nonlatin_orthography(self):
        entry=etree.fromstring(b'<entry xml:lang="grc"><orth extent="full">zzgreek</orth><cit lang="la"><quote>zzlatin</quote></cit></entry>')
        leads=m.surface_leads(entry,{b'zzgreek',b'zzlatin'},normalize)
        self.assertEqual(dict(leads),{('latin_citation','literal'):{b'zzlatin'}})

    def test_inventory_selects_changed_definitions_and_counts_duplicate_readings(self):
        records=[{'kind':'lost_form','form':'zzform','readings':[{'signature':['zzform','zzlemma',2,1,1,0,0,1,4,1,0],'preverb':''}]*2},
            {'kind':'lemma_review','lemma':'zzlemma','definition_state':'changed_definition_multisets'}]
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'dossier';p.write_text(''.join(json.dumps(r)+'\n' for r in records))
            selected,forms,readings=m.dossier_inventory(p)
            self.assertEqual(set(selected),{'zzlemma'});self.assertEqual(forms['zzlemma'],{b'zzform'})
            self.assertEqual(readings['zzlemma'],{'direct':2})
            p.write_text(p.read_text()+json.dumps(records[0])+'\n')
            with self.assertRaises(ValueError):m.dossier_inventory(p)

    def test_unknown_stem_flags_never_become_public_categories(self):
        tokens=m.token_records([{'line':':vs:zzroot PRIVATEFLAG','multiplicity':2},{'line':'private echo','multiplicity':1}])
        self.assertEqual(m.classes(tokens),{'unclassified':2})
        self.assertNotIn('PRIVATEFLAG',json.dumps(m.classes(tokens)))

    def test_receipt_rejection_precedes_source_native_and_output_access(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'input';source.write_bytes(b'synthetic')
            args=SimpleNamespace(**{n:source for n in ('dossier','headers','tei','candidate','diagnostic')},output=root/'private')
            with self.assertRaisesRegex(ValueError,'receipt differs'):m.prepare(args)
            self.assertFalse(args.output.exists())


if __name__=='__main__':unittest.main()
