#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check that the LSJ quantity diagnostic counts direct bare pron only."""

import importlib.util
from pathlib import Path
import unittest

from lxml import etree


SCRIPT = Path(__file__).resolve().parents[1] / "tools/audit-greek-pron-ambiguity.py"
spec = importlib.util.spec_from_file_location("pron_ambiguity", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PronAmbiguityTest(unittest.TestCase):
    def test_repeated_vowels_and_direct_bare_pron(self):
        root = etree.fromstring(b"""<TEI><entryFree><orth>mi_n-i/ths</orth>
          <pron>[i_]</pron></entryFree>
          <entryFree><orth>mi^n-i/ths</orth><pron>[i_]</pron></entryFree>
          <entryFree><orth>mi/n-i/ths</orth><sense><pron>[i_]</pron></sense></entryFree>
          <entryFree><orth>mi/n-i/ths</orth><pron>[ni_]</pron></entryFree>
          <entryFree><orth>mi/n-os</orth><pron>[i_]</pron></entryFree></TEI>""")
        self.assertEqual(module.count_tree(root), {
            "repeated_vowel_bare_long_pron": 2,
            "same_vowel_already_long_in_first_orth": 1,
            "same_vowel_short_in_first_orth": 1})


if __name__ == "__main__":
    unittest.main()
