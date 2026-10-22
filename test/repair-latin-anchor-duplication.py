#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import unittest
from lxml import etree

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/repair-latin-anchor-duplication.py'
spec = importlib.util.spec_from_file_location('m', SCRIPT); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
LITERAL = {'xi, ctum, 3', 'si, sum, 3'}


def fixture(xml=b'<entryFree id="n1" key="volvo"><orth extent="full">volvo</orth>, <itype>volvi, vo^lu_tum, 3</itype>, <pos>v. a.</pos><sense>x</sense></entryFree>'):
    entry = etree.fromstring(xml)
    row, _ = m.first.review.projection.project(entry, 'Latin'); row['id'] = entry.get('id')
    return row, entry


RAW = (b':le:volvo\n:vs:volv\tconj3\n:vs:volvolv perfstem\n:vs:volvo^lu_t pp4\n'
       b':le:cedo\n:vs:ce_d\tconj3\n:vs:cess perfstem\n:vs:cess pp4\n'
       b':le:bibo\n:vs:bi^b\tconj3\n:vs:bi^b perfstem\n:vs:bi^bi^t pp4\n'
       b':le:vivo\n:vs:vi_v\tconj3\n:vs:vi_vix perfstem\n:vs:vi_vict pp4 orth\n')
REPAIRED = RAW.replace(b':vs:volvolv perfstem\n:vs:volvo^lu_t pp4\n', b':vs:volv perfstem\n:vs:vo^lu_t pp4\n')


def entries_for(*xmls):
    rows, entries = [], {}
    for xml in xmls:
        row, entry = fixture(xml); rows.append(row); entries[entry.get('id')] = entry
    return rows, entries


class Helpers(unittest.TestCase):
    def test_historical_anchor_cuts_from_the_last_occurrence(self):
        self.assertEqual(m.historical_anchor(b'volv', b'v'), 3)
        self.assertEqual(m.historical_anchor(b'indulg', b's'), 2)
        self.assertEqual(m.historical_anchor(b'ex-pl', b'e'), 0)
        self.assertIsNone(m.historical_anchor(b're^-ferc', b's'))

    def test_duplication_and_earliest_anchor_disregard_notation(self):
        self.assertEqual(m.duplicated(b'vol', b'volv'), 3)
        self.assertEqual(m.duplicated(b'mansu^e', b'su^e_v'), 3)
        self.assertEqual(m.duplicated(b'con-', b'volv'), 0)
        self.assertEqual(m.duplicated(b'', b'cess'), 0)
        self.assertEqual(m.earliest_anchor(b'con-volv', b'volv'), 4)
        self.assertEqual(m.earliest_anchor(b'mansu^esc', b'su^e_v'), 3)
        self.assertEqual(m.earliest_anchor(b'vo^v', b'vo_v'), 0)
        self.assertIsNone(m.earliest_anchor(b'ex-pl', b'e_v'))


class Proof(unittest.TestCase):
    def test_written_parts_outside_the_literal_table(self):
        row, entry = fixture()
        self.assertEqual(m.proof(row, entry, LITERAL), (b'volvo', b'volv', b'vo^lu_t'))
        row, entry = fixture(b'<entryFree id="n1" key="sido1" n="1"><orth extent="full">si_do</orth>, <itype>si_di, 3</itype><sense>x</sense></entryFree>')
        self.assertEqual(m.proof(row, entry, LITERAL), (b'sido#1', b'si_d', None))

    def test_withhold_literal_vowel_initial_connectors_and_several_fields(self):
        for xml in [b'<entryFree id="n1" key="coquo"><orth extent="full">co^quo</orth>, <itype>xi, ctum, 3</itype><sense>x</sense></entryFree>',
                    b'<entryFree id="n1" key="abeo"><orth extent="full">ab-e^o</orth>, <itype>i_vi, i^tum, 4</itype><sense>x</sense></entryFree>',
                    b'<entryFree id="n1" key="volvo"><orth extent="full">volvo</orth>, <itype>volvi or volsi, vo^lu_tum, 3</itype><sense>x</sense></entryFree>',
                    b'<entryFree id="n1" key="volvo"><orth extent="full">volvo</orth>, <itype>volvi</itype>, <itype>3</itype><sense>x</sense></entryFree>',
                    b'<entryFree id="n1" key="volvo"><orth extent="full">volvo</orth>, <itype>volvere</itype><sense>x</sense></entryFree>']:
            row, entry = fixture(xml)
            self.assertIsNone(m.proof(row, entry, LITERAL), xml)

    def test_literal_table_comes_from_the_lexer(self):
        table = m.literal_table()
        self.assertIn('xi, ctum, 3', table); self.assertIn('u^i, 3', table)
        self.assertNotIn('volvi, vo^lu_tum, 3', table)


class Transform(unittest.TestCase):
    def test_only_the_doubled_historical_attachment_is_reanchored(self):
        rows, entries = entries_for(
            b'<entryFree id="n1" key="volvo"><orth extent="full">volvo</orth>, <itype>volvi, vo^lu_tum, 3</itype><sense>x</sense></entryFree>',
            b'<entryFree id="n2" key="cedo"><orth extent="full">ce_do</orth>, <itype>cessi, cessum, 3</itype><sense>x</sense></entryFree>',
            b'<entryFree id="n3" key="bibo"><orth extent="full">bi^bo</orth>, <itype>bi^bi, bi^bi^tum, 3</itype><sense>x</sense></entryFree>',
            b'<entryFree id="n4" key="vivo"><orth extent="full">vi_vo</orth>, <itype>vixi, victum, 3</itype><sense>x</sense></entryFree>',
            b'<entryFree id="n5" key="nemo"><orth extent="full">ne_mo</orth>, <itype>nemi, 3</itype><sense>x</sense></entryFree>')
        data, counts = m.transform(RAW, rows, entries, LITERAL)
        self.assertEqual(data, REPAIRED)
        self.assertEqual(counts, {'already_repaired': 1, 'doubled_letters_3': 1,
                                  'historical_attachment_without_duplication': 1,
                                  'lemma_without_candidate_block': 1, 'repaired_lemma_blocks': 1,
                                  'repaired_records': 2, 'withheld_block_shape_differs': 1})
        self.assertEqual(m.transform(REPAIRED, rows, entries, LITERAL)[1]['already_repaired'], 2)

    def test_records_that_are_not_the_historical_output_are_withheld(self):
        rows, entries = entries_for(
            b'<entryFree id="n1" key="volvo"><orth extent="full">volvo</orth>, <itype>volvi, vo^lu_tum, 3</itype><sense>x</sense></entryFree>')
        edited = RAW.replace(b':vs:volvolv perfstem', b':vs:volvols perfstem')
        data, counts = m.transform(edited, rows, entries, LITERAL)
        self.assertEqual(data, edited)
        self.assertEqual(counts, {'withheld_records_not_historical_output': 1})


if __name__ == '__main__':
    unittest.main()
