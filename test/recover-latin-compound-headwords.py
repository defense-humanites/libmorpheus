#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "tools/recover-latin-compound-headwords.py"
spec = importlib.util.spec_from_file_location("compound", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def sample(key="abforma", spelling="ab -forma", extent="full"):
    entry = m.review.etree.fromstring(f'<entryFree id="synthetic" key="{key}"><orth extent="{extent}">{spelling}</orth></entryFree>')
    row = dict(schema=1, source=m.review.SOURCE.name, id="synthetic", source_key=key,
               headword="ab", lemma=key, projection_error=None,
               fields=[dict(name="orth", value=spelling, projection=spelling, type=None)])
    return row, entry


class Compounds(unittest.TestCase):
    def test_explicit_compound_and_homograph_scope(self):
        for key, expected in [("abforma", "abforma"), ("abforma2", "abforma#2"), ("ab2", "abforma")]:
            row, entry = sample(key)
            result, kind = m.repair(row, entry)
            self.assertEqual(kind, "recovered")
            self.assertEqual(result["lemma"], expected)
            self.assertEqual(result["headword"].replace("-", ""), expected)
            self.assertEqual(result["source_key"], key)
            self.assertEqual(row["headword"], "ab")

    def test_unsupported_spelling_and_source_mismatch(self):
        for spelling, extent in [("ab forma", "full"), ("ab -forma, alia", "full"), ("ab -forma", "part"), ("ab-forma", "full")]:
            row, entry = sample(spelling=spelling, extent=extent)
            self.assertIs(m.repair(row, entry)[0], row)
        row, entry = sample()
        row["fields"][0]["projection"] = "different"
        with self.assertRaises(ValueError):
            m.repair(row, entry)

    def test_validate_before_private_stage_and_no_overwrite(self):
        row, entry = sample()
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            root = Path(directory)
            headers, lemmata, source = root/"headers", root/"lemmata", root/"source"
            headers.write_text(json.dumps(row)+"\n")
            lemmata.write_text(m.recovery.render(row))
            source.write_text("synthetic")
            with patch.object(m.review, "load_entries", return_value=({"synthetic": entry},source,"synthetic")):
                with self.assertRaises(ValueError):
                    m.stage(headers, lemmata, root/"lexica", root/"stage", 2)
                self.assertFalse((root/"stage").exists())
                report = m.stage(headers, lemmata, root/"lexica", root/"stage", 1)
                self.assertEqual(report["by_reason"]["recovered"], 1)
                self.assertEqual((root/"stage").stat().st_mode & 0o777, 0o700)
                with self.assertRaises(FileExistsError):
                    m.stage(headers, lemmata, root/"lexica", root/"stage", 1)
                with self.assertRaises(ValueError):
                    m.stage(headers, lemmata, root/"lexica", SCRIPT.parent/"forbidden", 1)
                lemmata.write_text("wrong\n")
                with self.assertRaises(ValueError):
                    m.stage(headers, lemmata, root/"lexica", root/"wrong")
                self.assertFalse((root/"wrong").exists())


if __name__ == "__main__":
    unittest.main()
