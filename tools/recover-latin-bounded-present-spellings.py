#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stage explicit same-article present spellings with bounded whole-word rules."""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import re

spec = importlib.util.spec_from_file_location('audit', Path(__file__).with_name('audit-latin-remaining-presents.py'))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
regular, first = audit.regular, audit.first


def spelling_rule(head, alternate):
    if '#' in head:
        return None
    left, right = (regular.letters(value.encode()).decode() for value in (head, alternate))
    match = re.fullmatch(r'con(i[A-Za-z]+io)', left)
    if match and right == 'co' + match[1]:
        return 'nasal_omission_before_initial_i'
    prefix = regular.letters(head.split('-', 1)[0].encode()).decode() if '-' in head else None
    match = re.fullmatch(r'ef(fi[A-Za-z]+io)', left)
    if prefix == 'ef' and match and right == 'ec' + 'fa' + match[1][2:]:
        return 'explicit_prefix_before_f_and_source_vowel_restoration'
    if len(left) == len(right) and left[:1] == right[:1]:
        changed = [i for i, pair in enumerate(zip(left, right)) if pair[0] != pair[1]]
        if (len(changed) == 1 and changed[0] + 1 < len(left) and
                {left[changed[0]], right[changed[0]]} == {'c', 'g'} and left[changed[0] + 1] == 'l'):
            return 'single_stop_alternation_before_l'
    match = re.fullmatch(r'are([A-Za-z]+io)', left)
    if prefix == 'are' and match and right == 'ar' + match[1]:
        return 'vowel_elision_at_explicit_prefix_boundary'
    match = re.fullmatch(r'tra(i[A-Za-z]+io)', left)
    if match and right in {'trans' + match[1], 'transj' + match[1]}:
        return 'short_and_full_preverb_before_initial_i_with_optional_j'
    return None


def selected_rows(rows):
    return audit.boundary.selected_rows(rows, lambda head, alternate: spelling_rule(head, alternate) is not None)


def present_family(stem, tag):
    root = regular.letters(stem).decode().lower()
    io = tag == b'conj3_io'
    if tag not in {b'conj3', b'conj3_io'}:
        raise ValueError('unsupported present family')
    records = []
    for mood, endings in [(4, ['io' if io else 'o', 'is', 'it', 'imus', 'itis', 'iunt' if io else 'unt']),
                          (8, ['iam', 'ias', 'iat', 'iamus', 'iatis', 'iant'] if io else ['am', 'as', 'at', 'amus', 'atis', 'ant'])]:
        for i, ending in enumerate(endings):
            records.append({'form': root + ending, 'person': i % 3 + 1,
                            'number': 1 if i < 3 else 3, 'mood': mood})
    records.append({'form': root + 'ere', 'person': 0, 'number': 0, 'mood': 5})
    return records


def prepare(candidate, headers, lexica, output, expected=None, witness_output=None):
    target = first.private_target(candidate, headers, lexica, output)
    witness_target = first.private_target(candidate, headers, lexica, witness_output) if witness_output is not None else None
    targets = [p for p in (target, witness_target) if p is not None]
    if len(set(targets)) != len(targets):
        raise ValueError('candidate and witness outputs must differ')
    if any(p.exists() or p.is_symlink() for p in targets):
        raise FileExistsError('private output already exists')
    rows, source, revision = regular.alternates.source_alternates(headers, lexica)
    selected = selected_rows(rows)
    before = candidate.read_bytes()
    after, counts = regular.transform(before, selected, 'present-only')
    choices = defaultdict(list)
    for row in selected:
        lemma = row['headword'].translate(str.maketrans('', '', '_^-')).encode()
        for alt in row['full_alternates']:
            parts = regular.parts(alt, '3', present_only=True)
            if parts:
                choices[(lemma, *parts[0])].append((row, alt))
    witnesses = []
    rules = Counter()
    for lemma, stem, tag in audit.inserted_records(before, after):
        matches = choices[(lemma, stem, tag)]
        if len(matches) != 1:
            raise ValueError('ambiguous bounded alternate source identity')
        row, alt = matches[0]
        rule = spelling_rule(row['headword'], alt)
        rules[rule] += 1
        witnesses.append({'schema': 1, 'lemma': lemma.decode(), 'rule': rule,
                          'source_revision': revision,
                          'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                          'headers_sha256': hashlib.sha256(headers.read_bytes()).hexdigest(),
                          'candidate_sha256': hashlib.sha256(after).hexdigest(),
                          'forms': present_family(stem, tag)})
    if len(witnesses) != counts.get('added_records', 0):
        raise ValueError('present-family witness count differs')
    if expected is not None and len(witnesses) != expected:
        raise ValueError('unexpected bounded present count: ' + json.dumps(counts, sort_keys=True))
    witness_data = ''.join(json.dumps(row, sort_keys=True) + '\n' for row in witnesses).encode()
    report = {'schema': 1, 'scope': 'explicit whole-word present alternates with bounded source spelling rules',
              'source_revision': revision, 'counts': counts, 'spelling_rules': dict(sorted(rules.items())),
              'source_families': len(witnesses), 'expected_family_cells': 13 * len(witnesses),
              'input_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (candidate, headers, source)},
              'output_sha256': hashlib.sha256(after).hexdigest(),
              'private_witness_sha256': hashlib.sha256(witness_data).hexdigest()}
    first.write_private(target, after)
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
    print(json.dumps(prepare(args.candidate, args.headers, args.lexica, args.private_output,
                             args.expected, args.private_witness), sort_keys=True))


if __name__ == '__main__':
    main()
