#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
SCRIPT=Path(__file__).resolve().parents[1]/'tools/recover-latin-regular-parts-alternates.py'
spec=importlib.util.spec_from_file_location('m',SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def row(head='za_-prendo#2',field='di, sum, 3',alts=None):
    return dict(headword=head,projection_error=None,fields=[dict(name='itype',projection=field)],full_alternates=alts or ['za_praendo'])

class Alternates(unittest.TestCase):
    raw=b':le:zaprendo#2\n:vs:za_-prend conj3\n:vs:za_-prend perfstem\n:vs:za_-prens pp4\n'
    def test_three_source_parts_prefixes_homograph_and_idempotence(self):
        data,counts=m.transform(self.raw,[row()])
        self.assertEqual(counts,{'added_records':3,'changed_lemma_blocks':1})
        self.assertTrue(data.endswith(b':vs:za_praend\tconj3 orth\n:vs:za_praend\tperfstem orth\n:vs:za_praens\tpp4 orth\n'))
        self.assertEqual(m.transform(data,[row()])[0],data)
    def test_fourth_quantities_and_missing_final_newline(self):
        raw=b':le:zavio\n:vs:za_v conj4\n:vs:za_vi_v perfstem\n:vs:za_vi_t pp4'
        source=row('za_vi^o','i_vi, i_tum, 4',['zauv_i^o'])
        data,counts=m.transform(raw,[source])
        self.assertEqual(counts['added_records'],3)
        self.assertIn(b'pp4\n:vs:zauv_\tconj4 orth\n',data)
        self.assertIn(b':vs:zauv_i_t\tpp4 orth\n',data)
    def test_withhold_missing_conflicting_and_flagged_primary_parts(self):
        for raw in [self.raw.replace(b'za_-prens',b'wrong'),self.raw.replace(b'perfstem',b'perfstem orth'),self.raw+b':vs:other pp4\n',self.raw*2]:
            self.assertEqual(m.transform(raw,[row()])[0],raw)
        source=row();source['fields'].append(dict(name='itype',projection='4'))
        self.assertEqual(m.transform(self.raw,[source])[0],self.raw)
        self.assertEqual(m.transform(self.raw,[row(),row()])[0],self.raw)
    def test_withhold_voice_abbreviations_and_notation_only(self):
        for source in [row(alts=['za_praendor']),row(alts=['za-']),row(alts=['za_prendo']),row(field='3'),row(head='za_prendor#2')]:
            self.assertEqual(m.transform(self.raw,[source])[0],self.raw)
        self.assertIsNone(m.parts('zavi^o','i_vi, 4'))
    def test_terminal_delimiter_is_opt_in_and_keeps_source_spelling(self):
        source=row(alts=['za_praen-do'])
        self.assertEqual(m.transform(self.raw,[source])[0],self.raw)
        data,counts=m.transform(self.raw,[source],'terminal-delimiter')
        self.assertEqual(counts['added_records'],3)
        self.assertTrue(data.endswith(b':vs:za_praen-d\tconj3 orth\n:vs:za_praen-d\tperfstem orth\n:vs:za_praen-s\tpp4 orth\n'))
        self.assertEqual(m.transform(data,[source],'terminal-delimiter')[0],data)
        with self.assertRaises(ValueError):m.transform(self.raw,[source],'unknown')
    def test_terminal_delimiter_withholds_abbreviations_voice_and_other_tiers(self):
        for source in [row(alts=['za_praen-dor']),row(alts=['za-pren-']),row(alts=['za_prendo']),row(field='3'),row(field='i_vi, i_tum, 4')]:
            self.assertEqual(m.transform(self.raw,[source],'terminal-delimiter')[0],self.raw)
        self.assertEqual(m.transform(self.raw.replace(b'za_-prens',b'other'),[row(alts=['za_praen-do'])],'terminal-delimiter')[0],self.raw.replace(b'za_-prens',b'other'))
    def test_present_only_keeps_missing_parts_missing_and_preserves_other_records(self):
        raw=b':le:zaprendo#2\n:vs:za_-prend conj3\n:vs:unrelated perfstem\n'
        source=row(field='3',alts=['za_praendo'])
        data,counts=m.transform(raw,[source],'present-only')
        self.assertEqual(counts['added_records'],1)
        self.assertIn(b':vs:za_praend\tconj3 orth\n',data)
        self.assertEqual(data.count(b'perfstem'),1);self.assertNotIn(b'pp4',data)
        self.assertEqual(m.transform(data,[source],'present-only')[0],data)
        io=b':le:zavio\n:vs:zav conj3_io\n'
        data,counts=m.transform(io,[row(head='zavi^o',field='3',alts=['zavvi^o'])],'present-only')
        self.assertEqual(data,io+b':vs:zavv\tconj3_io orth\n')
    def test_present_only_withholds_voice_subclass_flags_and_unproved_grammar(self):
        raw=b':le:zaprendo#2\n:vs:za_-prend conj3\n'
        for source in [row(field='3',alts=['za_praendor']),row(field='3',alts=['za_praendio']),row(field='4'),row(field='3',alts=['za-'])]:
            self.assertEqual(m.transform(raw,[source],'present-only')[0],raw)
        source=row(field='3');source['fields'].append(dict(name='pos',projection='v. dep.'))
        self.assertEqual(m.transform(raw,[source],'present-only')[0],raw)
        self.assertEqual(m.transform(raw.replace(b'conj3',b'conj3 dep'),[row(field='3')],'present-only')[0],raw.replace(b'conj3',b'conj3 dep'))
    def test_inchoative_present_requires_exact_same_prefix_and_preserves_parts(self):
        raw=b':le:zaresco\n:vs:zaresc conj3\n:vs:unrelated perfstem\n'
        source=row(head='zaresco',field='zaru^i, 3',alts=['zarisco'])
        data,counts=m.transform(raw,[source],'inchoative-present')
        self.assertEqual(data,raw.replace(b':vs:zaresc conj3\n',b':vs:zaresc conj3\n:vs:zarisc\tconj3 orth\n'))
        self.assertEqual(counts['added_records'],1)
        self.assertEqual(m.transform(data,[source],'inchoative-present')[0],data)
        self.assertEqual(data.count(b'perfstem'),1);self.assertNotIn(b'pp4',data)
        self.assertEqual(m.transform(raw,[source],'present-only')[0],raw)
    def test_inchoative_present_withholds_other_spellings_grammar_and_flags(self):
        raw=b':le:zaresco\n:vs:zaresc conj3\n'
        for source in [row(head='zaresco',field='3',alts=['zarisco']),
                       row(head='zaresco',field='zaru^i, 4',alts=['zarisco']),
                       row(head='zaresco',field='zaru^i, 3',alts=['zorisco']),
                       row(head='zaresco',field='zaru^i, 3',alts=['za_risco']),
                       row(head='zaresco',field='zaru^i, 3',alts=['zariscor'])]:
            self.assertEqual(m.transform(raw,[source],'inchoative-present')[0],raw)
        source=row(head='zaresco',field='zaru^i, 3',alts=['zarisco'])
        source['fields'].append(dict(name='pos',projection='v. dep.'))
        self.assertEqual(m.transform(raw,[source],'inchoative-present')[0],raw)
        self.assertEqual(m.transform(raw.replace(b'conj3',b'conj3 dep'),[row(head='zaresco',field='zaru^i, 3',alts=['zarisco'])],'inchoative-present')[0],raw.replace(b'conj3',b'conj3 dep'))
    def test_velar_present_matches_all_parts_but_adds_only_present(self):
        raw=b':le:zatingo\n:vs:za_ting conj3\n:vs:za_tinx perfstem\n:vs:za_tinct pp4\n'
        source=row(head='za_tingo',field='nxi, nctum, 3',alts=['za_tinguo'])
        data,counts=m.transform(raw,[source],'velar-present')
        self.assertEqual(counts['added_records'],1)
        self.assertEqual(data,raw.replace(b':vs:za_ting conj3\n',b':vs:za_ting conj3\n:vs:za_tingu\tconj3 orth\n'))
        self.assertEqual(data.count(b'perfstem'),1);self.assertEqual(data.count(b'pp4'),1)
        self.assertEqual(m.transform(data,[source],'velar-present')[0],data)
    def test_velar_present_withholds_prefix_quantity_voice_and_part_mismatch(self):
        raw=b':le:zatingo\n:vs:za_ting conj3\n:vs:za_tinx perfstem\n:vs:za_tinct pp4\n'
        for source in [row(head='za_tingo',field='nxi, nctum, 3',alts=['za_tungo']),
                       row(head='za_tingo',field='nxi, nctum, 3',alts=['za_ting^uo']),
                       row(head='za_tingo',field='nxi, nctum, 3',alts=['za_tinguor']),
                       row(head='za_tingo',field='nxi, nctum, 4',alts=['za_tinguo'])]:
            self.assertEqual(m.transform(raw,[source],'velar-present')[0],raw)
        source=row(head='za_tingo',field='nxi, nctum, 3',alts=['za_tinguo'])
        for data in [raw.replace(b'za_tinx',b'other'),raw.replace(b'za_tinct',b'other'),raw.replace(b'conj3',b'conj3 dep')]:
            self.assertEqual(m.transform(data,[source],'velar-present')[0],data)
    def test_private_output_expected_count_and_no_overwrite(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            p=Path(directory);candidate=p/'candidate';headers=p/'headers';source=p/'source';target=p/'out'
            candidate.write_bytes(self.raw);headers.write_text('synthetic');source.write_text('synthetic')
            with patch.object(m.alternates,'source_alternates',return_value=([row()],source,'synthetic')):
                with self.assertRaises(ValueError):m.prepare(candidate,headers,p/'lexica',target,4)
                self.assertFalse(target.exists());m.prepare(candidate,headers,p/'lexica',target,3)
                self.assertEqual(target.stat().st_mode&0o777,0o600)
                with self.assertRaises(FileExistsError):m.prepare(candidate,headers,p/'lexica',target,3)
                with self.assertRaises(ValueError):m.prepare(candidate,headers,p/'lexica',SCRIPT.parent/'forbidden',3)
if __name__=='__main__':unittest.main()
