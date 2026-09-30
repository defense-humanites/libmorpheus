#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Source topology and witness inventories must remain separate signals."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lxml import etree

SCRIPT = Path(__file__).resolve().parents[1] / "tools/prepare-latin-partition-review.py"
spec = importlib.util.spec_from_file_location("partition_review", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def header(key, lemma):
    return dict(schema=1, id=key, source=m.SOURCE.name, source_key=lemma,
                lemma=lemma, projection_error=None,
                fields=[dict(name="orth", projection=lemma, value=lemma)])


class SourceReviewTest(unittest.TestCase):
    def test_direct_initial_sense_fields_only_and_inventory_does_not_infer_signal(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "headers"
            rows = [header("a", "one"), header("b", "two"), header("c", "three")]
            path.write_text("".join(json.dumps(r) + "\n" for r in rows))
            entries = {
                "a": etree.fromstring(b'<entryFree key="one"><sense><cit><quote>example</quote></cit><itype>3</itype><pos>v. a.</pos></sense></entryFree>'),
                "b": etree.fromstring(b'<entryFree key="two"><sense><quote><pos>v. n.</pos></quote></sense><sense><pos>v. a.</pos></sense></entryFree>'),
                "c": etree.fromstring(b'<entryFree key="three"><sense><itype>3</itype></sense></entryFree>')}
            table, dossier = m.analyze(path, entries, {"one"}, {"two", "three"})
            self.assertEqual(table["nominal_only"]["first_sense_verbal_pos"], 1)
            self.assertEqual(table["verbal_only"]["no_first_sense_verbal_signal"], 1)
            self.assertEqual(table["verbal_only"]["first_sense_conjugation_itype"], 1)
            self.assertEqual([r["lemma"] for r in dossier], ["two", "three"])
            self.assertEqual(dossier[0]["first_sense_fields"], [])
            self.assertEqual(len(dossier[0]["header_row_sha256"]), 64)
            self.assertEqual(m.signal([dict(name="pos", projection=None)]),
                             "no_first_sense_verbal_signal")

    def test_italic_verb_labels_are_separate_from_grammatical_fields(self):
        entry = etree.fromstring(b'<entryFree><sense><hi rend="ital">v. dep. a.</hi><hi rend="ital">v. elsewhere</hi><quote><hi rend="ital">v. a.</hi></quote></sense><sense><pos>v. n.</pos></sense></entryFree>')
        fields = m.initial_sense_fields(entry)
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0]["name"], "italic_verbal_label")
        self.assertEqual(m.signal(fields), "first_sense_italic_verbal_label")

    def test_rejects_stale_join_and_duplicate_header_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "headers"
            row = header("a", "one")
            entries = {"a": etree.fromstring(b'<entryFree key="other"/>')}
            path.write_text(json.dumps(row) + "\n")
            with self.assertRaisesRegex(ValueError, "key mismatch"):
                m.analyze(path, entries, set(), set())
            entries["a"].set("key", "one")
            path.write_text((json.dumps(row) + "\n") * 2)
            with self.assertRaisesRegex(ValueError, "duplicate"):
                m.analyze(path, entries, set(), set())
            row["source"] = "other.xml"
            path.write_text(json.dumps(row) + "\n")
            with self.assertRaisesRegex(ValueError, "does not join"):
                m.analyze(path, entries, set(), set())

    def test_pinned_source_and_private_output_boundaries(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parents[2]) as directory:
            root = Path(directory)
            source = root / m.SOURCE
            source.parent.mkdir(parents=True)
            source.write_text('<TEI><entryFree id="a" key="one"><sense><pos>v. a.</pos></sense></entryFree></TEI>')
            headers, nominal, verbal = [root / n for n in ("h", "n", "v")]
            headers.write_text(json.dumps(header("a", "one")) + "\n")
            nominal.write_text("")
            verbal.write_text(":le:one\n")
            target = root / "dossier"
            def prepare(output=target, expected=1):
                with patch.object(m.subprocess, "check_output", side_effect=[m.REVISION + "\n", ""]):
                    return m.prepare(headers, root, nominal, verbal, output, expected)
            report = prepare()
            self.assertEqual(report["dossier_entries"], 1)
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                prepare()
            with self.assertRaises(ValueError):
                prepare(SCRIPT.parent / "forbidden")
            with self.assertRaises(ValueError):
                prepare(root / "invalid", expected=2)
            self.assertFalse((root / "invalid").exists())
            with patch.object(m.subprocess, "check_output", return_value="other\n"):
                with self.assertRaisesRegex(ValueError, "pinned"):
                    m.prepare(headers, root, nominal, verbal)
            with patch.object(m.subprocess, "check_output", side_effect=[m.REVISION, " M source"]):
                with self.assertRaisesRegex(ValueError, "selected"):
                    m.prepare(headers, root, nominal, verbal)


if __name__ == "__main__":
    unittest.main()
