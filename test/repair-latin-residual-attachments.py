#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import unittest
from lxml import etree

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/repair-latin-residual-attachments.py'
spec = importlib.util.spec_from_file_location('m', SCRIPT); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
LITERAL = {'u^i, 3': ('conj3', '0'), 'u^i': ('conj3', '0'), 'e^re': ('conj3', None), 'ui, u_tum, 3': ('conj3', 'yytext[7]')}
SPECTYPES = {'e_mi, emptum, 3', 'e_vi, e_tum, 2', 'exi, ectum, 3', 'ortus, 4'}
TABLES = (LITERAL, SPECTYPES)


def fixture(xml):
    entry = etree.fromstring(xml)
    row, _ = m.first.review.projection.project(entry, 'Latin'); row['id'] = entry.get('id')
    return row, entry


def entries_for(*xmls):
    rows, entries = [], {}
    for xml in xmls:
        row, entry = fixture(xml); rows.append(row); entries[entry.get('id')] = entry
    return rows, entries


def header(id, key, orth, itype):
    return b'<entryFree id="%s" key="%s"><orth extent="full">%s</orth>, <itype>%s</itype><sense>x</sense></entryFree>' % (id, key, orth, itype)


EXIMO = header(b'n1', b'eximo', b'ex-i^mo', b'e_mi, emptum, 3')
EXPLEO = header(b'n2', b'expleo', b'ex-ple^o', b'e_vi, e_tum, 2')
ADIMPLEO = header(b'n3', b'adimpleo', b'a^d-imple^o', b'e_vi, e_tum, 2')
SPICIO = header(b'n4', b'despicio', b'de_-spi^ci^o', b'exi, ectum, 3')
PECTO = header(b'n5', b'pecto', b'pecto', b'exi, ectum, 3')
CONGRUO = header(b'n6', b'congruo', b'congru^o', b'u^i, 3')
COLO = header(b'n7', b'colo', b'co^lo', b'u^i, 3')
SILEO = header(b'n8', b'sileo', b'si^le^o', b'u^i')
JACEO = header(b'n9', b'circumjaceo', b'circum-ja^ce^o', b'e^re')
LABOR = header(b'n10', b'illabor', b'illa_bor', b'psus, 3')
FRUOR = header(b'n11', b'perfruor', b'per-fru^or', b'ctus, 3')
RAW = (b':le:eximo\n:vs:ex-i^m\tconj3\n:vs:e_m perfstem\n:vs:empt pp4\n'
       b':le:expleo\n:vs:ex-pl\tconj2\n:vs:e_v perfstem\n:vs:e_t pp4\n'
       b':le:adimpleo\n:vs:a^d-impl\tconj2\n:vs:a^d-imple_v perfstem\n:vs:a^d-imple_t pp4\n'
       b':le:despicio\n:vs:de_-spi^c\tconj3_io\n:vs:dex perfstem\n:vs:dect pp4\n'
       b':le:pecto\n:vs:pect\tconj3\n:vs:pex perfstem\n:vs:pect pp4\n'
       b':le:congruo\n:vs:congru^\tconj3\n:vs:congru^u^ perfstem\n'
       b':le:colo\n:vs:co^l\tconj3\n:vs:co^lu^ perfstem\n'
       b':le:sileo\n:vs:si^l\tconj3\n:vs:si^lu^ perfstem\n'
       b':le:circumjaceo\n:vs:circum-ja^c\tconj3\n'
       b':le:illabor\n:vs:illa_b\tconj3\n:vs:illa_bps pp4\n'
       b':le:perfruor\n:vs:per-fru^\tconj3\n:vs:per-fru^ct pp4\n')
REPAIRED = (RAW.replace(b':vs:e_m perfstem\n:vs:empt pp4\n', b':vs:ex-e_m perfstem\n:vs:ex-empt pp4\n')
            .replace(b':vs:e_v perfstem\n:vs:e_t pp4\n', b':vs:ex-ple_v perfstem\n:vs:ex-ple_t pp4\n')
            .replace(b':vs:dex perfstem\n:vs:dect pp4\n', b':vs:de_-spex perfstem\n:vs:de_-spect pp4\n')
            .replace(b':vs:congru^u^ perfstem\n', b':vs:congru^ perfstem\n')
            .replace(b':vs:si^l\tconj3\n', b':vs:si^l\tconj2\n')
            .replace(b':vs:circum-ja^c\tconj3\n', b':vs:circum-ja^c\tconj2\n')
            .replace(b':vs:illa_bps pp4\n', b':vs:illa_ps pp4\n'))
ALL = (EXIMO, EXPLEO, ADIMPLEO, SPICIO, PECTO, CONGRUO, COLO, SILEO, JACEO, LABOR, FRUOR)


class Proof(unittest.TestCase):
    def test_each_family_is_recognized_from_the_single_source_itype(self):
        expected = {EXIMO: (b'eximo', 'vowel_anchor', b'e_m', b'empt'), EXPLEO: (b'expleo', 'vowel_anchor', b'e_v', b'e_t'),
                    CONGRUO: (b'congruo', 'doubled_u', b'u^', None), SILEO: (b'sileo', 'eo_class', None, None),
                    JACEO: (b'circumjaceo', 'eo_class', None, None), LABOR: (b'illabor', 'suffix_supine', None, b'ps')}
        for xml, value in expected.items():
            row, entry = fixture(xml)
            self.assertEqual(m.proof(row, entry, LITERAL, SPECTYPES), value, xml)
        for xml in [header(b'x1', b'oriormo', b'o^ri^or', b'ortus, 4'),  # supine-only spectype: not a perfect shape
                    header(b'x2', b'metuo', b'me^tu^o', b'ui, u_tum, 3'),  # literal with a letter trim
                    header(b'x3', b'fulcio', b'fulci^o', b'si, tum, 4'),  # sigmatic perfect, another recipe
                    header(b'x4', b'sumo', b'su_mo', b'mpsi, mptum, 3'),
                    header(b'x5', b'tergeo', b'terge^o', b'si, sum, 2 or 3'),
                    header(b'x6', b'cubo', b'cu^bo', b'u^i, i^tum, 1')]:
            row, entry = fixture(xml)
            self.assertIsNone(m.proof(row, entry, LITERAL, SPECTYPES), xml)

    def test_root_last_vowel_ignores_the_preverb(self):
        self.assertEqual(m.root_last_vowel(b'ex-i^m'), 3)
        self.assertEqual(m.root_last_vowel(b'circum-spi^c'), 9)
        self.assertIsNone(m.root_last_vowel(b'ex-pl'))
        self.assertEqual(m.root_last_vowel(b'pect'), 1)


class Transform(unittest.TestCase):
    def test_all_four_families_repaired_only_where_the_historical_output_is_defective(self):
        rows, entries = entries_for(*ALL)
        data, counts = m.transform(RAW, rows, entries, TABLES)
        self.assertEqual(data, REPAIRED)
        self.assertEqual(counts, {'doubled_u': 1, 'eo_class': 2, 'historical_anchor_in_root': 1,
                                  'historical_attachment_already_expected': 1, 'repaired_lemma_blocks': 7,
                                  'repaired_records': 10, 'stem_not_ending_in_u': 1, 'suffix_supine': 1,
                                  'vowel_anchor': 3, 'withheld_vowel_final_stem': 1})
        again, counts = m.transform(REPAIRED, rows, entries, TABLES)
        self.assertEqual(again, REPAIRED)
        self.assertEqual(counts['already_repaired'], 5)
        self.assertEqual(counts['withheld_present_class_differs'], 2)

    def test_edited_or_flagged_blocks_are_withheld(self):
        rows, entries = entries_for(EXIMO, CONGRUO, SILEO, LABOR)
        edited = (RAW.replace(b':vs:e_m perfstem', b':vs:em perfstem').replace(b':vs:congru^u^ perfstem', b':vs:congru^u perfstem')
                  .replace(b':vs:si^l\tconj3\n', b':vs:si^l\tconj3 orth\n').replace(b':vs:illa_b\tconj3\n', b':vs:illa_b\tconj3\n:vs:inla_b\tconj3 orth\n'))
        data, counts = m.transform(edited, rows, entries, TABLES)
        self.assertEqual(data, edited)
        self.assertEqual(counts, {'withheld_block_shape_differs': 2, 'withheld_records_not_historical_output': 2})


if __name__ == '__main__':
    unittest.main()
