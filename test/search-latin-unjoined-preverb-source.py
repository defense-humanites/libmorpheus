#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from lxml import etree

spec = importlib.util.spec_from_file_location('search', Path(__file__).resolve().parents[1] /
                                           'tools/search-latin-unjoined-preverb-source.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
normalize = m.loss.sibling('prepare-latin-partition-review').projection.normalize


class FullSourceSearch(unittest.TestCase):
    def routes(self, xml, lemma='zzprefixzo#2'):
        return m.article_routes(etree.fromstring(xml.encode()), lemma, normalize)

    def test_keys_keep_homographs_and_label_projection_convention(self):
        routes = self.routes('<entryFree key="zzprefixzo2"/>')
        self.assertEqual(routes[0]['match'], 'literal')
        self.assertEqual(routes[0]['route'], 'source_key_projection_convention')
        self.assertEqual(self.routes('<entryFree key="zzprefixzo1"/>')[0]['match'],
                         'case_or_homograph_or_notation_lead')

    def test_direct_orth_homograph_is_separate_from_unqualified_spelling(self):
        routes = self.routes('<entryFree key="zzother2"><orth extent="full">zzprefixzo</orth></entryFree>')
        self.assertEqual({r['match'] for r in routes}, {'literal', 'case_or_homograph_or_notation_lead'})
        self.assertEqual(next(r for r in routes if r['match'] == 'literal')['route'], 'direct_orth_with_entry_homograph')

    def test_notation_case_and_homograph_leads_never_become_literal(self):
        self.assertEqual(m.match('zz_prefixzo#2', 'zzprefixzo#2'), 'quantity_or_hyphen_notation_lead')
        self.assertEqual(m.match('ZZPREFIXZO#1', 'zzprefixzo#2'), 'case_or_homograph_or_notation_lead')
        self.assertIsNone(m.match('zzdifferent', 'zzprefixzo#2'))

    def test_nested_orth_and_reference_are_not_header_identity(self):
        routes = self.routes('<entryFree key="zzother"><sense><orth>zzprefixzo#2</orth>'
                             '<ref target="other">zzprefixzo#2</ref></sense></entryFree>')
        self.assertEqual({r['route'] for r in routes}, {'nested_orth', 'reference_text'})
        self.assertTrue(all(r['location'] == 'descendant' for r in routes))

    def test_whole_strings_only_and_projection_errors_do_not_exclude_articles(self):
        self.assertEqual(self.routes('<entryFree key="zzother"><orth>zzprefixzo and zzother</orth></entryFree>'), [])
        routes = self.routes('<entryFree key="unsupported key"><orth>zzprefixzo#2</orth><itype>λ</itype></entryFree>')
        self.assertEqual(routes[0]['match'], 'literal')

    def test_private_evidence_and_empty_search_are_explicit(self):
        entries = {'synthetic': etree.fromstring(b'<entryFree key="zzprefixzo2"/>')}
        private = io.StringIO(); report = m.search(entries, 'zzprefixzo#2', normalize, private)
        self.assertEqual(report['counts']['articles_with_search_evidence'], 1)
        self.assertNotIn('zz', json.dumps(report)); self.assertIn('zz', private.getvalue())
        empty = m.search(entries, 'zzdifferent', normalize, io.StringIO())
        self.assertEqual(empty['evidence_groups'], [])
        self.assertIn('not proof', empty['decision'])

    def test_scope_requires_one_unjoined_lemma_without_definitions(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'dossier'
            row = {'lemma': 'zzprefixzo#2', 'source_join': 'no_article_join', 'articles': [],
                'candidate_definitions': [], 'added_rows': 1, 'additions': [{'multiplicity': 1,
                'signature': ['zzform', 'zzprefixzo#2', 2, 1, 1, 0, 0, 1, 4, 1, 0, 'zzprefix']}]}
            path.write_text(json.dumps(row)+'\n'); self.assertEqual(m.selected(path, 1), row['lemma'])
            row['source_join'] = 'unique_article'; path.write_text(json.dumps(row)+'\n')
            with self.assertRaisesRegex(ValueError, 'scope differs'): m.selected(path, 1)

    def test_receipt_failure_precedes_source_loading(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'input'; path.write_text('synthetic')
            with self.assertRaisesRegex(ValueError, 'receipt differs'):
                m.prepare(SimpleNamespace(dossier=path, expected_dossier_sha256='wrong'))


if __name__ == '__main__':
    unittest.main()
