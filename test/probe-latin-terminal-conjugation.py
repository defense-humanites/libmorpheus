#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
from collections import Counter
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

spec = importlib.util.spec_from_file_location('terminal', Path(__file__).resolve().parents[1] /
                                           'tools/probe-latin-terminal-conjugation.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def reading(lemma=b'zzlemma', tense=1, preverb=b'', person=1, voice=1):
    return SimpleNamespace(workword=b'zzform', lemma=lemma, part_of_speech=2, person=person,
        number=1, gender=0, grammatical_case=0, tense=tense, mood=4, voice=voice, degree=0, preverb=preverb)


class Analyzer:
    def __init__(self, rows): self.values = rows
    def analyses(self, form, require_untruncated=False):
        if not require_untruncated: raise AssertionError('native probes need untruncated fields')
        return self.values


class TerminalConjugation(unittest.TestCase):
    def test_retained_input_comparison_excludes_only_substituted_source_and_binds_other_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); latin = root / 'Latin'
            (latin / 'lexical').mkdir(parents=True); (latin / 'stemsrc').mkdir()
            for name in ('vbs.latin', 'zzone', 'zztwo', 'zzthree'):
                (latin / 'stemsrc' / name).write_text('synthetic ' + name)
            manifest = ''.join('Latin\tverb\tstemsrc/'+name+'\tsynthetic\n' for name in ('vbs.latin', 'zzone', 'zztwo', 'zzthree'))
            (latin / 'lexical/inputs.tsv').write_text(manifest)
            before = m.retained_inputs(root)
            self.assertEqual(len(before), 3)
            (latin / 'stemsrc/vbs.latin').write_text('substituted')
            self.assertEqual(m.retained_inputs(root), before)
            (latin / 'stemsrc/zzone').write_text('changed retained bytes')
            self.assertNotEqual(m.retained_inputs(root), before)
            (latin / 'lexical/inputs.tsv').write_text(manifest + 'Latin\tverb\t../escape\tsynthetic\n')
            with self.assertRaises(ValueError): m.retained_inputs(root)

    def test_only_one_terminal_digit_is_replaced_without_mutating_source_fields(self):
        row = {'headword': 'zzsource', 'fields': [{'name': 'orth', 'projection': 'zzsource'},
            {'name': 'itype', 'projection': 'zzperf, zzsup, 3'}, {'name': 'pos', 'projection': 'v. a.'}]}
        result, digit = m.simplified(row)
        self.assertEqual(digit, 3)
        self.assertEqual(result['fields'][1]['projection'], '3')
        self.assertEqual(row['fields'][1]['projection'], 'zzperf, zzsup, 3')
        self.assertEqual(result['fields'][0], row['fields'][0])
        for fields in ([], [{'name': 'itype', 'projection': '3'}],
                       [{'name': 'itype', 'projection': 'zzperf, 3 or 4'}], row['fields'] + [row['fields'][1]]):
            with self.assertRaises(ValueError): m.simplified(dict(row, fields=fields))

    def test_trace_profile_has_no_lexical_strings_and_preserves_field_and_head_checks(self):
        traces = [{'filter': 'combitype', 'stdout': 'zzsource \t<itype>zzperf, 3</itype>', 'stderr': 'zzprivate'},
                  {'filter': 'conj1', 'stdout': 'zzsource \t<itype>e^re</itype>', 'stderr': ''}]
        profile = m.trace_profile(traces, 'zzperf, 3', 'zzsource')
        self.assertTrue(profile[0]['original_itype_survives'])
        self.assertFalse(profile[1]['original_itype_survives'])
        self.assertEqual([p['itype_fields'] for p in profile], [1, 1])
        self.assertNotIn('zz', json.dumps(profile))

    def test_new_blocks_are_append_only_and_cannot_duplicate_empty_blocks_or_emit_aliases(self):
        old = b':le:zzold\n:vs:zzoldstem conj3\n'
        case = {'lemma': 'zznew', 'counterfactual_definitions': {b'zznew': Counter({b':vs:zznewstem conj3': 2})}}
        result = m.candidate_payload(old, [case])
        self.assertTrue(result.startswith(old))
        self.assertEqual(result[len(old):], b':le:zznew\n:vs:zznewstem conj3\n:vs:zznewstem conj3\n')
        for candidate, records in ((old.rstrip(), [case]), (old+b':le:zznew\n', [case]),
                                   (old, [dict(case, counterfactual_definitions={b'zzalias': Counter({b':vs:zzstem conj3': 1})})])):
            with self.assertRaises(ValueError): m.candidate_payload(candidate, records)
        self.assertEqual(m.candidate_payload(old, [dict(case, counterfactual_definitions={})]), old)

    def test_source_headword_requires_direct_first_person_present_and_keeps_lemma_suffix(self):
        case = {'lemma': 'zzlemma#2', 'header': {'headword': 'zz-le_m^or#2'}}
        direct = reading(b'zzlemma#2', voice=2)
        other = reading(b'zzlemma#2', voice=2, preverb=b'ex')
        report = m.source_headword_probe(case, Analyzer([]), Analyzer([direct, other]))
        self.assertEqual(report['form'], 'zzlemor')
        self.assertEqual(report['after_expected'], 1)
        self.assertEqual(report['added_rows'], 2)
        self.assertEqual(m.source_headword_probe(case, Analyzer([]), Analyzer([reading(b'zzlemma#2', voice=1)]))['after_expected'], 0)

    def test_native_loss_probe_reproduces_witness_multiplicity_and_compares_exact_signatures(self):
        old = reading(); changed = reading(tense=2)
        forms = {b'zzform': Counter({m.loss.signature(old): 2})}
        output = io.StringIO()
        report = m.probe_losses(forms, Analyzer([old, old]), Analyzer([]), Analyzer([old, changed]), output)
        self.assertEqual(report['counts'], {'forms': 1, 'recognized_counterfactual_forms': 1,
            'expected_lost_readings': 2, 'recovered_exact_readings': 1, 'still_missing_exact_readings': 1,
            'other_counterfactual_readings': 1})
        self.assertNotIn('zz', json.dumps(report))
        self.assertIn('zzform', output.getvalue())
        for baseline, before in (([old], []), ([old, old], [old])):
            with self.assertRaises(ValueError):
                m.probe_losses(forms, Analyzer(baseline), Analyzer(before), Analyzer([]), io.StringIO())

    def test_target_inventory_counts_only_selected_literal_lemmas(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'losses'
            values = [m.loss.decoded(v) for v in m.loss.signature(reading())]
            other = list(values); other[1] = 'zzother'
            form = {'kind': 'lost_form', 'form': 'zzform', 'readings': [{'signature': values}] * 2 + [{'signature': other}]}
            path.write_text(json.dumps(form)+'\n'+json.dumps({'kind': 'lemma_review'})+'\n')
            forms, rows = m.target_forms(path, {'zzlemma'})
            self.assertEqual(rows, 2)
            self.assertEqual(forms, {b'zzform': Counter({m.loss.signature(reading()): 2})})
            path.write_text(json.dumps(form)+'\n'+json.dumps(form)+'\n')
            with self.assertRaises(ValueError): m.target_forms(path, {'zzlemma'})

    def test_expansion_report_exposes_regular_past_extrapolation_as_aggregates(self):
        records = {b'zzlemma': Counter({b':vs:zzroot conj3': 1, b':vs:zzperf perfstem': 2,
                   b':vs:zzsup pp4': 1, b':wd:zzword other': 1})}
        report = m.expanded_profiles(records, ['zzlemma'])
        self.assertEqual(report, {'present': 1, 'perfect': 2, 'supine': 1, 'literal_word': 1})
        self.assertNotIn('zz', json.dumps(report))

    def test_review_selection_keeps_only_qualified_principal_part_dossiers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'review'
            article = {'partition': 'verbal', 'headword_identity': 'same_literal_lemma', 'replay_state': 'emits_no_definitions',
                'grammar_profile': {'itype_shape': 'principal_parts_with_conjugation_digit', 'first_orth_extent': 'full'}}
            case = {'lemma': 'zzlemma', 'review_decision': 'historical_extraction_review', 'articles': [article]}
            path.write_text(json.dumps(case)+'\n')
            self.assertEqual(m.select_cases(path), [case])
            for rows in ([case, case], [dict(case, articles=[dict(article, headword_identity='different_literal_lemma')])]):
                path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
                with self.assertRaises(ValueError): m.select_cases(path)

    def test_regular_perfect_aliases_are_not_unknown_or_present(self):
        for tag in (b'avperf', b'evperf', b'ivperf', b'perfstem'):
            self.assertEqual(m.definition_type(b':vs:zzstem ' + tag), 'perfect')
            with self.assertRaises(ValueError): m.definition_type(b':vs:zzstem conj1 ' + tag)

    def test_derivatives_and_literal_words_are_distinct_from_explicit_stem_classes(self):
        self.assertEqual(m.definition_type(b':de:zzroot are_vb'), 'derivation')
        self.assertEqual(m.definition_type(b':vb:zzword perf act 1st sg'), 'literal_verbal_word')
        self.assertEqual(m.definition_type(b':wd:zzword unknown'), 'literal_word')
        self.assertEqual(m.definition_type(b':vs:conj1 unknown'), 'other')
        profiles = m.expanded_directive_profiles({b'zzlemma': Counter({
            b':de:zzprivate are_vb zzsecret': 2, b':vs:zzstem conj3': 1,
            b':vb:zzword perf act 1st sg': 1})}, ['zzlemma'])
        self.assertEqual(profiles[0], {'directive': ':de:', 'definition_type': 'derivation',
            'declared_classes': ('are_vb',), 'rows': 2})
        self.assertNotIn('zz', json.dumps(profiles))

    def test_direct_comparison_preserves_multiplicity_and_detects_equal_count_target_substitution(self):
        old = reading(); other = reading(tense=5)
        forms = {b'zzform': Counter({m.loss.signature(old): 2})}
        report = m.compare_counterfactuals(forms, Analyzer([old, old, other]), Analyzer([old, old]), io.StringIO())
        self.assertTrue(report['same_exact_target_recoveries'])
        self.assertTrue(report['present_multisets_included_in_full'])
        self.assertEqual(report['counts']['removed_rows'], 1)
        self.assertEqual(report['counts']['retained_rows'], 2)
        self.assertEqual(report['removed_readings_by_tense'], [{'tense': 5, 'rows': 1}])
        self.assertNotIn('zz', json.dumps(report))
        report = m.compare_counterfactuals(forms, Analyzer([old, old]), Analyzer([old, other]), io.StringIO())
        self.assertFalse(report['same_exact_target_recoveries'])
        self.assertFalse(report['present_multisets_included_in_full'])
        self.assertEqual(report['counts']['target_recoveries_removed'], 1)
        self.assertEqual(report['counts']['added_rows'], 1)

    def test_source_families_use_headword_and_digit_with_distinct_infinitives_and_voices(self):
        for head, digit, second, infinitive, voice in (
            ('zzrootzo', 1, 'zzrootzas', 'zzrootzare', 1),
            ('zzrootzo', 3, 'zzrootzis', 'zzrootzere', 1),
            ('zzrootzio', 3, 'zzrootzis', 'zzrootzere', 1),
            ('zzrootzio', 4, 'zzrootzis', 'zzrootzire', 1),
            ('zzrootzor', 1, 'zzrootzaris', 'zzrootzari', 2),
            ('zzrootzor', 3, 'zzrootzeris', 'zzrootzi', 2),
            ('zzrootzior', 3, 'zzrootzeris', 'zzrootzi', 2),
            ('zzrootzior', 4, 'zzrootziris', 'zzrootziri', 2)):
            cells = m.source_present_family({'header': {'headword': head+'#2'}, 'digit': digit})
            self.assertEqual(len(cells), 13)
            self.assertEqual(cells[0]['form'], head)
            self.assertEqual(cells[1]['form'], second)
            self.assertEqual(cells[-1], {'form': infinitive, 'person': 0, 'number': 0, 'mood': 5, 'voice': voice})
            self.assertEqual({(c['person'], c['number'], c['mood']) for c in cells},
                {(person, number, mood) for mood in (4,8) for number in (1,3) for person in (1,2,3)} | {(0,0,5)})
        for head, digit in (('zzrootzo', 4), ('zzrootzo', 2), ('zz rootzo', 3), ('o', 1)):
            with self.assertRaises(ValueError): m.source_present_family({'header': {'headword': head}, 'digit': digit})

    def test_present_isolation_preserves_literal_directive_without_derivative_or_past(self):
        case = {'lemma': 'zzlemma', 'header': {'headword': 'zzlemma'}}
        present = b':vs:zzroot conj3_io dep'
        expanded = {b'zzlemma': Counter({present: 1, b':vs:zzperf ivperf': 1,
                                       b':vs:zzsup pp4': 1, b':wd:zzword unknown': 1})}
        selected = m.present_cases(expanded, [case])
        self.assertEqual(selected[0]['counterfactual_definitions'], {b'zzlemma': Counter({present: 1})})
        self.assertEqual(case, {'lemma': 'zzlemma', 'header': {'headword': 'zzlemma'}})
        for records in ({}, {present: 2}, {present: 1, b':vs:zzother conj3': 1},
                        {b':de:zzroot conj3': 1}, {b':vs:zzperf ivperf': 1}):
            with self.assertRaises(ValueError): m.present_cases({b'zzlemma': Counter(records)}, [case])


if __name__ == '__main__': unittest.main()
