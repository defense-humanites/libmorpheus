#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stage complete source alternates with bounded prefix-boundary spellings."""
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


def boundary_pair(head, alternate):
    """Recognize only explicit whole-word boundary transformations."""
    head = re.sub(r'#[1-9]$', '', head)
    literal = lambda value: regular.letters(value.encode())
    for pattern, replacement in [(r'a[_^]?-(?P<root>[A-Za-z_^]+o)', b'ab'),
                                 (r'dis-(?P<root>[A-Za-z_^]+o)', b'di'),
                                 (r'trans-(?P<root>[A-Za-z_^]+o)', b'tra')]:
        match = re.fullmatch(pattern, head)
        if match and literal(alternate) == replacement + literal(match['root']):
            return True
    match = re.fullmatch(r'ex-(s[A-Za-z_^]+o)', head)
    if match and literal(alternate) == b'ex' + literal(match[1])[1:]:
        return True
    match = re.fullmatch(r'trans-(s[A-Za-z_^]+o)', alternate)
    if (match and re.fullmatch(r'tran[A-Za-z_^]+o', head) and
            literal(head) == b'tran' + literal(match[1])):
        return True
    return False


def selected_rows(rows, predicate):
    selected = []
    for row in rows:
        fields = [f['projection'] for f in row['fields'] if f['name'] == 'itype']
        if (row.get('projection_error') is not None or len(fields) != 1 or
                not re.fullmatch(r'[A-Za-z_^]+(?:, [A-Za-z_^]+)?, 3', fields[0]) or
                any(f['name'] == 'pos' and f['projection'] not in {'v. a.', 'v. n.'} for f in row['fields'])):
            continue
        admitted = [alt for alt in row.get('full_alternates', []) if predicate(row['headword'], alt)]
        if admitted:
            trial = copy.deepcopy(row)
            trial['full_alternates'] = admitted
            for field in trial['fields']:
                if field['name'] == 'itype':
                    field['projection'] = '3'
            selected.append(trial)
    return selected


def transform(candidate, rows):
    return regular.transform(candidate, selected_rows(rows, boundary_pair), 'present-only')


def prepare(candidate, headers, lexica, output, expected=None):
    target = first.private_target(candidate, headers, lexica, output)
    rows, source, revision = regular.alternates.source_alternates(headers, lexica)
    data, counts = transform(candidate.read_bytes(), rows)
    if expected is not None and counts.get('added_records', 0) != expected:
        raise ValueError('unexpected added record count')
    report = {'schema': 1, 'scope': 'complete source class-three present alternates with bounded prefix-boundary transformations',
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
