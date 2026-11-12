#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/screen-latin-witness-backlog.py'
spec = importlib.util.spec_from_file_location('m', SCRIPT); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def row(head, grammars, alternates=()):
    return {'headword': head, 'projection_error': None, 'full_alternates': list(alternates),
            'fields': [{'name': 'orth', 'projection': head}] + [{'name': 'itype', 'projection': g} for g in grammars]}


class Screen(unittest.TestCase):
    def test_literal_table_and_grammar_shapes(self):
        literal = m.literal_grammars()
        self.assertIn('xi, ctum, 3', literal); self.assertGreater(len(literal), 50)
        self.assertEqual(m.grammar_shape([], literal), 'no_inflection_field')
        self.assertEqual(m.grammar_shape(['a', 'b'], literal), 'several_inflection_fields')
        self.assertEqual(m.grammar_shape(['xi, ctum, 3'], literal), 'literal_table_grammar')
        self.assertEqual(m.grammar_shape(['i^di, i^tum, 3'], literal), 'vowel_initial_digit_grammar')
        self.assertEqual(m.grammar_shape(['zzi, zzum, 3'], literal), 'consonant_initial_digit_grammar')
        self.assertEqual(m.grammar_shape(['e^re'], literal), 'literal_table_grammar')
        self.assertEqual(m.grammar_shape(['zzre'], literal), 'bare_infinitive')
        self.assertEqual(m.grammar_shape(['a_tus sum'], literal), 'other_grammar')

    def test_classification_uses_witness_for_membership_only(self):
        rows = [row('ba^do', ['i^di, i^tum, 3']), row('ca_vor', ['a_tus, 1']), row('da^do', ['a_re'], ['dedo']),
                row('ex-do', ['e^re']), row('ex-do', ['3']), row('fa^do', ['xi, ctum, 3'])]
        witness = (b':le:bado\n:vs:ba^d\tconj3\n:le:cavo\n:vs:ca_v\tconj1\n:le:dedo\n:vs:ded\tconj3\n'
                   b':le:exdo\n:vs:exd\tconj3\n:le:fado\n:vs:fa^d\tconj3\n:le:gado#1\n:vs:ga^d\tconj3\n'
                   b':le:hado\n:vs:ha^d\tconj3\n:le:empty\n')
        candidate = b':le:fado\n:vs:fa^d\tconj3\n:le:bado\n'
        report = m.screen(candidate, witness, rows)
        self.assertEqual(report['counts']['without_candidate_definitions'], 6)
        self.assertEqual(report['counts']['unjoined:deponent_article_for_active_lemma'], 1)
        self.assertEqual(report['counts']['unjoined:alternate_spelling_kept_as_lemma'], 1)
        self.assertEqual(report['counts']['unjoined:no_projected_header'], 2)
        self.assertEqual(report['counts']['joined:ambiguous_headers'], 1)
        self.assertEqual(report['joined_grammar_shapes'], {'vowel_initial_digit_grammar': 1})
        self.assertNotIn('unjoined:homograph_numbering_differs', report['counts'])
        rows.append(row('ga^do', ['3']))
        self.assertEqual(m.screen(candidate, witness, rows)['counts']['unjoined:homograph_numbering_differs'], 1)


if __name__ == '__main__':
    unittest.main()
