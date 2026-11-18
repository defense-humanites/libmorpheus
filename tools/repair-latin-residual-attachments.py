#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Repair four residual attachment defects of the historical Latin verb lexer.

The written-part anchor and sigmatic suffix repairs left four small defect
families in the changed-definition dossiers, each visible from the source
header and the historical ``latvb`` rule alone:

* **Vowel-anchored special parts.** ``spectypes[]`` strings such as ``e_mi,
  emptum, 3``, ``exi, ectum, 3`` or ``e_vi, e_tum, 2`` hand ``truncstem()``
  a vowel. When that vowel is absent from the root or found only in the
  preverb, the stem is appended whole (``a^d-i^me_m``) or cut back to the
  preverb's vowel (``ex-i^mo`` gives ``e_m``, ``de_-spi^ci^o`` gives
  ``dex``). A second-conjugation stem lost its thematic vowel to the lemma
  stripping (``ex-pl`` for *expleo*) and takes the part whole; any other
  stem takes it from the root's last vowel (``ex-e_m``, ``de_-spex``).
* **Doubled u.** The literal ``u^i`` cases attach ``u^`` without trimming;
  on a stem that already ends in ``u`` (*congruo*, *arguo*, *tribuo*) the
  perfect stem is doubled (``congru^u^``). The perfect stem is the present
  stem itself.
* **Second-conjugation lemma read as third.** The class-less ``u^i`` and
  ``e^re`` cases default to ``conj3``; a headword in ``-eo``, whose ending
  the lemma stripping removes, is second conjugation (*sileo*, *exsorbeo*).
* **Suffix supine after a final consonant.** A deponent supine written as a
  bare ``psus`` or ``ctus`` suffix replaces the stem's final consonant
  (*illabor, lapsus*; *praevehor, vectus*); with the letter absent the
  historical rule appends it (``illa_bps``, ``prae-ve^hct``).

The tool acts only on blocks whose records are exactly the historical
output, reads no other header, infers no part and leaves the lexer
unchanged; lexical values stay private.
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
VOWELS = (b'a', b'e', b'i', b'o', b'u')
NOTATION = (b'_', b'^', b'-')
PARTS = re.compile(r'([a-z_^]+i), (?:([a-z_^]+um), )?([1-4])')
SUPINE = re.compile(r'([a-z_^]+us), ([1-4])')
SUFFIXES = (b'ps', b'ct')
CLASSLESS = ('u^i', 'e^re')


def lexer_tables(lexer=LEXER):
    """Literal cases with their trim argument, and spectypes[], from the lexer with its C comments removed.

    The reader shared with the joined-itype repair: a case inside a C comment
    (``u^i, u_tum, 3`` trimming nothing, commented out in the lexer) is not
    live, and a trim given as a character literal (``'d'``, ``'u'``, ``'v'``,
    ``'q'``) is a case like any other.
    """
    text = re.sub(r'/\*.*?\*/', '', lexer.read_text(errors='replace'), flags=re.S)
    literal = {}
    for match in re.finditer(r'strcmp\(yytext,"<itype>([^"]*)</itype>"\)\s*\)\s*return\(\s*do(?:verb|_vstems)\("([^"]+)"(?:,\s*(0|1|yytext\[7\]|\'[a-z]\'))?\s*\)', text):
        literal.setdefault(match.group(1), (match.group(2), match.group(3)))
    table = re.search(r'char \*spectypes\[\] = \{(.*?)\};', text, re.S).group(1)
    return literal, set(re.findall(r'"<itype>(.*?)</itype>"', table))


def single_itype(row, entry):
    """The lemma and the one itype string of a header whose projection equals the source's."""
    if row.get('projection_error') is not None or row.get('id') != entry.get('id'):
        return None
    base, _ = first.review.projection.project(entry, 'Latin')
    if base.get('projection_error') is not None:
        return None
    itypes = [f['projection'] for f in row['fields'] if f['name'] == 'itype']
    source_itypes = [f['projection'] for f in base['fields'] if f['name'] == 'itype']
    if len(itypes) != 1 or itypes != source_itypes:
        return None
    headword = row['headword'].translate(str.maketrans('', '', '_^-'))
    return headword.encode(), itypes[0]


def proof(row, entry, literal, spectypes):
    """Exact source shape of one of the four defect families, or None."""
    found = single_itype(row, entry)
    if found is None:
        return None
    lemma, itype = found
    if itype in spectypes and itype[0] in 'aeiou':
        match = PARTS.fullmatch(itype)
        if match:
            perfect, supine, _ = match.groups()
            return lemma, 'vowel_anchor', perfect[:-1].encode(), supine[:-2].encode() if supine else None
    case = literal.get(itype)
    if itype in CLASSLESS and case is not None and case[0] == 'conj3' and lemma.endswith(b'eo'):
        return lemma, 'eo_class', None, None
    if case is not None and case[1] == '0' and re.fullmatch(r'u\^i(?:, [1-4])?', itype):
        return lemma, 'doubled_u', b'u^', None
    if itype not in literal and itype not in spectypes and itype[0] not in 'aeioux':
        match = SUPINE.fullmatch(itype)
        if match and anchor.stripped(match.group(1)[:-2].encode()) in SUFFIXES:
            return lemma, 'suffix_supine', None, match.group(1)[:-2].encode()
    return None


def root_last_vowel(stem):
    """Raw index of the last vowel after the stem's last hyphen, or None."""
    for index in range(len(stem) - 1, stem.rfind(b'-'), -1):
        if stem[index:index + 1] in VOWELS:
            return index
    return None


def expected_records(kind, present, klass, perfsuff, supsuff):
    """Historical and expected perfstem/pp4 records of one block, or None when the shape is outside the recipe."""
    if kind == 'vowel_anchor':
        cut = anchor.historical_anchor(present, perfsuff[:1])
        hyphen = present.rfind(b'-')
        if cut is not None and cut > hyphen:
            return None, 'historical_anchor_in_root'
        prefix = present if cut is None else present[:cut]
        historical = {b'perfstem': prefix + perfsuff, **({b'pp4': prefix + supsuff} if supsuff else {})}
        if klass == b'conj2':
            root = present
        else:
            vowel = root_last_vowel(present)
            root = present if vowel is None else present[:vowel]
        expected = {b'perfstem': root + perfsuff, **({b'pp4': root + supsuff} if supsuff else {})}
        return (historical, expected), None
    if kind == 'doubled_u':
        if present[-2:] not in (b'u^', b'u_') and present[-1:] != b'u':
            return None, 'stem_not_ending_in_u'
        return ({b'perfstem': present + perfsuff}, {b'perfstem': present}), None
    if kind == 'suffix_supine':
        if present[-1:] in VOWELS + NOTATION:
            return None, 'withheld_vowel_final_stem'
        if anchor.historical_anchor(present, supsuff[:1]) is not None:
            return None, 'historical_anchor_in_stem'
        return ({b'pp4': present + supsuff}, {b'pp4': present[:-1] + supsuff}), None
    raise ValueError(kind)


def transform(candidate, rows, entries, tables=None):
    literal, spectypes = lexer_tables() if tables is None else tables
    proofs = defaultdict(list)
    for row in rows:
        if row.get('id') not in entries:
            raise ValueError('missing source article')
        result = proof(row, entries[row['id']], literal, spectypes)
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
        _, kind, perfsuff, supsuff = choices[0]
        by_kind = defaultdict(list)
        for index, match in records[lemma]:
            by_kind[b'present' if match[3].startswith(b'conj') else match[3]].append((index, match))
        if len(by_kind[b'present']) != 1 or by_kind[b'present'][0][1][4]:
            counts['withheld_block_shape_differs'] += 1; continue
        index, match = by_kind[b'present'][0]
        present, klass = match[1], match[3]
        if kind == 'eo_class':
            if klass != b'conj3':
                counts['withheld_present_class_differs'] += 1; continue
            replacements[index] = b':vs:' + present + match[2] + b'conj2' + (match[5] or b'\n')
            counts['repaired_records'] += 1; counts['repaired_lemma_blocks'] += 1; counts[kind] += 1
            continue
        result, reason = expected_records(kind, present, klass, perfsuff, supsuff)
        if result is None:
            counts[reason] += 1; continue
        historical, expected = result
        wanted = list(historical)
        if any(len(by_kind[k]) != 1 or by_kind[k][0][1][4] for k in wanted) or any(
                by_kind[k] for k in (b'perfstem', b'pp4') if k not in wanted):
            counts['withheld_block_shape_differs'] += 1; continue
        actual = {k: by_kind[k][0][1][1] for k in wanted}
        if actual != historical:
            counts['already_repaired' if actual == expected else 'withheld_records_not_historical_output'] += 1
            continue
        if historical == expected:
            counts['historical_attachment_already_expected'] += 1; continue
        for k, stem in expected.items():
            index, match = by_kind[k][0]
            replacements[index] = b':vs:' + stem + match[2] + k + (match[5] or b'\n')
            counts['repaired_records'] += 1
        counts['repaired_lemma_blocks'] += 1; counts[kind] += 1
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
              'scope': 'four residual attachment families of the historical lexer, each proven by the single source itype and the block being the exact historical output: vowel-anchored spectypes[] parts whose anchor lies outside the root, literal u^i perfects doubled on a stem in -u, class-less u^i and e^re headwords in -eo read as conj3, and bare psus/ctus deponent supines appended after a final consonant; no other header read',
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
