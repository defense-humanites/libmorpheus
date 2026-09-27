#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the historical Greek split rules on a synthetic projected stream."""

import hashlib
import os
from pathlib import Path
import runpy
from tempfile import TemporaryDirectory
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "tools/split-greek-lexical-headers.py"
split = runpy.run_path(str(SCRIPT))["split"]


class GreekSplitTest(unittest.TestCase):
    def test_lexical_rules_and_private_output(self):
        with TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            source = Path(directory) / "headers"
            output = Path(directory) / "split"
            source.write_bytes(
                b"alpha-\t<gen>x</gen>\t<orth>al-pha</orth>\n"
                b"\t*extra</gen>\t<itype>z\n"
                b"beta\t<pos>Adv.</pos>\t<orth>surface</orth>\n")
            expected = (b"alpha\t<gen>x</gen>\nal-pha\t\n"
                        b"\n*extra</gen>\nalpha\t<itype>z\n"
                        b"beta\t<pos>Adv.</pos>\nsurface\t\n")
            report = split(source, output)
            self.assertEqual(output.read_bytes(), expected)
            self.assertEqual(report, {"split_rows": expected.count(b"\n"),
                                      "split_sha256": hashlib.sha256(expected).hexdigest()})
            self.assertEqual(os.stat(output).st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                split(source, output)
            with self.assertRaises(ValueError):
                split(source, SCRIPT.parent / "split")
            source.write_bytes(b"alpha\t<quant>[a^]</quant>\n")
            with self.assertRaisesRegex(ValueError, "<quant>"):
                split(source, Path(directory) / "rejected")


if __name__ == "__main__":
    unittest.main()
