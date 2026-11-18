#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from lxml import etree

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/repair-latin-velar-short-suffix.py'
spec = importlib.util.spec_from_file_location('m', SCRIPT); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def fixture(xml=b'<entryFree id="n1" key="bacoquo"><orth extent="full">ba^-co^quo</orth>, <itype>xi, ctum, 3</itype>, <pos>v. a.</pos><sense>x</sense></entryFree>'):
    entry = etree.fromstring(xml)
    row, _ = m.first.review.projection.project(entry, 'Latin'); row['id'] = entry.get('id')
    return row, entry


RAW = b':le:bacoquo\n:vs:ba^-co^qu\tconj3\n:vs:ba^-co^qx perfstem\n:vs:ba^-co^qct pp4\n'
REPAIRED = b':le:bacoquo\n:vs:ba^-co^qu\tconj3\n:vs:ba^-co^x perfstem\n:vs:ba^-co^ct pp4\n'


class Proof(unittest.TestCase):
    def test_labiovelar_headword_with_literal_short_parts(self):
        row, entry = fixture()
        self.assertEqual(m.proof(row, entry), (b'bacoquo', b'ba^-co^qu', b'ba^-co^'))
        row, entry = fixture(b'<entryFree id="n1" key="stinguo2" n="2"><orth extent="full">stinguo</orth>, <itype>xi, ctum, 3</itype><sense>x</sense></entryFree>')
        self.assertEqual(m.proof(row, entry), (b'stinguo#2', b'stingu', b'stin'))

    def test_withhold_other_parts_headwords_and_unjoined_rows(self):
        row, entry = fixture()
        for xml in [b'<entryFree id="n1" key="bacoquo"><orth extent="full">ba^-co^quo</orth>, <itype>coxi, coctum, 3</itype><sense>x</sense></entryFree>',
                    b'<entryFree id="n1" key="bacoquo"><orth extent="full">ba^-co^quo</orth>, <itype>xi, 3</itype><sense>x</sense></entryFree>',
                    b'<entryFree id="n1" key="baduco"><orth extent="full">ba^-du_co</orth>, <itype>xi, ctum, 3</itype><sense>x</sense></entryFree>',
                    b'<entryFree id="n1" key="bacoquor"><orth extent="full">ba^-co^quor</orth>, <itype>xi, ctum, 3</itype><sense>x</sense></entryFree>',
                    b'<entryFree id="n1" key="quo"><orth extent="full">quo</orth>, <itype>xi, ctum, 3</itype><sense>x</sense></entryFree>']:
            other_row, other_entry = fixture(xml)
            self.assertIsNone(m.proof(other_row, other_entry), xml)
        appended = copy.deepcopy(row); appended['fields'].append({'name': 'itype', 'projection': 'xi, ctum, 3'})
        self.assertIsNone(m.proof(appended, entry))
        self.assertIsNone(m.proof(dict(row, id='n9'), entry))
        self.assertIsNone(m.proof(dict(row, projection_error='x'), entry))


class Transform(unittest.TestCase):
    def test_replace_exactly_the_two_defective_records(self):
        row, entry = fixture()
        data, counts = m.transform(RAW + b':le:other\n:vs:oth\tconj3\n', [row], {'n1': entry})
        self.assertEqual(data, REPAIRED + b':le:other\n:vs:oth\tconj3\n')
        self.assertEqual(counts, {'repaired_lemma_blocks': 1, 'repaired_records': 2})
        self.assertEqual(m.transform(data, [row], {'n1': entry}), (data, {'already_repaired': 1}))

    def test_preserve_separators_and_line_endings(self):
        row, entry = fixture()
        raw = RAW.replace(b'\n', b'\r\n').replace(b'co^qx perfstem', b'co^qx\tperfstem')
        data, _ = m.transform(raw, [row], {'n1': entry})
        self.assertEqual(data, REPAIRED.replace(b'\n', b'\r\n').replace(b'co^x perfstem', b'co^x\tperfstem'))

    def test_withhold_unexpected_block_shapes(self):
        row, entry = fixture()
        cases = {'withheld_unmatched_defective_records': RAW.replace(b'co^qct', b'co^qt'),
                 'withheld_block_shape_differs': RAW + b':vs:ba^-co^qx perfstem\n',
                 'withheld_ambiguous_lemma_block': RAW * 2,
                 'lemma_without_candidate_block': b':le:other\n:vs:oth\tconj3\n'}
        cases['withheld_block_shape_differs_flag'] = RAW.replace(b'co^qx perfstem', b'co^qx perfstem orth')
        for reason, data in cases.items():
            output, counts = m.transform(data, [row], {'n1': entry})
            self.assertEqual(output, data, reason)
            self.assertEqual(counts.get(reason.replace('_flag', '')), 1, reason)
        with self.assertRaises(ValueError):
            m.transform(RAW, [row], {})


class Preparation(unittest.TestCase):
    def test_private_output_expected_count_and_no_overwrite(self):
        row, entry = fixture()
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            p = Path(directory); candidate = p / 'candidate'; headers = p / 'headers'; source = p / 'source'
            lexica = p / 'lexica'; target = p / 'out'
            candidate.write_bytes(RAW); headers.write_bytes(b'headers'); source.write_bytes(b'source'); lexica.mkdir()
            with patch.object(m.first, 'source_rows', return_value=([row], source, 'pinned')), \
                    patch.object(m.first.review, 'load_entries', return_value=({'n1': entry}, source, 'pinned')):
                with self.assertRaises(ValueError):
                    m.prepare(candidate, headers, lexica, target, 1)
                self.assertFalse(target.exists())
                m.prepare(candidate, headers, lexica, target, 2)
                self.assertEqual(target.stat().st_mode & 0o777, 0o600)
                self.assertEqual(target.read_bytes(), REPAIRED)
                with self.assertRaises(FileExistsError):
                    m.prepare(candidate, headers, lexica, target, 2)


if __name__ == '__main__':
    unittest.main()
