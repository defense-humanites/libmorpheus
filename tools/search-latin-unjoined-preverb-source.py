#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Search all pinned Latin articles for the qualified unjoined preverb lemma.

Exact keys, complete orthographies and references are separate evidence routes.
Notation/case/homograph leads are diagnostic only, never identity substitutions.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re

from lxml import etree

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('preverb_review', REPO / 'tools/review-latin-source-present-preverbs.py')
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
loss = review.loss


def selected(path, expected_rows):
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    if (len(rows) != 1 or rows[0]['source_join'] != 'no_article_join' or
            rows[0]['articles'] or rows[0]['candidate_definitions'] or rows[0]['added_rows'] != expected_rows):
        raise ValueError('unjoined preverb scope differs')
    row = rows[0]
    if not re.fullmatch(r'[A-Za-z_^#0-9-]+', row['lemma']):
        raise ValueError('unsupported literal search lemma')
    if sum(a['multiplicity'] for a in row['additions']) != expected_rows or any(
            a['signature'][1] != row['lemma'] or not a['signature'][11] for a in row['additions']):
        raise ValueError('unjoined additions differ')
    return row['lemma']


def key_spelling(value):
    # The historical projection convention is labelled, not treated as approval.
    return re.sub(r'(?<=[A-Za-z)])([1-9])$', r'#\1', value)


def plain(value):
    return value.translate(str.maketrans('', '', '_^-'))


def lead(value):
    # Keep this lossy comparison separate from all literal evidence routes.
    return re.sub(r'#[1-9]$', '', plain(value)).lower()


def match(value, lemma):
    if value == lemma:
        return 'literal'
    if plain(value) == lemma:
        return 'quantity_or_hyphen_notation_lead'
    if lead(value) == lead(lemma):
        return 'case_or_homograph_or_notation_lead'
    return None


def article_routes(entry, lemma, normalize):
    routes = []
    key = entry.get('key') or ''
    def append(value, kind, location, attributes):
        quality = match(value, lemma)
        if quality:
            routes.append({'route': kind, 'match': quality, 'location': location,
                           'value': value, 'attributes': attributes})
    append(key_spelling(key), 'source_key_projection_convention', 'entry-key', {})
    number = re.search(r'#[1-9]$', key_spelling(key))
    for node in entry.iter('orth', 'ref'):
        if any(isinstance(n, etree._Entity) for n in node.iter()):
            continue
        raw = ' '.join(''.join(node.itertext()).split())
        value = normalize(raw, 'Latin')
        # Whole strings only: never take the first token of an abbreviation,
        # coordinated alternative, phrase or reference gloss.
        if not value or not re.fullmatch(r'[A-Za-z_^+#0-9-]+', value):
            continue
        direct = node.getparent() is entry
        kind = ('direct_orth' if direct else 'nested_orth') if node.tag == 'orth' else 'reference_text'
        append(value, kind, 'direct-child' if direct else 'descendant', dict(node.attrib))
        if direct and node.tag == 'orth' and number and not re.search(r'#[1-9]$', value):
            append(value + number.group(), 'direct_orth_with_entry_homograph', 'direct-child', dict(node.attrib))
    return routes


def search(entries, lemma, normalize, output):
    groups, article_groups = Counter(), Counter()
    matched = 0
    for source_id, entry in sorted(entries.items()):
        routes = article_routes(entry, lemma, normalize)
        if not routes:
            continue
        matched += 1
        per_article = set()
        for route in routes:
            key = (route['route'], route['match'], route['location'])
            groups[key] += 1; per_article.add(key)
        article_groups.update(per_article)
        output.write(json.dumps({'source_id': source_id, 'source_key': entry.get('key'),
            'searched_lemma': lemma, 'routes': routes,
            'article_sha256': hashlib.sha256(etree.tostring(entry)).hexdigest(),
            'article_xml': etree.tostring(entry, encoding='unicode'),
            'decision': 'search_evidence_only_no_identity_or_lexical_approval'}, sort_keys=True) + '\n')
    fields = ('route', 'match', 'location')
    return {'schema': 1, 'scope': 'all entry keys and whole orth/ref strings in pinned Latin TEI; no prose-token or external-source search',
        'counts': {'articles_scanned': len(entries), 'articles_with_search_evidence': matched},
        'evidence_groups': [dict(zip(fields, key), occurrences=n, articles=article_groups[key])
            for key, n in sorted(groups.items())],
        'decision': 'no_lexical_approval; empty search is not proof of nonattestation'}


def prepare(args):
    if loss.digest(args.dossier) != args.expected_dossier_sha256:
        raise ValueError('unjoined preverb receipt differs')
    lemma = selected(args.dossier, args.expected_rows)
    source_review = loss.sibling('prepare-latin-partition-review')
    entries, source, revision = source_review.load_entries(args.lexica)
    if loss.digest(source) != args.expected_tei_sha256:
        raise ValueError('pinned full TEI receipt differs')
    target = loss.private_target(args.private_output, [args.dossier, args.lexica, source])
    with review.isolated.private_stream(target) as output:
        report = search(entries, lemma, source_review.projection.normalize, output)
    if loss.digest(args.dossier) != args.expected_dossier_sha256 or loss.digest(source) != args.expected_tei_sha256:
        raise ValueError('source search changed input evidence')
    report.update(source_revision=revision, input_sha256={'dossier': args.expected_dossier_sha256,
        'Latin_TEI': args.expected_tei_sha256}, private_search_sha256=loss.digest(target), inputs_unchanged=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('dossier', 'lexica', 'private-output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('dossier', 'tei'):
        parser.add_argument('--expected-' + name + '-sha256', required=True)
    parser.add_argument('--expected-rows', type=int, required=True)
    previous = os.umask(0o077)
    try:
        report = prepare(parser.parse_args())
    finally:
        os.umask(previous)
    print(json.dumps({'latin_unjoined_preverb_source_search': report}, sort_keys=True))


if __name__ == '__main__':
    main()
