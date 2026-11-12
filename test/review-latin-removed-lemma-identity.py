#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Synthetic checks for the lemma-identity review of removed readings."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('identity', Path(__file__).resolve().parents[1] / 'tools/review-latin-removed-lemma-identity.py')
identity = importlib.util.module_from_spec(spec); spec.loader.exec_module(identity)


def signature(work, lemma, voice=1, pos=2, tense=1):
    return [work, lemma, pos, 3, 1, 0, 0, tense, 4, voice, 0]


def row(form, removed, added, after):
    return {'form': form, 'curated_count': len(removed), 'rebuilt_count': len(after), 'retained_rows': 0,
            'removed': [{'signature': s, 'multiplicity': m} for s, m in removed],
            'added': [{'signature': s, 'multiplicity': m} for s, m in added]}


def run(rows, after):
    with tempfile.TemporaryDirectory() as directory:
        delta = Path(directory) / 'delta.jsonl'
        delta.write_text(''.join(json.dumps(r) + '\n' for r in rows))
        report = identity.review(delta, lambda form: after.get(form, []), Path(directory) / 'pairs.jsonl')
        pairs = [json.loads(l) for l in (Path(directory) / 'pairs.jsonl').read_text().splitlines()]
    return report, pairs


class Relations(unittest.TestCase):
    def test_lemma_relations_are_mechanical(self):
        self.assertEqual(identity.relation('calvo', 'calvor'), 'active_lemma_matched_by_deponent')
        self.assertEqual(identity.relation('calvor', 'calvo'), 'deponent_lemma_matched_by_active')
        self.assertEqual(identity.relation('aggero#1', 'aggero#2'), 'homograph_numbering')
        self.assertEqual(identity.relation('decoquo', 'de_-coquo'), 'native_composition_for_lemma')
        self.assertEqual(identity.relation('de_-coquo', 'decoquo'), 'lemma_for_native_composition')
        self.assertEqual(identity.relation('con-manduco#1', 'commanduco'), 'lemma_for_assimilated_native_composition')
        self.assertEqual(identity.relation('commanduco', 'con-manduco#1'), 'assimilated_native_composition_for_lemma')
        self.assertEqual(identity.relation('claudo', 'claudeo'), 'single_letter_spelling')
        self.assertEqual(identity.relation('ba^lo', 'balo#2'), 'homograph_numbering')
        self.assertEqual(identity.relation('facio', 'fio'), 'other_lemma')

    def test_single_edit(self):
        self.assertTrue(identity.single_edit('claudo', 'cludo'))
        self.assertTrue(identity.single_edit('inclitus', 'inclutus'))
        self.assertFalse(identity.single_edit('claudo', 'claudo'))
        self.assertFalse(identity.single_edit('claudo', 'cudo'))

    def test_keys_disregard_workword_notation_only(self):
        self.assertEqual(identity.ten(signature('calvi_s', 'calvio')), identity.ten(signature('calvis', 'calvo')))
        self.assertNotEqual(identity.ten(signature('calvis', 'calvo', voice=2)), identity.ten(signature('calvis', 'calvor', voice=5)))
        self.assertEqual(identity.nine(signature('calvis', 'calvo', voice=2)), identity.nine(signature('calvis', 'calvor', voice=5)))


class Review(unittest.TestCase):
    def test_matches_added_or_retained_readings_by_tier(self):
        calvitur = signature('calvitur', 'calvo', voice=2); calvitur_dep = signature('calvitur', 'calvor', voice=5)
        claudit = signature('claudit', 'claudo'); claudit_alt = signature('claudit', 'claudeo')
        aggerit = signature('aggerit', 'aggero#1'); aggerit2 = signature('aggerit', 'aggero#2'); aggerit3 = signature('aggerit', 'aggero#3')
        manducatur = signature('mandu_ca_tur', 'manducor', voice=2); manducatur_art = signature('mandu_ca_tur', 'manduco', voice=2)
        calvis = signature('calvis', 'calvo'); calvis_io = signature('calvi_s', 'calvio')
        perditum = signature('perditum', 'perdo'); abeo = signature('abeo', 'abeo'); abeo2 = signature('abeo', 'abeo', tense=2)
        rows = [row('calvitur', [(calvitur, 1)], [(calvitur_dep, 1)], [calvitur_dep]),
                row('claudit', [(claudit, 2)], [(claudit_alt, 1)], [claudit_alt]),
                row('aggerit', [(aggerit, 1)], [(aggerit2, 1), (aggerit3, 1)], [aggerit2, aggerit3]),
                row('manducatur', [(manducatur, 1)], [], [manducatur_art]),
                row('calvis', [(calvis, 1)], [(calvis_io, 1)], [calvis_io]),
                row('perditum', [(perditum, 1)], [], []),
                row('abeo', [(abeo, 1)], [(abeo2, 1)], [abeo2]),
                row('quiet', [], [(signature('quiet', 'quiesco'), 1)], [signature('quiet', 'quiesco')])]
        after = {'calvitur': [calvitur_dep], 'claudit': [claudit_alt], 'aggerit': [aggerit2, aggerit3],
                 'manducatur': [manducatur_art], 'calvis': [calvis_io], 'abeo': [abeo2], 'quiet': [signature('quiet', 'quiesco')]}
        report, pairs = run(rows, after)
        self.assertEqual(report['counts'], {'forms_with_removed_readings': 7, 'removed_readings': 8,
                                            'removed_readings_on_completely_lost_forms': 1,
                                            'forms_with_lemma_matches': 5,
                                            'removed_readings_matched_at_ten_fields': 5,
                                            'removed_readings_matched_at_nine_fields': 1,
                                            'removed_readings_without_lemma_match': 1,
                                            'matched_readings_with_workword_notation_differing': 1})
        self.assertEqual(report['ten_field_matches_by_relation'],
                         {'deponent_lemma_matched_by_active': 1, 'homograph_numbering': 1, 'single_letter_spelling': 3})
        self.assertEqual(report['nine_field_matches_by_relation'], {'active_lemma_matched_by_deponent': 1})
        self.assertEqual(report['nine_field_voice_pairs'], {'2>5': 1})
        self.assertEqual(report['matched_reading_origin'], {'added_reading': 5, 'retained_reading': 1})
        self.assertEqual(report['matched_readings_by_part_of_speech'], {'2': 6})
        self.assertEqual(report['removed_lemmas'], {'total': 6, 'fully_matched': 4, 'unmatched': 2})
        self.assertEqual([p['form'] for p in pairs], ['calvitur', 'claudit', 'aggerit', 'manducatur', 'calvis'])
        self.assertEqual(pairs[2]['pairs'], [{'removed_lemma': 'aggero#1', 'matched_lemma': 'aggero#2', 'fields': 'ten',
                                              'relation': 'homograph_numbering', 'multiplicity': 1}])
        self.assertEqual(pairs[0]['pairs'][0]['fields'], 'nine')
        self.assertEqual(pairs[1]['pairs'][0]['multiplicity'], 2)

    def test_closest_relation_wins_and_same_lemma_never_matches(self):
        removed = signature('f', 'calvo')
        after = [signature('f', 'calvo', tense=2), signature('f', 'calvio'), signature('f', 'calvo#2')]
        self.assertEqual(identity.match(removed, after)[:2], ('ten', 'homograph_numbering'))
        self.assertEqual(identity.match(removed, [signature('f', 'calvo', tense=2)]), (None, None, None))

    def test_candidate_readings_must_match_the_difference_file(self):
        rows = [row('f', [(signature('f', 'a'), 1)], [], [signature('f', 'b')])]
        with self.assertRaises(ValueError):
            run(rows, {'f': []})


if __name__ == '__main__':
    unittest.main()
