#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from lxml import etree

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/repair-latin-itype-tag-leak.py'
spec = importlib.util.spec_from_file_location('m', SCRIPT); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def fixture(xml=b'<entryFree id="n1" key="basileo"><orth extent="full">ba^si^le^o</orth>, <itype>u^i</itype><sense>x</sense></entryFree>'):
    entry = etree.fromstring(xml)
    row, _ = m.first.review.projection.project(entry, 'Latin'); row['id'] = entry.get('id')
    return row, entry


RAW = b':le:basileo\n:vs:ba^si^l\tconj3\n:vs:ba^si^lu^ perfstem\n:vs:ba^si^l/ityp pp4\n:le:other\n:vs:oth\tconj3\n'
FIXED = b':le:basileo\n:vs:ba^si^l\tconj3\n:vs:ba^si^lu^ perfstem\n:le:other\n:vs:oth\tconj3\n'


class Proof(unittest.TestCase):
    def test_bare_one_token_perfect(self):
        row, entry = fixture()
        self.assertEqual(m.proof(row, entry), b'basileo')
        row, entry = fixture(b'<entryFree id="n1" key="bacomo1" n="1"><orth extent="full">ba-co_mo</orth>, <itype>mpsi</itype><sense>x</sense></entryFree>')
        self.assertEqual(m.proof(row, entry), b'bacomo#1')
        for xml in [b'<entryFree id="n1" key="basileo"><orth extent="full">ba^si^le^o</orth>, <itype>u^i, 2</itype><sense>x</sense></entryFree>',
                    b'<entryFree id="n1" key="basileo"><orth extent="full">ba^si^le^o</orth>, <itype>u^i</itype>, <itype>2</itype><sense>x</sense></entryFree>',
                    b'<entryFree id="n1" key="basileo"><orth extent="full">ba^si^le^o</orth>, <itype>u^i, itum</itype><sense>x</sense></entryFree>',
                    b'<entryFree id="n1" key="basileo"><orth extent="full">ba^si^le^o</orth><sense>x</sense></entryFree>']:
            row, entry = fixture(xml)
            self.assertIsNone(m.proof(row, entry), xml)
        row, entry = fixture()
        appended = dict(row, fields=row['fields'] + [{'name': 'itype', 'projection': 'u^i'}])
        self.assertIsNone(m.proof(appended, entry))
        self.assertIsNone(m.proof(dict(row, id='n9'), entry))


class Transform(unittest.TestCase):
    def test_delete_exactly_the_leaked_record(self):
        row, entry = fixture()
        data, counts = m.transform(RAW, [row], {'n1': entry})
        self.assertEqual(data, FIXED)
        self.assertEqual(counts, {'bare_perfect_headers': 1, 'bare_perfect_headers_without_leak': 0,
                                  'removed_records': 1, 'repaired_lemma_blocks': 1})
        self.assertEqual(m.transform(data, [row], {'n1': entry})[0], data)

    def test_withhold_leaks_without_source_proof_and_ambiguous_blocks(self):
        row, entry = fixture()
        other = RAW.replace(b'basileo', b'other2')
        data, counts = m.transform(other, [row], {'n1': entry})
        self.assertEqual(data, other); self.assertEqual(counts['withheld_leak_without_bare_perfect_source'], 1)
        data, counts = m.transform(RAW * 2, [row], {'n1': entry})
        self.assertEqual(data, RAW * 2); self.assertEqual(counts['withheld_ambiguous_block'], 1)
        data, counts = m.transform(RAW, [row, row], {'n1': entry})
        self.assertEqual(data, RAW); self.assertEqual(counts['withheld_ambiguous_block'], 1)
        with self.assertRaises(ValueError):
            m.transform(RAW, [row], {})

    def test_private_output_expected_count_and_no_overwrite(self):
        row, entry = fixture()
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            p = Path(directory); candidate = p / 'candidate'; headers = p / 'headers'; source = p / 'source'
            lexica = p / 'lexica'; target = p / 'out'
            candidate.write_bytes(RAW); headers.write_bytes(b'headers'); source.write_bytes(b'source'); lexica.mkdir()
            with patch.object(m.first, 'source_rows', return_value=([row], source, 'pinned')), \
                    patch.object(m.first.review, 'load_entries', return_value=({'n1': entry}, source, 'pinned')):
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
