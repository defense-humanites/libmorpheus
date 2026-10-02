#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stage complete third-conjugation alternates attested in Latin quotations."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re

spec = importlib.util.spec_from_file_location('regular', Path(__file__).with_name('recover-latin-regular-parts-alternates.py'))
regular = importlib.util.module_from_spec(spec)
spec.loader.exec_module(regular)
first = regular.first


def cited_alternates(row, entry):
    """Require a whole quoted word from a bounded present paradigm."""
    fields = [f['projection'] for f in row['fields'] if f['name'] == 'itype']
    if (row.get('projection_error') is not None or len(fields) != 1 or
            not re.fullmatch(r'[A-Za-z_^]+(?:, [A-Za-z_^]+)?, 3', fields[0]) or
            any(f['name'] == 'pos' and f['projection'] not in {'v. a.', 'v. n.'} for f in row['fields'])):
        return []
    primary = regular.parts(row['headword'], '3', present_only=True)
    if not primary:
        return []
    words = set()
    for quote in entry.iter('quote'):
        if quote.get('lang') != 'la':
            continue
        for word in re.findall(r'[^\W\d_]+', ''.join(quote.itertext()), re.UNICODE):
            projected = first.review.projection.normalize(word, 'Latin')
            if projected is not None:
                words.add(regular.letters(projected.encode()).lower())
    admitted = []
    for alt in row.get('full_alternates', []):
        parts = regular.parts(alt, '3', present_only=True)
        if not parts or parts[0][1] != primary[0][1]:
            continue
        stem, tag = parts[0]
        endings = (b'io is it imus itis iunt ere iam ias iat iamus iatis iant'
                   if tag == b'conj3_io' else b'o is it imus itis unt ere am as at amus atis ant').split()
        if any(regular.letters(stem + ending).lower() in words for ending in endings):
            admitted.append(alt)
    return admitted


def transform(candidate, rows, entries):
    selected = []
    for row in rows:
        if row['id'] not in entries:
            raise ValueError('missing source article')
        admitted = cited_alternates(row, entries[row['id']])
        if admitted:
            trial = copy.deepcopy(row)
            trial['full_alternates'] = admitted
            for field in trial['fields']:
                if field['name'] == 'itype':
                    field['projection'] = '3'
            selected.append(trial)
    return regular.transform(candidate, selected, 'present-only')


def prepare(candidate, headers, lexica, output, expected=None):
    target = first.private_target(candidate, headers, lexica, output)
    rows, source, revision = regular.alternates.source_alternates(headers, lexica)
    entries, second_source, second_revision = first.review.load_entries(lexica)
    if source != second_source or revision != second_revision:
        raise ValueError('source changed during validation')
    data, counts = transform(candidate.read_bytes(), rows, entries)
    if expected is not None and counts.get('added_records', 0) != expected:
        raise ValueError('unexpected added record count')
    report = {'schema': 1, 'scope': 'complete class-three present alternates with whole-word Latin quotation evidence',
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
