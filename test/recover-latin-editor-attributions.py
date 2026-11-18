#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from lxml import etree

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/recover-latin-editor-attributions.py'
spec = importlib.util.spec_from_file_location('m', SCRIPT); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
XML = (b'<entryFree id="n1" key="barrodo"><orth extent="full">bar-ro_do</orth> (<orth extent="full">badr-</orth>, '
       b'<itype>Kayser</itype>, Jan), <itype>ro_si, ro_sum, 3</itype>, <pos>v. a.</pos><sense>x</sense></entryFree>')
WITH = b':le:barrodo\n:vs:bar-ro_d\tconj3\n:vs:bar-ro_dKayser perfstem\n'
WITHOUT = b':le:barrodo\n:vs:bar-ro_d\tconj3\n:vs:bar-ro_s perfstem\n:vs:bar-ro_s pp4\n'


def fixture(xml=XML):
    entry = etree.fromstring(xml)
    row, _ = m.first.review.projection.project(entry, 'Latin'); row['id'] = entry.get('id')
    return row, entry


def fake_replay(row, filters, target, name):
    """Stand-in for the historical filters: attribution fields decide the shape."""
    marked = any(f['name'] == 'itype' and m.attribution(f['projection']) for f in row['fields'])
    data = WITH if marked else WITHOUT
    lines = data.splitlines(keepends=True)
    return lines[0][4:].strip(), lines[1:]


class Attribution(unittest.TestCase):
    def test_capitalized_fields_are_attributions(self):
        for value in ('Kayser', 'Ritschl, Fleckeisen', 'Liv 33', 'Baiter, Halm', 'Ritschl, Baiter, Halm, Jahn'):
            self.assertTrue(m.attribution(value), value)
        for value in ('a_vi, a_tum, 1', 'xi, ctum, 3', '3', 'e^re', 'i_vi, or i^i, 4', 'kayser'):
            self.assertFalse(m.attribution(value), value)

    def test_proof_requires_source_field_and_following_grammar(self):
        row, entry = fixture()
        result, reason = m.proof(row, entry)
        self.assertEqual(reason, 'accepted_header'); self.assertEqual(result[0], b'barrodo')
        self.assertEqual([f['projection'] for f in result[2]['fields'] if f['name'] == 'itype'], ['ro_si, ro_sum, 3'])
        plain, plain_entry = fixture(XML.replace(b'<itype>Kayser</itype>, Jan', b'Kayser, Jan'))
        self.assertEqual(m.proof(plain, plain_entry), (None, 'no_attribution_field'))
        trailing, trailing_entry = fixture(XML.replace(b'<itype>Kayser</itype>, Jan), <itype>ro_si, ro_sum, 3</itype>', b'<itype>ro_si, ro_sum, 3</itype>), <itype>Kayser</itype>'))
        self.assertEqual(m.proof(trailing, trailing_entry), (None, 'withheld_no_following_grammar_field'))
        io, io_entry = fixture(XML.replace(b'bar-ro_do', b'bar-ro_di^o').replace(b'key="barrodo"', b'key="barrodio"'))
        self.assertEqual(m.proof(io, io_entry), (None, 'withheld_io_class_separate_repair'))
        altered = copy.deepcopy(row); altered['fields'][2]['projection'] = 'Halm'
        self.assertEqual(m.proof(altered, entry), (None, 'withheld_attribution_not_in_source'))
        self.assertEqual(m.proof(dict(row, id='n9'), entry), (None, 'withheld_unprojected_or_unjoined'))


class Transform(unittest.TestCase):
    def test_replace_block_records_only(self):
        row, entry = fixture()
        raw = b'bar-ro_do \t<orth>badr-</orth>\t\n' + WITH + b'\t<pos>v. a.</pos>\n:le:other\n:vs:oth\tconj3\n'
        with patch.object(m, 'replay', fake_replay):
            data, counts = m.transform(raw, [row], {'n1': entry}, Path('.'), Path('.'))
        self.assertEqual(data, b'bar-ro_do \t<orth>badr-</orth>\t\n' + WITHOUT + b'\t<pos>v. a.</pos>\n:le:other\n:vs:oth\tconj3\n')
        self.assertEqual(counts, {'accepted_header': 1, 'added_records': 3, 'reclassed_intact_records': 0, 'removed_records': 2, 'replaced_lemma_blocks': 1})

    def test_anchor_and_bounds(self):
        row, entry = fixture()
        cases = {'withheld_candidate_block_not_reproduced': WITH.replace(b'perfstem', b'pp4'),
                 'withheld_missing_or_duplicate_block': WITH * 2,
                 'block_unaffected_by_attribution': WITHOUT}
        for reason, data in cases.items():
            with patch.object(m, 'replay', fake_replay if reason != 'block_unaffected_by_attribution' else
                              (lambda r, f, t, n: (b'barrodo', WITHOUT.splitlines(keepends=True)[1:]))):
                output, counts = m.transform(data, [row], {'n1': entry}, Path('.'), Path('.'))
            self.assertEqual(output, data, reason); self.assertEqual(counts.get(reason), 1, reason)
        with patch.object(m, 'replay', lambda r, f, t, n: (b'barrodo', WITH.splitlines(keepends=True)[1:])):
            output, counts = m.transform(WITH, [row], {'n1': entry}, Path('.'), Path('.'))
        self.assertEqual(output, WITH); self.assertEqual(counts['withheld_replay_still_capitalized'], 1)
        dropping = lambda r, f, t, n: (b'barrodo', WITH.splitlines(keepends=True)[1:] if 'Kayser' in str(r) else [b':vs:other\tconj3\n'])
        with patch.object(m, 'replay', dropping):
            output, counts = m.transform(WITH, [row], {'n1': entry}, Path('.'), Path('.'))
        self.assertEqual(output, WITH); self.assertEqual(counts['withheld_replay_drops_an_intact_stem'], 1)
        empty = lambda r, f, t, n: (b'barrodo', WITH.splitlines(keepends=True)[1:]) if 'Kayser' in str(r) else (None, [])
        with patch.object(m, 'replay', empty):
            output, counts = m.transform(WITH, [row], {'n1': entry}, Path('.'), Path('.'))
        self.assertEqual(counts['withheld_replay_yields_no_block'], 1)

    def test_reclassed_present_is_counted_not_withheld(self):
        row, entry = fixture()
        before = b':le:barrodo\n:vs:bar-ro_d\tconj1\n:vs:bar-ro_dKayser perfstem\n'
        after = [b':de:bar-ro_d\tare_vb\n']
        fake = lambda r, f, t, n: (b'barrodo', before.splitlines(keepends=True)[1:] if 'Kayser' in str(r) else after)
        with patch.object(m, 'replay', fake):
            output, counts = m.transform(before, [row], {'n1': entry}, Path('.'), Path('.'))
        self.assertEqual(output, b':le:barrodo\n:de:bar-ro_d\tare_vb\n')
        self.assertEqual(counts['reclassed_intact_records'], 1)


class Replay(unittest.TestCase):
    def test_replay_runs_the_four_filters_and_parses_one_block(self):
        row, _ = fixture()
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            filters = Path(directory) / 'filters'; filters.mkdir(); target = Path(directory) / 'out'; target.mkdir()
            for stage in m.FILTERS[:-1]:
                (filters / stage).write_text('#!/bin/sh\ncat\n'); os.chmod(filters / stage, 0o700)
            (filters / 'latvb').write_text('#!/bin/sh\nprintf "echo of input\\n:le:barrodo\\n:vs:bar-ro_s perfstem\\n"\n')
            os.chmod(filters / 'latvb', 0o700)
            self.assertEqual(m.replay(row, filters, target, 'probe'), (b'barrodo', [b':vs:bar-ro_s perfstem\n']))
            self.assertEqual((target / 'probe-combitype.stdout').read_bytes(), m.recovery.render(row).encode())
            (filters / 'latvb').write_text('#!/bin/sh\nprintf ":le:a\\n:vs:x conj3\\n:le:b\\n"\n')
            with self.assertRaises(ValueError):
                m.replay(row, filters, target, 'twice')
            (filters / 'latvb').write_text('#!/bin/sh\ncat\n')
            self.assertEqual(m.replay(row, filters, target, 'none'), (None, []))


class Preparation(unittest.TestCase):
    def test_private_output_expected_count_and_no_overwrite(self):
        row, entry = fixture()
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            p = Path(directory); candidate = p / 'candidate'; headers = p / 'headers'; source = p / 'source'
            lexica = p / 'lexica'; filters = p / 'filters'; target = p / 'out'
            candidate.write_bytes(WITH); headers.write_bytes(b'headers'); source.write_bytes(b'source'); lexica.mkdir(); filters.mkdir()
            for stage in m.FILTERS:
                (filters / stage).write_bytes(b'')
            with patch.object(m.first, 'source_rows', return_value=([row], source, 'pinned')), \
                    patch.object(m.first.review, 'load_entries', return_value=({'n1': entry}, source, 'pinned')), \
                    patch.object(m, 'replay', fake_replay):
                with self.assertRaises(ValueError):
                    m.prepare(candidate, headers, lexica, filters, target, 2)
                report = m.prepare(candidate, headers, lexica, filters, target / 'ok', 1)
                self.assertEqual((target / 'ok/after.stems').read_bytes(), WITHOUT)
                self.assertEqual((target / 'ok/after.stems').stat().st_mode & 0o777, 0o600)
                self.assertEqual(set(report['filter_sha256']), set(m.FILTERS))
                with self.assertRaises(FileExistsError):
                    m.prepare(candidate, headers, lexica, filters, target / 'ok', 1)


if __name__ == '__main__':
    unittest.main()
