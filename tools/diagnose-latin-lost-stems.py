#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reprobe completely lost forms and join private stem/source review dossiers."""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SIGNATURE = ('workword', 'lemma', 'part_of_speech', 'person', 'number', 'gender',
             'grammatical_case', 'tense', 'mood', 'voice', 'degree')
STEM_PREFIXES = (b':vs:', b':vb:', b':de:', b':wd:')


def sibling(name):
    spec = importlib.util.spec_from_file_location(name, REPO / 'tools' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def definitions(path):
    """Keep literal definition lines and duplicate occurrences under exact lemmas."""
    result = defaultdict(Counter)
    lemma = None
    for raw in path.read_bytes().splitlines():
        if raw.startswith(b':le:'):
            lemma = raw[4:].strip()
            if not lemma or any(c < 33 or c > 126 for c in lemma):
                raise ValueError('invalid literal definition lemma')
            result[lemma]
        elif raw.strip() and not raw.lstrip().startswith(b'#') and lemma is not None:
            result[lemma][raw] += 1
    return dict(result)


def tokens(records):
    return {line[4:].split()[0] for line in records
            if line.startswith(STEM_PREFIXES) and line[4:].split()}


def notation_free(value):
    # A separately labelled diagnostic lead, never an identity or repair rule.
    return value.translate(None, b'_^-' )


def definition_state(before, after):
    if not before and not after:
        return 'no_definitions_in_either'
    if not before:
        return 'no_baseline_definitions'
    if not after:
        return 'no_final_definitions'
    return 'equal_definition_multisets' if before == after else 'changed_definition_multisets'


def stem_match(stem, before, after):
    old, new = tokens(before), tokens(after)
    if stem in old:
        return 'baseline_exact__final_exact' if stem in new else 'baseline_exact__final_no_exact'
    if notation_free(stem) in {notation_free(v) for v in old}:
        return ('baseline_notation_lead__final_notation_lead' if
                notation_free(stem) in {notation_free(v) for v in new} else
                'baseline_notation_lead__final_no_notation_lead')
    return 'baseline_stem_unmatched'


def source_index(rows, entries):
    result = defaultdict(dict)
    for row in rows:
        if row.get('projection_error') is not None:
            continue
        names = [(row.get('lemma'), 'projected_key'),
                 (row['headword'].translate(str.maketrans('', '', '_^-')), 'emitted_headword')]
        for lemma, kind in names:
            if lemma is not None:
                choice = result[lemma.encode()].setdefault(row['id'],
                    {'row': row, 'entry': entries[row['id']], 'join_routes': []})
                if kind not in choice['join_routes']:
                    choice['join_routes'].append(kind)
    return result


def signature(row):
    return tuple(getattr(row, field) for field in SIGNATURE)


def decoded(value):
    if isinstance(value, bytes):
        return value.decode('utf-8')
    return value


def grouped(counter, fields):
    return [dict(zip(fields, key), rows=count) for key, count in sorted(counter.items())]


def diagnose(differences, left, right, old_defs, new_defs, substituted, retained, sources,
             output, article_details):
    groups, states, matches, joins, membership = (Counter() for _ in range(5))
    lemmas, seen = {}, set()
    forms = rows_total = nonverbal = 0
    with differences.open('rb') as stream:
        for raw in stream:
            record = json.loads(raw)
            if record['rebuilt_count'] != 0 or record['curated_count'] == 0:
                continue
            word = record['form'].encode('ascii')
            if not word or any(c < 33 or c > 126 for c in word) or word in seen:
                raise ValueError('invalid or duplicate lost form')
            seen.add(word)
            if record['retained_rows'] or record['added']:
                raise ValueError('lost form has retained or added signatures')
            expected = Counter()
            for removed in record['removed']:
                values = removed['signature']
                amount = removed['multiplicity']
                if len(values) != len(SIGNATURE) or type(amount) is not int or amount <= 0:
                    raise ValueError('invalid private removed signature')
                expected[tuple(v.encode('utf-8') if isinstance(v, str) else v for v in values)] += amount
            old = left.analyses(word, require_untruncated=True)
            new = right.analyses(word, require_untruncated=True)
            if new or len(old) != record['curated_count'] or Counter(map(signature, old)) != expected:
                raise ValueError('lost-form reprobe differs from qualified grammatical multiset')
            forms += 1
            details = []
            for row in old:
                rows_total += 1
                lemma = row.lemma
                before, after = old_defs.get(lemma, Counter()), new_defs.get(lemma, Counter())
                state, match = definition_state(before, after), stem_match(row.stem, before, after)
                choices = sources.get(lemma, {})
                join = 'unique_article' if len(choices) == 1 else 'ambiguous_articles' if choices else 'no_article_join'
                origin = 'native_preverb' if row.preverb else 'direct'
                present, kept = lemma in substituted, lemma in retained
                membership[(present, kept)] += 1
                states[state] += 1
                matches[match] += 1
                joins[join] += 1
                groups[(row.part_of_speech, row.tense, origin, state, match, join, present, kept)] += 1
                if row.part_of_speech != 2:
                    nonverbal += 1
                if lemma not in lemmas:
                    lemmas[lemma] = {'lemma': decoded(lemma), 'definition_state': state,
                        'in_substituted_source': present, 'in_retained_sources': kept,
                        'baseline_definitions': [{'line': decoded(line), 'multiplicity': n} for line, n in sorted(before.items())],
                        'final_definitions': [{'line': decoded(line), 'multiplicity': n} for line, n in sorted(after.items())],
                        'source_join': join, 'articles': [article_details(c) for _, c in sorted(choices.items())]}
                details.append({'signature': [decoded(v) for v in signature(row)],
                                'stem_match': match,
                                **{f: decoded(getattr(row, f)) for f in ('preverb', 'raw_preverb', 'stem', 'suffix', 'ending')}})
            output.write(json.dumps({'kind': 'lost_form', 'form': decoded(word), 'readings': details}, sort_keys=True)+'\n')
    for _, dossier in sorted(lemmas.items()):
        output.write(json.dumps({'kind': 'lemma_review', **dossier}, sort_keys=True)+'\n')
    lemma_states = Counter(v['definition_state'] for v in lemmas.values())
    lemma_joins = Counter(v['source_join'] for v in lemmas.values())
    return {'schema': 1, 'scope': 'complete losses only; literal definitions and stem/source review leads; no repair approval',
            'counts': {'forms': forms, 'readings': rows_total, 'distinct_lemmas': len(lemmas), 'nonverbal_readings': nonverbal},
            'definition_states': {'readings': dict(sorted(states.items())), 'lemmas': dict(sorted(lemma_states.items()))},
            'stem_matches_by_readings': dict(sorted(matches.items())),
            'source_joins': {'readings': dict(sorted(joins.items())), 'lemmas': dict(sorted(lemma_joins.items()))},
            'source_membership_by_readings': grouped(membership, ('in_substituted_source', 'in_retained_sources')),
            'reading_groups': grouped(groups, ('part_of_speech', 'tense', 'provenance', 'definition_state',
                'stem_match', 'source_join', 'in_substituted_source', 'in_retained_sources'))}


def private_target(output, inputs):
    if output.is_symlink():
        raise FileExistsError('private loss dossier is a symlink')
    target = output.resolve()
    if target == REPO or REPO in target.parents or any(
            target == p.resolve() or p.resolve() in target.parents or target in p.resolve().parents for p in inputs):
        raise ValueError('private loss dossier must be outside repository and inputs')
    return target


def prepare(args):
    differences = args.comparison_dir / 'baseline-to-final-global.jsonl'
    comparison_report = args.comparison_dir / 'report.json'
    old_source = args.baseline / 'Latin/lexical/verb.expanded'
    new_source = args.candidate / 'Latin/lexical/present-trial.expanded'
    report = json.loads(comparison_report.read_text())
    global_report = report['global_comparisons']['baseline-to-final-global']
    if digest(differences) != global_report['private_difference_sha256'] or (
            args.expected_difference_sha256 and digest(differences) != args.expected_difference_sha256):
        raise ValueError('private global difference receipt differs')
    if digest(args.candidate_source) != report['input_sha256']['bounded-present']:
        raise ValueError('candidate source differs from global qualification')
    raw_sources = []
    for line in (args.baseline / 'Latin/lexical/inputs.tsv').read_text().splitlines():
        if not line or line.startswith('#'):
            continue
        language, role, name, _ = line.split('\t')
        if language == 'Latin' and role in {'verb', 'irregular-verb-baseline'}:
            path = (args.baseline / 'Latin' / name).resolve()
            if (args.baseline / 'Latin').resolve() not in path.parents:
                raise ValueError('verbal assembly path leaves baseline')
            raw_sources.append((name, path))
    if len(raw_sources) != 4 or sum(name == 'stemsrc/vbs.latin' for name, _ in raw_sources) != 1:
        raise ValueError('unexpected verbal assembly inventory')
    retained = set().union(*(definitions(path) for name, path in raw_sources if name != 'stemsrc/vbs.latin'))
    substituted = definitions(args.candidate_source)
    first = sibling('repair-latin-first-conjugation')
    headers, source, revision = first.source_rows(args.headers, args.lexica)
    entries, checked_source, checked_revision = first.review.load_entries(args.lexica)
    if source != checked_source or revision != checked_revision:
        raise ValueError('source changed during loss review')
    sources = source_index(headers, entries)
    target = private_target(args.private_output, [args.comparison_dir, args.baseline, args.candidate,
        args.candidate_source, args.headers, args.lexica, args.library, source])
    from lxml import etree
    def article_details(choice):
        row, entry = choice['row'], choice['entry']
        return {'join_routes': choice['join_routes'], 'header': row,
                'partition': first.review.partition.classify(row),
                'article_sha256': hashlib.sha256(etree.tostring(entry)).hexdigest(),
                'article_xml': etree.tostring(entry, encoding='unicode')}
    native = sibling('qualify-latin-present-stages')
    left = native.NativeRows(args.library, args.baseline)
    try:
        right = native.NativeRows(args.library, args.candidate)
        try:
            with os.fdopen(os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                                  getattr(os, 'O_NOFOLLOW', 0), 0o600), 'w') as output:
                result = diagnose(differences, left, right, definitions(old_source), definitions(new_source),
                                  substituted, retained, sources, output, article_details)
                for name in ('forms', 'lemmas', 'rows'):
                    expected = getattr(args, 'expected_' + name)
                    field = {'forms': 'forms', 'lemmas': 'distinct_lemmas', 'rows': 'readings'}[name]
                    if expected is not None and result['counts'][field] != expected:
                        raise ValueError('complete loss diagnostic count differs')
                if result['counts']['forms'] != global_report['lost_forms_diagnostic']['forms']:
                    raise ValueError('loss diagnostic differs from global loss count')
        finally:
            right.close()
    finally:
        left.close()
    result['source_revision'] = revision
    result['input_sha256'] = {name: digest(path) for name, path in [
        ('global_difference', differences), ('global_report', comparison_report), ('baseline_expanded', old_source),
        ('final_expanded', new_source), ('candidate_source', args.candidate_source), ('headers', args.headers),
        ('Latin_TEI', source), ('native_library', args.library), *[('assembly_input_' + str(i), path)
        for i, (_, path) in enumerate(raw_sources)]]}
    result['private_dossier_sha256'] = digest(target)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('comparison-dir', 'baseline', 'candidate', 'candidate-source', 'headers', 'lexica', 'library', 'private-output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('forms', 'lemmas', 'rows'):
        parser.add_argument('--expected-' + name, type=int)
    parser.add_argument('--expected-difference-sha256')
    args = parser.parse_args()
    print(json.dumps({'latin_lost_stem_diagnostic': prepare(args)}, sort_keys=True))


if __name__ == '__main__':
    main()
