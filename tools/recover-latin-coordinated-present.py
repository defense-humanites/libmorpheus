#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stage bounded class-three alternates attested by a quoted passive present."""
import argparse
import copy
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unicodedata

spec = importlib.util.spec_from_file_location('audit', Path(__file__).with_name('audit-latin-remaining-presents.py'))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
regular, first = audit.regular, audit.first
GRAMMAR = re.compile(r'[A-Za-z_^]+i, [A-Za-z_^]+um and [A-Za-z_^]+um, 3')


def quoted_passive(entry, word):
    """Require an explicit Latin quotation, never surrounding explanatory text."""
    for quote in entry.iter('quote'):
        if quote.get('lang') != 'la' or any(isinstance(n, audit.etree._Entity) for n in quote.iter()):
            continue
        text = unicodedata.normalize('NFD', ''.join(quote.itertext()))
        text = ''.join(c for c in text if not unicodedata.combining(c))
        words = re.findall(r'(?<!\w)[A-Za-z]+(?!\w)', text)
        if word.decode() in {w.lower() for w in words}:
            return hashlib.sha256(audit.etree.tostring(quote)).hexdigest()
    return None


def selected_rows(rows, entries, counts=None):
    counts = Counter() if counts is None else counts
    selected = []
    for row in rows:
        fields = [f['projection'] for f in row['fields'] if f['name'] == 'itype']
        if (row.get('projection_error') is not None or len(fields) != 1 or
                not GRAMMAR.fullmatch(fields[0] or '') or
                any(f['name'] == 'pos' and f['projection'] not in {'v. a.', 'v. n.'} for f in row['fields'])):
            continue
        counts['coordinated_active_headers'] += 1
        head = row['headword']
        primary = regular.parts(head, '3', present_only=True)
        if not primary or primary[0][1] != b'conj3':
            continue
        counts['plain_class_three_headers'] += 1
        left = regular.letters(head.encode())
        if row['id'] not in entries:
            raise ValueError('missing source article')
        witnesses = {}
        for alt in row.get('full_alternates', []):
            parts = regular.parts(alt, '3', present_only=True)
            right = regular.letters(alt.encode())
            # This bound alone is not approval: the source quotation is required.
            if (not parts or parts[0][1] != b'conj3' or len(left) != len(right) or
                    left[:1] != right[:1] or
                    sum(a != b for a, b in zip(left, right)) != 1):
                continue
            counts['bounded_full_alternates'] += 1
            word = regular.letters(parts[0][0]) + b'itur'
            fingerprint = quoted_passive(entries[row['id']], word)
            if fingerprint:
                witnesses[alt] = (word.decode(), fingerprint)
                counts['quoted_passive_alternates'] += 1
        if witnesses:
            trial = copy.deepcopy(row)
            trial['full_alternates'] = list(witnesses)
            trial['_quoted_passives'] = witnesses
            for field in trial['fields']:
                if field['name'] == 'itype':
                    field['projection'] = '3'
            selected.append(trial)
    return selected


def transform(candidate, rows, entries):
    return regular.transform(candidate, selected_rows(rows, entries), 'present-only')


def source_witnesses(before, after, selected, entries, source, headers, revision):
    choices = {}
    for row in selected:
        lemma = row['headword'].translate(str.maketrans('', '', '_^-')).encode()
        for alt, (word, quote_hash) in row['_quoted_passives'].items():
            stem, tag = regular.parts(alt, '3', present_only=True)[0]
            choices.setdefault((lemma, stem, tag), []).append((row, word, quote_hash))
    records = []
    for lemma, stem, tag in audit.inserted_records(before, after):
        matches = choices.get((lemma, stem, tag), [])
        if len(matches) != 1:
            raise ValueError('ambiguous quoted alternate identity')
        row, word, quote_hash = matches[0]
        records.append({'schema': 1, 'form': word, 'lemma': lemma.decode(),
                        'source_revision': revision,
                        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                        'headers_sha256': hashlib.sha256(headers.read_bytes()).hexdigest(),
                        'candidate_sha256': hashlib.sha256(after).hexdigest(),
                        'article_sha256': hashlib.sha256(audit.etree.tostring(entries[row['id']])).hexdigest(),
                        'quote_sha256': quote_hash})
    return records


def prepare(candidate, headers, lexica, output, expected=None, witness_output=None):
    target = first.private_target(candidate, headers, lexica, output)
    witness_target = (first.private_target(candidate, headers, lexica, witness_output)
                      if witness_output is not None else None)
    targets = [p for p in (target, witness_target) if p is not None]
    if len(set(targets)) != len(targets):
        raise ValueError('candidate and witness outputs must differ')
    if any(p.exists() or p.is_symlink() for p in targets):
        raise FileExistsError('private output already exists')
    rows, source, revision = regular.alternates.source_alternates(headers, lexica)
    entries, second_source, second_revision = first.review.load_entries(lexica)
    if (source, revision) != (second_source, second_revision):
        raise ValueError('source changed during validation')
    before = candidate.read_bytes()
    selector_counts = Counter()
    selected = selected_rows(rows, entries, selector_counts)
    data, counts = regular.transform(before, selected, 'present-only')
    witnesses = source_witnesses(before, data, selected, entries, source, headers, revision)
    if len(witnesses) != counts.get('added_records', 0):
        raise ValueError('source witness count differs from insertions')
    if expected is not None and len(witnesses) != expected:
        raise ValueError('unexpected quoted coordinated present count: ' + json.dumps(
            {'selector_counts': dict(selector_counts), 'transform_counts': counts}, sort_keys=True))
    witness_data = ''.join(json.dumps(row, sort_keys=True) + '\n' for row in witnesses).encode()
    report = {'schema': 1, 'scope': 'coordinated supines; one-letter full alternate with a quoted passive present',
              'source_revision': revision, 'counts': counts, 'selector_counts': dict(sorted(selector_counts.items())),
              'source_quote_witnesses': len(witnesses),
              'input_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (candidate, headers, source)},
              'output_sha256': hashlib.sha256(data).hexdigest(),
              'private_witness_sha256': hashlib.sha256(witness_data).hexdigest()}
    first.write_private(target, data)
    if witness_target is not None:
        first.write_private(witness_target, witness_data)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate', 'headers', 'lexica', 'private-output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--private-witness', type=Path)
    parser.add_argument('--expected', type=int)
    args = parser.parse_args()
    print(json.dumps(prepare(args.candidate, args.headers, args.lexica,
                             args.private_output, args.expected, args.private_witness), sort_keys=True))


if __name__ == '__main__':
    main()
