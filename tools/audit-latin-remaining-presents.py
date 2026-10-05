#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Rebuild private remaining-alternate dossiers; publish aggregates only."""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import re

from lxml import etree

spec = importlib.util.spec_from_file_location('boundary', Path(__file__).with_name('recover-latin-boundary-present.py'))
boundary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(boundary)
regular = boundary.regular
first = regular.first


def inserted_records(before, after):
    old = iter(before.splitlines(keepends=True))
    pending = next(old, None)
    lemma = None
    records = []
    pattern = re.compile(rb':vs:([^\s]+)[ \t]+(conj3|conj3_io)[ \t]+orth\r?\n')
    for line in after.splitlines(keepends=True):
        if line == pending:
            if line.startswith(b':le:'):
                lemma = line[4:].strip()
            pending = next(old, None)
            continue
        match = pattern.fullmatch(line)
        if lemma is None or match is None:
            raise ValueError('diagnostic proposal is not a present-only insertion')
        records.append((lemma, match[1], match[2]))
    if pending is not None:
        raise ValueError('diagnostic proposal changed existing source bytes')
    return records


def spelling_shape(head, alternate):
    left = regular.letters(re.sub(r'#[1-9]$', '', head).encode())
    right = regular.letters(alternate.encode())
    prefix = 0
    while prefix < min(len(left), len(right)) and left[prefix] == right[prefix]:
        prefix += 1
    suffix = 0
    while (suffix < min(len(left), len(right)) - prefix and
           left[-suffix - 1] == right[-suffix - 1]):
        suffix += 1
    removed, inserted = len(left) - prefix - suffix, len(right) - prefix - suffix
    if not removed and not inserted:
        shape = 'notation_only'
    elif removed == inserted == 1:
        shape = 'single_substitution'
    elif not removed:
        shape = 'insertion'
    elif not inserted:
        shape = 'deletion'
    else:
        shape = 'multiple_letter_change'
    segment = 'no_explicit_delimiter'
    if '-' in head:
        initial = regular.letters(head.split('-', 1)[0].encode())
        segment = ('first_delimited_segment_retained' if right.startswith(initial)
                   else 'first_delimited_segment_not_retained')
    return {'shape': shape, 'delimiter_review': segment,
            'common_initial_letters': prefix, 'common_final_letters': suffix,
            'removed_letters': removed, 'inserted_letters': inserted}


def inventory(candidate, rows, entries):
    # This unrestricted proposal is only an inventory selector. It is never
    # written as a stem source, used to build an index or source-qualified.
    selected = boundary.selected_rows(rows, lambda head, alternate: True)
    proposed, counts = regular.transform(candidate, selected, 'present-only')
    records = inserted_records(candidate, proposed)
    if len(records) != counts.get('added_records', 0):
        raise ValueError('diagnostic proposal count differs from inserted records')
    choices = defaultdict(list)
    for row in rows:
        if row['id'] not in entries:
            raise ValueError('missing source article')
    for row in selected:
        lemma = row['headword'].translate(str.maketrans('', '', '_^-')).encode()
        for alternate in dict.fromkeys(row['full_alternates']):
            parts = regular.parts(alternate, '3', present_only=True)
            if parts:
                stem, tag = parts[0]
                choices[(lemma, stem, tag)].append((row['id'], alternate))
    sources = {row['id']: row for row in rows}
    if len(sources) != len(rows):
        raise ValueError('duplicate source article ID')
    dossiers = []
    for lemma, stem, tag in records:
        matches = choices[(lemma, stem, tag)]
        if len(matches) != 1:
            raise ValueError('ambiguous remaining-alternate source identity')
        identity, alternate = matches[0]
        row, entry = sources[identity], entries[identity]
        shape = spelling_shape(row['headword'], alternate)
        dossiers.append({'schema': 1, 'id': identity, 'headword': row['headword'],
                         'alternate': alternate, 'candidate_lemma': lemma.decode(),
                         'proposed_present': stem.decode(), 'conjugation': tag.decode(),
                         'projected_fields': row['fields'],
                         'article_sha256': hashlib.sha256(etree.tostring(entry)).hexdigest(),
                         'article_xml': etree.tostring(entry, encoding='unicode'),
                         'latin_quotes': [''.join(n.itertext()) for n in entry.iter('quote')
                                          if n.get('lang') == 'la'],
                         'spelling_review': shape,
                         'scope': 'private diagnostic; no paradigm approval'})
    dossiers.sort(key=lambda row: (row['id'], row['alternate']))
    report = {'variants': len(dossiers), 'articles': len({row['id'] for row in dossiers}),
              'spelling_shapes': dict(sorted(Counter(row['spelling_review']['shape'] for row in dossiers).items())),
              'delimiter_reviews': dict(sorted(Counter(row['spelling_review']['delimiter_review'] for row in dossiers).items())),
              'quotation_reviews': dict(sorted(Counter('has_latin_quote' if row['latin_quotes'] else 'no_latin_quote'
                                                       for row in dossiers).items()))}
    return dossiers, report


def prepare(candidate, headers, lexica, output, expected=None, expected_articles=None):
    target = first.private_target(candidate, headers, lexica, output)
    rows, source, revision = regular.alternates.source_alternates(headers, lexica)
    entries, second_source, second_revision = first.review.load_entries(lexica)
    if source != second_source or revision != second_revision:
        raise ValueError('source changed during validation')
    original = candidate.read_bytes()
    dossiers, counts = inventory(original, rows, entries)
    if expected is not None and counts['variants'] != expected:
        raise ValueError(f"remaining variant count {counts['variants']} differs from expected {expected}")
    if expected_articles is not None and counts['articles'] != expected_articles:
        raise ValueError(f"remaining article count {counts['articles']} differs from expected {expected_articles}")
    data = ''.join(json.dumps(row, sort_keys=True, ensure_ascii=True) + '\n' for row in dossiers).encode()
    report = {'schema': 1, 'scope': 'remaining complete class-three alternates; diagnostics only',
              'source_revision': revision, 'counts': counts,
              'input_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in (candidate, headers, source)},
              'private_inventory_sha256': hashlib.sha256(data).hexdigest()}
    if candidate.read_bytes() != original:
        raise ValueError('candidate changed during inventory review')
    first.write_private(target, data)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate', 'headers', 'lexica', 'private-output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--expected', type=int)
    parser.add_argument('--expected-articles', type=int)
    args = parser.parse_args()
    print(json.dumps(prepare(args.candidate, args.headers, args.lexica, args.private_output,
                             args.expected, args.expected_articles), sort_keys=True))


if __name__ == '__main__':
    main()
