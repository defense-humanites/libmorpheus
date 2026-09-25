#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small contract checks for the separate TEI investigation tool."""

import importlib.util
from pathlib import Path
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
        self.assertEqual(line, "abactus#2 \t<orth>a^bactus</orth>\t"
                         "<orth type=alt>a_bactus</orth>\t<itype>u_s</itype>\t<gen>m.</gen>")

    def test_unsupported_character_is_retained_in_ir_but_not_projected(self):
        entry = etree.fromstring('<entryFree key="Aba"><orth>Aba</orth><gen>ἡ</gen></entryFree>')
        record, line = exports.project(entry, "Latin")
        self.assertIsNone(line)
        self.assertEqual(record["projection_error"], "unsupported-character")
        self.assertEqual(record["fields"][1]["value"], "ἡ")

    def test_unknown_entity_is_not_silently_discarded(self):
        parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True)
        entry = etree.fromstring(b'<!DOCTYPE entryFree [<!ENTITY x "value">]>'
                                 b'<entryFree key="abc"><orth>&x;</orth></entryFree>', parser)
        record, line = exports.project(entry, "Latin")
        self.assertIsNone(line)
        self.assertEqual(record["projection_error"], "unresolved-entity")


if __name__ == "__main__":
    unittest.main()
