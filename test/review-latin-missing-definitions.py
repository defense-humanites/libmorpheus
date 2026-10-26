#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('missing', Path(__file__).resolve().parents[1] /
                                           'tools/review-latin-missing-definitions.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def choice(head='zzmissing', category='verbal', kind='3'):
    from lxml import etree
    return {'row': {'headword': head, 'fields': [{'name': 'itype', 'projection': kind}]},
            'entry': etree.fromstring(b'<entryFree><orth extent="full">zzsource</orth></entryFree>'),
            'join_routes': ['projected_key'], 'category': category}


review = SimpleNamespace(partition=SimpleNamespace(classify=lambda r: ('verbal', 'synthetic')),
                         signal=lambda f: 'no_first_sense_verbal_signal', initial_sense_fields=lambda e: [])
dossier = {'lemma': 'zzmissing', 'baseline_definitions': [{'line': ':vs:zzold conj3', 'multiplicity': 1}]}


class MissingDefinitions(unittest.TestCase):
    def case(self, choices, emitted=b'', candidate=None, expanded=None, category='verbal'):
        source_review = SimpleNamespace(**vars(review))
        source_review.partition = SimpleNamespace(classify=lambda r: (category, 'synthetic'))
        return m.review_case(dossier, choices, candidate or {}, expanded or {},
            lambda header: (m.replay_definitions(emitted), [{'stdout': 'private zztrace'}]),
            lambda r: 'private zzheader', source_review)

    def test_no_join_ambiguity_and_literal_identity_remain_separate(self):
        self.assertEqual(self.case({})['review_decision'], 'source_join_required')
        self.assertEqual(self.case({'one': choice(), 'two': choice()})['review_decision'], 'ambiguous_source_identity')
        case = self.case({'one': choice('zzother#2')}, b':le:zzother#2\n:vs:zzstem conj3\n',
                         {b'zzother#2': m.Counter({b':vs:zzstem conj3': 1})})
        self.assertEqual(case['review_decision'], 'literal_lemma_identity_review')
        self.assertEqual(case['articles'][0]['replay_state'], 'emits_only_other_lemmas')
        self.assertTrue(case['articles'][0]['candidate_has_headword_definitions'])
        self.assertFalse(case['articles'][0]['final_has_headword_definitions'])
        self.assertEqual(case['articles'][0]['emitted_headword'], 'zzother#2')

    def test_partition_no_emission_and_isolated_emission_require_different_reviews(self):
        self.assertEqual(self.case({'one': choice()}, category='nominal')['review_decision'], 'nonverbal_partition_review')
        self.assertEqual(self.case({'one': choice()})['review_decision'], 'historical_extraction_review')
        case = self.case({'one': choice()}, b':le:zzmissing\n:vs:zzstem conj3\n')
        self.assertEqual(case['review_decision'], 'isolated_vs_full_pipeline_review')
        self.assertEqual(case['articles'][0]['replay_state'], 'emits_missing_lemma')

    def test_only_bound_stem_directives_count_not_echoed_text_or_empty_blocks(self):
        data = b'zzsource <itype>3</itype>\n:le:zzmissing\nprivate ECHO\n:le:zzother\n:vs:zzstem conj3\n:vs:zzstem conj3\n'
        records = m.replay_definitions(data)
        self.assertEqual(records, {b'zzother': m.Counter({b':vs:zzstem conj3': 2})})
        for bad in (b':le:\n', b':vs:zzstem conj3\n', b':le:zzmissing\n:vs:\n'):
            with self.assertRaises(ValueError): m.replay_definitions(bad)

    def test_public_counts_preserve_multiplicity_and_exclude_all_lexical_evidence(self):
        cases = [(self.case({'one': choice('zzother#2')}), 5), (self.case({}), 2)]
        report = m.summarize(cases)
        self.assertEqual(report['counts'], {'lemmas': 2, 'readings': 7})
        self.assertEqual(sum(g['lemmas'] for g in report['reading_groups']), 2)
        self.assertEqual(sum(g['readings'] for g in report['reading_groups']), 7)
        for value in ('zzmissing', 'zzother', 'zzold', 'zztrace', 'zzheader', 'zzsource'):
            self.assertNotIn(value, json.dumps(report))

    def test_grammar_shapes_are_leads_and_keep_homograph_suffix(self):
        for kind, expected in [('3', 'bare_conjugation_digit'), ('zzperf, zzsup, 3', 'principal_parts_with_conjugation_digit'),
                               ('zze^re', 'infinitive_itype'), ('zzpart', 'other_itype')]:
            c = choice('zzheador#2', kind=kind)
            profile = m.grammar_profile(c['row'], c['entry'], review)
            self.assertEqual(profile['itype_shape'], expected)
            self.assertEqual(profile['headword_shape'], 'deponent_present')
            self.assertEqual(profile['first_orth_extent'], 'full')

    def test_receipt_mismatch_aborts_before_loading_private_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'dossier'; path.write_bytes(b'private zzsource')
            with self.assertRaisesRegex(ValueError, 'receipt differs'):
                m.prepare(SimpleNamespace(dossier=path, expected_dossier_sha256='wrong'))

    def test_private_selection_counts_occurrences_and_rejects_inconsistent_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'dossier'
            values = ['zzform', 'zzmissing', 2, 1, 1, 0, 0, 1, 4, 1, 0]
            form = {'kind': 'lost_form', 'form': 'zzform', 'readings': [{'signature': values}] * 2}
            lemma = dict(dossier, kind='lemma_review', definition_state='no_final_definitions', final_definitions=[])
            path.write_text(json.dumps(form)+'\n'+json.dumps(lemma)+'\n')
            self.assertEqual(m.selected_dossiers(path), [(lemma, 2)])
            for records in ([form], [form, form, lemma], [form, lemma, lemma], [form, dict(lemma, final_definitions=[{}])]):
                path.write_text(''.join(json.dumps(r)+'\n' for r in records))
                with self.assertRaises(ValueError): m.selected_dossiers(path)

    def test_filter_stages_receive_preceding_output_and_private_errors_are_not_exposed(self):
        outputs = [b'zzone', b'zztwo', b'zzthree', b':le:zzmissing\n:vs:zzstem conj3\n']
        result = lambda out: SimpleNamespace(returncode=0, stdout=out, stderr=b'private zzstderr')
        with patch.object(m.subprocess, 'run', side_effect=list(map(result, outputs))) as run:
            records, traces = m.historical_replay('zzheader', Path('/synthetic'))
            self.assertTrue(records[b'zzmissing'])
            self.assertEqual([c.kwargs['input'] for c in run.call_args_list], [b'zzheader', *outputs[:-1]])
            self.assertEqual([t['filter'] for t in traces], list(m.FILTERS))
        failed = SimpleNamespace(returncode=1, stdout=b'private zzstdout', stderr=b'private zzstderr')
        with patch.object(m.subprocess, 'run', return_value=failed):
            with self.assertRaisesRegex(ValueError, '^historical source replay failed$'):
                m.historical_replay('zzheader', Path('/synthetic'))


if __name__ == '__main__': unittest.main()
