#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Repair the historical anchor defect on written principal parts.

For a consonant-initial principal-part string ending in a conjugation digit
that the historical ``latvb`` table does not list, ``is_spectype()`` hands
``do_vstems()`` the first letter of the written perfect as the trim: the
present stem is cut from the *last* occurrence of that letter and the
written part is appended. When the part repeats the stem's own letters, as
in ``volvo, volvi, volutum`` or ``vivo, vixi, victum``, the last occurrence
lies inside the letters the part already contains and the result doubles
them (``volvolv``, ``vi_vix``, ``bi^bi^b``, ``inscenscend``). This tool
re-reads the written parts of exactly those blocks whose perfect and supine
records are the historical output and whose trimmed prefix ends with two or
more of the part's leading letters, and anchors the part at the earliest
occurrence of its first two letters in the present stem instead. It reads
no other header, infers no part and leaves the lexer unchanged; lexical
values stay private.
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
REPO = Path(__file__).resolve().parents[1]
LEXER = REPO / 'src/gkdict/latvb.l'
STRIP = b'_^-'
SHAPE = re.compile(r'([a-z_^]+i), (?:([a-z_^]+um), )?([1-4])')


def literal_table(lexer=LEXER):
    """The itype strings the historical filter handles by an explicit case, outside the generic anchor."""
    return set(re.findall(r'strcmp\(yytext,"<itype>([^"]*)</itype>"\)', lexer.read_text(errors='replace')))


def stripped(stem):
    return stem.translate(None, STRIP)


def historical_anchor(stem, letter):
    """Emulate truncstem(): cut from the last occurrence of the trim letter (s also matches d and q)."""
    for index in range(len(stem) - 1, -1, -1):
        byte = stem[index:index + 1]
        if byte == letter or (letter == b's' and byte in (b'd', b'q')):
            return index
    return None


def duplicated(prefix, part):
    """Letters the attachment doubled: the longest lead of the part that the trimmed prefix ends with."""
    prefix, part = stripped(prefix), stripped(part)
    return max((k for k in range(2, min(len(prefix), len(part)) + 1) if prefix.endswith(part[:k])), default=0)


def earliest_anchor(stem, part):
    """Raw index in the stem of the earliest occurrence of the part's first two letters, notation disregarded."""
    lead = stripped(part)[:2]
    if len(lead) < 2:
        return None
    found = stripped(stem).find(lead)
    if found < 0:
        return None
    plain = 0
    for index in range(len(stem)):
        if stem[index:index + 1] in (b'_', b'^', b'-'):
            continue
        if plain == found:
            return index
        plain += 1
    return None


def proof(row, entry, literal):
    """Exact source shape: one consonant-initial, digit-terminated written part string outside the literal table."""
    if row.get('projection_error') is not None or row.get('id') != entry.get('id'):
        return None
    base, _ = first.review.projection.project(entry, 'Latin')
    if base.get('projection_error') is not None:
        return None
    itypes = [f['projection'] for f in row['fields'] if f['name'] == 'itype']
    source_itypes = [f['projection'] for f in base['fields'] if f['name'] == 'itype']
    if len(itypes) != 1 or itypes != source_itypes or itypes[0] in literal:
        return None
    match = SHAPE.fullmatch(itypes[0])
    if not match or itypes[0][0] in 'aeioux':
        return None
    perfect, supine, _ = match.groups()
    lemma = row['headword'].translate(str.maketrans('', '', '_^-')).encode()
    return lemma, perfect[:-1].encode(), supine[:-2].encode() if supine else None


def transform(candidate, rows, entries, literal=None):
    literal = literal_table() if literal is None else literal
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
        anchor = historical_anchor(present, perfsuff[:1])
        prefix = present if anchor is None else present[:anchor]
        historical = {b'perfstem': prefix + perfsuff, **({b'pp4': prefix + supsuff} if supsuff else {})}
        earliest = earliest_anchor(present, perfsuff)
        if earliest is None or (anchor is not None and earliest >= anchor):
            expected = None
        else:
            expected = {b'perfstem': present[:earliest] + perfsuff,
                        **({b'pp4': present[:earliest] + supsuff} if supsuff else {})}
        actual = {kind: by_kind[kind][0][1][1] for kind in historical}
        if actual != historical:
            counts['already_repaired' if actual == expected else 'withheld_records_not_historical_output'] += 1
            continue
        if not duplicated(prefix, perfsuff):
            counts['historical_attachment_without_duplication'] += 1; continue
        if expected is None or duplicated(present[:earliest], perfsuff):
            counts['withheld_duplication_without_earlier_anchor'] += 1; continue
        for kind, stem in expected.items():
            index, match = by_kind[kind][0]
            replacements[index] = b':vs:' + stem + match[2] + kind + (match[5] or b'\n')
            counts['repaired_records'] += 1
        counts['repaired_lemma_blocks'] += 1
        counts['doubled_letters_%d' % duplicated(prefix, perfsuff)] += 1
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
              'scope': 'consonant-initial digit-terminated written parts outside the historical literal table; blocks whose perfect and supine are the historical last-letter attachment with doubled letters; re-anchored at the earliest occurrence of the part; no other header read',
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
