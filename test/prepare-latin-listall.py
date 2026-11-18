#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""LISTALL pinning must preserve spelling and reject malformed stages."""

import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / "tools/prepare-latin-listall.py"
spec = importlib.util.spec_from_file_location("listall", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def archive(raw, name="listall"):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr(name, raw)
    return out.getvalue()


class ListallTest(unittest.TestCase):
    def test_literal_dedup_preserves_case_and_ij_uv(self):
        raw = b"jus\r\niUs\r\njus\r\nvis\r\nuis\r\n"
        data = archive(raw)
        original, distinct, report = m.inspect(data, m.digest(data), m.digest(raw))
        self.assertEqual(original, raw)
        self.assertEqual(distinct, b"iUs\njus\nuis\nvis\n")
        self.assertEqual(report["duplicate_lines"], 1)
        self.assertEqual(report["crlf_lines"], 5)
        self.assertFalse(report["sorted_literal_input"])

    def test_pin_members_and_invalid_tokens(self):
        data = archive(b"word\n")
        with self.assertRaisesRegex(ValueError, "pinned bytes"):
            m.inspect(data)
        for raw, name in [(b"word\n", "../listall"), (b"two words\n", "listall"),
                          (b"\xff\n", "listall"), (b"\n", "listall")]:
            data = archive(raw, name)
            with self.assertRaises(ValueError):
                m.inspect(data, m.digest(data), m.digest(raw))
        data = archive(b"word\n")
        with self.assertRaisesRegex(ValueError, "member differs"):
            m.inspect(data, m.digest(data), "wrong")

    def test_validation_before_private_stage_and_no_overwrite(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            root = Path(directory)
            source = root / "source.zip"
            source.write_bytes(b"invalid")
            output = root / "stage"
            with self.assertRaises(ValueError):
                m.prepare(source, output)
            self.assertFalse(output.exists())
            with patch.object(m, "inspect", return_value=(b"word\r\n", b"word\n", {})):
                m.prepare(source, output)
                self.assertEqual(output.stat().st_mode & 0o777, 0o700)
                self.assertEqual((output / "LISTALL.original.txt").stat().st_mode & 0o777, 0o600)
                with self.assertRaises(FileExistsError):
                    m.prepare(source, output)
                for target in [SCRIPT.parent / "forbidden", root, source]:
                    with self.assertRaises(ValueError):
                        m.prepare(source, target)


if __name__ == "__main__":
    unittest.main()
