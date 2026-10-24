#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Native diagnostic of successful source-field isolations, in separate roots."""
import argparse
from collections import Counter
import importlib.util
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('blockers', REPO / 'tools/review-latin-extraction-blockers.py')
blockers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(blockers)
loss, review = blockers.loss, blockers.review
terminal = loss.sibling('probe-latin-terminal-conjugation')
native = loss.sibling('qualify-latin-present-stages')


def revalidate_cases(path, headers, replay, render):
    """Recreate every source isolation, not merely the successful variants."""
    cases, trials, seen = [], [], set()
    for line in path.read_text().splitlines():
        case = json.loads(line)
        if case['lemma'] in seen:
            raise ValueError('duplicate isolated-field source lemma')
        seen.add(case['lemma'])
        header = case['original_header']
        if headers.get(header['id']) != header:
            raise ValueError('isolated-field original header differs from source')
        records, traces = replay(render(header))
        if records or blockers.stage_profiles(header, traces) != case['original_stages']:
            raise ValueError('isolated-field original replay differs')
        variants = blockers.isolated_headers(header)
        if len(variants) != len(case['isolated_source_fields']):
            raise ValueError('isolated-field trial inventory differs')
        for (position, variant), saved in zip(variants, case['isolated_source_fields']):
            if saved['source_field_position'] != position or saved['header'] != variant:
                raise ValueError('isolated-field variant differs from literal source occurrence')
            records, traces = replay(render(variant))
            serial = {key.decode(): [{'line': line.decode(), 'multiplicity': n}
                      for line, n in sorted(lines.items())] for key, lines in sorted(records.items())}
            state = review.replay_state(case['lemma'], records)
            shape = blockers.field_shape(header['fields'][position]['projection'])
            if (saved['filter_traces'] != traces or saved['replay_state'] != state or
                    saved['replayed_definitions'] != serial or saved['source_field_shape'] != shape or
                    saved['stages'] != blockers.stage_profiles(variant, traces)):
                raise ValueError('isolated-field replay differs from qualified dossier')
            if state == 'emits_missing_lemma':
                if set(records) != {case['lemma'].encode()}:
                    raise ValueError('isolated-field trial also emits another lemma')
                trials.append({'lemma': case['lemma'], 'header': header,
                    'source_field_position': position, 'source_field_shape': shape,
                    'lost_readings': case['lost_readings'], 'counterfactual_definitions': records})
        cases.append(case)
    return cases, sorted(trials, key=lambda t: (t['lemma'], t['source_field_position']))


def probe_root(trial, forms, baseline, before, after, output):
    losses = terminal.probe_losses(forms, baseline, before, after, output)
    head = terminal.source_headword_probe(trial, before, after)
    cell = {'person': 1, 'number': 1, 'mood': 4, 'voice': 2 if head['form'].endswith('or') else 1}
    left = before.analyses(head['form'].encode(), require_untruncated=True)
    right = after.analyses(head['form'].encode(), require_untruncated=True)
    counts, profiles, private = terminal.compare_family_routes(left, right, trial['lemma'].encode(), cell)
    output.write(json.dumps({'kind': 'isolated_source_headword', 'lemma': trial['lemma'],
        'source_headword_probe': head, 'route_sensitive_comparison': private}, sort_keys=True) + '\n')
    return {'lost_reading_control': losses,
            'source_headword_control': {k: v for k, v in head.items() if k != 'form'},
            'source_headword_route_control': {'counts': counts,
                'other_added_reading_profiles': terminal.public_reading_profiles(profiles)}}


def private_stream(path):
    return os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                            getattr(os, 'O_NOFOLLOW', 0), 0o600), 'w')


def probe_trial(trial, forms, args, target, original_indexes):
    """Build one isolated full directive, then its literal present expansion."""
    target.mkdir(mode=0o700)
    source = target / 'full.stems'
    native.write_private(source, terminal.candidate_payload(args.candidate_source.read_bytes(), [trial]))
    full_hashes = native.build_trial(args.baseline, source, args.tools, target / 'full-native')
    expanded = loss.definitions(target / 'full-native/Latin/lexical/present-trial.expanded')
    present_trial = terminal.present_cases(expanded, [trial])[0]
    present_source = target / 'present.stems'
    native.write_private(present_source, terminal.candidate_payload(args.candidate_source.read_bytes(), [present_trial]))
    present_hashes = native.build_trial(args.baseline, present_source, args.tools, target / 'present-native')
    present_expanded = loss.definitions(target / 'present-native/Latin/lexical/present-trial.expanded')
    if terminal.expanded_profiles(present_expanded, [trial['lemma']]) != {'present': 1}:
        raise ValueError('isolated-field present trial retains other stem classes')
    for hashes in (full_hashes, present_hashes):
        if any(hashes[name] != original_indexes[name] for name in ('nomind', 'nomind.lindex')):
            raise ValueError('isolated-field trial changes controlled nominal indexes')
    roots = {}
    try:
        for name, root in (('baseline', args.baseline), ('before', args.candidate),
                           ('full', target / 'full-native'), ('present', target / 'present-native')):
            roots[name] = native.NativeRows(args.library, root)
        reports = {}
        with private_stream(target / 'native-probes.jsonl') as output:
            output.write(json.dumps({'kind': 'isolated_field_trial', 'lemma': trial['lemma'],
                'header': trial['header'], 'source_field_position': trial['source_field_position'],
                'full_definitions': {k.decode(): [{'line': line.decode(), 'multiplicity': n}
                    for line, n in sorted(lines.items())] for k, lines in trial['counterfactual_definitions'].items()}}, sort_keys=True) + '\n')
            for name in ('full', 'present'):
                output.write(json.dumps({'kind': 'root_label', 'root': name}) + '\n')
                reports[name] = probe_root(trial, forms, roots['baseline'], roots['before'], roots[name], output)
            comparison = terminal.compare_counterfactuals(forms, roots['full'], roots['present'], output)
    finally:
        for root in reversed(list(roots.values())):
            root.close()
    for name, src, hashes, definitions in (('full', source, full_hashes, expanded),
                                          ('present', present_source, present_hashes, present_expanded)):
        reports[name].update(source_sha256=loss.digest(src), indexes_sha256=hashes,
            expanded_definition_types=terminal.expanded_profiles(definitions, [trial['lemma']]),
            expanded_directive_profiles=terminal.expanded_directive_profiles(definitions, [trial['lemma']]))
    return {'source_field_shape': trial['source_field_shape'], 'target_lost_readings': trial['lost_readings'],
        'full_control': reports['full'], 'present_control': reports['present'],
        'full_to_present_comparison': comparison,
        'private_native_probe_sha256': loss.digest(target / 'native-probes.jsonl')}


def prepare(args):
    for path, expected in ((args.blocker_dossier, args.expected_blocker_sha256),
                           (args.loss_dossier, args.expected_loss_sha256),
                           (args.candidate_source, args.expected_candidate_sha256),
                           (args.candidate / 'Latin/lexical/present-trial.expanded', args.expected_expanded_sha256),
                           (args.baseline / 'Latin/lexical/verb.expanded', args.expected_baseline_expanded_sha256)):
        if loss.digest(path) != expected:
            raise ValueError('qualified isolated-field input receipt differs')
    first = loss.sibling('repair-latin-first-conjugation')
    headers, source, revision = first.source_rows(args.headers, args.lexica)
    recovery = loss.sibling('recover-latin-initial-sense')
    cases, trials = revalidate_cases(args.blocker_dossier, {r['id']: r for r in headers},
        lambda h: review.historical_replay(h, args.filters), recovery.render)
    if len(cases) != args.expected_cases or sum(c['lost_readings'] for c in cases) != args.expected_rows or len(trials) != args.expected_trials:
        raise ValueError('isolated-field cohort differs')
    original_indexes = {name: loss.digest(args.candidate / 'Latin/steminds' / name)
                        for name in ('nomind', 'nomind.lindex', 'vbind', 'vbind.lindex')}
    if terminal.retained_inputs(args.baseline) != terminal.retained_inputs(args.candidate) or any(
            original_indexes[name] != loss.digest(args.baseline / 'Latin/steminds' / name)
            for name in ('nomind', 'nomind.lindex')):
        raise ValueError('isolated-field retained assembly inputs differ')
    target = loss.private_target(args.output, [args.blocker_dossier, args.loss_dossier, args.headers,
        args.lexica, args.candidate_source, args.baseline, args.candidate, args.library, args.tools, args.filters, source])
    if target.exists():
        raise FileExistsError('isolated-field native stage already exists')
    target.mkdir(mode=0o700)
    trial_lemmas = {t['lemma'] for t in trials}
    unique_forms, unique_rows = terminal.target_forms(args.loss_dossier, trial_lemmas)
    expected_unique_rows = sum(c['lost_readings'] for c in cases if c['lemma'] in trial_lemmas)
    if unique_rows != expected_unique_rows:
        raise ValueError('unique isolated-field loss inventory differs')
    reports = []
    for i, trial in enumerate(trials, 1):
        forms, rows = terminal.target_forms(args.loss_dossier, {trial['lemma']})
        if rows != trial['lost_readings']:
            raise ValueError('per-trial isolated-field loss inventory differs')
        reports.append(probe_trial(trial, forms, args, target / ('trial-' + str(i)), original_indexes))
    if any(loss.digest(args.candidate / 'Latin/steminds' / name) != digest for name, digest in original_indexes.items()):
        raise ValueError('isolated-field probe mutated final candidate indexes')
    return {'schema': 1, 'scope': 'separate successful source-field diagnostic trials; no source approval or global qualification',
        'counts': {'reviewed_cases': len(cases), 'successful_trials': len(trials), 'unique_trial_lemmas': len(trial_lemmas),
                   'unique_target_forms': len(unique_forms), 'unique_target_lost_readings': unique_rows},
        'trials': reports, 'final_candidate_indexes_unchanged': True, 'source_revision': revision,
        'input_sha256': {name: loss.digest(path) for name, path in [('blocker_dossier', args.blocker_dossier),
            ('loss_dossier', args.loss_dossier), ('headers', args.headers), ('Latin_TEI', source),
            ('candidate_source', args.candidate_source), ('native_library', args.library)]}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('blocker-dossier', 'loss-dossier', 'headers', 'lexica', 'candidate-source', 'baseline',
                 'candidate', 'library', 'tools', 'filters', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('blocker', 'loss', 'candidate', 'expanded', 'baseline-expanded'):
        parser.add_argument('--expected-' + name + '-sha256', required=True)
    for name in ('cases', 'rows', 'trials'):
        parser.add_argument('--expected-' + name, type=int, required=True)
    previous = os.umask(0o077)
    try:
        report = prepare(parser.parse_args())
    finally:
        os.umask(previous)
    print(json.dumps({'latin_isolated_field_native_probe': report}, sort_keys=True))


if __name__ == '__main__':
    main()
