#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Repair the historical short-suffix defect after a labiovelar present.

For a ``-quo``/``-guo`` headword with the abbreviated parts ``xi, ctum, 3``,
the historical ``latvb`` trim removes only the final ``u`` before appending
the suffix, producing ``qx``/``gx`` and ``qct``/``gct`` stems. The written
``x`` already contains the velar; this tool replaces exactly those two
defective records with the stem ending in ``x`` and ``ct``. Lexical values
stay private.
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


def proof(row, entry):
    """Exact source shape: labiovelar active headword and literal ``xi, ctum, 3``."""
    if row.get('projection_error') is not None or row.get('id') != entry.get('id'):
        return None
    base, _ = first.review.projection.project(entry, 'Latin')
    if base.get('projection_error') is not None:
        return None
    itypes = [(i, f['projection']) for i, f in enumerate(row['fields']) if f['name'] == 'itype']
    source_itypes = [f['projection'] for f in base['fields'] if f['name'] == 'itype']
    if len(itypes) != 1 or itypes[0][1] != 'xi, ctum, 3' or source_itypes != ['xi, ctum, 3']:
        return None
    match = re.fullmatch(r'([a-z_^]+-)?([a-z_^]+[qg]u)o(#[1-9])?', row['headword'])
    if not match:
        return None
    prefix, radical, _ = match.groups()
    # The written x already contains the velar; only ``qu``/``gu`` is removed.
    if len(radical.translate(NOTATION)) < 3:
        return None
    lemma = row['headword'].translate(NOTATION).encode()
    present = ((prefix or '') + radical).encode()
    velarless = ((prefix or '') + radical[:-2]).encode()
    return lemma, present, velarless


def transform(candidate, rows, entries):
    proofs = defaultdict(list)
    for row in rows:
        if row.get('id') not in entries:
            raise ValueError('missing source article')
        result = proof(row, entries[row['id']])
        if result:
            proofs[result[0]].append(result)
    blocks = Counter(); records = defaultdict(list); lemma = None
    pattern = re.compile(rb':vs:([^\s]+)([ \t]+)(conj3|perfstem|pp4)((?: [a-z_]+)*)(\r?\n)?$')
    lines = candidate.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.startswith(b':le:'):
            lemma = line[4:].strip(); blocks[lemma] += 1
        match = pattern.fullmatch(line)
        if match and lemma is not None:
            records[lemma].append((index, match))
    replacements = {}; counts = Counter()
    for lemma, choices in sorted(proofs.items()):
        if blocks[lemma] == 0:
            counts['lemma_without_candidate_block'] += 1; continue
        if len(choices) != 1 or blocks[lemma] != 1:
            counts['withheld_ambiguous_lemma_block'] += 1; continue
        _, present, velarless = choices[0]
        by_kind = defaultdict(list)
        for index, match in records[lemma]:
            by_kind[match[3]].append((index, match))
        # The historical trim removed only the final u before appending the suffix.
        expected = {b'conj3': present, b'perfstem': present[:-1] + b'x', b'pp4': present[:-1] + b'ct'}
        if any(len(by_kind[kind]) != 1 or by_kind[kind][0][1][4] for kind in expected):
            counts['withheld_block_shape_differs'] += 1; continue
        if any(by_kind[kind][0][1][1] != stem for kind, stem in expected.items()):
            if (by_kind[b'perfstem'][0][1][1] == velarless + b'x' and by_kind[b'pp4'][0][1][1] == velarless + b'ct'
                    and by_kind[b'conj3'][0][1][1] == present):
                counts['already_repaired'] += 1
            else:
                counts['withheld_unmatched_defective_records'] += 1
            continue
        for kind, suffix in ((b'perfstem', b'x'), (b'pp4', b'ct')):
            index, match = by_kind[kind][0]
            replacements[index] = b':vs:' + velarless + suffix + match[2] + kind + (match[5] or b'\n')
            counts['repaired_records'] += 1
        counts['repaired_lemma_blocks'] += 1
    output = [replacements.get(index, line) for index, line in enumerate(lines)]
    return b''.join(output), dict(sorted(counts.items()))


def prepare(candidate, headers, lexica, output, expected=None):
    target = first.private_target(candidate, headers, lexica, output)
    rows, source, revision = first.source_rows(headers, lexica)
    entries, second_source, second_revision = first.review.load_entries(lexica)
    if source != second_source or revision != second_revision:
        raise ValueError('source changed during validation')
    data, counts = transform(candidate.read_bytes(), rows, entries)
    if expected is not None and counts.get('repaired_records', 0) != expected:
        raise ValueError('unexpected repaired record count')
    report = {'schema': 1,
              'scope': 'labiovelar -quo/-guo headwords with the literal source parts xi, ctum, 3; exact defective perfstem and pp4 records only',
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
