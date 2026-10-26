#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from lxml import etree

spec = importlib.util.spec_from_file_location('preverb_review', Path(__file__).resolve().parents[1] /
                                           'tools/review-latin-source-present-preverbs.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def header(head='zzprefixzo#2', digit='1'):
    return {'id': 'synthetic', 'headword': head, 'lemma': head, 'fields': [
        {'name': 'itype', 'projection': digit}]}


def entry(extent='full'):
    return etree.fromstring(('<entryFree id="synthetic"><orth extent="' + extent +
        '">zzprefixzo</orth><itype>1</itype></entryFree>').encode())


def addition(lemma='zzprefixzo#2', form='zzprefixzo', preverb='zzprefix', tense=1):
    return {'form': form, 'signature': [form, lemma, 2, 1, 1, 0, 0, tense, 4, 1, 0,
                                       preverb, preverb, 'zzstem', '', 'o'], 'multiplicity': 1}


class PreverbReview(unittest.TestCase):
    def files(self, directory, extra=None):
        root = Path(directory)
        direct = addition('zzsourcezo', 'zzsourcezo', '')
        derived = addition()
        added = [direct, derived] if extra is None else extra
        routes = root / 'routes'; delta = root / 'delta'; family = root / 'family'
        routes.write_text(''.join(json.dumps({'form': a['form'], 'removed': [], 'added': [
            {'signature': a['signature'], 'multiplicity': a['multiplicity']}]}) + '\n' for a in added))
        delta.write_text(''.join(json.dumps({'form': a['form'], 'removed': [], 'added': [
            {'signature': a['signature'][:11], 'multiplicity': a['multiplicity']}]}) + '\n' for a in added))
        family.write_text(''.join(json.dumps({'kind': 'source_present_family', 'lemma': 'zzsourcezo',
            'form': 'zzcell' + str(i)}) + '\n' for i in range(13)))
        return routes, delta, family

    def test_exact_scope_selects_only_other_lemma_native_preverbs(self):
        with tempfile.TemporaryDirectory() as d:
            paths = self.files(d)
            lemma, selected, counts = m.qualified_additions(*paths, 2, 2, 1)
            self.assertEqual(lemma, 'zzsourcezo')
            self.assertEqual(set(selected), {'zzprefixzo#2'})
            self.assertEqual(counts, {'direct_rows': 1, 'native_preverb_rows': 1, 'added_rows': 2})
            with self.assertRaisesRegex(ValueError, 'scope differs'):
                m.qualified_additions(*paths, 3, 2, 1)

    def test_projection_drift_and_duplicate_forms_abort(self):
        with tempfile.TemporaryDirectory() as d:
            routes, delta, family = self.files(d)
            rows = delta.read_text().splitlines(); row = json.loads(rows[0]); row['added'] = []
            delta.write_text(json.dumps(row) + '\n' + rows[1] + '\n')
            with self.assertRaisesRegex(ValueError, 'projection differs'):
                m.qualified_additions(routes, delta, family, 2, 2, 1)
            routes, delta, family = self.files(d)
            routes.write_text(routes.read_text() + routes.read_text().splitlines()[0] + '\n')
            with self.assertRaisesRegex(ValueError, 'duplicate changed form'):
                m.qualified_additions(routes, delta, family, 2, 2, 1)

    def test_routes_cannot_silently_broaden_qualified_scope(self):
        for a, message in ((addition('zzsourcezo'), 'not under another lemma'),
                           (addition(preverb=''), 'outside source lemma'),
                           (addition(tense=5), 'outside present-derived')):
            with tempfile.TemporaryDirectory() as d:
                paths = self.files(d, [a])
                with self.assertRaisesRegex(ValueError, message):
                    m.qualified_additions(*paths, 1, 1, 1)

    def test_signatures_require_positive_multiplicity_and_numeric_grammar(self):
        a = addition()
        for n in (0, -1, True):
            with self.assertRaisesRegex(ValueError, 'invalid private signature'):
                m.signatures([dict(a, multiplicity=n)], 16)
        a['signature'][7] = '1'
        with self.assertRaisesRegex(ValueError, 'invalid private signature'):
            m.signatures([a], 16)

    def test_source_family_requires_full_unambiguous_supported_source_morphology(self):
        self.assertEqual(m.source_family(header(), entry())[0], 'explicit_present_family')
        self.assertEqual(m.source_family(header(), entry('partial'))[0], 'nonfull_headword')
        self.assertEqual(m.source_family(header(digit='zzpast'), entry())[0], 'no_explicit_conjugation_digit')
        h = header(); h['fields'].append({'name': 'itype', 'projection': 'zzparts, 3'})
        self.assertEqual(m.source_family(h, entry())[0], 'conflicting_conjugation_digits')
        self.assertEqual(m.source_family(header(digit='2'), entry())[0], 'unsupported_present_morphology')

    def case(self, head='zzprefixzo#2', choices=True):
        h = header(head)
        c = {'synthetic': {'row': h, 'entry': entry(), 'join_routes': ['projected_key', 'emitted_headword']}} if choices else {}
        return m.inspect_lemma('zzprefixzo#2', [addition(), addition(form='zzprefixzem')], c, {},
            lambda _: ({}, []), lambda _: 'synthetic', m.loss.sibling('prepare-latin-partition-review'))

    def test_literal_homograph_identity_is_not_erased_and_evidence_is_private(self):
        case = self.case()
        self.assertEqual(case['articles'][0]['added_expected_present_rows'], 1)
        self.assertEqual(case['articles'][0]['historical_replay_state'], 'emits_no_definitions')
        report = m.summarize([case])
        self.assertEqual(report['counts']['expected_present_rows_under_unique_literal_article'], 1)
        self.assertNotIn('zz', json.dumps(report))
        self.assertIn('zz', json.dumps(case))
        other = self.case('zzprefixzo#1')
        self.assertEqual(other['articles'][0]['added_expected_present_rows'], 0)
        self.assertEqual(other['articles'][0]['headword_identity'], 'different_literal_lemma')

    def test_ambiguous_and_absent_joins_are_not_counted_as_source_expectations(self):
        case = self.case(); case['articles'].append(dict(case['articles'][0]))
        case['source_join'] = 'ambiguous_articles'
        absent = self.case(choices=False)
        report = m.summarize([case, absent])
        self.assertEqual(report['counts']['expected_present_rows_under_unique_literal_article'], 0)
        self.assertEqual({g['source_join'] for g in report['source_groups']}, {'ambiguous_articles', 'no_article_join'})

    def test_receipt_mismatch_aborts_before_loading_source(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'input'; p.write_text('synthetic')
            args = SimpleNamespace(**{k: p for k in ('routes', 'delta', 'family', 'headers', 'expanded')},
                **{'expected_' + k + '_sha256': 'wrong' for k in ('routes', 'delta', 'family', 'headers', 'expanded')})
            with self.assertRaisesRegex(ValueError, 'input receipt differs'):
                m.prepare(args)


if __name__ == '__main__':
    unittest.main()
