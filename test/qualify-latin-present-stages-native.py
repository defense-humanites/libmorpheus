#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exercise the replay with real native indexes and synthetic source notices."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/qualify-latin-present-stages.py'
spec = importlib.util.spec_from_file_location('qualification', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
global_spec = importlib.util.spec_from_file_location('global_readings', SCRIPT.with_name('audit-latin-global-readings.py'))
g = importlib.util.module_from_spec(global_spec)
global_spec.loader.exec_module(g)
loss_spec = importlib.util.spec_from_file_location('losses', SCRIPT.with_name('diagnose-latin-lost-stems.py'))
losses = importlib.util.module_from_spec(loss_spec)
loss_spec.loader.exec_module(losses)
BUILD = Path(sys.argv.pop(1)).resolve()
BASELINE = BUILD / 'stemlib-production/latin'
LIBRARY = BUILD / ('libmorpheus.dylib' if sys.platform == 'darwin' else 'libmorpheus.so')


class NativeQualification(unittest.TestCase):
    def test_source_present_families_cover_active_and_deponent_conjugations(self):
        terminal_spec = importlib.util.spec_from_file_location('terminal_families', SCRIPT.with_name('probe-latin-terminal-conjugation.py'))
        terminal = importlib.util.module_from_spec(terminal_spec)
        terminal_spec.loader.exec_module(terminal)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases, blocks = [], []
            for letter, digit, tag, passive in (
                ('b', 1, 'conj1', False), ('c', 3, 'conj3', False),
                ('d', 3, 'conj3_io', False), ('f', 4, 'conj4', False),
                ('g', 1, 'conj1', True), ('h', 3, 'conj3', True),
                ('k', 3, 'conj3_io', True), ('l', 4, 'conj4', True)):
                stem = 'zzfamily' + letter + 'z'
                head = stem + ('io' if tag in ('conj3_io', 'conj4') else 'o') + ('r' if passive else '')
                cases.append({'lemma': head+'#2', 'header': {'headword': head+'#2'}, 'digit': digit})
                blocks.append(':le:'+head+'#2\n:vs:'+stem+' '+tag+(' dep' if passive else '')+'\n')
            source = root / 'families.stems'; source.write_text(''.join(blocks))
            m.build_trial(BASELINE, source, BUILD, root / 'trial')
            before = m.NativeRows(LIBRARY, BASELINE)
            after = m.NativeRows(LIBRARY, root / 'trial')
            try:
                report = terminal.probe_present_families(cases, before, after, io.StringIO())
                self.assertEqual(report['counts']['cells'], 104)
                self.assertEqual(report['counts']['before_covered'], 0)
                self.assertEqual(report['counts']['after_covered'], 104)
                self.assertEqual(report['counts']['removed_rows'], 0)
                self.assertEqual(report['counts']['added_expected_rows'], 104)
                self.assertEqual(report['counts']['added_other_rows'],
                    sum(row['rows'] for row in report['other_added_reading_profiles']))
                routes=report['route_sensitive_comparison']['counts']
                self.assertEqual(routes['added_expected_rows'],104)
                self.assertEqual(routes['removed_rows'],0)
                self.assertEqual(routes['added_native_preverb_rows'],0)
            finally:
                after.close(); before.close()

    def test_present_isolation_rebuilds_without_regular_perfect_alias(self):
        terminal_spec = importlib.util.spec_from_file_location('terminal_isolation', SCRIPT.with_name('probe-latin-terminal-conjugation.py'))
        terminal = importlib.util.module_from_spec(terminal_spec)
        terminal_spec.loader.exec_module(terminal)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'full.stems'
            source.write_bytes(b':le:zzsourcezo\n:vs:zzsourcez conj3\n:vs:zzpastz avperf\n')
            m.build_trial(BASELINE, source, BUILD, root / 'full')
            expanded = losses.definitions(root / 'full/Latin/lexical/present-trial.expanded')
            cases = terminal.present_cases(expanded, [{'lemma': 'zzsourcezo'}])
            isolated = root / 'present.stems'
            isolated.write_bytes(terminal.candidate_payload(b'', cases))
            m.build_trial(BASELINE, isolated, BUILD, root / 'present')
            profile = terminal.expanded_profiles(losses.definitions(root / 'present/Latin/lexical/present-trial.expanded'), ['zzsourcezo'])
            self.assertEqual(profile, {'present': 1})
            full = m.NativeRows(LIBRARY, root / 'full')
            present = m.NativeRows(LIBRARY, root / 'present')
            try:
                self.assertTrue(any(r.lemma == b'zzsourcezo' for r in full.analyses(b'zzpastzavi', require_untruncated=True)))
                self.assertFalse(any(r.lemma == b'zzsourcezo' for r in present.analyses(b'zzpastzavi', require_untruncated=True)))
                self.assertTrue(any(r.lemma == b'zzsourcezo' for r in present.analyses(b'zzsourcezo', require_untruncated=True)))
            finally:
                present.close(); full.close()

    def test_terminal_conjugation_counterfactual_uses_source_headword_and_exact_lost_signature(self):
        terminal_spec = importlib.util.spec_from_file_location('terminal', SCRIPT.with_name('probe-latin-terminal-conjugation.py'))
        terminal = importlib.util.module_from_spec(terminal_spec)
        terminal_spec.loader.exec_module(terminal)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, source_text in [('missing', ':le:zzunrelated\n:vs:zzotherz conj3\n'),
                                     ('supplied', ':le:zzsourcezo\n:vs:zzsourcez conj3\n')]:
                source = root / (name + '.stems'); source.write_text(source_text)
                m.build_trial(BASELINE, source, BUILD, root / name)
            before = m.NativeRows(LIBRARY, root / 'missing')
            after = m.NativeRows(LIBRARY, root / 'supplied')
            try:
                case = {'lemma': 'zzsourcezo', 'header': {'headword': 'zzsourcezo'}}
                probe = terminal.source_headword_probe(case, before, after)
                self.assertEqual(probe['before_expected'], 0)
                self.assertEqual(probe['after_expected'], 1)
                expected = terminal.Counter(map(losses.signature, after.analyses(b'zzsourcezo', require_untruncated=True)))
                report = terminal.probe_losses({b'zzsourcezo': expected}, after, before, after, io.StringIO())
                self.assertEqual(report['counts']['recovered_exact_readings'], sum(expected.values()))
                self.assertEqual(report['counts']['still_missing_exact_readings'], 0)
            finally:
                after.close(); before.close()

    def test_complete_loss_reprobes_native_stem_and_expanded_definitions(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for name,stem in [('before','zzstemz'),('after','zzotherz')]:
                source=root/(name+'.stems')
                source.write_text(':le:zzlemma\n:vs:'+stem+' conj3\n')
                m.build_trial(BASELINE,source,BUILD,root/name)
            forms=root/'forms'; forms.write_bytes(b'zzstemzo\n')
            left=m.NativeRows(LIBRARY,root/'before'); right=m.NativeRows(LIBRARY,root/'after')
            try:
                g.audit(forms,left,right,root/'diff')
                output=io.StringIO()
                report=losses.diagnose(root/'diff',left,right,
                    losses.definitions(root/'before/Latin/lexical/present-trial.expanded'),
                    losses.definitions(root/'after/Latin/lexical/present-trial.expanded'),
                    {b'zzlemma'},set(),{},output,lambda x:x)
            finally:
                right.close(); left.close()
            self.assertEqual(report['counts'],{'forms':1,'readings':1,'distinct_lemmas':1,'nonverbal_readings':0})
            self.assertEqual(report['stem_matches_by_readings'],{'baseline_exact__final_no_exact':1})
            self.assertEqual(report['definition_states']['lemmas'],{'changed_definition_multisets':1})
            self.assertEqual(json.loads(output.getvalue().splitlines()[0])['readings'][0]['stem'],'zzstemz')

    def test_global_comparison_detects_equal_count_lemma_change_with_real_api(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, lemma in [('before','zzbefore'),('after','zzafter')]:
                source=root/(name+'.stems')
                source.write_text(':le:'+lemma+'\n:vs:zzstemz conj3\n')
                m.build_trial(BASELINE,source,BUILD,root/name)
            forms=root/'forms'; forms.write_bytes(b'zzstemzo\n')
            left=m.NativeRows(LIBRARY,root/'before')
            try:
                right=m.NativeRows(LIBRARY,root/'after')
                try:
                    report=g.audit(forms,left,right,root/'private',g.source_lemmas(root/'after.stems'))
                finally: right.close()
            finally: left.close()
            self.assertEqual(report['changed_analysis_counts'],0)
            self.assertEqual(report['changed_grammatical_multisets'],1)
            self.assertEqual(report['changed_multisets_at_equal_counts'],1)
            self.assertEqual(report['global_eleven_field_multisets']['removed_rows'],1)
            self.assertEqual(report['global_eleven_field_multisets']['added_rows'],1)

    def witness(self, lemma, candidate):
        return {'schema': 1, 'lemma': lemma,
                'source_revision': '56061ca127f4a2844980baffc5f2b6d1332897b3',
                'source_sha256': 'ccbd2f79db1006edc607fe51227babab6872fbdaa4e925f4c1999a3b978041ee',
                'candidate_sha256': m.digest(candidate), 'headers_sha256': 'synthetic-headers'}

    def test_native_quote_covers_new_and_preexisting_direct_passive_readings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'source'
            source.write_bytes(b':le:zzlemma\n:vs:zzalternz conj3 orth\n')
            m.build_trial(BASELINE, source, BUILD, root/'trial')
            row = dict(self.witness('zzlemma', source), form='zzalternzitur')
            witness = root/'witness'; witness.write_text(json.dumps(row)+'\n')
            for name, before, covered in [('new', BASELINE, 0), ('existing', root/'trial', 1)]:
                report = m.source_quote_control(witness, LIBRARY, before, root/'trial', root/name,
                                                {b'zzlemma'}, m.digest(source), 'synthetic-headers')
                self.assertEqual(report['counts']['before_covered'], covered)
                self.assertEqual(report['counts']['after_covered'], 1)
                self.assertEqual(report['counts']['removed_rows'], 0)

    def test_native_active_families_cover_both_class_three_subclasses(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'source'
            source.write_bytes(b':le:zzlemmaa\n:vs:zzalternz conj3 orth\n:le:zzlemmab\n:vs:zzalternb conj3_io orth\n')
            m.build_trial(BASELINE, source, BUILD, root/'trial')
            records = []
            for io, lemma, stem in [(False, 'zzlemmaa', 'zzalternz'), (True, 'zzlemmab', 'zzalternb')]:
                forms = []
                for mood, endings in [(4, ['io' if io else 'o', 'is', 'it', 'imus', 'itis', 'iunt' if io else 'unt']),
                                      (8, ['iam', 'ias', 'iat', 'iamus', 'iatis', 'iant'] if io else ['am', 'as', 'at', 'amus', 'atis', 'ant'])]:
                    for i, suffix in enumerate(endings):
                        forms.append({'form': stem+suffix, 'person': i % 3 + 1, 'number': 1 if i < 3 else 3, 'mood': mood})
                forms.append({'form': stem+'ere', 'person': 0, 'number': 0, 'mood': 5})
                records.append(dict(self.witness(lemma, source), forms=forms))
            witness = root/'witness'; witness.write_text(''.join(json.dumps(row)+'\n' for row in records))
            report = m.source_family_control(witness, LIBRARY, BASELINE, root/'trial', root/'output',
                                              {b'zzlemmaa', b'zzlemmab'}, m.digest(source), 'synthetic-headers')
            self.assertEqual(report['counts']['before_covered'], 0)
            self.assertEqual(report['counts']['after_covered'], 26)
            self.assertEqual(report['counts']['removed_rows'], 0)

    def test_controlled_source_replays_exact_indexes_and_abi_readings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hashes = m.build_trial(BASELINE, BASELINE / 'Latin/stemsrc/vbs.latin', BUILD, root / 'trial')
            self.assertEqual(hashes, {name: m.digest(BASELINE / 'Latin/steminds' / name) for name in hashes})
            self.assertFalse(list((root / 'trial').glob('MORPHEUS-*')))
            forms = root / 'forms'
            forms.write_bytes(b'amo\namat\nest\n')
            result = m.comparison(forms, LIBRARY, BASELINE, root / 'trial', root / 'difference.jsonl', {b'amo'})
            self.assertEqual(result['changed_analysis_counts'], 0)
            native = m.NativeRows(LIBRARY, BASELINE)
            try:
                self.assertTrue(any(row[1] == b'amo' for row, _ in native.rows(b'amat')))
            finally:
                native.close()

    def test_staged_insertions_and_all_five_comparisons(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root / 'stages'
            stage.mkdir()
            letters = 'bcdfghklmnpqrsz'
            def block(letter, extra=False):
                return (f':le:zzlemma{letter}\n:vs:zzroot{letter} conj3\n' +
                        (f':vs:zzalternate{letter}\tconj3 orth\n' if extra else ''))
            inputs = {'cited-future-imperative': ''.join(block(c) for c in letters).encode(),
                      'boundary-present': ''.join(block(c, i < 11) for i, c in enumerate(letters)).encode(),
                      'vowel-present': ''.join(block(c, True) for c in letters).encode()}
            for name, data in inputs.items():
                (stage / ('verbal-letters-only-' + name + '.stems')).write_bytes(data)
            (stage / 'verbal-all-vowel-present.stems').write_bytes(inputs['vowel-present'])
            forms = root / 'forms'
            forms.write_bytes(b'zzrootbo\nzzalternatebo\nzzalternatezo\nest\n')
            with contextlib.redirect_stdout(io.StringIO()):
                report = m.qualify(forms, LIBRARY, BASELINE, stage, BUILD, root / 'output', 4,
                                   include_global_readings=True)
            for name in ('boundary-step', 'vowel-step'):
                rows = report['comparisons'][name]['changed_form_eleven_field_multisets']
                self.assertGreater(rows['direct_source_verb'], 0)
                self.assertEqual(rows['removed_rows'], 0)
            for name in ('boundary-control', 'vowel-control'):
                self.assertEqual(report['comparisons'][name]['changed_analysis_counts'], 0)
            self.assertEqual(len(report['comparisons']), 5)
            global_control=report['global_comparisons']['final-global-control']
            self.assertEqual(global_control['changed_grammatical_multisets'],0)
            global_delta=report['global_comparisons']['baseline-to-final-global']
            self.assertEqual(global_delta['counts']['absent_curated__recognized_rebuilt'],3)
            multisets=global_delta['global_eleven_field_multisets']
            self.assertEqual(multisets['retained_rows']+multisets['removed_rows'],
                             global_delta['analysis_rows']['curated'])
            self.assertEqual(multisets['retained_rows']+multisets['added_rows'],
                             global_delta['analysis_rows']['rebuilt'])
            self.assertEqual((root / 'output').stat().st_mode & 0o777, 0o700)
            self.assertEqual((root / 'output/report.json').stat().st_mode & 0o777, 0o600)


if __name__ == '__main__':
    unittest.main()
