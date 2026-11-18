#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay pinned source headers for lost lemmas with no final definitions.

This review classifies extraction and identity leads. It never approves a
replacement, copies witness stems into a candidate, or publishes lexical data.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

import importlib.util

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('loss_diagnostic', REPO / 'tools/diagnose-latin-lost-stems.py')
loss = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loss)
FILTERS = ('combitype', 'splitlat', 'conj1', 'latvb')


def selected_dossiers(path):
    counts, dossiers = Counter(), {}
    seen = set()
    with path.open() as stream:
        for line in stream:
            row = json.loads(line)
            if row['kind'] == 'lost_form':
                if row['form'] in seen:
                    raise ValueError('duplicate private lost form')
                seen.add(row['form'])
                for reading in row['readings']:
                    values = reading['signature']
                    if len(values) != len(loss.SIGNATURE):
                        raise ValueError('invalid private reading signature')
                    counts[values[1]] += 1
            elif row['kind'] == 'lemma_review':
                if row['lemma'] in dossiers:
                    raise ValueError('duplicate private lemma dossier')
                dossiers[row['lemma']] = row
            else:
                raise ValueError('unknown private dossier record')
    if set(counts) != set(dossiers):
        raise ValueError('private reading and lemma inventories differ')
    selected = []
    for lemma, row in sorted(dossiers.items()):
        if row['definition_state'] == 'no_final_definitions':
            if not row['baseline_definitions'] or row['final_definitions']:
                raise ValueError('missing-definition dossier is inconsistent')
            selected.append((row, counts[lemma]))
    return selected


def replay_definitions(data):
    """Only genuine stem directives count; default lexer ECHO text is private."""
    records, lemma = {}, None
    for line in data.splitlines():
        if line.startswith(b':le:'):
            lemma = line[4:].strip()
            if not lemma or any(c < 33 or c > 126 for c in lemma):
                raise ValueError('historical replay emitted an invalid lemma')
            records.setdefault(lemma, Counter())
        elif line.startswith(loss.STEM_PREFIXES):
            if lemma is None or not line[4:].split():
                raise ValueError('historical replay emitted an unbound stem')
            records[lemma][line] += 1
    return {key: value for key, value in records.items() if value}


def historical_replay(header, filters):
    traces = []
    data = header.encode('utf-8')
    for name in FILTERS:
        try:
            result = subprocess.run([str(filters / name)], input=data, capture_output=True,
                                    timeout=15, check=False)
        except (OSError, subprocess.TimeoutExpired):
            raise ValueError('historical source replay could not complete') from None
        if result.returncode or len(result.stdout) + len(result.stderr) > 2 * 1024 * 1024:
            raise ValueError('historical source replay failed')
        traces.append({'filter': name, 'stdout': result.stdout.decode('utf-8'),
                       'stderr': result.stderr.decode('utf-8')})
        data = result.stdout
    return replay_definitions(data), traces


def grammar_profile(row, entry, review):
    types = [field['projection'] for field in row['fields'] if field['name'] == 'itype']
    if not types:
        kind = 'no_itype'
    elif len(types) != 1:
        kind = 'multiple_itypes'
    elif re.fullmatch(r'[1-4]', types[0] or ''):
        kind = 'bare_conjugation_digit'
    elif re.search(r'(?:^|,\s*)[1-4]$', types[0] or ''):
        kind = 'principal_parts_with_conjugation_digit'
    elif re.fullmatch(r'[A-Za-z_^]+r[ei]', types[0] or ''):
        kind = 'infinitive_itype'
    else:
        kind = 'other_itype'
    first = entry.find('orth')
    extent = 'full' if first is not None and first.get('extent') == 'full' else 'other_or_unspecified'
    head = re.sub(r'#[1-9]$', '', row['headword'])
    ending = ('deponent_present' if head.endswith('or') else
              'active_present' if head.endswith('o') else
              'impersonal_present' if head.endswith(('et', 'it')) else 'other_headword_ending')
    return {'itype_shape': kind, 'first_orth_extent': extent, 'headword_shape': ending,
            'first_sense_signal': review.signal(review.initial_sense_fields(entry))}


def replay_state(lemma, records):
    if records.get(lemma.encode()):
        return 'emits_missing_lemma'
    return 'emits_only_other_lemmas' if records else 'emits_no_definitions'


def review_case(dossier, choices, candidate, expanded, replay, render, source_review):
    lemma = dossier['lemma']
    articles = []
    for _, choice in sorted(choices.items()):
        row, entry = choice['row'], choice['entry']
        head = row['headword'].translate(str.maketrans('', '', '_^-'))
        records, traces = replay(render(row))
        category, reason = source_review.partition.classify(row)
        articles.append({'header': row, 'join_routes': choice['join_routes'],
            'partition': category, 'partition_reason': reason,
            'emitted_headword': head, 'headword_identity': 'same_literal_lemma' if head == lemma else 'different_literal_lemma',
            'replay_state': replay_state(lemma, records), 'grammar_profile': grammar_profile(row, entry, source_review),
            'candidate_has_headword_definitions': bool(candidate.get(head.encode())),
            'final_has_headword_definitions': bool(expanded.get(head.encode())),
            'replayed_definitions': {key.decode(): [{'line': line.decode(), 'multiplicity': n}
                                       for line, n in sorted(value.items())] for key, value in sorted(records.items())},
            'filter_traces': traces})
    if not articles:
        decision = 'source_join_required'
    elif len(articles) != 1:
        decision = 'ambiguous_source_identity'
    elif articles[0]['headword_identity'] != 'same_literal_lemma':
        decision = 'literal_lemma_identity_review'
    elif articles[0]['partition'] != 'verbal':
        decision = 'nonverbal_partition_review'
    elif articles[0]['replay_state'] == 'emits_missing_lemma':
        decision = 'isolated_vs_full_pipeline_review'
    else:
        decision = 'historical_extraction_review'
    return {'lemma': lemma, 'review_decision': decision, 'articles': articles,
            'baseline_definitions': dossier['baseline_definitions'],
            'scope': 'review lead only; no identity substitution or stem insertion approved'}


def summarize(cases):
    decisions, groups, lemma_groups = Counter(), Counter(), Counter()
    for case, readings in cases:
        decisions[case['review_decision']] += 1
        if len(case['articles']) == 1:
            article = case['articles'][0]
            profile = article['grammar_profile']
            key = (case['review_decision'], article['partition'], article['headword_identity'],
                article['replay_state'], article['candidate_has_headword_definitions'],
                article['final_has_headword_definitions'], profile['itype_shape'],
                profile['first_orth_extent'], profile['headword_shape'], profile['first_sense_signal'])
        else:
            key = (case['review_decision'],) + ('not_unique',) * 9
        groups[key] += readings
        lemma_groups[key] += 1
    fields = ('review_decision', 'source_partition', 'headword_identity', 'replay_state',
        'candidate_has_headword_definitions', 'final_has_headword_definitions', 'itype_shape',
        'first_orth_extent', 'headword_shape', 'first_sense_signal')
    # Mixed boolean/string columns are sorted by their JSON representation.
    return {'schema': 1, 'scope': 'no-final-definition complete losses; source/extraction review, no repair approval',
        'counts': {'lemmas': len(cases), 'readings': sum(n for _, n in cases)},
        'review_decisions_by_lemmas': dict(sorted(decisions.items())),
        'reading_groups': [dict(zip(fields, key), readings=n, lemmas=lemma_groups[key]) for key, n in
                           sorted(groups.items(), key=lambda item: json.dumps(item[0]))]}


def prepare(args):
    if loss.digest(args.dossier) != args.expected_dossier_sha256:
        raise ValueError('private diagnostic receipt differs')
    for path, expected in ((args.candidate_source, args.expected_candidate_sha256),
                           (args.final_expanded, args.expected_expanded_sha256)):
        if loss.digest(path) != expected:
            raise ValueError('qualified candidate receipt differs')
    selected = selected_dossiers(args.dossier)
    if len(selected) != args.expected_lemmas or sum(n for _, n in selected) != args.expected_rows:
        raise ValueError('missing-definition review scope differs')
    first = loss.sibling('repair-latin-first-conjugation')
    rows, source, revision = first.source_rows(args.headers, args.lexica)
    entries, checked_source, checked_revision = first.review.load_entries(args.lexica)
    if source != checked_source or revision != checked_revision:
        raise ValueError('source changed during missing-definition review')
    index = loss.source_index(rows, entries, first.review.partition.classify)
    from lxml import etree
    # Verify the complete join, not just one plausible article from the dossier.
    for dossier, _ in selected:
        choices = index.get(dossier['lemma'].encode(), {})
        expected = [{'join_routes': c['join_routes'], 'header': c['row'],
            'partition': list(first.review.partition.classify(c['row'])),
            'article_sha256': hashlib.sha256(etree.tostring(c['entry'])).hexdigest(),
            'article_xml': etree.tostring(c['entry'], encoding='unicode')}
            for _, c in sorted(choices.items())]
        if expected != dossier['articles']:
            raise ValueError('private article evidence differs from pinned source')
    candidate, expanded = loss.definitions(args.candidate_source), loss.definitions(args.final_expanded)
    if any(expanded.get(d['lemma'].encode()) for d, _ in selected):
        raise ValueError('reviewed lemma has final definitions')
    recovery = loss.sibling('recover-latin-initial-sense')
    cases = [(review_case(d, index.get(d['lemma'].encode(), {}), candidate, expanded,
                 lambda header: historical_replay(header, args.filters), recovery.render, first.review), n)
             for d, n in selected]
    paths = [args.dossier, args.headers, args.lexica, args.candidate_source, args.final_expanded,
             args.filters, source]
    target = loss.private_target(args.private_output, paths)
    with os.fdopen(os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                          getattr(os, 'O_NOFOLLOW', 0), 0o600), 'w') as output:
        for case, count in cases:
            output.write(json.dumps(dict(case, lost_readings=count), sort_keys=True) + '\n')
    report = summarize(cases)
    report['source_revision'] = revision
    report['input_sha256'] = {name: loss.digest(path) for name, path in [
        ('diagnostic_dossier', args.dossier), ('headers', args.headers), ('Latin_TEI', source),
        ('candidate_source', args.candidate_source), ('final_expanded', args.final_expanded),
        *[(name, args.filters / name) for name in FILTERS]]}
    report['private_review_sha256'] = loss.digest(target)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('dossier', 'headers', 'lexica', 'candidate-source', 'final-expanded', 'filters', 'private-output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--expected-dossier-sha256', required=True)
    parser.add_argument('--expected-candidate-sha256', required=True)
    parser.add_argument('--expected-expanded-sha256', required=True)
    parser.add_argument('--expected-lemmas', type=int, required=True)
    parser.add_argument('--expected-rows', type=int, required=True)
    print(json.dumps({'latin_missing_definition_review': prepare(parser.parse_args())}, sort_keys=True))


if __name__ == '__main__':
    main()
