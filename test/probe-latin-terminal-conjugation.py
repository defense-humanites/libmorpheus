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
        self.assertEqual(report, {'present': 1, 'perfect': 2, 'supine': 1, 'other': 1})
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


if __name__ == '__main__': unittest.main()
