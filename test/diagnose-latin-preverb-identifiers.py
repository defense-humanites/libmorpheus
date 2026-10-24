#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

spec = importlib.util.spec_from_file_location('identifiers', Path(__file__).resolve().parents[1] /
                                           'tools/diagnose-latin-preverb-identifiers.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def data(identifier='zzprefix-zzsourcezo#2'):
    def sig(lemma, preverb):
        return [lemma, lemma, 2, 1, 1, 0, 0, 1, 4, 1, 0, preverb, preverb, 'zzstem', '', 'o']
    direct = {'signature': sig('zzsourcezo#2', ''), 'multiplicity': 1}
    derived = {'signature': sig(identifier, 'zzprefix'), 'multiplicity': 1}
    routes = [{'form': 'zzform', 'removed': [], 'added': [direct, derived]}]
    family = [{'kind': 'source_present_family', 'lemma': 'zzsourcezo#2'} for _ in range(13)]
    dossier = [{'lemma': identifier, 'source_join': 'no_article_join', 'articles': [],
        'candidate_definitions': [], 'added_rows': 1, 'additions': [dict(derived, form='zzform')]}]
    return routes, family, dossier


class IdentifierDiagnostic(unittest.TestCase):
    def test_composed_identifier_and_shared_decomposition_are_private(self):
        private = io.StringIO(); report = m.inspect(*data(), 1, 2, 1, private)
        self.assertEqual(report['counts']['literal_preverb_base_identifier_rows'], 1)
        self.assertEqual(report['counts']['same_decomposition_as_direct_addition_rows'], 1)
        self.assertNotIn('zz', json.dumps(report)); self.assertIn('zz', private.getvalue())

    def test_homograph_is_not_removed_for_composition_identity(self):
        report = m.inspect(*data('zzprefix-zzsourcezo#1'), 1, 2, 1, io.StringIO())
        self.assertEqual(report['counts']['other_native_identifier_rows'], 1)

    def test_peer_requires_same_grammar_and_literal_decomposition(self):
        routes, family, dossier = data(); routes[0]['added'][0]['signature'][13] = 'zzotherstem'
        report = m.inspect(routes, family, dossier, 1, 2, 1, io.StringIO())
        self.assertEqual(report['counts']['same_decomposition_as_direct_addition_rows'], 0)

    def test_scope_drift_duplicate_form_and_removal_abort(self):
        routes, family, dossier = data()
        with self.assertRaisesRegex(ValueError, 'inventories differ'):
            m.inspect(routes, family, dossier, 2, 2, 1, io.StringIO())
        with self.assertRaisesRegex(ValueError, 'form or removal'):
            m.inspect(routes + routes, family, dossier, 2, 4, 1, io.StringIO())
        routes[0]['removed'] = [routes[0]['added'][0]]
        with self.assertRaisesRegex(ValueError, 'form or removal'):
            m.inspect(routes, family, dossier, 1, 2, 1, io.StringIO())

    def test_dossier_route_drift_is_not_accepted(self):
        routes, family, dossier = data(); dossier[0]['additions'][0]['signature'] = list(dossier[0]['additions'][0]['signature'])
        dossier[0]['additions'][0]['signature'][12] = 'zzotherraw'
        with self.assertRaisesRegex(ValueError, 'inventories differ'):
            m.inspect(routes, family, dossier, 1, 2, 1, io.StringIO())

    def test_receipt_mismatch_precedes_output_creation(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'input'; path.write_text('synthetic')
            args = SimpleNamespace(**{n: path for n in ('routes', 'family', 'dossier')},
                **{'expected_' + n + '_sha256': 'wrong' for n in ('routes', 'family', 'dossier')})
            with self.assertRaisesRegex(ValueError, 'receipt differs'): m.prepare(args)


if __name__ == '__main__':
    unittest.main()
