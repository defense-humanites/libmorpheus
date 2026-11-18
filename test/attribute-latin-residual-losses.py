#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Synthetic checks for the residual loss attribution."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('attribution', Path(__file__).resolve().parents[1] / 'tools/attribute-latin-residual-losses.py')
attribution = importlib.util.module_from_spec(spec); spec.loader.exec_module(attribution)


def signature(work, lemma, pos=2, tense=1, mood=4, voice=1):
    return [work, lemma, pos, 3, 1, 0, 0, tense, mood, voice, 0]


def row(form, removed, after):
    return {'form': form, 'curated_count': len(removed), 'rebuilt_count': len(after), 'retained_rows': 0,
            'removed': [{'signature': s, 'multiplicity': 1} for s in removed], 'added': []}


CATEGORIES = {b'calvo': 'unjoined:deponent_article_for_active_lemma', b'perdo': 'with_candidate_definitions',
              b'fax': 'unjoined:no_projected_header', b'eo#2': 'joined:vowel_initial_digit_grammar'}
BLOCKS = {b'perdo': [b':vs:perd\tconj3'], b'calvor': [b':vs:calv\tconj3'], b'amo': [b':de:am\tare_vb']}


class Categories(unittest.TestCase):
    def test_lemma_categories_follow_the_open_decisions(self):
        category = lambda lemma, pos=2: attribution.lemma_category(lemma, pos, CATEGORIES, BLOCKS, {b'defatiscor', b'eo#2', b'amo'})
        self.assertEqual(category('con-manduco#1'), 'native_preverb_identifier:hyphenated')
        self.assertEqual(category('defatiscor'), 'native_preverb_identifier:mapped_composition')
        # a curated or candidate lemma keeps its category even when the engine reports its name for a composition
        self.assertEqual(category('perdo'), 'curated_lemma_with_candidate_definition')
        self.assertEqual(category('calvo'), 'curated_lemma_without_definition:unjoined:deponent_article_for_active_lemma')
        self.assertEqual(category('eo#2'), 'curated_lemma_without_definition:joined:vowel_initial_digit_grammar')
        self.assertEqual(category('amo'), 'candidate_lemma_outside_curated_witness')
        self.assertEqual(category('nemo'), 'lemma_outside_curated_witness_and_candidate')
        self.assertEqual(category('rosa', pos=1), 'lemma_outside_curated_witness_and_candidate')

    def test_differing_fields_take_the_closest_reading_and_ignore_workword_notation(self):
        removed = signature('amat', 'amo')
        after = [signature('ama_t', 'amo', tense=2), signature('amat', 'amo#2', tense=2, mood=3)]
        self.assertEqual(attribution.differing_fields(removed, after), 'tense')
        self.assertEqual(attribution.differing_fields(removed, [signature('amat', 'amo', pos=1)]), 'part_of_speech')
        self.assertEqual(attribution.differing_fields(removed, []), 'no_candidate_reading')
        self.assertEqual(attribution.differing_fields(removed, [signature('ama_t', 'amo')]), 'identical_reading_at_lower_multiplicity')
        self.assertEqual(attribution.difference_size('identical_reading_at_lower_multiplicity'), 'identical_reading_at_lower_multiplicity')


class Attribution(unittest.TestCase):
    def test_lost_forms_and_unmatched_readings_are_attributed_separately(self):
        rows = [row('calvit', [signature('calvit', 'calvo')], []),
                row('calvunt', [signature('calvunt', 'calvo'), signature('calvunt', 'con-calvo')], []),
                row('faxit', [signature('faxit', 'fax')], []),
                row('perdit', [signature('perdit', 'perdo')], [signature('perdit', 'perdo', tense=2)]),
                row('calvitur', [signature('calvitur', 'calvo', voice=2)], [signature('calvitur', 'calvor', voice=2)]),
                row('amant', [signature('amant', 'amo', mood=3)], [signature('amant', 'amo'), signature('amant', 'amo', tense=2)]),
                row('quiet', [], [signature('quiet', 'quiesco')])]
        after = {'perdit': [signature('perdit', 'perdo', tense=2)], 'calvitur': [signature('calvitur', 'calvor', voice=2)],
                 'amant': [signature('amant', 'amo'), signature('amant', 'amo', tense=2)], 'quiet': [signature('quiet', 'quiesco')]}
        with tempfile.TemporaryDirectory() as directory:
            delta = Path(directory) / 'delta.jsonl'
            delta.write_text(''.join(json.dumps(r) + '\n' for r in rows))
            report = attribution.attribute(delta, lambda form: after.get(form, []), CATEGORIES, BLOCKS)
        self.assertEqual(report['counts'], {'completely_lost_forms': 3, 'readings_on_completely_lost_forms': 4,
                                            'removed_readings_matched_by_lemma_identity': 1,
                                            'unmatched_readings_on_recognized_forms': 2})
        self.assertEqual(report['completely_lost_forms_by_lemma_category'], {
            'curated_lemma_without_definition:unjoined:deponent_article_for_active_lemma': {'readings': 2, 'forms': 2, 'lemmas': 1},
            'curated_lemma_without_definition:unjoined:no_projected_header': {'readings': 1, 'forms': 1, 'lemmas': 1},
            'native_preverb_identifier:hyphenated': {'readings': 1, 'forms': 1, 'lemmas': 1}})
        self.assertEqual(report['readings_by_part_of_speech'], {'completely_lost_forms': {'2': 4}, 'unmatched_on_recognized_forms': {'2': 2}})
        self.assertEqual(report['unmatched_readings_by_lemma_category'], {
            'candidate_lemma_outside_curated_witness': {'readings': 1, 'lemmas': 1},
            'curated_lemma_with_candidate_definition': {'readings': 1, 'lemmas': 1}})
        self.assertEqual(report['unmatched_readings_by_differing_fields'], {'mood': 1, 'tense': 1})
        self.assertEqual(report['unmatched_readings_by_difference_size'], {'one_grammatical_field': 2})
        self.assertEqual(attribution.difference_size('lemma+tense'), 'one_grammatical_field_and_lemma')
        self.assertEqual(attribution.difference_size('lemma+person+gender+tense+mood+voice'), 'four_or_more_grammatical_fields_and_lemma')
        self.assertEqual(attribution.difference_size('tense+mood'), 'two_or_three_grammatical_fields')
        self.assertEqual(report['unmatched_readings_by_category_and_fields'], [
            {'lemma_category': 'candidate_lemma_outside_curated_witness', 'differing_fields': 'mood', 'readings': 1},
            {'lemma_category': 'curated_lemma_with_candidate_definition', 'differing_fields': 'tense', 'readings': 1}])

    def test_voice_only_readings_name_the_voice_on_each_side(self):
        # A deponent participle of the baseline (voice 5) that the candidate reads as passive (2), under the
        # same lemma; one the candidate reads both as active and as passive; and a reading that differs by
        # tense as well, which is not a voice-only reading.
        rows = [row('perditus', [signature('perditus', 'perdo', tense=5, mood=7, voice=5)], [signature('perditus', 'perdo', tense=5, mood=7, voice=2)]),
                row('perdita', [signature('perdi_ta', 'perdo', tense=5, mood=7, voice=5)],
                    [signature('perdita', 'perdo', tense=5, mood=7, voice=2), signature('perdita', 'perdo', tense=5, mood=7, voice=1)]),
                row('amatur', [signature('amatur', 'amo', voice=5)], [signature('amatur', 'amo', tense=2, voice=2)])]
        after = {r['form']: [s for s in json.loads(json.dumps(candidates))] for r, candidates in zip(rows, (
            [signature('perditus', 'perdo', tense=5, mood=7, voice=2)],
            [signature('perdita', 'perdo', tense=5, mood=7, voice=2), signature('perdita', 'perdo', tense=5, mood=7, voice=1)],
            [signature('amatur', 'amo', tense=2, voice=2)]))}
        with tempfile.TemporaryDirectory() as directory:
            delta = Path(directory) / 'delta.jsonl'
            delta.write_text(''.join(json.dumps(r) + '\n' for r in rows))
            report = attribution.attribute(delta, lambda form: after.get(form, []), CATEGORIES, BLOCKS)
        self.assertEqual(report['unmatched_readings_by_differing_fields'], {'voice': 2, 'tense+voice': 1})
        self.assertEqual(report['voice_only_readings_by_voice_pair'], [
            {'lemma_category': 'curated_lemma_with_candidate_definition', 'voice_pair': '5>1+2', 'readings': 1, 'lemmas': 1},
            {'lemma_category': 'curated_lemma_with_candidate_definition', 'voice_pair': '5>2', 'readings': 1, 'lemmas': 1}])
        self.assertEqual(report['voice_only_readings_by_mood_and_tense'], [
            {'lemma_category': 'curated_lemma_with_candidate_definition', 'voice_pair': '5>1+2', 'mood': '7', 'tense': '5', 'readings': 1},
            {'lemma_category': 'curated_lemma_with_candidate_definition', 'voice_pair': '5>2', 'mood': '7', 'tense': '5', 'readings': 1}])

    def test_baseline_comparison_is_qualified_per_combination_and_runtime(self):
        eleven = 'ec3fc3d4b154db5ad0b9df0d7f337716f7ceb7e94eea760857800fc5c74ed46e'
        current = '3955d877e17378d1365c6462d8d6ab1b42fba4dcff435c21e260b47457e45ec9'
        self.assertEqual(attribution.qualified_comparison(eleven, attribution.EARLIER_RUNTIME), {'removed_rows': 37519, 'forms': 5413})
        # The removed readings move with the runtime; the lost forms do not.
        self.assertEqual(attribution.qualified_comparison(eleven, current), {'removed_rows': 37868, 'forms': 5413})
        # A combination that no receipt qualified on a runtime is refused before any analysis.
        six = 'f719a4e118195bc0d7696c30121a11495fac21cdfadb70ad95dd378443812463'
        self.assertEqual(attribution.qualified_comparison(six, attribution.EARLIER_RUNTIME)['forms'], 5766)
        for combined, runtime in ((six, current), (eleven, '0' * 64), ('0' * 64, current)):
            with self.assertRaisesRegex(ValueError, 'no qualified baseline comparison'):
                attribution.qualified_comparison(combined, runtime)
        candidate = attribution.sibling('qualify-latin-historical-source-candidate')
        self.assertEqual({runtime for _, runtime in attribution.QUALIFIED_BASELINE_COMPARISON}, set(candidate.ORIGINAL_ROWS))


if __name__ == '__main__':
    unittest.main()
