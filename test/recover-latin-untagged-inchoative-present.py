#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from lxml import etree

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/recover-latin-untagged-inchoative-present.py'
spec = importlib.util.spec_from_file_location('m', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixture():
    entry = etree.fromstring(b'<entryFree id="n1" key="zavisco"><orth extent="full">za^-visco</orth> (<orth extent="full">za^vesco</orth>; <bibl>reference</bibl>), zaxi, 3, <sense><hi rend="ital">v. inch. n.</hi> definition</sense></entryFree>')
    base, _ = m.first.review.projection.project(entry, 'Latin')
    row, _ = m.first.compound.recovery.augment(base, entry)
    row['id'] = 'n1'
    return row, entry


class Recovery(unittest.TestCase):
    def test_exact_tail_two_source_spellings_only_presents_and_idempotence(self):
        row, entry = fixture(); original = copy.deepcopy(row)
        lemma, raw, records = m.proof(row, entry)
        self.assertEqual(records, b':le:zavisco\n:vs:za^-visc\tconj3\n:vs:za^vesc\tconj3 orth\n')
        data, counts = m.transform(raw, [row], {'n1': entry})
        self.assertEqual(data, raw + records)
        self.assertEqual(counts, {'added_stem_records': 2, 'recovered_headers': 1})
        self.assertEqual(row, original)
        self.assertNotIn(b'perfstem', records); self.assertNotIn(b'pp4', records)
        self.assertEqual(m.transform(data, [row], {'n1': entry})[0], data)
    def test_reject_other_tail_voice_structure_and_incomplete_spelling(self):
        row, entry = fixture()
        for tail in ['), zaxi, 4,', '), zaxi, 3, extra', '), 3,', '), zaxi, 3?']:
            altered = copy.deepcopy(entry); altered[2].tail = tail
            self.assertIsNone(m.proof(row, altered))
        for change in ['voice', 'extent', 'spelling', 'location']:
            altered = copy.deepcopy(entry)
            if change == 'voice': altered[3][0].text = 'v. dep.'
            elif change == 'extent': altered[1].set('extent', 'part')
            elif change == 'spelling': altered[1].text = 'zovesco'
            else: altered[2].tag = 'note'
            self.assertIsNone(m.proof(row, altered))
    def test_reject_changed_projected_fields_and_source_identity(self):
        row, entry = fixture()
        for change in ['pos', 'head', 'id', 'itype']:
            altered = copy.deepcopy(row)
            if change == 'pos': altered['fields'][-1]['projection'] = 'v. n.'
            elif change == 'head': altered['headword'] = 'zovesco'
            elif change == 'id': altered['id'] = 'other'
            else: altered['fields'].append(dict(name='itype', projection='3', type=None))
            self.assertIsNone(m.proof(altered, entry))
    def test_withhold_duplicate_source_header_existing_block_and_missing_join(self):
        row, entry = fixture(); lemma, raw, _ = m.proof(row, entry)
        for candidate, rows in [(raw * 2, [row]), (raw, [row, row]), (raw + b':le:' + lemma + b'\n', [row]), (b'changed\n', [row])]:
            self.assertEqual(m.transform(candidate, rows, {'n1': entry})[0], candidate)
        with self.assertRaises(ValueError): m.transform(raw, [row], {})
    def test_private_output_expected_count_and_no_overwrite(self):
        row, entry = fixture(); _, raw, _ = m.proof(row, entry)
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            p = Path(directory); candidate = p/'candidate'; headers = p/'headers'; source = p/'source'; lexica = p/'lexica'; target = p/'out'
            candidate.write_bytes(raw); headers.write_bytes(b'headers'); source.write_bytes(b'source'); lexica.mkdir()
            with patch.object(m.first, 'source_rows', return_value=([row], source, 'pinned')), patch.object(m.first.review, 'load_entries', return_value=({'n1': entry}, source, 'pinned')):
                with self.assertRaises(ValueError): m.prepare(candidate, headers, lexica, target, 2)
                self.assertFalse(target.exists())
                report = m.prepare(candidate, headers, lexica, target, 1)
                self.assertEqual(report['counts']['added_stem_records'], 2)
                self.assertEqual(target.stat().st_mode & 0o777, 0o600)
                with self.assertRaises(FileExistsError): m.prepare(candidate, headers, lexica, target, 1)


if __name__ == '__main__':
    unittest.main()
