#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay headers whose editor attribution is tagged as an inflection field.

The archival Lewis & Short TEI tags some editor names and citations as
``<itype>`` (``<itype>Ritschl</itype>``, ``<itype>Liv 33</itype>``). When
such a field immediately precedes the real principal parts, the historical
``latvb`` filter treats the attribution as the perfect and concatenates it
to the stem, then ignores the written parts. This tool renders each affected
header without its attribution fields, replays the unchanged historical
filter chain on that single header, and replaces the candidate block with
the replayed records. It infers no stem: every record is the historical
filters' own output. Lexical values stay private.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re

spec = importlib.util.spec_from_file_location('first', Path(__file__).with_name('repair-latin-first-conjugation.py'))
first = importlib.util.module_from_spec(spec)
spec.loader.exec_module(first)
spec = importlib.util.spec_from_file_location('recovery', Path(__file__).with_name('recover-latin-initial-sense.py'))
recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)
spec = importlib.util.spec_from_file_location('probe', Path(__file__).with_name('probe-latin-historical-filter-portability.py'))
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
FILTERS = ('combitype', 'splitlat', 'conj1', 'latvb')
NOTATION = str.maketrans('', '', '_^-')
RECORD = re.compile(rb'(:vs:|:de:|:vb:|:wd:)')


def attribution(value):
    """An ``<itype>`` beginning with an ASCII capital is an attribution, never Latin grammar."""
    return bool(re.fullmatch(r'[A-Z][A-Za-z.]*(?:[ ,]+[A-Za-z0-9.]+)*', value))


def proof(row, entry):
    """Rows with attribution itypes followed by a grammar itype; io-class withheld."""
    if row.get('projection_error') is not None or row.get('id') != entry.get('id'):
        return None, 'withheld_unprojected_or_unjoined'
    fields = row['fields']
    marked = [i for i, f in enumerate(fields) if f['name'] == 'itype' and attribution(f['projection'])]
    if not marked:
        return None, 'no_attribution_field'
    source = [' '.join(''.join(e.itertext()).split()) for e in entry.findall('itype')]
    if not all(fields[i]['projection'] in source for i in marked):
        return None, 'withheld_attribution_not_in_source'
    grammar = [i for i, f in enumerate(fields) if f['name'] == 'itype' and i not in marked]
    if not grammar or max(marked) > max(grammar):
        return None, 'withheld_no_following_grammar_field'
    if re.search(r'i\^?o(?:#[1-9])?$', row['headword']):
        return None, 'withheld_io_class_separate_repair'
    lemma = row['headword'].translate(NOTATION).encode('ascii')
    stripped = dict(row, fields=[f for i, f in enumerate(fields) if i not in marked])
    return (lemma, row, stripped), 'accepted_header'


def replay(row, filters, target, name):
    data = recovery.render(row).encode('utf-8')
    for stage in FILTERS:
        data = probe.run_private([str(filters / stage)], target, name + '-' + stage, data)
    records = []
    for line in data.splitlines(keepends=True):
        if line.startswith(b':le:') or RECORD.match(line):
            records.append(line)
    if not records:
        return None, []
    if not records[0].startswith(b':le:') or any(r.startswith(b':le:') for r in records[1:]):
        raise ValueError('isolated replay did not yield exactly one lemma block')
    return records[0][4:].strip(), records[1:]


def blocks(candidate):
    """Lemma -> (start index, [record line indexes]); records follow ``:le:`` contiguously."""
    lines = candidate.splitlines(keepends=True)
    found = {}; counts = Counter(); lemma = None
    for index, line in enumerate(lines):
        if line.startswith(b':le:'):
            lemma = line[4:].strip(); counts[lemma] += 1
            found[lemma] = (index, [])
        elif lemma is not None and RECORD.match(line) and index == (found[lemma][1] or [found[lemma][0]])[-1] + 1:
            found[lemma][1].append(index)
    return lines, found, counts


def normalized(records):
    return Counter(tuple(r.split()) for r in records)


def transform(candidate, rows, entries, filters, target):
    lines, found, counts_by_lemma = blocks(candidate)
    counts = Counter(); replacements = {}
    for row in rows:
        if row.get('id') not in entries:
            raise ValueError('missing source article')
        result, reason = proof(row, entries[row['id']])
        counts[reason] += 1
        if result is None:
            continue
        lemma, original, stripped = result
        if counts_by_lemma[lemma] != 1:
            counts['withheld_missing_or_duplicate_block'] += 1; continue
        start, indexes = found[lemma]
        current = [lines[i] for i in indexes]
        anchor_lemma, anchor = replay(original, filters, target, lemma.decode('ascii') + '-with')
        if anchor_lemma != lemma or normalized(anchor) != normalized(current):
            counts['withheld_candidate_block_not_reproduced'] += 1; continue
        if not any(re.search(rb'[A-Z]', r.split()[0]) for r in current):
            counts['block_unaffected_by_attribution'] += 1; continue
        replay_lemma, replayed = replay(stripped, filters, target, lemma.decode('ascii') + '-without')
        if replay_lemma is None or not replayed:
            counts['withheld_replay_yields_no_block'] += 1; continue
        if replay_lemma != lemma:
            counts['withheld_replay_lemma_differs'] += 1; continue
        if any(re.search(rb'[A-Z]', r.split()[0]) for r in replayed):
            counts['withheld_replay_still_capitalized'] += 1; continue
        intact = [r for r in current if not re.search(rb'[A-Z]', r.split()[0])]
        stems = Counter(r.split()[0][4:] for r in replayed)
        if Counter(r.split()[0][4:] for r in intact) - stems:
            counts['withheld_replay_drops_an_intact_stem'] += 1; continue
        # The filters may reclass a present kept alive by the attribution
        # (historical conj1 record versus the regular are_vb derivative).
        counts['reclassed_intact_records'] += sum((normalized(intact) - normalized(replayed)).values())
        if lemma in replacements:
            raise ValueError('duplicate replacement')
        replacements[lemma] = (indexes, replayed)
        counts['replaced_lemma_blocks'] += 1
        counts['removed_records'] += len(current); counts['added_records'] += len(replayed)
    output = []; skip = set(); insert = {}
    for lemma, (indexes, replayed) in replacements.items():
        skip.update(indexes); insert[indexes[0]] = replayed
    for index, line in enumerate(lines):
        if index in insert:
            newline = b'\r\n' if line.endswith(b'\r\n') else b'\n'
            output.extend(r[:-1] + newline if r.endswith(b'\n') else r + newline for r in insert[index])
        if index not in skip:
            output.append(line)
    return b''.join(output), dict(sorted(counts.items()))


def prepare(candidate, headers, lexica, filters, output, expected=None):
    target = first.private_target(candidate, headers, lexica, output)
    rows, source, revision = first.source_rows(headers, lexica)
    entries, second_source, second_revision = first.review.load_entries(lexica)
    if source != second_source or revision != second_revision:
        raise ValueError('source changed during validation')
    if any(not (filters / stage).is_file() for stage in FILTERS):
        raise ValueError('historical filter binaries missing')
    target.mkdir(mode=0o700)
    (target / 'replay').mkdir(mode=0o700)
    data, counts = transform(candidate.read_bytes(), rows, entries, filters, target / 'replay')
    if expected is not None and counts.get('replaced_lemma_blocks', 0) != expected:
        raise ValueError('unexpected replaced block count')
    report = {'schema': 1,
              'scope': 'headers whose capitalized <itype> attribution precedes the written parts; single-header replay of the unchanged historical filters; io-class withheld',
              'source_revision': revision, 'counts': counts, 'filters': FILTERS,
              'input_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (candidate, headers, source)},
              'filter_sha256': {stage: hashlib.sha256((filters / stage).read_bytes()).hexdigest() for stage in FILTERS},
              'output_sha256': hashlib.sha256(data).hexdigest()}
    first.write_private(target / 'after.stems', data)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate', 'headers', 'lexica', 'filters', 'private-output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--expected', type=int)
    args = parser.parse_args()
    print(json.dumps(prepare(args.candidate, args.headers, args.lexica, args.filters, args.private_output, args.expected), sort_keys=True))


if __name__ == '__main__':
    main()
