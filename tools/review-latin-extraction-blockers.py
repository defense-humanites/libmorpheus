#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Locate extraction blockers in eight source-backed missing-definition cases.

All lexical evidence remains private. Field isolation is a diagnostic, not a
replacement source header or permission to insert the resulting definitions.
"""
import argparse
from collections import Counter
import importlib.util
import json
import os
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('missing', REPO / 'tools/review-latin-missing-definitions.py')
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
loss = review.loss
SHAPES = frozenset(('multiple_itypes', 'no_itype', 'other_itype', 'infinitive_itype'))


def field_shape(value):
    if not value:
        return 'empty'
    if re.fullmatch(r'[1-4]', value):
        return 'bare_conjugation_digit'
    if re.search(r'(?:^|,\s*)[1-4]$', value):
        return 'principal_parts_with_conjugation_digit'
    if re.fullmatch(r'[A-Za-z_^]+r[ei]', value):
        return 'infinitive_spelling'
    return 'other_field_structure'


def select_cases(path):
    selected, seen = [], set()
    for line in path.read_text().splitlines():
        case = json.loads(line)
        if case['lemma'] in seen:
            raise ValueError('duplicate extraction-blocker lemma')
        seen.add(case['lemma'])
        if case['review_decision'] != 'historical_extraction_review' or len(case['articles']) != 1:
            continue
        article = case['articles'][0]
        if article['grammar_profile']['itype_shape'] not in SHAPES:
            continue
        if (article['partition'] != 'verbal' or article['headword_identity'] != 'same_literal_lemma' or
                article['replay_state'] != 'emits_no_definitions' or
                article['candidate_has_headword_definitions'] or article['final_has_headword_definitions']):
            raise ValueError('extraction-blocker scope differs')
        selected.append(case)
    return sorted(selected, key=lambda c: c['lemma'])


def isolated_headers(header):
    """Keep one original itype occurrence; retain every other field verbatim."""
    positions = [i for i, f in enumerate(header['fields']) if f['name'] == 'itype']
    if len(positions) < 2:
        return []
    return [(position, dict(header, fields=[dict(f) for i, f in enumerate(header['fields'])
                                           if f['name'] != 'itype' or i == position]))
            for position in positions]


def stage_profiles(header, traces):
    if [t['filter'] for t in traces] != list(review.FILTERS):
        raise ValueError('unexpected extraction filter sequence')
    source = Counter(f['projection'] or '' for f in header['fields'] if f['name'] == 'itype')
    stages = []
    for trace in traces:
        text = trace['stdout']
        types = Counter(re.findall(r'<itype>([^<>]*)</itype>', text))
        shapes = Counter()
        for value, n in types.items():
            shapes[field_shape(value)] += n
        # Compare literal field values with multiplicity, not substring presence.
        records = review.replay_definitions(text.encode())
        prefixes = Counter()
        for lines in records.values():
            for line, n in lines.items():
                prefixes[line[:4].decode()] += n
        stages.append({'filter': trace['filter'],
            'source_itype_occurrences_retained': sum((source & types).values()),
            'output_itype_occurrences': sum(types.values()),
            'output_itype_shapes': dict(sorted(shapes.items())),
            'headword_prefix_preserved': text.startswith(header['headword'] + ' '),
            'emitted_stem_directives': dict(sorted(prefixes.items())),
            'stderr_present': bool(trace['stderr'])})
    return stages


def inspect_case(case, replay, render):
    article = case['articles'][0]
    header = article['header']
    records, traces = replay(render(header))
    if traces != article['filter_traces'] or review.replay_state(case['lemma'], records) != article['replay_state']:
        raise ValueError('original extraction replay differs from qualified review')
    isolated = []
    for position, variant in isolated_headers(header):
        emitted, variant_traces = replay(render(variant))
        isolated.append({'source_field_position': position,
            'source_field_shape': field_shape(header['fields'][position]['projection']),
            'replay_state': review.replay_state(case['lemma'], emitted),
            'header': variant, 'filter_traces': variant_traces,
            'stages': stage_profiles(variant, variant_traces),
            'replayed_definitions': {key.decode(): [{'line': line.decode(), 'multiplicity': n}
                for line, n in sorted(lines.items())] for key, lines in sorted(emitted.items())}})
    return {'lemma': case['lemma'], 'lost_readings': case['lost_readings'],
        'grammar_profile': article['grammar_profile'], 'original_header': header,
        'original_stages': stage_profiles(header, traces), 'isolated_source_fields': isolated,
        'scope': 'source-field isolation diagnostic only; no candidate mutation or repair approval'}


def summarize(cases):
    original, trials = Counter(), Counter()
    for case in cases:
        key = json.dumps({'grammar_profile': case['grammar_profile'], 'stages': case['original_stages']}, sort_keys=True)
        original[key] += 1
        for trial in case['isolated_source_fields']:
            key = json.dumps({k: trial[k] for k in ('source_field_shape', 'replay_state', 'stages')}, sort_keys=True)
            trials[key] += 1
    return {'schema': 1, 'scope': 'eight remaining verbal extraction blockers; isolation is not source approval',
        'counts': {'lemmas': len(cases), 'lost_readings': sum(c['lost_readings'] for c in cases),
                   'isolated_field_trials': sum(len(c['isolated_source_fields']) for c in cases)},
        'original_groups': [dict(json.loads(k), lemmas=n) for k, n in sorted(original.items())],
        'isolated_field_groups': [dict(json.loads(k), trials=n) for k, n in sorted(trials.items())]}


def prepare(args):
    if loss.digest(args.review_dossier) != args.expected_review_sha256:
        raise ValueError('qualified missing-definition review receipt differs')
    selected = select_cases(args.review_dossier)
    if len(selected) != args.expected_lemmas or sum(c['lost_readings'] for c in selected) != args.expected_rows:
        raise ValueError('extraction-blocker inventory differs')
    first = loss.sibling('repair-latin-first-conjugation')
    rows, source, revision = first.source_rows(args.headers, args.lexica)
    entries, checked_source, checked_revision = first.review.load_entries(args.lexica)
    if source != checked_source or revision != checked_revision:
        raise ValueError('source changed during extraction-blocker review')
    by_id = {r['id']: r for r in rows}
    for case in selected:
        article = case['articles'][0]
        header = article['header']
        if by_id.get(header['id']) != header or review.grammar_profile(header, entries[header['id']], first.review) != article['grammar_profile']:
            raise ValueError('extraction-blocker source header differs')
    recovery = loss.sibling('recover-latin-initial-sense')
    cases = [inspect_case(c, lambda h: review.historical_replay(h, args.filters), recovery.render) for c in selected]
    target = loss.private_target(args.private_output, [args.review_dossier, args.headers, args.lexica, args.filters, source])
    with os.fdopen(os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600), 'w') as output:
        for case in cases:
            output.write(json.dumps(case, sort_keys=True) + '\n')
    report = summarize(cases)
    report.update(source_revision=revision, private_review_sha256=loss.digest(target),
        input_sha256={name: loss.digest(path) for name, path in [('review_dossier', args.review_dossier),
            ('headers', args.headers), ('Latin_TEI', source), *[(name, args.filters / name) for name in review.FILTERS]]})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('review-dossier', 'headers', 'lexica', 'filters', 'private-output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--expected-review-sha256', required=True)
    parser.add_argument('--expected-lemmas', type=int, required=True)
    parser.add_argument('--expected-rows', type=int, required=True)
    previous = os.umask(0o077)
    try:
        report = prepare(parser.parse_args())
    finally:
        os.umask(previous)
    print(json.dumps({'latin_extraction_blocker_review': report}, sort_keys=True))


if __name__ == '__main__':
    main()
