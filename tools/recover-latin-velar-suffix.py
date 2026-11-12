#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stage an explicit velar suffix alternate under its source homograph."""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import re

spec = importlib.util.spec_from_file_location('first', Path(__file__).with_name('repair-latin-first-conjugation.py'))
first = importlib.util.module_from_spec(spec)
spec.loader.exec_module(first)


def proof(row, entry):
    if row.get('projection_error') is not None or row.get('id') != entry.get('id'):
        return None
    base, _ = first.review.projection.project(entry, 'Latin')
    fields = lambda record: [(f['name'], f['projection'], f.get('type')) for f in record['fields']]
    if fields(row) != fields(base) or row['headword'] != base['headword']:
        return None
    if [f['name'] for f in row['fields']] != ['orth', 'orth', 'itype'] or row['fields'][2]['projection'] != 'e^re':
        return None
    match = re.fullmatch(r'([A-Za-z_^]+)-([A-Za-z_^]+ngo)(#[1-9])?', row['headword'])
    if not match:
        return None
    orths = entry.findall('orth'); senses = entry.findall('sense')
    if (len(orths) != 2 or orths[0].get('extent') != 'full' or
            orths[1].get('type') != 'alt' or orths[1].get('extent') not in {'full', 'part'} or not senses):
        return None
    label = senses[0][0] if len(senses[0]) else None
    if (label is None or label.tag != 'hi' or label.get('rend') != 'ital' or
            ' '.join(''.join(label.itertext()).split()) not in {'v. a.', 'v. a., to'}):
        return None
    prefix, root, homograph = match.groups()
    if row['fields'][1]['projection'] != '-' + root[:-1] + 'uo':
        return None
    lemma = row['headword'].translate(str.maketrans('', '', '_^-')).encode()
    stem = (prefix + '-' + root[:-1]).encode()
    alternate = (prefix + '-' + root[:-1] + 'u').encode()
    return lemma, stem, alternate


def transform(candidate, rows, entries):
    proofs = defaultdict(list)
    for row in rows:
        if row.get('id') not in entries:
            raise ValueError('missing source article')
        result = proof(row, entries[row['id']])
        if result:
            proofs[result[0]].append(result)
    blocks = Counter(); records = defaultdict(list); lemma = None
    pattern = re.compile(rb':vs:([^\s]+)[ \t]+conj3([^\r\n]*)(?:\r?\n)?$')
    lines = candidate.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.startswith(b':le:'):
            lemma = line[4:].strip(); blocks[lemma] += 1
        match = pattern.fullmatch(line)
        if match:
            records[lemma].append((index, match[1], match[2].strip()))
    additions = {}; counts = Counter(); short = lambda stem: stem.replace(b'^', b'')
    for lemma, choices in proofs.items():
        if len(choices) != 1 or blocks[lemma] != 1:
            counts['withheld_ambiguity'] += 1; continue
        _, stem, alternate = choices[0]
        primary = [r for r in records[lemma] if not r[2]]
        if len(primary) != 1 or short(primary[0][1]) != short(stem):
            counts['withheld_unmatched_primary'] += 1; continue
        if any(short(r[1]) == short(alternate) for r in records[lemma]):
            counts['already_present'] += 1; continue
        additions[primary[0][0]] = b':vs:' + alternate + b'\tconj3 orth\n'
        counts['added_records'] += 1; counts['changed_lemma_blocks'] += 1
    output = []
    for index, line in enumerate(lines):
        output.append(line)
        if index in additions:
            if not line.endswith(b'\n'): output.append(b'\n')
            output.append(additions[index])
    return b''.join(output), dict(sorted(counts.items()))


def prepare(candidate, headers, lexica, output, expected=None):
    target = first.private_target(candidate, headers, lexica, output)
    rows, source, revision = first.source_rows(headers, lexica)
    entries, second_source, second_revision = first.review.load_entries(lexica)
    if source != second_source or revision != second_revision:
        raise ValueError('source changed during validation')
    data, counts = transform(candidate.read_bytes(), rows, entries)
    if expected is not None and counts.get('added_records', 0) != expected:
        raise ValueError('unexpected added record count')
    report = {'schema': 1, 'scope': 'explicit dash suffix, short-e infinitive and matched source homograph',
              'source_revision': revision, 'counts': counts,
              'input_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (candidate, headers, source)},
              'output_sha256': hashlib.sha256(data).hexdigest()}
    first.write_private(target, data)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate', 'headers', 'lexica', 'private-output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--expected', type=int)
    args = parser.parse_args()
    print(json.dumps(prepare(args.candidate, args.headers, args.lexica, args.private_output, args.expected), sort_keys=True))


if __name__ == '__main__':
    main()
