#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from lxml import etree

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/recover-latin-backlinked-present-classes.py'
spec = importlib.util.spec_from_file_location('m', SCRIPT); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def article(xml):
    entry = etree.fromstring(xml)
    row, _ = m.first.review.projection.project(entry, 'Latin'); row['id'] = entry.get('id'); row['source_key'] = entry.get('key')
    return row, entry


MAIN = b'<entryFree id="n1" key="bafeteo"><orth extent="full">ba^fe_te^o</orth> (<orth type="alt" extent="full">ba^foete^o</orth>), <itype>e_re</itype>, <pos>v. n.</pos><sense>x</sense></entryFree>'
REF = b'<entryFree id="n2" key="bafoeteo"><orth extent="full">ba^foete^o</orth>, <itype>e_re</itype>, v. bafeteo.</entryFree>'
RAW = b':le:bafeteo\n:vs:ba^fe_t\tconj2\n:le:other\n:vs:oth\tconj3\n'
FIXED = b':le:bafeteo\n:vs:ba^fe_t\tconj2\n:vs:ba^foet\tconj2 orth\n:le:other\n:vs:oth\tconj3\n'


def rows_and_entries(main=MAIN, ref=REF):
    row, entry = article(main); _, reference = article(ref)
    row['full_alternates'] = [f['projection'] for f in row['fields'][1:] if f['name'] == 'orth']
    return [row], {'n1': entry, 'n2': reference}


class Roots(unittest.TestCase):
    def test_present_root_follows_the_block_class(self):
        self.assertEqual(m.present_root('ba^fe_te^o', b'conj2', False), 'ba^fe_t')
        self.assertEqual(m.present_root('pelli^ci^o', b'conj3_io', False), 'pelli^c')
        self.assertEqual(m.present_root('hirri^o', b'ire_vb', False), 'hirr')
        self.assertEqual(m.present_root('be_to#2', b'conj3', False), 'be_t')
        self.assertEqual(m.present_root('ex-se^quor', b'conj3', True), 'ex-se^qu')
        self.assertEqual(m.present_root('po^pu^lor', b'are_vb', True), 'po^pu^l')
        for spelling, tag, dep in [('claudo', b'conj2', False), ('ci^o', b'conj2', False), ('a^pio', b'conj3', False),
                                   ('fe_te^o', b'conj3', False), ('bafeteo', b'conj2', True), ('-uttio', b'conj4', False),
                                   ('o', b'conj3', False), ('ab-o', b'conj3', False), ('advor-', b'conj3', False)]:
            self.assertIsNone(m.present_root(spelling, tag, dep), (spelling, tag, dep))


class Proof(unittest.TestCase):
    def test_bare_reference_entry(self):
        _, reference = article(REF)
        self.assertEqual(m.backlink(reference, 'bafeteo'), ['e_re'])
        self.assertIsNone(m.backlink(reference, 'other'))
        _, embedded = article(REF.replace(b', v. bafeteo.', b', <sense>v. bafeteo.</sense>'))
        self.assertIsNone(m.backlink(embedded, 'bafeteo'))
        _, nominal = article(REF.replace(b'<itype>e_re</itype>', b'<pos>adj.</pos>'))
        self.assertIsNone(m.backlink(nominal, 'bafeteo'))
        self.assertEqual(m.full_head(reference), b'bafoeteo')
        _, typed = article(REF.replace(b'<orth extent="full">', b'<orth type="alt" extent="full">'))
        self.assertIsNone(m.full_head(typed))


class Transform(unittest.TestCase):
    def test_add_one_present_record_in_the_block_class(self):
        rows, entries = rows_and_entries()
        data, counts = m.transform(RAW, rows, entries)
        self.assertEqual(data, FIXED)
        self.assertEqual(counts, {'added_conj2': 1, 'added_records': 1, 'changed_lemma_blocks': 1})
        again, counts = m.transform(data, rows, entries)
        self.assertEqual(again, data); self.assertEqual(counts['already_present'], 1)

    def test_deponent_block_keeps_its_flag(self):
        rows, entries = rows_and_entries(MAIN.replace(b'ba^fe_te^o', b'ba^fe_te^or').replace(b'ba^foete^o', b'ba^foete^or'),
                                         REF.replace(b'ba^foete^o', b'ba^foete^or').replace(b'e_re', b'e_ri'))
        data, counts = m.transform(b':le:bafeteor\n:vs:ba^fe_t\tconj2 dep\n', rows, entries)
        self.assertEqual(data, b':le:bafeteor\n:vs:ba^fe_t\tconj2 dep\n:vs:ba^foet\tconj2 dep orth\n')

    def test_withheld_cases(self):
        rows, entries = rows_and_entries()
        for data, reason in [(b':le:other\n:vs:oth\tconj3\n', 'rows_without_unique_verbal_block'),
                             (RAW * 2, 'rows_without_unique_verbal_block'),
                             (b':le:bafeteo\n:vs:ba^fe_t\tconj2\n:vs:ba^f\tconj2\n', 'withheld_present_record_not_unique'),
                             (b':le:bafeteo\n:vs:ba^fe_te\tconj3\n', 'withheld_headword_outside_present_class'),
                             (b':le:bafeteo\n:vs:ba^fe_t\tconj2 orth\n', 'withheld_present_record_not_unique')]:
            output, counts = m.transform(data, rows, entries)
            self.assertEqual(output, data, reason); self.assertEqual(counts.get(reason), 1, reason)
        cases = {'withheld_alternate_outside_present_class': (MAIN.replace(b'ba^foete^o', b'ba^foeto'), REF),
                 'withheld_notation_only': (MAIN.replace(b'ba^foete^o', b'ba^fe^te^o'), REF),
                 'withheld_no_unique_standalone_entry': (MAIN, REF.replace(b'ba^foete^o', b'ba^foete^a')),
                 'withheld_entry_not_a_bare_reference': (MAIN, REF.replace(b'v. bafeteo.', b'v. bafeteo. Also elsewhere.')),
                 'withheld_reference_class_differs': (MAIN, REF.replace(b'e_re', b'i_re'))}
        for reason, (main, ref) in cases.items():
            rows, entries = rows_and_entries(main, ref)
            output, counts = m.transform(RAW, rows, entries)
            self.assertEqual(output, RAW, reason); self.assertEqual(counts.get(reason), 1, reason)


class Quotation(unittest.TestCase):
    def test_whole_quoted_present_form_of_the_block_class(self):
        quoted = lambda text, lang=b'la': MAIN.replace(b'<sense>x</sense>', b'<sense><quote lang="' + lang + b'">' + text + b'</quote></sense>')
        unlinked = REF.replace(b'v. bafeteo.', b'other text.')
        rows, entries = rows_and_entries(quoted(b'illa bafoetent'), unlinked)
        self.assertEqual(m.transform(RAW, rows, entries, 'backlink')[1].get('withheld_entry_not_a_bare_reference'), 1)
        data, counts = m.transform(RAW, rows, entries, 'quotation')
        self.assertEqual(data, FIXED); self.assertEqual(counts['added_records'], 1)
        for text, lang in [(b'bafoetentur', b'la'), (b'bafoetebat', b'la'), (b'bafoe tent', b'la'), (b'bafoetent', b'greek')]:
            rows, entries = rows_and_entries(quoted(text, lang), unlinked)
            output, counts = m.transform(RAW, rows, entries, 'quotation')
            self.assertEqual(output, RAW, text); self.assertEqual(counts.get('withheld_no_whole_quoted_present_form'), 1, text)
        with self.assertRaises(ValueError):
            m.transform(RAW, rows, entries, 'other')


class Preparation(unittest.TestCase):
    def test_private_output_expected_count_and_no_overwrite(self):
        rows, entries = rows_and_entries()
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            p = Path(directory); candidate = p / 'candidate'; headers = p / 'headers'; source = p / 'source'
            lexica = p / 'lexica'; target = p / 'out'
            candidate.write_bytes(RAW); headers.write_bytes(b'headers'); source.write_bytes(b'source'); lexica.mkdir()
            with patch.object(m.regular.alternates, 'source_alternates', return_value=(rows, source, 'pinned')), \
                    patch.object(m.first.review, 'load_entries', return_value=(entries, source, 'pinned')):
                with self.assertRaises(ValueError):
                    m.prepare(candidate, headers, lexica, target, 2)
                self.assertFalse(target.exists())
                m.prepare(candidate, headers, lexica, target, 1)
                self.assertEqual(target.read_bytes(), FIXED)
                self.assertEqual(target.stat().st_mode & 0o777, 0o600)
                with self.assertRaises(FileExistsError):
                    m.prepare(candidate, headers, lexica, target, 1)


if __name__ == '__main__':
    unittest.main()
