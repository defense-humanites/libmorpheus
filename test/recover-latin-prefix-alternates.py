#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from lxml import etree

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/recover-latin-prefix-alternates.py'
spec = importlib.util.spec_from_file_location('m', SCRIPT); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
TABLE = {'ab', 'ad', 'as', 'at', 'il', 'in', 'im', 'com', 'con', 'col', 'ob', 'op'}


def fixture(xml):
    entry = etree.fromstring(xml)
    row, _ = m.first.review.projection.project(entry, 'Latin'); row['id'] = entry.get('id')
    return row, entry


UNHYPHENATED = b'<entryFree id="n1" key="illido"><orth extent="full">illi_do</orth> (<orth type="alt" extent="full">inl-</orth>), <itype>si, sum, 3</itype><sense>x</sense></entryFree>'
HYPHENATED = b'<entryFree id="n2" key="comprimo"><orth extent="full">com-pri^mo</orth> (<orth type="alt" extent="full">conp-</orth>), <itype>pressi, pressum, 3</itype><sense>x</sense></entryFree>'
ATTRIBUTED = b'<entryFree id="n3" key="assero2" n="2"><orth extent="full">as-se^ro</orth> (<orth extent="full">ads-</orth>, <itype>Ritschl</itype>; <orth extent="full">ats-</orth>, Halm), <itype>se^ru^i, sertum, 3</itype><sense>x</sense></entryFree>'


class Alignment(unittest.TestCase):
    def test_single_prefix_letter_inside_known_preverbs(self):
        self.assertEqual(m.alignment('inl', 'illi_do', TABLE), ((2, 'il', 'in'), None))
        self.assertEqual(m.alignment('conp', 'com-pri^mo', TABLE), ((3, 'com', 'con'), None))
        self.assertEqual(m.alignment('opt', 'ob-tingo', TABLE), ((2, 'ob', 'op'), None))
        self.assertEqual(m.alignment('inl', 'illi^go#2', TABLE), ((2, 'il', 'in'), None))

    def test_withheld_shapes(self):
        cases = {('app', 'ap-pa_re^o'): 'withheld_identical_spelling',
                 ('adgn', 'agnosco'): 'withheld_not_single_prefix_substitution',
                 ('hall', 'a_lu_ci^nor'): 'withheld_not_single_prefix_substitution',
                 ('advor', 'adverso'): 'withheld_prefix_not_in_preverb_table',
                 ('adr', 'ar-ro_do'): 'withheld_prefix_not_in_preverb_table',
                 ('adc', 'a-bcde'): 'withheld_explicit_boundary_differs',
                 ('inlidoque', 'illi_do'): 'withheld_alternate_longer_than_headword',
                 ('In', 'illi_do'): 'withheld_alternate_shape',
                 ('i', 'illi_do'): 'withheld_alternate_shape'}
        for (alternate, headword), reason in cases.items():
            self.assertEqual(m.alignment(alternate, headword, TABLE), (None, reason), (alternate, headword))
        # The last letter of the abbreviation must be a shared anchor letter.
        self.assertEqual(m.alignment('in', 'illi_do', TABLE), (None, 'withheld_not_single_prefix_substitution'))


class Proof(unittest.TestCase):
    def test_source_alternates_and_lexer_handled_literals(self):
        row, entry = fixture(UNHYPHENATED)
        self.assertEqual(m.proof(row, entry, TABLE), ((b'illido', 'illi_do', [(2, 'il', 'in')]), {'accepted_alternate': 1}))
        row, entry = fixture(ATTRIBUTED)
        result, reasons = m.proof(row, entry, TABLE)
        self.assertEqual(result, (b'assero#2', 'as-se^ro#2', [(2, 'as', 'at')]))
        self.assertEqual(reasons, {'accepted_alternate': 1, 'lexer_handled_alternate': 1})

    def test_reject_partial_extent_unjoined_and_unprojected(self):
        row, entry = fixture(UNHYPHENATED)
        partial = copy.deepcopy(entry); partial[1].set('extent', 'part')
        self.assertEqual(m.proof(row, partial, TABLE)[1], {'other_alternate_shape': 1})
        other = copy.deepcopy(entry); other.set('id', 'n9')
        self.assertEqual(m.proof(row, other, TABLE), (None, {'withheld_unprojected_or_unjoined': 1}))
        broken = dict(row, projection_error='x')
        self.assertEqual(m.proof(broken, entry, TABLE), (None, {'withheld_unprojected_or_unjoined': 1}))


class Transform(unittest.TestCase):
    def test_substitute_keeps_notation_and_hyphens(self):
        self.assertEqual(m.substitute('illi_d', (2, 'il', 'in')), 'inli_d')
        self.assertEqual(m.substitute('com-pri^m', (3, 'com', 'con')), 'con-pri^m')
        self.assertEqual(m.substitute('ad-su^e_-fact', (2, 'ad', 'at')), 'at-su^e_-fact')
        self.assertIsNone(m.substitute('press', (3, 'com', 'con')))
        self.assertIsNone(m.substitute('co', (3, 'com', 'con')))

    def test_add_every_block_record_once_with_orth_flag(self):
        row, entry = fixture(UNHYPHENATED)
        raw = (b':le:illido\n:vs:illi_d\tconj3\n:vs:illi_s perfstem\n:vs:illi_s pp4\n'
               b':vs:illi_sKayser perfstem\n:vs:lis\tconj3\n:vs:inli_d\tconj3 orth\n:le:other\n:vs:oth\tconj3\n')
        data, counts = m.transform(raw, [row], {'n1': entry}, TABLE)
        self.assertEqual(data, (b':le:illido\n:vs:illi_d\tconj3\n:vs:illi_s perfstem\n:vs:inli_s perfstem orth\n'
                                b':vs:illi_s pp4\n:vs:inli_s pp4 orth\n:vs:illi_sKayser perfstem\n:vs:lis\tconj3\n'
                                b':vs:inli_d\tconj3 orth\n:le:other\n:vs:oth\tconj3\n'))
        self.assertEqual(counts, {'accepted_alternate': 1, 'added_perfstem': 1, 'added_pp4': 1, 'added_records': 2,
                                  'changed_lemma_blocks': 1, 'records_already_present': 1, 'records_outside_prefix': 1,
                                  'records_skipped_existing_orth': 1, 'records_withheld_unparsed_stem': 1})
        self.assertEqual(m.transform(data, [row], {'n1': entry}, TABLE)[0], data)

    def test_hyphenated_compound_and_derivative_records(self):
        row, entry = fixture(HYPHENATED)
        raw = b':le:comprimo\n:vs:com-pri^m\tconj3\n:de:com-pri^m\tare_vb dep\n:vs:com-press perfstem'
        data, counts = m.transform(raw, [row], {'n2': entry}, TABLE)
        self.assertEqual(data, (b':le:comprimo\n:vs:com-pri^m\tconj3\n:vs:con-pri^m\tconj3 orth\n'
                                b':de:com-pri^m\tare_vb dep\n:de:con-pri^m\tare_vb dep orth\n'
                                b':vs:com-press perfstem\n:vs:con-press perfstem orth\n'))
        self.assertEqual(counts['added_records'], 3)

    def test_withhold_missing_duplicate_and_ambiguous_blocks(self):
        row, entry = fixture(UNHYPHENATED)
        for data, rows, reason in [(b':le:other\n:vs:oth\tconj3\n', [row], 'lemma_without_candidate_block'),
                                   (b':le:illido\n:vs:illi_d\tconj3\n' * 2, [row], 'withheld_ambiguous_lemma_block'),
                                   (b':le:illido\n:vs:illi_d\tconj3\n', [row, row], 'withheld_ambiguous_lemma_block')]:
            output, counts = m.transform(data, rows, {'n1': entry}, TABLE)
            self.assertEqual(output, data); self.assertEqual(counts[reason], 1)
            self.assertNotIn('added_records', counts)
        with self.assertRaises(ValueError):
            m.transform(b':le:illido\n', [row], {}, TABLE)


class Preparation(unittest.TestCase):
    def test_private_output_expected_count_and_no_overwrite(self):
        row, entry = fixture(UNHYPHENATED); raw = b':le:illido\n:vs:illi_d\tconj3\n'
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            p = Path(directory); candidate = p / 'candidate'; headers = p / 'headers'; source = p / 'source'
            lexica = p / 'lexica'; target = p / 'out'
            candidate.write_bytes(raw); headers.write_bytes(b'headers'); source.write_bytes(b'source'); lexica.mkdir()
            with patch.object(m.first, 'source_rows', return_value=([row], source, 'pinned')), \
                    patch.object(m.first.review, 'load_entries', return_value=({'n1': entry}, source, 'pinned')), \
                    patch.object(m, 'preverbs', return_value=TABLE):
                with self.assertRaises(ValueError):
                    m.prepare(candidate, headers, lexica, target, 2)
                self.assertFalse(target.exists())
                report = m.prepare(candidate, headers, lexica, target, 1)
                self.assertEqual(target.stat().st_mode & 0o777, 0o600)
                self.assertEqual(target.read_bytes(), raw + b':vs:inli_d\tconj3 orth\n')
                self.assertEqual(set(report['input_sha256']), {'candidate', 'headers', 'source', 'raw_preverbs.table'})
                with self.assertRaises(FileExistsError):
                    m.prepare(candidate, headers, lexica, target, 1)

    def test_real_preverb_table_contains_assimilation_pairs(self):
        table = m.preverbs()
        self.assertTrue({'il', 'in', 'im', 'com', 'con', 'col', 'ob', 'op', 'ad', 'as'} <= table)
        self.assertNotIn('#', table)


if __name__ == '__main__':
    unittest.main()
