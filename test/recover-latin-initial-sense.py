#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Source-only recovery must preserve the old stream and exclude weak signals."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lxml import etree

SCRIPT = Path(__file__).resolve().parents[1] / "tools/recover-latin-initial-sense.py"
spec = importlib.util.spec_from_file_location("sense_recovery", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def record():
    return dict(schema=1, id="a", source=m.review.SOURCE.name, source_key="one",
                lemma="one", headword="one", projection_error=None,
                fields=[dict(name="orth", value="one", projection="one", type=None)])


class RecoveryTest(unittest.TestCase):
    def test_explicit_verbal_labels_recover_grammar_but_not_weak_or_quoted_signals(self):
        row = record()
        entry = etree.fromstring(b'<entryFree><sense><itype>3</itype><pos>v. a.</pos></sense></entryFree>')
        updated, kind = m.augment(row, entry)
        self.assertEqual(kind, "first_sense_verbal_pos")
        self.assertEqual(m.render(updated), "one \t<itype>3</itype>\t<pos>v. a.</pos>\n")
        self.assertEqual(len(row["fields"]), 1)
        for xml in (b'<entryFree><sense><itype>Mela, 2</itype></sense></entryFree>',
                    b'<entryFree><sense><quote><pos>v. a.</pos></quote></sense></entryFree>',
                    b'<entryFree><sense/><sense><pos>v. a.</pos></sense></entryFree>'):
            unchanged, kind = m.augment(row, etree.fromstring(xml))
            self.assertIs(unchanged, row)
            self.assertEqual(kind, "no_explicit_verbal_label")
        entry = etree.fromstring(b'<entryFree><sense><hi rend="ital">v. dep. a.</hi></sense></entryFree>')
        updated, kind = m.augment(row, entry)
        self.assertEqual(kind, "first_sense_italic_verbal_label")
        self.assertIn("<pos>v. dep. a.</pos>", m.render(updated))

    def test_unsupported_field_withholds_whole_recovery(self):
        entry = etree.fromstring('<entryFree><sense><pos>v. a.</pos><itype>ἡ</itype></sense></entryFree>')
        row = record()
        updated, kind = m.augment(row, entry)
        self.assertIs(updated, row)
        self.assertEqual(kind, "withheld_unsupported_field")

    def test_exact_old_fields_and_counts_are_validated_before_output(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            root = Path(directory)
            source, headers, lemmata = [root / n for n in ("source", "h", "l")]
            source.write_text("source")
            headers.write_text(json.dumps(record()) + "\n")
            lemmata.write_text("one \t\n")
            entry = etree.fromstring(b'<entryFree key="one"><sense><pos>v. a.</pos></sense></entryFree>')
            def recover(target, expected=1):
                with patch.object(m.review, "load_entries", return_value=({"a": entry}, source, m.review.REVISION)):
                    return m.recover(headers, lemmata, root / "lexica", target, expected)
            stage = root / "stage"
            report = recover(stage)
            self.assertEqual(report["recovered_records"], 1)
            self.assertEqual(stage.stat().st_mode & 0o777, 0o700)
            self.assertEqual((stage / "Latin.headers.jsonl").stat().st_mode & 0o777, 0o600)
            with self.assertRaises(ValueError):
                recover(stage)
            with self.assertRaises(ValueError):
                recover(root / "wrong-count", 2)
            self.assertFalse((root / "wrong-count").exists())
            lemmata.write_text("one \t<itype>altered</itype>\n")
            with self.assertRaisesRegex(ValueError, "fields differ"):
                recover(root / "stale")
            self.assertFalse((root / "stale").exists())
            lemmata.write_text("one \t\none \t\n")
            with self.assertRaisesRegex(ValueError, "longer"):
                recover(root / "extra")
            lemmata.write_text("")
            with self.assertRaisesRegex(ValueError, "order"):
                recover(root / "missing")


if __name__ == "__main__":
    unittest.main()
