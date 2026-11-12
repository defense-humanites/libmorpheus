#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Repair the historical anchor defect on sigmatic suffix parts.

A sigmatic perfect written as a bare suffix (``si``, ``psi``, ``xi``) replaces
the final consonant of the present stem: ``fulcio, si, tum`` is *fulsi,
fultum*, ``nubo, psi`` is *nupsi*. The historical ``latvb`` generic rule
hands ``truncstem()`` the part's first letter and cuts the stem from its
last occurrence; when that letter is absent from the stem nothing is cut and
the suffix is appended to the whole stem (``in-fulcs``, ``e_-nu_bps``,
``re^-fercs``), and when the ``s`` rule, which also matches ``d`` and ``q``,
finds a letter before the stem's last vowel it cuts the root away
(``indulgeo, si`` becomes ``ins``; ``sub-sentio, si`` becomes ``sub-s``).
This tool re-reads the written parts of exactly those blocks whose perfect
and supine records are the historical output and whose historical anchor
lies outside the final consonant cluster, and attaches the suffix after
removing the stem's final consonant instead. It reads no other header,
infers no part and leaves the lexer unchanged; lexical values stay private.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import re

spec = importlib.util.spec_from_file_location('anchor', Path(__file__).with_name('repair-latin-anchor-duplication.py'))
anchor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(anchor)
first = anchor.first
LEXER = anchor.LEXER
SIGMATIC = (b's', b'ps', b'x')
VOWELS = b'aeiou'


def last_vowel(stem):
    """Raw index of the stem's last vowel, or -1."""
    for index in range(len(stem) - 1, -1, -1):
        if stem[index:index + 1] in (b'a', b'e', b'i', b'o', b'u'):
            return index
    return -1


def proof(row, entry, literal):
    """Exact source shape: one sigmatic suffix perfect, optionally a short consonant supine, a digit."""
    result = anchor.proof(row, entry, literal)
    if result is None:
        return None
    lemma, perfsuff, supsuff = result
    if anchor.stripped(perfsuff) not in SIGMATIC:
        return None
    if supsuff is not None:
        core = anchor.stripped(supsuff)
        if not 1 <= len(core) <= 2 or any(byte in VOWELS for byte in core):
            return None
    return lemma, perfsuff, supsuff


def transform(candidate, rows, entries, literal=None):
    literal = anchor.literal_table() if literal is None else literal
    proofs = defaultdict(list)
    for row in rows:
        if row.get('id') not in entries:
            raise ValueError('missing source article')
        result = proof(row, entries[row['id']], literal)
        if result:
            proofs[result[0]].append(result)
    blocks = Counter(); records = defaultdict(list); lemma = None
    pattern = re.compile(rb':vs:([^\s]+)([ \t]+)(conj[0-9a-z_]+|perfstem|pp4)((?: [a-z_]+)*)(\r?\n)?$')
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
        _, perfsuff, supsuff = choices[0]
        by_kind = defaultdict(list)
        for index, match in records[lemma]:
            kind = b'present' if match[3].startswith(b'conj') else match[3]
            by_kind[kind].append((index, match))
        wanted = [b'present', b'perfstem'] + ([b'pp4'] if supsuff else [])
        if any(len(by_kind[kind]) != 1 or by_kind[kind][0][1][4] for kind in wanted) or (
                not supsuff and by_kind[b'pp4']):
            counts['withheld_block_shape_differs'] += 1; continue
        present = by_kind[b'present'][0][1][1]
        if present[-1:] in (b'a', b'e', b'i', b'o', b'u', b'_', b'^', b'-'):
            counts['withheld_vowel_final_stem'] += 1; continue
        cut = anchor.historical_anchor(present, perfsuff[:1])
        prefix = present if cut is None else present[:cut]
        historical = {b'perfstem': prefix + perfsuff, **({b'pp4': prefix + supsuff} if supsuff else {})}
        expected = {b'perfstem': present[:-1] + perfsuff, **({b'pp4': present[:-1] + supsuff} if supsuff else {})}
        actual = {kind: by_kind[kind][0][1][1] for kind in historical}
        if actual != historical:
            counts['already_repaired' if actual == expected else 'withheld_records_not_historical_output'] += 1
            continue
        if cut is not None and cut > last_vowel(present):
            counts['historical_anchor_in_final_cluster'] += 1; continue
        if historical == expected:
            counts['historical_attachment_already_expected'] += 1; continue
        for kind, stem in expected.items():
            index, match = by_kind[kind][0]
            replacements[index] = b':vs:' + stem + match[2] + kind + (match[5] or b'\n')
            counts['repaired_records'] += 1
        counts['repaired_lemma_blocks'] += 1
        counts['letter_absent' if cut is None else 'anchor_before_last_vowel'] += 1
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
              'scope': 'sigmatic suffix perfects (si, psi, xi) with an optional short consonant supine outside the historical literal table; blocks whose records are the historical attachment with the anchor outside the final consonant cluster; suffix attached after the stem minus its final consonant; no other header read',
              'source_revision': revision, 'counts': counts,
              'input_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (candidate, headers, source, LEXER)},
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
