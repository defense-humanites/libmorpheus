#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stage complete alternates only when all three regular parts match the source."""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import re

spec = importlib.util.spec_from_file_location('alternates', Path(__file__).with_name('recover-latin-full-alternates.py'))
alternates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alternates)
first = alternates.first
short = lambda x: x.replace(b'^', b'')
letters = lambda x: x.translate(None, b'_^-' )


def parts(head, field):
    head = re.sub(r'#[1-9]$', '', head)
    if field == 'di, sum, 3' and re.fullmatch(r'[A-Za-z_^]+(?:-[A-Za-z_^]+)*ndo', head):
        root = head[:-1]
        return [(root.encode(), b'conj3'), (root.encode(), b'perfstem'), ((root[:-1]+'s').encode(), b'pp4')]
    if field == 'i_vi, i_tum, 4' and re.fullmatch(r'[A-Za-z_^]+(?:-[A-Za-z_^]+)*i[_^]?o', head):
        root = re.sub(r'i[_^]?o$', '', head)
        return [(root.encode(), b'conj4'), ((root+'i_v').encode(), b'perfstem'), ((root+'i_t').encode(), b'pp4')]
    return None


def transform(candidate, rows):
    sources = defaultdict(list)
    for row in rows:
        if row.get('projection_error') is not None:
            continue
        fields = [f['projection'] for f in row['fields'] if f['name']=='itype']
        primary = parts(row['headword'], fields[0]) if len(fields)==1 else None
        if primary:
            lemma = row['headword'].translate(str.maketrans('', '', '_^-')).encode()
            sources[lemma].append((primary, fields[0], row.get('full_alternates', [])))
    pattern = re.compile(rb':vs:([^\s]+)[ \t]+(conj3|conj4|perfstem|pp4)([^\r\n]*)(?:\r?\n)?$')
    records = defaultdict(list); blocks = Counter(); lemma = None
    for index, line in enumerate(candidate.splitlines(keepends=True)):
        if line.startswith(b':le:'):
            lemma = line[4:].strip(); blocks[lemma] += 1
        match = pattern.fullmatch(line)
        if match:
            records[lemma].append((index, match[1], match[2], match[3].strip()))
    additions = {}; counts = Counter()
    for lemma, choices in sources.items():
        if len(choices)!=1 or blocks[lemma]!=1:
            counts['withheld_ambiguity'] += 1; continue
        primary, field, orthographies = choices[0]
        existing = records[lemma]
        if any(len([r for r in existing if r[2]==tag and not r[3]])!=1 or
               not any(short(r[1])==short(stem) and r[2]==tag and not r[3] for r in existing)
               for stem, tag in primary):
            counts['withheld_unmatched_primary_parts'] += 1; continue
        seen = {(short(r[1]), r[2], r[3]) for r in existing}
        added = []
        for alt in orthographies:
            alternate = parts(alt, field)
            if not alternate:
                counts['withheld_incomplete_or_voice_alternate'] += 1; continue
            if letters(alternate[0][0])==letters(primary[0][0]):
                counts['withheld_notation_only'] += 1; continue
            for stem, tag in alternate:
                key = (short(stem), tag, b'orth')
                if key in seen:
                    counts['already_present'] += 1; continue
                seen.add(key); added.append(b':vs:'+stem+b'\t'+tag+b' orth\n')
                counts['added_records'] += 1
        if added:
            anchor = next(r[0] for r in existing if r[2]==b'pp4' and not r[3])
            additions[anchor] = added; counts['changed_lemma_blocks'] += 1
    output = []
    for index, line in enumerate(candidate.splitlines(keepends=True)):
        output.append(line)
        if index in additions:
            if not line.endswith(b'\n'): output.append(b'\n')
            output.extend(additions[index])
    return b''.join(output), dict(sorted(counts.items()))


def prepare(candidate, headers, lexica, output, expected=None):
    target = first.private_target(candidate, headers, lexica, output)
    rows, source, revision = alternates.source_alternates(headers, lexica)
    data, counts = transform(candidate.read_bytes(), rows)
    if expected is not None and counts.get('added_records',0)!=expected:
        raise ValueError('unexpected added record count')
    report = {'schema':1, 'scope':'complete same-article alternates with all three regular parts matched',
              'source_revision':revision, 'counts':counts,
              'input_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (candidate,headers,source)},
              'output_sha256':hashlib.sha256(data).hexdigest()}
    first.write_private(target, data)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate','headers','lexica','private-output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--expected',type=int)
    args = parser.parse_args()
    print(json.dumps(prepare(args.candidate,args.headers,args.lexica,args.private_output,args.expected),sort_keys=True))


if __name__=='__main__':
    main()
