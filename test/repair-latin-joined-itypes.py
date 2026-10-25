#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import unittest
from lxml import etree

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/repair-latin-joined-itypes.py'
spec = importlib.util.spec_from_file_location('m', SCRIPT); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
LITERAL = {'u^i, 3': ('conj3', '0'), 'u^i': ('conj3', '0'), 'e^re': ('conj3', None), 'u^i, u_tum, 3': ('conj3', "'u'")}
SPECTYPES = {'e_mi, emptum, 3', 'e_vi, e_tum, 2'}
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


DIRIMO = b'<entryFree id="n1" key="dirimo"><orth extent="full">di^ri^mo</orth>, <itype>e_mi, emptum</itype> <itype>3</itype><sense>x</sense></entryFree>'
BIBO = b'<entryFree id="n2" key="bibo1"><orth extent="full">bi^bo</orth>, <itype>bi^bi</itype> <itype>3</itype><sense>x</sense></entryFree>'
INSUO = b'<entryFree id="n3" key="insuo"><orth extent="full">in-su^o</orth>, <itype>u^i</itype> <itype>3</itype><sense>x</sense></entryFree>'
EXIMO = b'<entryFree id="n4" key="eximo"><orth extent="full">ex-i^mo</orth>, <itype>e_mi, emptum, 3</itype><sense>x</sense></entryFree>'
SPLIT = b'<entryFree id="n5" key="redimo"><orth extent="full">re^d-i^mo</orth>, <itype>e_mi, emptum</itype> <orth>redemo</orth> <itype>3</itype><sense>x</sense></entryFree>'
RAW = (b':le:dirimo\n:vs:di^ri^m\tconj3\n:vs:di^ri^me_m perfstem\n:vs:di^ri^mempt pp4\n'
       b':le:bibo#1\n:vs:bi^b\tconj3\n:vs:bi^bi^b perfstem\n'
       b':le:insuo\n:vs:in-su^\tconj3\n:vs:in-su^u^ perfstem\n'
       b':le:eximo\n:vs:ex-i^m\tconj3\n:vs:e_m perfstem\n:vs:empt pp4\n'
       b':le:redimo\n:vs:re^d-i^m\tconj3\n:vs:re_m perfstem\n:vs:rempt pp4\n')
REPAIRED = (RAW.replace(b':vs:di^ri^me_m perfstem\n:vs:di^ri^mempt pp4\n', b':vs:di^re_m perfstem\n:vs:di^rempt pp4\n')
            .replace(b':vs:bi^bi^b perfstem\n', b':vs:bi^b perfstem\n')
            .replace(b':vs:in-su^u^ perfstem\n', b':vs:in-su^ perfstem\n'))


class View(unittest.TestCase):
    def test_consecutive_itype_fields_are_joined_into_one_field_view(self):
        row, entry = fixture(DIRIMO)
        view, xml = m.joined_view(row, entry)
        self.assertEqual([f['projection'] for f in view['fields'] if f['name'] == 'itype'], ['e_mi, emptum, 3'])
        self.assertEqual(view['headword'], 'di^ri^mo')
        self.assertEqual(xml.get('id'), 'n1')
        self.assertEqual([f['projection'] for f in m.first.review.projection.project(xml, 'Latin')[0]['fields'] if f['name'] == 'itype'], ['e_mi, emptum, 3'])
        row, entry = fixture(BIBO)
        self.assertEqual(m.joined_view(row, entry)[0]['headword'], 'bi^bo#1')
        for xml in (EXIMO, SPLIT):
            row, entry = fixture(xml)
            self.assertIsNone(m.joined_view(row, entry), xml)

    def test_lexer_tables_ignore_comments_and_read_character_trims(self):
        literal, spectypes = m.lexer_tables()
        self.assertEqual(literal['u^i, u_tum, 3'], ('conj3', "'u'"))
        self.assertEqual(literal['u^i, 3'], ('conj3', '0'))
        self.assertEqual(literal['e^re'], ('conj3', None))
        self.assertIn('e_mi, emptum, 3', spectypes)
        self.assertIs(m.lexer_tables, m.residual.lexer_tables)
        self.assertEqual(m.join_rule(), ', ')


class Transform(unittest.TestCase):
    def test_only_joined_headers_go_through_the_three_repairs(self):
        rows, entries = entries_for(DIRIMO, BIBO, INSUO, EXIMO, SPLIT)
        data, counts = m.transform(RAW, rows, entries, TABLES)
        self.assertEqual(data, REPAIRED)
        self.assertEqual(counts['joined_headers'], 3)
        self.assertEqual((counts['repaired_lemma_blocks'], counts['repaired_records']), (3, 4))
        self.assertEqual(counts['stages']['anchor_duplication']['repaired_records'], 1)
        self.assertEqual(counts['stages']['residual_attachments'], {'doubled_u': 1, 'repaired_lemma_blocks': 2, 'repaired_records': 3, 'vowel_anchor': 1})
        self.assertEqual(m.transform(REPAIRED, rows, entries, TABLES)[0], REPAIRED)


if __name__ == '__main__':
    unittest.main()
