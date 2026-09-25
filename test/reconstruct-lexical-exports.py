#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small contract checks for the separate TEI investigation tool."""

import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from lxml import etree


SCRIPT = Path(__file__).resolve().parents[1] / "tools/reconstruct-lexical-exports.py"
spec = importlib.util.spec_from_file_location("lexical_exports", SCRIPT)
exports = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exports)


class LexicalProjectionTest(unittest.TestCase):
    def test_ordered_latin_header_and_quantity(self):
        entry = etree.fromstring(
            '<entryFree key="abactus2"><orth>ăbactus</orth>'
            '<orth type="alt">ābactus</orth><itype>ūs</itype>'
            '<gen>m.</gen><sense><orth>not a header</orth></sense></entryFree>'
        )
        record, line = exports.project(entry, "Latin")
        self.assertEqual(record["lemma"], "abactus#2")
        self.assertEqual(line, "a^bactus#2 \t<orth type=alt>a_bactus</orth>\t"
                         "<itype>u_s</itype>\t<gen>m.</gen>")

    def test_greek_first_orth_precedes_gen_and_preserves_alternates(self):
        entry = etree.fromstring(
            '<entryFree key="logos2"><orth>lo/gos</orth>'
            '<gen>o(</gen><orth type="alt">lo/gon</orth></entryFree>'
        )
        record, line = exports.project(entry, "Greek")
        self.assertEqual(record["lemma"], "logos#2")
        self.assertEqual(record["headword"], "lo/gos#2")
        self.assertEqual(line, "lo/gos#2 \t<gen>o(</gen>\t<orth type=alt>lo/gon</orth>")

    def test_greek_complex_first_orth_is_not_silently_truncated(self):
        entry = etree.fromstring('<entryFree key="lego"><orth>le/gw,fw</orth>'
                                 '<itype>e/</itype></entryFree>')
        record, line = exports.project(entry, "Greek")
        self.assertIsNone(line)
        self.assertEqual(record["projection_error"], "unsupported-headword")

    def test_unsupported_character_is_retained_in_ir_but_not_projected(self):
        entry = etree.fromstring('<entryFree key="Aba"><orth>Aba</orth><gen>ἡ</gen></entryFree>')
        record, line = exports.project(entry, "Latin")
        self.assertIsNone(line)
        self.assertEqual(record["projection_error"], "unsupported-character")
        self.assertEqual(record["fields"][1]["value"], "ἡ")

    def test_latin_short_y_from_archival_tei(self):
        entry = etree.fromstring('<entryFree key="Abdalonymus"><orth>Abdalonўmus</orth>'
                                      '<itype>i</itype></entryFree>')
        record, line = exports.project(entry, "Latin")
        self.assertIsNone(record["projection_error"])
        self.assertEqual(record["fields"][0]["value"], "Abdalonўmus")
        self.assertTrue(line.startswith("Abdalony^mus \t<itype>i</itype>"))
        self.assertNotIn("<orth>", line)

    def test_unknown_entity_is_not_silently_discarded(self):
        parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True)
        entry = etree.fromstring(b'<!DOCTYPE entryFree [<!ENTITY x "value">]>'
                                 b'<entryFree key="abc"><orth>&x;</orth></entryFree>', parser)
        record, line = exports.project(entry, "Latin")
        self.assertIsNone(line)
        self.assertEqual(record["projection_error"], "unresolved-entity")

    def test_curated_header_requires_immediately_adjacent_raw_line(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "ls.nom"
            path.write_text("A^by^la\t\t\n:le:Abyla\n:no:A^by^l\ta_ae fem\n"
                            ":le:other\nAbdalony^mus\t\n:le:Abdalonymus\n", encoding="utf-8")
            self.assertEqual(exports.latin_baseline_header_orths(path),
                             {"Abyla": {"A^by^la"}, "Abdalonymus": {"Abdalony^mus"}})


if __name__ == "__main__":
    unittest.main()
