#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Remove supine records that contain the leaked ``</itype>`` closing tag.

When a source header carries a bare one-token perfect (``u^i``, ``mpsi``)
with neither a supine nor a conjugation digit, ``do_vstems()`` in the historical
``latvb`` filter reads the closing tag as the supine and emits a ``pp4``
record whose stem ends in ``/ityp``. The source supplies no supine, so this
tool deletes exactly that record and nothing else. Lexical values stay
private.
"""
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
NOTATION = str.maketrans('', '', '_^-')
LEAK = re.compile(rb':vs:([^\s]+)/ityp[ \t]+pp4(\r?\n)?$')


def proof(row, entry):
    """A joined header whose only inflection field is a bare one-token perfect in ``-i``."""
    if row.get('projection_error') is not None or row.get('id') != entry.get('id'):
        return None
    base, _ = first.review.projection.project(entry, 'Latin')
    if base.get('projection_error') is not None:
        return None
    itypes = [f['projection'] for f in row['fields'] if f['name'] == 'itype']
    source = [f['projection'] for f in base['fields'] if f['name'] == 'itype']
    if itypes != source or len(itypes) != 1 or not re.fullmatch(r'[a-z_^]+i', itypes[0]):
        return None
    if not re.fullmatch(r'[a-z_^]+(?:-[a-z_^]+)?(?:#[1-9])?', row['headword']):
        return None
    return row['headword'].translate(NOTATION).encode('ascii')


def transform(candidate, rows, entries):
    lemmas = Counter()
    for row in rows:
        if row.get('id') not in entries:
            raise ValueError('missing source article')
        lemma = proof(row, entries[row['id']])
        if lemma:
            lemmas[lemma] += 1
    blocks = Counter(); leaks = defaultdict(list); lemma = None
    lines = candidate.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.startswith(b':le:'):
            lemma = line[4:].strip(); blocks[lemma] += 1
        elif lemma is not None and LEAK.fullmatch(line):
            leaks[lemma].append(index)
    counts = Counter(); removed = set()
    for lemma, indexes in sorted(leaks.items()):
        if lemma not in lemmas:
            counts['withheld_leak_without_bare_perfect_source'] += 1; continue
        if lemmas[lemma] != 1 or blocks[lemma] != 1 or len(indexes) != 1:
            counts['withheld_ambiguous_block'] += 1; continue
        removed.add(indexes[0]); counts['removed_records'] += 1; counts['repaired_lemma_blocks'] += 1
    counts['bare_perfect_headers'] = sum(lemmas.values())
    counts['bare_perfect_headers_without_leak'] = sum(n for l, n in lemmas.items() if l not in leaks)
    return b''.join(line for index, line in enumerate(lines) if index not in removed), dict(sorted(counts.items()))


def prepare(candidate, headers, lexica, output, expected=None):
    target = first.private_target(candidate, headers, lexica, output)
    rows, source, revision = first.source_rows(headers, lexica)
    entries, second_source, second_revision = first.review.load_entries(lexica)
    if source != second_source or revision != second_revision:
        raise ValueError('source changed during validation')
    data, counts = transform(candidate.read_bytes(), rows, entries)
    if expected is not None and counts.get('removed_records', 0) != expected:
        raise ValueError('unexpected removed record count')
    report = {'schema': 1,
              'scope': 'pp4 records whose stem ends in the leaked /ityp tag, under headers whose only inflection field is a bare one-token perfect in -i; deletion only',
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
