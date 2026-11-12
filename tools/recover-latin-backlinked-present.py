#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stage same-article presents confirmed by an independent reverse reference."""
import argparse
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import re

spec = importlib.util.spec_from_file_location('boundary', Path(__file__).with_name('recover-latin-boundary-present.py'))
boundary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(boundary)
regular, first = boundary.regular, boundary.first


def full_head(entry):
    orths = entry.findall('orth')
    if len(orths) != 1 or orths[0].get('extent') != 'full' or orths[0].get('type') is not None:
        return None
    if any(isinstance(n, first.review.etree._Entity) for n in entry.iter()):
        return None
    head = first.review.projection.normalize(''.join(orths[0].itertext()), 'Latin')
    if head is None or not re.fullmatch(r'[A-Za-z_^]+(?:-[A-Za-z_^]+)*o', head):
        return None
    return regular.letters(head.encode())


def backlink(entry, target):
    """Accept a standalone 'v. TARGET.' entry, never an embedded reference."""
    text = entry.text or ''
    for child in entry:
        if child.tag == 'orth':
            if len(child):
                return False
        elif child.tag == 'itype':
            value = first.review.projection.normalize(''.join(child.itertext()), 'Latin')
            if len(child) or value not in {'3', 'ere', 'e^re', 'e_re'}:
                return False
        elif child.tag == 'pos':
            if len(child) or ''.join(child.itertext()) not in {'v. a.', 'v. n.'}:
                return False
        elif child.tag == 'sense':
            # One source uses a separately encoded 'init.' qualifier.
            if (len(child) != 1 or child[0].tag != 'hi' or child[0].get('rend') != 'ital' or
                    len(child[0]) or ''.join(child.itertext()).strip() != 'init.'):
                return False
            text += 'init.'
        else:
            return False
        text += child.tail or ''
    match = re.fullmatch(r'\s*(?:,\s*)*v\.\s+([A-Za-z]+)(?:\s+init)?\.\s*', text)
    return bool(match and match[1] == target)


def select(rows, entries):
    index = defaultdict(list)
    for entry in entries.values():
        head = full_head(entry)
        if head:
            index[head].append(entry)
    selected = []
    for row in boundary.selected_rows(rows, lambda head, alternate: True):
        admitted = []
        for alt in row['full_alternates']:
            matches = index[regular.letters(alt.encode())]
            if (len(matches) == 1 and matches[0].get('id') != row['id'] and
                    backlink(matches[0], row['source_key'])):
                admitted.append(alt)
        if admitted:
            row['full_alternates'] = admitted
            selected.append(row)
    return selected


def transform(candidate, rows, entries):
    return regular.transform(candidate, select(rows, entries), 'present-only')


def prepare(candidate, headers, lexica, output, expected=None):
    target = first.private_target(candidate, headers, lexica, output)
    rows, source, revision = regular.alternates.source_alternates(headers, lexica)
    entries, second_source, second_revision = first.review.load_entries(lexica)
    if (source, revision) != (second_source, second_revision):
        raise ValueError('source changed during validation')
    data, counts = transform(candidate.read_bytes(), rows, entries)
    if expected is not None and counts.get('added_records', 0) != expected:
        raise ValueError('unexpected backlinked present count')
    report = {'schema': 1, 'scope': 'same-article full present alternate with a unique standalone reverse reference',
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
