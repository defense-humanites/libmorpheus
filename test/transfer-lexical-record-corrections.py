#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools/transfer-lexical-record-corrections.py"
spec = importlib.util.spec_from_file_location("transfer", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
ORIGINAL = b":le:one\n:aj:root old\n"
CORRECTIONS = ("Latin\tstemsrc/example\t2\t" + m.digest(b":aj:root old") + "\t" +
               json.dumps(":aj:root reviewed") + "\n").encode()


class TransferTest(unittest.TestCase):
    def test_same_lemma_and_literal_record_required(self):
        candidate = b":le:other\r\n:aj:root old\r\n:le:one\r\n:aj:root old\r\n:aj:other old\r\n"
        data, report = m.transform(candidate, ORIGINAL, CORRECTIONS, "Latin", "stemsrc/example")
        self.assertEqual(data, candidate.replace(b":le:one\r\n:aj:root old", b":le:one\r\n:aj:root reviewed"))
        self.assertEqual(report["applied_records"], 1)
        with self.assertRaisesRegex(ValueError, "source record mismatch"):
            m.transform(candidate, ORIGINAL.replace(b"root", b"changed"), CORRECTIONS, "Latin", "stemsrc/example")

    def test_invalid_scope_and_replacement(self):
        for corrections in [CORRECTIONS * 2, CORRECTIONS.replace(b'"', b'"\\n', 1)]:
            with self.assertRaises(ValueError):
                m.transform(ORIGINAL, ORIGINAL, corrections, "Latin", "stemsrc/example")
        for name in ["../escape", "/absolute", "stemsrc/missing"]:
            with self.assertRaises(ValueError):
                m.transform(ORIGINAL, ORIGINAL, CORRECTIONS, "Latin", name)

    def test_validate_before_private_write_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            root = Path(directory)
            inputs = [root / n for n in ["candidate", "original", "corrections"]]
            for path, data in zip(inputs, [ORIGINAL, ORIGINAL, CORRECTIONS]):
                path.write_bytes(data)
            output = root / "out"
            def prepare(target=output, expected=1):
                return m.prepare(*inputs, "Latin", "stemsrc/example", target, expected)
            with self.assertRaises(ValueError):
                prepare(expected=2)
            self.assertFalse(output.exists())
            prepare()
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                prepare()
            for target in [SCRIPT.parent / "forbidden", *inputs]:
                with self.assertRaises(ValueError):
                    prepare(target)


if __name__ == "__main__":
    unittest.main()
