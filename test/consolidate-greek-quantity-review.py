#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Synthetic checks for source binding and explicit review boundaries."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools/consolidate-greek-quantity-review.py"
spec = importlib.util.spec_from_file_location("consolidator", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ReviewTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=SCRIPT.parents[2])
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.reviews = self.root / "reviews"
        self.rows = [dict(lemma=str(i), candidate=":no:" + candidate + " os_on",
                          witness=":no:" + witness + " os_on",
                          sources=[dict(id=str(i), headword="pipios", fields=[],
                                        pron=[dict(direct=True, text="[i_]")])])
                     for i, (candidate, witness) in enumerate(
                         [("pipi", "pi_pi"), ("pipi", "pi_pi"), ("pi_pi", "pi__pi")])]
        self.source.write_text("".join(json.dumps(r) + "\n" for r in self.rows))
        self.records = [dict(lemma=str(i), source_ids=[str(i)], evidence="Synthetic evidence",
                             source_row_sha256=hashlib.sha256(raw).hexdigest(),
                             long_position=position, disposition=disposition)
                        for i, (raw, position, disposition) in enumerate(zip(
                            self.source.read_bytes().splitlines(keepends=True), [1, 3, 1],
                            ["retain_witness_position", "relocate_witness_long",
                             "deduplicate_witness_long"]))]
        self.save()

    def save(self):
        self.reviews.write_text("".join(json.dumps(r) + "\n" for r in self.records))

    def test_consolidation_and_private_output(self):
        target = self.root / "ledger"
        report = m.consolidate(self.source, self.reviews, target, expected=3)
        self.assertEqual(report["individual_positions_resolved"], 2)
        self.assertEqual(report["multiplicity_only"], 1)
        self.assertEqual(sum(report["by_disposition"].values()), 3)
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)
        self.assertFalse(json.loads(target.read_text().splitlines()[2])["position_resolved"])
        with self.assertRaises(FileExistsError):
            m.consolidate(self.source, self.reviews, target)
        with self.assertRaises(ValueError):
            m.consolidate(self.source, self.reviews, SCRIPT.parent / "forbidden")
        with self.assertRaises(ValueError):
            m.consolidate(self.source, self.reviews, expected=4)

    def test_circumflex_resolves_position_only_with_matching_monophthong(self):
        row = self.rows[2]
        row["sources"][0]["headword"] = "pi=pis"
        review = self.records[2].copy()
        review["disposition"] = "deduplicate_witness_long_from_source_circumflex"
        self.assertEqual(m.validate(row, review["source_row_sha256"], review),
                         review["disposition"])
        self.source.write_text("".join(json.dumps(r) + "\n" for r in self.rows))
        review["source_row_sha256"] = hashlib.sha256(
            self.source.read_bytes().splitlines(keepends=True)[2]).hexdigest()
        self.records[2] = review
        self.save()
        report = m.consolidate(self.source, self.reviews)
        self.assertEqual(report["individual_positions_resolved"], 3)
        self.assertEqual(report["multiplicity_only"], 0)
        for head in ("pipi=s", "pi/pis", "pi=pi=s", "pi^=pis", "other"):
            row["sources"][0]["headword"] = head
            with self.subTest(head=head), self.assertRaises(ValueError):
                m.validate(row, review["source_row_sha256"], review)
        row["candidate"], row["witness"] = ":no:ai_p os_on", ":no:ai__p os_on"
        row["sources"][0]["headword"] = "ai=pis"
        with self.assertRaises(ValueError):
            m.validate(row, review["source_row_sha256"], review)

    def test_invalid_reviews_write_nothing(self):
        for field, value in [("source_row_sha256", "stale"), ("source_ids", ["wrong"]),
                             ("evidence", " "), ("long_position", True),
                             ("long_position", 0), ("long_position", 99),
                             ("disposition", "inferred")]:
            with self.subTest(field=field):
                old = self.records[0][field]
                self.records[0][field] = value
                self.save()
                target = self.root / "invalid"
                with self.assertRaises(ValueError):
                    m.consolidate(self.source, self.reviews, target)
                self.assertFalse(target.exists())
                self.records[0][field] = old
        self.records[1]["long_position"] = 1
        self.save()
        with self.assertRaises(ValueError):
            m.consolidate(self.source, self.reviews)

    def test_unknown_duplicate_and_automatic_override(self):
        self.records.append(self.records[0])
        self.save()
        with self.assertRaises(ValueError):
            m.consolidate(self.source, self.reviews)
        self.records.pop()
        self.records[0]["lemma"] = "absent"
        self.save()
        with self.assertRaises(ValueError):
            m.consolidate(self.source, self.reviews)
        self.records[0]["lemma"] = "0"
        self.rows[0]["sources"][0]["headword"] = "pipos"
        self.rows[0]["candidate"] = ":no:pip os_on"
        self.rows[0]["witness"] = ":no:pi_p os_on"
        self.source.write_text("".join(json.dumps(r) + "\n" for r in self.rows))
        self.records[0]["source_row_sha256"] = hashlib.sha256(
            self.source.read_bytes().splitlines(keepends=True)[0]).hexdigest()
        self.save()
        with self.assertRaisesRegex(ValueError, "manual queue"):
            m.consolidate(self.source, self.reviews)


if __name__ == "__main__":
    unittest.main()
