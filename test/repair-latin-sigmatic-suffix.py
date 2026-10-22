#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import unittest
from lxml import etree

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/repair-latin-sigmatic-suffix.py'
spec = importlib.util.spec_from_file_location('m', SCRIPT); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
LITERAL = {'xi, ctum, 3', 'si, sum, 3', 'si, sum, 4'}


def fixture(xml):
    entry = etree.fromstring(xml)
    row, _ = m.first.review.projection.project(entry, 'Latin'); row['id'] = entry.get('id')
    return row, entry


def entries_for(*xmls):
    rows, entries = [], {}
    for xml in xmls:
        row, entry = fixture(xml); rows.append(row); entries[entry.get('id')] = entry
    return rows, entries


FULCIO = b'<entryFree id="n1" key="refulcio"><orth extent="full">re^-fulci^o</orth>, <itype>si, tum, 4</itype><sense>x</sense></entryFree>'
INDULGEO = b'<entryFree id="n2" key="indulgeo"><orth extent="full">indulge^o</orth>, <itype>si, tum, 2</itype><sense>x</sense></entryFree>'
NUBO = b'<entryFree id="n3" key="enubo"><orth extent="full">e_-nu_bo</orth>, <itype>psi, 3</itype><sense>x</sense></entryFree>'
TERGEO = b'<entryFree id="n4" key="abstergeo"><orth extent="full">abs-terge^o</orth>, <itype>rsi, rsum, 2</itype><sense>x</sense></entryFree>'
ARDEO = b'<entryFree id="n5" key="ardeo"><orth extent="full">arde^o</orth>, <itype>si, 2</itype><sense>x</sense></entryFree>'
RAW = (b':le:refulcio\n:vs:re^-fulc\tconj4\n:vs:re^-fulcs perfstem\n:vs:re^-fulct pp4\n'
       b':le:indulgeo\n:vs:indulg\tconj2\n:vs:ins perfstem\n:vs:int pp4\n'
       b':le:enubo\n:vs:e_-nu_b\tconj3\n:vs:e_-nu_bps perfstem\n'
       b':le:ardeo\n:vs:ard\tconj2\n:vs:ars perfstem\n')
REPAIRED = (RAW.replace(b':vs:re^-fulcs perfstem\n:vs:re^-fulct pp4\n', b':vs:re^-fuls perfstem\n:vs:re^-fult pp4\n')
            .replace(b':vs:ins perfstem\n:vs:int pp4\n', b':vs:induls perfstem\n:vs:indult pp4\n')
            .replace(b':vs:e_-nu_bps perfstem\n', b':vs:e_-nu_ps perfstem\n'))


class Proof(unittest.TestCase):
    def test_sigmatic_suffix_parts_only(self):
        row, entry = fixture(FULCIO)
        self.assertEqual(m.proof(row, entry, LITERAL), (b'refulcio', b's', b't'))
        row, entry = fixture(NUBO)
        self.assertEqual(m.proof(row, entry, LITERAL), (b'enubo', b'ps', None))
        for xml in [TERGEO,
                    b'<entryFree id="n6" key="volvo"><orth extent="full">volvo</orth>, <itype>volvi, vo^lu_tum, 3</itype><sense>x</sense></entryFree>',
                    b'<entryFree id="n7" key="haurio"><orth extent="full">hauri^o</orth>, <itype>si, sum, 4</itype><sense>x</sense></entryFree>',
                    b'<entryFree id="n8" key="x"><orth extent="full">xo</orth>, <itype>si, i_tum, 3</itype><sense>x</sense></entryFree>']:
            row, entry = fixture(xml)
            self.assertIsNone(m.proof(row, entry, LITERAL), xml)

    def test_last_vowel(self):
        self.assertEqual(m.last_vowel(b'indulg'), 3)
        self.assertEqual(m.last_vowel(b're^-fulc'), 5)
        self.assertEqual(m.last_vowel(b'xyz'), -1)


class Transform(unittest.TestCase):
    def test_suffix_attached_after_the_final_consonant_only_where_the_anchor_missed(self):
        rows, entries = entries_for(FULCIO, INDULGEO, NUBO, TERGEO, ARDEO)
        data, counts = m.transform(RAW, rows, entries, LITERAL)
        self.assertEqual(data, REPAIRED)
        self.assertEqual(counts, {'anchor_before_last_vowel': 1, 'historical_anchor_in_final_cluster': 1,
                                  'letter_absent': 2, 'repaired_lemma_blocks': 3, 'repaired_records': 5})
        self.assertEqual(m.transform(REPAIRED, rows, entries, LITERAL)[1]['already_repaired'], 3)

    def test_vowel_final_stems_and_edited_records_are_withheld(self):
        rows, entries = entries_for(NUBO, INDULGEO)
        edited = RAW.replace(b':vs:e_-nu_b\tconj3', b':vs:e_-nu\tconj3').replace(b':vs:ins perfstem', b':vs:inds perfstem')
        data, counts = m.transform(edited, rows, entries, LITERAL)
        self.assertEqual(data, edited)
        self.assertEqual(counts, {'withheld_records_not_historical_output': 1, 'withheld_vowel_final_stem': 1})


if __name__ == '__main__':
    unittest.main()
