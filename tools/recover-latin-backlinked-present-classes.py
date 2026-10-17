#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stage backlinked complete present alternates of every verbal class.

The earlier backlinked-present recipe admits only class-three active headers
with explicit parts. This tier applies the same proof, a standalone source
entry whose sole full orthography is the alternate and whose text is a bare
``v. TARGET.`` reference, to the other present classes: second and fourth
conjugation, regular first-conjugation and ``-ire`` derivatives, deponents,
and headers whose only inflection field is an infinitive. It stages one
present record per alternate under the lemma's existing present class and
supplies no perfect or supine. Lexical values stay private.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import re

spec = importlib.util.spec_from_file_location('backlinked', Path(__file__).with_name('recover-latin-backlinked-present.py'))
backlinked = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backlinked)
regular, first = backlinked.regular, backlinked.first
letters = regular.letters
NOTATION = str.maketrans('', '', '_^-')
# Present ending of a headword or alternate for each engine class the
# historical filters assign; deponents take the same ending plus r.
ENDINGS = {b'conj2': r'e[_^]?o', b'conj3': r'(?<![ei][_^])(?<![ei])o', b'conj3_io': r'i[_^]?o', b'conj4': r'i[_^]?o',
           b'ire_vb': r'i[_^]?o', b'are_vb': r'(?<![ei][_^])(?<![ei])o', b'conj1': r'(?<![ei][_^])(?<![ei])o'}
# Inflection fields a standalone reference may carry for each class.
COMPATIBLE = {b'conj2': {'e_re', 'ere', '2', 'e_ri'}, b'conj3': {'e^re', 'ere', '3', 'i'},
              b'conj3_io': {'e^re', 'ere', '3', 'i'}, b'conj4': {'i_re', 'ire', '4', 'i_ri'},
              b'ire_vb': {'i_re', 'ire', '4', 'i_ri'}, b'are_vb': {'a_re', 'are', '1', 'a_ri'}, b'conj1': {'a_re', 'are', '1', 'a_ri'}}
RECORD = re.compile(rb'(:vs:|:de:)([^\s]+)[ \t]+(conj2|conj3_io|conj3|conj4|ire_vb|are_vb|conj1)((?: [a-z_]+)*)(\r?\n)?$')


def present_root(spelling, tag, deponent):
    """Root under the class ending, or None when the spelling has another ending."""
    spelling = re.sub(r'#[1-9]$', '', spelling)
    if not re.fullmatch(r'[A-Za-z_^]+(?:-[A-Za-z_^]+)*', spelling):
        return None
    pattern = ENDINGS[tag] + ('r' if deponent else '') + '$'
    match = re.search(pattern, spelling)
    if not match or match.start() == 0 or spelling[:match.start()].endswith('-'):
        return None
    return spelling[:match.start()]


def full_head(entry):
    orths = entry.findall('orth')
    if len(orths) != 1 or orths[0].get('extent') != 'full' or orths[0].get('type') is not None:
        return None
    if any(isinstance(n, first.review.etree._Entity) for n in entry.iter()):
        return None
    head = first.review.projection.normalize(''.join(orths[0].itertext()), 'Latin')
    if head is None or not re.fullmatch(r'[A-Za-z_^]+(?:-[A-Za-z_^]+)*or?', head):
        return None
    return letters(head.encode())


def backlink(entry, target):
    """A standalone 'v. TARGET.' entry; returns its inflection fields or None."""
    text = entry.text or ''; fields = []
    for child in entry:
        if child.tag == 'orth':
            if len(child):
                return None
        elif child.tag == 'itype':
            value = first.review.projection.normalize(''.join(child.itertext()), 'Latin')
            if len(child) or value is None:
                return None
            fields.append(value)
        elif child.tag == 'pos':
            if len(child) or not ''.join(child.itertext()).startswith('v.'):
                return None
        elif child.tag == 'sense':
            if (len(child) != 1 or child[0].tag != 'hi' or child[0].get('rend') != 'ital' or
                    len(child[0]) or ''.join(child.itertext()).strip() != 'init.'):
                return None
            text += 'init.'
        else:
            return None
        text += child.tail or ''
    match = re.fullmatch(r'\s*(?:,\s*)*v\.\s+([A-Za-z]+)(?:\s+init)?\.\s*', text)
    return fields if match and match[1] == target else None


def blocks(candidate):
    lines = candidate.splitlines(keepends=True)
    presents = defaultdict(list); stems = defaultdict(set); counts = Counter(); lemma = None
    for index, line in enumerate(lines):
        if line.startswith(b':le:'):
            lemma = line[4:].strip(); counts[lemma] += 1
            continue
        match = RECORD.fullmatch(line)
        if match and lemma is not None:
            flags = tuple(match[4].split())
            stems[lemma].add(letters(match[2]))
            if b'orth' not in flags and all(f in {b'dep'} for f in flags):
                presents[lemma].append((index, match))
    return lines, presents, stems, counts


def transform(candidate, rows, entries):
    index = defaultdict(list)
    for entry in entries.values():
        head = full_head(entry)
        if head:
            index[head].append(entry)
    lines, presents, stems, block_counts = blocks(candidate)
    counts = Counter(); additions = defaultdict(list)
    for row in rows:
        if row.get('projection_error') is not None or not row.get('full_alternates'):
            continue
        lemma = row['headword'].translate(NOTATION).encode('ascii')
        if block_counts[lemma] != 1:
            counts['rows_without_unique_verbal_block'] += 1; continue
        if len(presents[lemma]) != 1:
            counts['withheld_present_record_not_unique'] += 1; continue
        _, match = presents[lemma][0]
        tag = match[3]; deponent = b'dep' in match[4].split(); prefix = match[1]
        root = present_root(row['headword'], tag, deponent)
        if root is None or letters(root.encode()) != letters(match[2]):
            counts['withheld_headword_outside_present_class'] += 1; continue
        head_letters = letters(re.sub(r'#[1-9]$', '', row['headword']).encode())
        for alt in row['full_alternates']:
            alt_root = present_root(alt, tag, deponent)
            if alt_root is None:
                counts['withheld_alternate_outside_present_class'] += 1; continue
            if letters(alt.encode()) == head_letters:
                counts['withheld_notation_only'] += 1; continue
            matches = index[letters(alt.encode())]
            if len(matches) != 1 or matches[0].get('id') == row['id']:
                counts['withheld_no_unique_standalone_entry'] += 1; continue
            fields = backlink(matches[0], row['source_key'])
            if fields is None:
                counts['withheld_entry_not_a_bare_reference'] += 1; continue
            if any(f not in COMPATIBLE[tag] for f in fields):
                counts['withheld_reference_class_differs'] += 1; continue
            stem = alt_root.encode()
            if letters(stem) in stems[lemma]:
                counts['already_present'] += 1; continue
            stems[lemma].add(letters(stem))
            flags = b' dep' if deponent else b''
            additions[presents[lemma][0][0]].append(prefix + stem + b'\t' + tag + flags + b' orth\n')
            counts['added_records'] += 1; counts['added_' + tag.decode()] += 1
    counts['changed_lemma_blocks'] = len(additions)
    output = []
    for i, line in enumerate(lines):
        output.append(line)
        if i in additions:
            if not line.endswith(b'\n'):
                output.append(b'\n')
            newline = b'\r\n' if line.endswith(b'\r\n') else b'\n'
            output.extend(r[:-1] + newline for r in additions[i])
    return b''.join(output), dict(sorted(counts.items()))


def prepare(candidate, headers, lexica, output, expected=None):
    target = first.private_target(candidate, headers, lexica, output)
    rows, source, revision = regular.alternates.source_alternates(headers, lexica)
    entries, second_source, second_revision = first.review.load_entries(lexica)
    if (source, revision) != (second_source, second_revision):
        raise ValueError('source changed during validation')
    data, counts = transform(candidate.read_bytes(), rows, entries)
    if expected is not None and counts.get('added_records', 0) != expected:
        raise ValueError('unexpected backlinked present count')
    report = {'schema': 1,
              'scope': 'complete same-article present alternates of any verbal class, confirmed by a unique standalone reverse reference; present record only',
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
