#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Synthetic full native family control; no historical lexical fixtures."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('tool',Path(__file__).resolve().parents[1]/'tools/qualify-latin-loss-primary-source.py')
tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
BUILD=Path(sys.argv.pop()).resolve()


class NativePrimary(unittest.TestCase):
    def test_regular_deponent_compound_and_fourth_families(self):
        fixtures=[('zzzaxamo','a_vi, a_tum, 1'),('zzzaxamor','a_tus, 1'),
                  ('zzza_-maxo','ma_xi, ma_xum, 3'),('zzzmi^o','i_vi, 4')]
        selected=[]
        for head,grammar in fixtures:
            row={'headword':head,'projection_error':None,'fields':[{'name':'itype','projection':grammar}]}
            _,records=tool.source_recipe(row);selected.append((tool.review.source_key(row),records))
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp).resolve();source=target/'source.stems'
            source.write_bytes(b''.join(tool.supines.payload(lemma,records) for lemma,records in selected))
            tool.native.build_trial(BUILD/'stemlib-production/latin',source,BUILD,target/'native')
            library=next(BUILD.glob('libmorpheus.*'))
            reader=tool.supines.direct.StrictRows(library,target/'native')
            try:
                for lemma,records in selected:
                    cells=tool.family_cells(records);counts,_=tool.check_cells(reader,lemma,cells,reader)
                    self.assertEqual(counts['covered_cells'],len(cells))
                    self.assertEqual(counts['missing_reference_readings'],0)
            finally:reader.close()


if __name__=='__main__':unittest.main()
