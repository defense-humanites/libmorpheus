#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Recover only inchoative presents proved by an exact untagged header tail."""
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
plain = lambda text: text.translate(str.maketrans('', '', '_^-'))


def proof(row, entry):
    if row.get('projection_error') is not None or row.get('id') != entry.get('id'):
        return None
    children = list(entry)
    if len(children) < 4 or [node.tag for node in children[:4]] != ['orth', 'orth', 'bibl', 'sense']:
        return None
    if not re.fullmatch(r'\), [A-Za-z]+i, 3,', ' '.join((children[2].tail or '').split())):
        return None
    label = children[3][0] if len(children[3]) else None
    if (label is None or label.tag != 'hi' or label.get('rend') != 'ital' or
            ' '.join(''.join(label.itertext()).split()) != 'v. inch. n.'):
        return None
    base, _ = first.review.projection.project(entry, 'Latin')
    expected, kind = first.compound.recovery.augment(base, entry)
    fields = lambda record: [(f['name'], f['projection'], f.get('type')) for f in record['fields']]
    if (kind != 'first_sense_italic_verbal_label' or fields(row) != fields(expected) or
            row['headword'] != base['headword'] or
            any(f['name'] not in {'orth', 'pos'} for f in row['fields'])):
        return None
    orths = [f['projection'] for f in row['fields'] if f['name'] == 'orth']
    if (len(orths) != 2 or any(node.get('extent') != 'full' or node.get('type') not in {None, 'alt'} for node in children[:2]) or
            not all(re.fullmatch(r'[A-Za-z_^]+(?:-[A-Za-z_^]+)*[ie]sco', h) for h in orths) or
            {h[-4:] for h in orths} != {'isco', 'esco'} or plain(orths[0][:-4]) != plain(orths[1][:-4])):
        return None
    lemma = plain(row['headword']).encode()
    records = [b':le:' + lemma + b'\n']
    for index, head in enumerate(orths):
        records.append(b':vs:' + head[:-1].encode() + b'\tconj3' + (b' orth' if index else b'') + b'\n')
    return lemma, first.compound.recovery.render(row).encode(), b''.join(records)


def transform(candidate, rows, entries):
    proofs = defaultdict(list)
    for row in rows:
        if row.get('id') not in entries:
            raise ValueError('missing source article')
        result = proof(row, entries[row['id']])
        if result:
            proofs[result[0]].append(result)
    lemmas = {line[4:].strip() for line in candidate.splitlines() if line.startswith(b':le:')}
    lines = candidate.splitlines(keepends=True); additions = {}; counts = Counter()
    for lemma, choices in proofs.items():
        if len(choices) != 1:
            counts['withheld_ambiguous_source'] += 1; continue
        _, raw, records = choices[0]
        if lemma in lemmas:
            counts['withheld_existing_lemma'] += 1; continue
        if lines.count(raw) != 1:
            counts['withheld_missing_or_duplicate_header'] += 1; continue
        additions[raw] = records; counts['recovered_headers'] += 1; counts['added_stem_records'] += 2
    return b''.join(line + additions.get(line, b'') for line in lines), dict(sorted(counts.items()))


def prepare(candidate, headers, lexica, output, expected=None):
    target = first.private_target(candidate, headers, lexica, output)
    rows, source, revision = first.source_rows(headers, lexica)
    entries, second_source, second_revision = first.review.load_entries(lexica)
    if source != second_source or revision != second_revision:
        raise ValueError('source changed during validation')
    data, counts = transform(candidate.read_bytes(), rows, entries)
    if expected is not None and counts.get('recovered_headers', 0) != expected:
        raise ValueError('unexpected recovered header count')
    report = {'schema': 1, 'scope': 'exact untagged conjugation tail; complete inchoative presents only',
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
