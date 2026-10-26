#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Join qualified source-present preverb additions to pinned source articles.

This is evidence collection, not lexical approval or a candidate mutation.
Literal forms, decompositions, articles and historical replay stay private.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re

from lxml import etree

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('source_present', REPO / 'tools/qualify-latin-isolated-source-present.py')
present = importlib.util.module_from_spec(spec)
spec.loader.exec_module(present)
loss, terminal, isolated = present.loss, present.terminal, present.isolated


def records(path):
    seen = set()
    for line in path.read_text().splitlines():
        row = json.loads(line)
        form = row['form']
        if not isinstance(form, str) or not form or any(ord(c) < 33 or ord(c) > 126 for c in form) or form in seen:
            raise ValueError('invalid or duplicate changed form')
        seen.add(form)
        yield row


def signatures(items, size):
    result = Counter()
    for item in items:
        sig, n = item['signature'], item['multiplicity']
        if (len(sig) != size or type(n) is not int or n <= 0 or
                any(not isinstance(sig[i], str) for i in (0, 1)) or
                any(type(v) is not int for v in sig[2:11]) or
                (size == 16 and any(not isinstance(v, str) for v in sig[11:]))):
            raise ValueError('invalid private signature')
        key = tuple(sig)
        if key in result:
            raise ValueError('duplicate private signature')
        result[key] = n
    return result


def qualified_additions(routes, delta, family, expected_forms, expected_rows, expected_preverbs):
    family_rows = [json.loads(line) for line in family.read_text().splitlines()]
    lemmas = {row['lemma'] for row in family_rows}
    if len(family_rows) != 13 or len(lemmas) != 1 or any(row['kind'] != 'source_present_family' for row in family_rows):
        raise ValueError('qualified source family scope differs')
    source_lemma = next(iter(lemmas))
    grammatical = {row['form']: row for row in records(delta)}
    selected, totals, seen = defaultdict(list), Counter(), set()
    for row in records(routes):
        form = row['form']; seen.add(form)
        if form not in grammatical:
            raise ValueError('route form absent from grammatical delta')
        old, new = signatures(row['removed'], 16), signatures(row['added'], 16)
        saved = grammatical[form]
        for counter, kind in ((old, 'removed'), (new, 'added')):
            projected = Counter()
            for sig, n in counter.items():
                projected[sig[:11]] += n
            if projected != signatures(saved[kind], 11):
                raise ValueError('route projection differs from grammatical delta')
        if old:
            raise ValueError('qualified present has removed routes')
        for sig, n in new.items():
            if sig[2] != 2 or sig[7] not in {0, 1, 2, 3}:
                raise ValueError('qualified addition is outside present-derived verbal scope')
            if sig[11]:
                if sig[1] == source_lemma:
                    raise ValueError('preverb addition is not under another lemma')
                selected[sig[1]].append({'form': form, 'signature': list(sig), 'multiplicity': n})
                totals['native_preverb_rows'] += n
            else:
                if sig[1] != source_lemma:
                    raise ValueError('direct addition is outside source lemma')
                totals['direct_rows'] += n
            totals['added_rows'] += n
    if (seen != set(grammatical) or len(seen) != expected_forms or
            totals['added_rows'] != expected_rows or totals['native_preverb_rows'] != expected_preverbs):
        raise ValueError('qualified addition scope differs')
    return source_lemma, selected, dict(totals)


def source_family(header, entry):
    """A source-only expectation; never inherit morphology from a base verb."""
    first = entry.find('orth')
    if first is None or first.get('extent') != 'full':
        return 'nonfull_headword', []
    digits = []
    for field in header['fields']:
        if field['name'] == 'itype':
            match = re.search(r'(?:^|,\s*)([1-4])$', field['projection'] or '')
            if match:
                digits.append(int(match[1]))
    if not digits:
        return 'no_explicit_conjugation_digit', []
    if len(set(digits)) != 1:
        return 'conflicting_conjugation_digits', []
    lemma = header['headword'].translate(str.maketrans('', '', '_^-'))
    try:
        cells = terminal.source_present_family({'lemma': lemma, 'header': header, 'digit': digits[0]})
    except ValueError:
        return 'unsupported_present_morphology', []
    return 'explicit_present_family', cells


def inspect_lemma(lemma, additions, choices, definitions, replay, render, review):
    articles = []
    for _, choice in sorted(choices.items()):
        header, entry = choice['row'], choice['entry']
        emitted = header['headword'].translate(str.maketrans('', '', '_^-'))
        identity = 'same_literal_lemma' if emitted == lemma else 'different_literal_lemma'
        state, cells = source_family(header, entry)
        expected = {(c['form'], c['person'], c['number'], c['mood'], c['voice']) for c in cells}
        matched = sum(a['multiplicity'] for a in additions if identity == 'same_literal_lemma' and
            a['signature'][7] == 1 and (a['form'], a['signature'][3], a['signature'][4],
                                      a['signature'][8], a['signature'][9]) in expected)
        emitted_defs, traces = replay(render(header))
        article_xml = etree.tostring(entry, encoding='unicode')
        articles.append({'header': header, 'join_routes': choice['join_routes'],
            'headword_identity': identity, 'source_partition': review.partition.classify(header)[0],
            'grammar_profile': isolated.review.grammar_profile(header, entry, review),
            'source_present_state': state, 'added_expected_present_rows': matched,
            'historical_replay_state': isolated.review.replay_state(lemma, emitted_defs),
            'replayed_definitions': {k.decode(): [{'line': line.decode(), 'multiplicity': n}
                for line, n in sorted(v.items())] for k, v in sorted(emitted_defs.items())},
            'filter_traces': traces, 'article_xml': article_xml,
            'article_sha256': hashlib.sha256(etree.tostring(entry)).hexdigest()})
    join = 'unique_article' if len(articles) == 1 else 'ambiguous_articles' if articles else 'no_article_join'
    return {'lemma': lemma, 'source_join': join, 'added_rows': sum(a['multiplicity'] for a in additions),
        'additions': additions, 'articles': articles,
        'candidate_definitions': [{'line': line.decode(), 'multiplicity': n}
            for line, n in sorted(definitions.get(lemma.encode(), {}).items())],
        'decision': 'source_evidence_only_no_lexical_approval'}


def summarize(cases):
    groups, lemma_groups, tenses = Counter(), Counter(), Counter()
    matched = 0
    fields = ('source_join', 'headword_identity', 'source_partition', 'source_present_state',
              'historical_replay_state', 'candidate_has_definitions')
    for case in cases:
        for addition in case['additions']:
            tenses[addition['signature'][7]] += addition['multiplicity']
        if len(case['articles']) == 1:
            a = case['articles'][0]
            key = (case['source_join'], a['headword_identity'], a['source_partition'],
                   a['source_present_state'], a['historical_replay_state'], bool(case['candidate_definitions']))
            matched += a['added_expected_present_rows']
        else:
            key = (case['source_join'],) + ('not_unique',) * 4 + (bool(case['candidate_definitions']),)
        groups[key] += case['added_rows']; lemma_groups[key] += 1
    return {'schema': 1, 'scope': 'other-lemma native preverb additions on eleven-field-changed forms only; no lexical approval',
        'counts': {'lemmas': len(cases), 'added_rows': sum(c['added_rows'] for c in cases),
                   'expected_present_rows_under_unique_literal_article': matched},
        'rows_by_tense': {str(k): v for k, v in sorted(tenses.items())},
        'source_groups': [dict(zip(fields, key), rows=n, lemmas=lemma_groups[key])
            for key, n in sorted(groups.items(), key=lambda item: json.dumps(item[0]))]}


def prepare(args):
    inputs = {name: getattr(args, name) for name in ('routes', 'delta', 'family', 'headers', 'expanded')}
    if any(loss.digest(path) != getattr(args, 'expected_' + name + '_sha256') for name, path in inputs.items()):
        raise ValueError('preverb review input receipt differs')
    _, selected, totals = qualified_additions(args.routes, args.delta, args.family,
        args.expected_forms, args.expected_rows, args.expected_preverbs)
    first = loss.sibling('repair-latin-first-conjugation')
    rows, source, revision = first.source_rows(args.headers, args.lexica)
    entries, checked_source, checked_revision = first.review.load_entries(args.lexica)
    if source != checked_source or revision != checked_revision or loss.digest(source) != args.expected_tei_sha256:
        raise ValueError('pinned preverb review source differs')
    index = loss.source_index(rows, entries, first.review.partition.classify)
    definitions = loss.definitions(args.expanded)
    recovery = loss.sibling('recover-latin-initial-sense')
    target = loss.private_target(args.private_output, [*inputs.values(), args.lexica, args.filters, source])
    cases = [inspect_lemma(lemma, additions, index.get(lemma.encode(), {}), definitions,
        lambda h: isolated.review.historical_replay(h, args.filters), recovery.render, first.review)
        for lemma, additions in sorted(selected.items())]
    with isolated.private_stream(target) as output:
        for case in cases:
            output.write(json.dumps(case, sort_keys=True) + '\n')
    if any(loss.digest(path) != getattr(args, 'expected_' + name + '_sha256') for name, path in inputs.items()):
        raise ValueError('preverb review mutated an input')
    report = summarize(cases)
    report.update(source_revision=revision, qualified_route_counts=totals,
        input_sha256={name: loss.digest(path) for name, path in inputs.items()},
        tei_sha256=loss.digest(source), private_review_sha256=loss.digest(target), inputs_unchanged=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('routes', 'delta', 'family', 'headers', 'expanded', 'lexica', 'filters', 'private-output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('routes', 'delta', 'family', 'headers', 'expanded', 'tei'):
        parser.add_argument('--expected-' + name + '-sha256', required=True)
    for name in ('forms', 'rows', 'preverbs'):
        parser.add_argument('--expected-' + name, type=int, required=True)
    previous = os.umask(0o077)
    try:
        report = prepare(parser.parse_args())
    finally:
        os.umask(previous)
    print(json.dumps({'latin_source_present_preverb_review': report}, sort_keys=True))


if __name__ == '__main__':
    main()
