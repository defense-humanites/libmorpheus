#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stage explicit complete present alternates with one internal a/e change."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re

spec = importlib.util.spec_from_file_location('boundary', Path(__file__).with_name('recover-latin-boundary-present.py'))
boundary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(boundary)
first = boundary.first


def vowel_pair(head, alternate):
    head = re.sub(r'#[1-9]$', '', head)
    literal = lambda value: boundary.regular.letters(value.encode())
    left, right = literal(head), literal(alternate)
    if len(left) != len(right):
        return False
    differences = [i for i, (a, b) in enumerate(zip(left, right)) if a != b]
    if len(differences) != 1:
        return False
    index = differences[0]
    if (index < 2 or index >= len(left) - 1 or
            (left[index:index+1], right[index:index+1]) not in {(b'a', b'e'), (b'e', b'a')}):
        return False
    consonants = b'bcdfghjklmnpqrstvwxz'
    if left[index-1] not in consonants or left[index+1] not in consonants:
        return False
    if '-' in head and index < len(literal(head.split('-', 1)[0])):
        return False
    return True


def transform(candidate, rows):
    return boundary.regular.transform(candidate, boundary.selected_rows(rows, vowel_pair), 'present-only')


def prepare(candidate, headers, lexica, output, expected=None):
    target = first.private_target(candidate, headers, lexica, output)
    rows, source, revision = boundary.regular.alternates.source_alternates(headers, lexica)
    data, counts = transform(candidate.read_bytes(), rows)
    if expected is not None and counts.get('added_records', 0) != expected:
        raise ValueError('unexpected added record count')
    report = {'schema': 1, 'scope': 'complete source class-three present alternates with one consonant-bounded internal a/e change',
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
