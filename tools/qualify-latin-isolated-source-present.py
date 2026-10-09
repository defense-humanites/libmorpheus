#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Qualify a source-digit present trial, preserving all original field evidence."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import importlib.util

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('isolated', REPO / 'tools/probe-latin-isolated-fields.py')
isolated = importlib.util.module_from_spec(spec)
spec.loader.exec_module(isolated)
loss, terminal, native = isolated.loss, isolated.terminal, isolated.native
global_readings = loss.sibling('audit-latin-global-readings')


class StrictRows(native.NativeRows):
    def rows(self, word):
        return [(loss.signature(row), row.preverb) for row in self.analyses(word, require_untruncated=True)]


def select_source_trial(trials, entries, expected_digit):
    choices = []
    for i, trial in enumerate(trials, 1):
        if trial['source_field_shape'] != 'bare_conjugation_digit':
            continue
        header = trial['header']
        value = header['fields'][trial['source_field_position']]['projection']
        if not re.fullmatch(r'[1-4]', value or ''):
            raise ValueError('source present field is not a literal conjugation digit')
        digits = []
        for field in header['fields']:
            if field['name'] == 'itype':
                match = re.search(r'(?:^|,\s*)([1-4])$', field['projection'] or '')
                if match:
                    digits.append(int(match[1]))
        bare = [f for f in header['fields'] if f['name'] == 'itype' and re.fullmatch(r'[1-4]', f['projection'] or '')]
        digit = int(value)
        if len(bare) != 1 or set(digits) != {digit} or digit != expected_digit:
            raise ValueError('source present conjugation is ambiguous or conflicts')
        first = entries[header['id']].find('orth')
        head = header['headword'].translate(str.maketrans('', '', '_^-'))
        if first is None or first.get('extent') != 'full' or head != trial['lemma']:
            raise ValueError('source present lacks full literal headword identity')
        selected = dict(trial, digit=digit)
        terminal.source_present_family(selected)  # Validate source morphology independently.
        choices.append((i, selected))
    if len(choices) != 1:
        raise ValueError('source present needs exactly one supported source-digit trial')
    return choices[0]


def changed_route_review(path, before, after, lemma, output):
    counts, profiles = Counter(), Counter()
    for line in path.read_text().splitlines():
        row = json.loads(line)
        word = row['form'].encode('ascii')
        left = before.analyses(word, require_untruncated=True)
        right = after.analyses(word, require_untruncated=True)
        old, new = Counter(map(terminal.route_signature, left)), Counter(map(terminal.route_signature, right))
        # Reproduce the saved eleven-field delta before reviewing decomposition.
        if (global_readings.serialized(Counter(map(loss.signature, left)) - Counter(map(loss.signature, right))) != row['removed'] or
                global_readings.serialized(Counter(map(loss.signature, right)) - Counter(map(loss.signature, left))) != row['added']):
            raise ValueError('changed-form grammatical reanalysis differs')
        counts['changed_forms_reviewed'] += 1
        counts['removed_rows'] += sum((old-new).values())
        counts['added_rows'] += sum((new-old).values())
        for sig, n in (new-old).items():
            key = (sig[2], sig[7], 'native_preverb' if sig[11] else 'direct',
                   'selected_source_lemma' if sig[1] == lemma else 'other_lemma')
            profiles[key] += n
        def serial(counter):
            return [{'signature': [loss.decoded(v) for v in sig], 'multiplicity': n} for sig, n in sorted(counter.items())]
        output.write(json.dumps({'form': row['form'], 'removed': serial(old-new), 'added': serial(new-old)}, sort_keys=True) + '\n')
    return {'scope': 'extended decomposition on forms with an eleven-field change only; not a global sixteen-field audit',
        'counts': dict(sorted(counts.items())), 'added_profiles': global_readings.grouped(profiles,
            ('part_of_speech', 'tense', 'provenance', 'lemma_relation'))}


def prepare(args):
    if loss.digest(args.blocker_dossier) != args.expected_blocker_sha256 or loss.digest(args.forms) != args.expected_forms_sha256:
        raise ValueError('source-present input receipt differs')
    first = loss.sibling('repair-latin-first-conjugation')
    headers, source, revision = first.source_rows(args.headers, args.lexica)
    recovery = loss.sibling('recover-latin-initial-sense')
    _, trials = isolated.revalidate_cases(args.blocker_dossier, {r['id']: r for r in headers},
        lambda h: isolated.review.historical_replay(h, args.filters), recovery.render)
    entries, checked_source, checked_revision = first.review.load_entries(args.lexica)
    if source != checked_source or revision != checked_revision:
        raise ValueError('source changed during present qualification')
    index, trial = select_source_trial(trials, entries, args.expected_digit)
    del entries
    root = args.native_trials / ('trial-' + str(index))
    checks = [(root / 'native-probes.jsonl', args.expected_probe_sha256),
              (root / 'present.stems', args.expected_source_sha256),
              (root / 'present-native/Latin/steminds/vbind', args.expected_vbind_sha256),
              (root / 'present-native/Latin/steminds/vbind.lindex', args.expected_vside_sha256),
              (args.candidate_source, args.expected_candidate_sha256)]
    if any(loss.digest(p) != h for p, h in checks):
        raise ValueError('qualified source-present native receipt differs')
    original_indexes = {name: loss.digest(args.candidate / 'Latin/steminds' / name)
                        for name in ('nomind', 'nomind.lindex', 'vbind', 'vbind.lindex')}
    present_root = root / 'present-native'
    if terminal.retained_inputs(present_root) != terminal.retained_inputs(args.candidate) or any(
            loss.digest(present_root / 'Latin/steminds' / name) != original_indexes[name] for name in ('nomind', 'nomind.lindex')):
        raise ValueError('source present changes retained inputs or nominal indexes')
    # Bind the received source to an insertion of only the qualified literal present.
    expanded = loss.definitions(root / 'full-native/Latin/lexical/present-trial.expanded')
    present_case = terminal.present_cases(expanded, [trial])[0]
    if (root / 'present.stems').read_bytes() != terminal.candidate_payload(args.candidate_source.read_bytes(), [present_case]):
        raise ValueError('source present is not the qualified insertion-only payload')
    if terminal.expanded_profiles(loss.definitions(present_root / 'Latin/lexical/present-trial.expanded'), [trial['lemma']]) != {'present': 1}:
        raise ValueError('source present retains another stem class')
    target = loss.private_target(args.output, [args.blocker_dossier, args.forms, args.headers, args.lexica,
        args.filters, args.native_trials, args.candidate_source, args.candidate, args.library, source])
    if target.exists():
        raise FileExistsError('source-present qualification stage exists')
    target.mkdir(mode=0o700)
    roots = {}
    try:
        roots['before'] = StrictRows(args.library, args.candidate)
        roots['after'] = StrictRows(args.library, present_root)
        with isolated.private_stream(target / 'source-family.jsonl') as stream:
            family = terminal.probe_present_families([trial], roots['before'], roots['after'], stream)
        control = global_readings.audit(args.forms, roots['after'], roots['after'], target / 'global-control.jsonl', require_identical=True)
        delta = global_readings.audit(args.forms, roots['before'], roots['after'], target / 'global-delta.jsonl',
                                     global_readings.source_lemmas(root / 'present.stems'))
        for report in (control, delta):
            if report['counts']['distinct_forms'] != args.expected_forms or report['input_sha256'] != args.expected_forms_sha256:
                raise ValueError('source-present global input scope differs')
        with isolated.private_stream(target / 'changed-routes.jsonl') as stream:
            routes = changed_route_review(target / 'global-delta.jsonl', roots['before'], roots['after'], trial['lemma'].encode(), stream)
    finally:
        for reader in reversed(list(roots.values())):
            reader.close()
    if any(loss.digest(args.candidate / 'Latin/steminds' / name) != h for name, h in original_indexes.items()):
        raise ValueError('source-present qualification mutated final indexes')
    return {'schema': 1, 'scope': 'source-backed explicit present trial; no past reconstruction or production replacement',
        'source_conjugation_digit': trial['digit'], 'source_present_family_control': family,
        'global_control': control, 'global_delta': delta, 'changed_form_route_review': routes,
        'final_candidate_indexes_unchanged': True, 'source_revision': revision,
        'private_family_sha256': loss.digest(target / 'source-family.jsonl'),
        'private_routes_sha256': loss.digest(target / 'changed-routes.jsonl'),
        'source_sha256': loss.digest(root / 'present.stems')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('blocker-dossier', 'forms', 'headers', 'lexica', 'filters', 'native-trials',
                 'candidate-source', 'candidate', 'library', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('blocker', 'forms', 'probe', 'source', 'vbind', 'vside', 'candidate'):
        parser.add_argument('--expected-' + name + '-sha256', required=True)
    parser.add_argument('--expected-digit', type=int, required=True)
    parser.add_argument('--expected-forms', type=int, required=True)
    previous = os.umask(0o077)
    try:
        report = prepare(parser.parse_args())
    finally:
        os.umask(previous)
    print(json.dumps({'latin_isolated_source_present_qualification': report}, sort_keys=True))


if __name__ == '__main__':
    main()
