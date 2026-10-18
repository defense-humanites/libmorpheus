#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Screen the curated verbal lemmas still without definitions in a candidate.

After the combined candidate, the complete-loss backlog is dominated by
curated verbal lemmas whose block is empty or absent. This diagnostic joins
each such lemma to the projected source headers and classifies, without
reading any stem of the witness, why the historical filter chain yields
nothing: no projected header (voice variant of an article, homograph
numbering, alternate spelling kept as its own lemma, or no relation), or a
joined header whose single grammar string the historical ``latvb`` table
does not handle. The witness supplies lemma membership only; it labels no
stem and no classification. Only categories, counts and hashes are
published.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('alternates', Path(__file__).with_name('recover-latin-full-alternates.py'))
alternates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alternates)
first = alternates.first
NOTATION = str.maketrans('', '', '_^-')
LEXER = REPO / 'src/gkdict/latvb.l'
RECORD = (b':vs:', b':de:', b':vb:', b':wd:')


def literal_grammars(lexer=LEXER):
    """The itype strings the historical filter matches literally."""
    return set(re.findall(r'"<itype>([^"]*)</itype>"', lexer.read_text(errors='replace')))


def blocks(data):
    found = defaultdict(list); lemma = None
    for line in data.splitlines():
        if line.startswith(b':le:'):
            lemma = line[4:].strip(); found.setdefault(lemma, [])
        elif lemma is not None and line.startswith(RECORD):
            found[lemma].append(line)
    return found


def grammar_shape(grammars, literal):
    if not grammars:
        return 'no_inflection_field'
    if len(grammars) > 1:
        return 'several_inflection_fields'
    grammar = grammars[0]
    if grammar in literal:
        return 'literal_table_grammar'
    if re.search(r'(?:^|, )[1-4]$', grammar):
        return 'vowel_initial_digit_grammar' if grammar[0] in 'aeioux' else 'consonant_initial_digit_grammar'
    if re.fullmatch(r'[a-z_^]+re', grammar):
        return 'bare_infinitive'
    return 'other_grammar'


def screen(candidate, witness, rows):
    literal = literal_grammars()
    by_head = defaultdict(list); by_alternate = defaultdict(set)
    for row in rows:
        if row.get('projection_error') is not None:
            continue
        by_head[row['headword'].translate(NOTATION)].append(row)
        for alternate in row.get('full_alternates', []):
            by_alternate[alternate.translate(NOTATION)].add(row['headword'])
    candidate_blocks = blocks(candidate); witness_blocks = blocks(witness)
    counts = Counter(); joined = Counter()
    for lemma, records in sorted(witness_blocks.items()):
        if not records:
            continue
        counts['witness_verbal_lemmas'] += 1
        if candidate_blocks.get(lemma):
            counts['with_candidate_definitions'] += 1; continue
        counts['without_candidate_definitions'] += 1
        key = lemma.decode('ascii', 'replace'); base = re.sub(r'#?\d$', '', key)
        heads = by_head.get(key, [])
        if not heads:
            if key in by_alternate: reason = 'alternate_spelling_kept_as_lemma'
            elif base in by_alternate or base in by_head: reason = 'homograph_numbering_differs'
            elif base.endswith('or') and base[:-2] + 'o' in by_head: reason = 'active_article_for_deponent_lemma'
            elif base.endswith('o') and base[:-1] + 'or' in by_head: reason = 'deponent_article_for_active_lemma'
            else: reason = 'no_projected_header'
            counts['unjoined:' + reason] += 1; continue
        if len(heads) > 1:
            counts['joined:ambiguous_headers'] += 1; continue
        row = heads[0]
        grammars = [f['projection'] for f in row['fields'] if f['name'] == 'itype']
        joined[grammar_shape(grammars, literal)] += 1
    return {'counts': dict(sorted(counts.items())), 'joined_grammar_shapes': dict(sorted(joined.items())),
            'literal_table_size': len(literal)}


def prepare(candidate, witness, headers, lexica):
    rows, source, revision = alternates.source_alternates(headers, lexica)
    report = screen(candidate.read_bytes(), witness.read_bytes(), rows)
    report.update({'schema': 1,
                   'scope': 'curated verbal lemmas without candidate definitions, joined to projected headers; grammar-string shape of the historical table; witness used for membership only, no stem labelled',
                   'source_revision': revision,
                   'input_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (candidate, witness, headers, source, LEXER)}})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate', 'witness', 'headers', 'lexica'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.candidate, args.witness, args.headers, args.lexica), sort_keys=True))


if __name__ == '__main__':
    main()
