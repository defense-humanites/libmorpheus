#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stage abbreviated prefix alternates the historical latvb filter discards.

The historical ``set_orth()`` rule in ``src/gkdict/latvb.l`` expands exactly
four literal abbreviated alternates (``adf-``, ``adl-``, ``adn-``, ``ads-``)
and drops every other ``<orth>`` of that shape. This tool stages the other
abbreviated prefix alternates under bounded, engine-grounded conditions and
keeps every lexical value private.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('first', Path(__file__).with_name('repair-latin-first-conjugation.py'))
first = importlib.util.module_from_spec(spec)
spec.loader.exec_module(first)
PREVERB_TABLE = REPO / 'stemlib/Latin/rule_files/raw_preverbs.table'
LEXER_HANDLED = {'adf-', 'adl-', 'adn-', 'ads-'}
NOTATION = str.maketrans('', '', '_^-')


def preverbs(path=PREVERB_TABLE):
    """Raw Latin preverb spellings known to the engine; the sole prefix oracle."""
    table = set()
    for line in path.read_text().splitlines():
        if not line or line.startswith('#'):
            continue
        table.add(line.split('\t')[0])
    return table


def alignment(alternate, headword, table):
    """One substituted letter inside an engine-known prefix, then shared letters.

    Returns (prefix_length, old_prefix, new_prefix) or a withholding reason.
    The alternate is the abbreviation without its trailing hyphen.
    """
    plain = re.sub(r'#[1-9]$', '', headword).translate(NOTATION)
    if not re.fullmatch(r'[a-z]+', alternate) or len(alternate) < 2:
        return None, 'withheld_alternate_shape'
    if len(alternate) > len(plain):
        return None, 'withheld_alternate_longer_than_headword'
    differences = [i for i in range(len(alternate)) if alternate[i] != plain[i]]
    if not differences:
        return None, 'withheld_identical_spelling'
    if len(differences) != 1 or differences[0] == len(alternate) - 1:
        return None, 'withheld_not_single_prefix_substitution'
    length = differences[0] + 1
    old, new = plain[:length], alternate[:length]
    if old not in table or new not in table:
        return None, 'withheld_prefix_not_in_preverb_table'
    hyphen = re.sub(r'#[1-9]$', '', headword).translate(str.maketrans('', '', '_^')).find('-')
    if hyphen != -1 and hyphen != length:
        return None, 'withheld_explicit_boundary_differs'
    return (length, old, new), None


def proof(row, entry, table):
    """Source alternates for one projected header; never a stem decision."""
    if row.get('projection_error') is not None or row.get('id') != entry.get('id'):
        return None, Counter({'withheld_unprojected_or_unjoined': 1})
    orths = entry.findall('orth')
    if not orths or orths[0].get('extent') != 'full':
        return None, Counter({'withheld_no_full_headword': 1})
    headword = row['headword']
    if not re.fullmatch(r'[A-Za-z_^#0-9-]+', headword) or not ''.join(orths[0].itertext()).strip():
        return None, Counter({'withheld_no_full_headword': 1})
    # Exact historical lemma spelling: remove notation, preserve case and digits.
    lemma = headword.translate(NOTATION).encode('ascii')
    reasons = Counter(); accepted = []
    for orth in orths[1:]:
        text = ' '.join(''.join(orth.itertext()).split())
        if orth.get('extent') != 'full' or not re.fullmatch(r'[a-z]+-', text):
            reasons['other_alternate_shape'] += 1
            continue
        if text in LEXER_HANDLED:
            reasons['lexer_handled_alternate'] += 1
            continue
        aligned, reason = alignment(text[:-1], headword, table)
        if aligned is None:
            reasons[reason] += 1
            continue
        reasons['accepted_alternate'] += 1
        accepted.append(aligned)
    return (lemma, headword, accepted), reasons


def substitute(stem, prefix):
    """Replace the prefix letters of a stem, keeping notation and hyphens."""
    length, old, new = prefix
    letters = [i for i, c in enumerate(stem) if c.isalpha()]
    if len(letters) < length or ''.join(stem[i] for i in letters[:length]) != old:
        return None
    out = list(stem)
    for i, c in zip(letters[:length], new):
        out[i] = c
    return ''.join(out)


def transform(candidate, rows, entries, table):
    proofs = defaultdict(list); counts = Counter()
    for row in rows:
        if row.get('id') not in entries:
            raise ValueError('missing source article')
        result, reasons = proof(row, entries[row['id']], table)
        counts.update(reasons)
        if result and result[2]:
            proofs[result[0]].append(result)
    blocks = Counter(); records = defaultdict(list); lemma = None
    pattern = re.compile(rb'(:vs:|:de:)([^\s]+)([ \t]+)([^\r\n]*?)(\r?\n)?$')
    lines = candidate.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.startswith(b':le:'):
            lemma = line[4:].strip(); blocks[lemma] += 1
        match = pattern.fullmatch(line)
        if match and lemma is not None:
            records[lemma].append((index, match))
    additions = {}
    for lemma, choices in sorted(proofs.items()):
        if blocks[lemma] == 0:
            counts['lemma_without_candidate_block'] += 1
            continue
        if len(choices) != 1 or blocks[lemma] != 1:
            counts['withheld_ambiguous_lemma_block'] += 1
            continue
        if not records[lemma]:
            counts['withheld_block_without_records'] += 1
            continue
        _, _, prefixes = choices[0]
        existing = {(m[2].decode('ascii', 'replace').translate(NOTATION), tuple(m[4].split()))
                    for _, m in records[lemma]}
        changed = False
        for prefix in sorted(set(prefixes)):
            for index, match in records[lemma]:
                stem = match[2].decode('ascii', 'replace'); tags = match[4].split()
                if not re.fullmatch(r'[a-z_^-]+', stem):
                    counts['records_withheld_unparsed_stem'] += 1
                    continue
                if b'orth' in tags:
                    counts['records_skipped_existing_orth'] += 1
                    continue
                alternate = substitute(stem, prefix)
                if alternate is None:
                    counts['records_outside_prefix'] += 1
                    continue
                key = (alternate.translate(NOTATION), tuple(tags + [b'orth']))
                if key in existing:
                    counts['records_already_present'] += 1
                    continue
                existing.add(key)
                additions.setdefault(index, []).append(
                    match[1] + alternate.encode() + match[3] + b' '.join(tags + [b'orth']) + b'\n')
                counts['added_records'] += 1
                counts['added_' + tags[0].decode('ascii', 'replace')] += 1
                changed = True
        if changed:
            counts['changed_lemma_blocks'] += 1
        else:
            counts['lemma_blocks_without_addition'] += 1
    output = []
    for index, line in enumerate(lines):
        output.append(line)
        if index in additions:
            if not line.endswith(b'\n'):
                output.append(b'\n')
            output.extend(additions[index])
    return b''.join(output), dict(sorted(counts.items()))


def prepare(candidate, headers, lexica, output, expected=None):
    target = first.private_target(candidate, headers, lexica, output)
    table = preverbs()
    rows, source, revision = first.source_rows(headers, lexica)
    entries, second_source, second_revision = first.review.load_entries(lexica)
    if source != second_source or revision != second_revision:
        raise ValueError('source changed during validation')
    data, counts = transform(candidate.read_bytes(), rows, entries, table)
    if expected is not None and counts.get('added_records', 0) != expected:
        raise ValueError('unexpected added record count')
    report = {'schema': 1,
              'scope': 'abbreviated full-extent prefix alternates outside the four lexer-handled literals; '
                       'one letter substituted inside an engine-known preverb; existing block records only',
              'source_revision': revision, 'counts': counts,
              'input_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in (candidate, headers, source, PREVERB_TABLE)},
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
