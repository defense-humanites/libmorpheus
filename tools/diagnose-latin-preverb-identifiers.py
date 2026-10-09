#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Distinguish native composition identifiers from source lexical identities."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def signature(item):
    sig, n = item['signature'], item['multiplicity']
    if (len(sig) != 16 or type(n) is not int or n <= 0 or
            any(not isinstance(sig[i], str) for i in (0, 1, 11, 12, 13, 14, 15)) or
            any(type(v) is not int for v in sig[2:11])):
        raise ValueError('invalid qualified route signature')
    return tuple(sig), n


def inspect(routes, family, dossier, expected_forms, expected_rows, expected_preverbs, output):
    source_lemmas = {row['lemma'] for row in family}
    if len(family) != 13 or len(source_lemmas) != 1 or any(r['kind'] != 'source_present_family' for r in family):
        raise ValueError('qualified source family differs')
    source = next(iter(source_lemmas))
    if len(dossier) != 1 or dossier[0]['source_join'] != 'no_article_join' or dossier[0]['articles'] or dossier[0]['candidate_definitions']:
        raise ValueError('qualified unjoined dossier differs')
    wanted = Counter()
    for a in dossier[0]['additions']:
        sig, n = signature(a)
        if sig[1] != dossier[0]['lemma'] or not sig[11]:
            raise ValueError('unjoined dossier provenance differs')
        wanted[(a['form'], sig)] += n
    if sum(wanted.values()) != expected_preverbs or dossier[0]['added_rows'] != expected_preverbs:
        raise ValueError('unjoined dossier row count differs')
    direct, derived, forms = Counter(), Counter(), set()
    for row in routes:
        form = row['form']
        if not isinstance(form, str) or not form or not form.isascii() or form in forms or row['removed']:
            raise ValueError('qualified route form or removal differs')
        forms.add(form)
        for item in row['added']:
            sig, n = signature(item)
            if sig[2] != 2:
                raise ValueError('qualified addition is not verbal')
            if sig[11]:
                derived[(form, sig)] += n
            else:
                if sig[1] != source:
                    raise ValueError('direct source identity differs')
                # Exclude workword/lemma/preverb/raw_preverb; keep all grammar
                # and the literal stem, suffix and ending decomposition.
                direct[sig[2:11] + sig[13:16]] += n
    if (len(forms) != expected_forms or sum(direct.values()) + sum(derived.values()) != expected_rows or derived != wanted):
        raise ValueError('qualified route and dossier inventories differ')
    counts, groups, identifiers, preverbs = Counter(), Counter(), set(), set()
    for (form, sig), n in sorted(derived.items()):
        assembled = sig[1] == sig[11] + '-' + source
        peer = bool(direct[sig[2:11] + sig[13:16]])
        category = 'literal_preverb_base_identifier' if assembled else 'other_native_identifier'
        counts[category + '_rows'] += n
        counts['same_decomposition_as_direct_addition_rows'] += n if peer else 0
        counts['reviewed_preverb_rows'] += n
        identifiers.add(sig[1]); preverbs.add((sig[11], sig[12]))
        groups[(category, peer, sig[7])] += n
        output.write(json.dumps({'form': form, 'signature': list(sig), 'multiplicity': n,
            'source_lemma': source, 'identifier_category': category,
            'same_decomposition_as_direct_addition': peer,
            'decision': 'native_composition_diagnostic_only_no_lexical_approval'}, sort_keys=True) + '\n')
    return {'schema': 1, 'scope': 'qualified other-lemma preverb additions; literal native identifier structure, not lexical identity approval',
        'counts': dict(counts, distinct_output_identifiers=len(identifiers), distinct_preverb_pairs=len(preverbs)),
        'groups': [{'identifier_category': k[0], 'same_decomposition_as_direct_addition': k[1], 'tense': k[2], 'rows': n}
            for k, n in sorted(groups.items())],
        'peer_scope': 'at least one added direct reading shares grammar/stem/suffix/ending; no one-to-one form or source-attestation assertion'}


def prepare(args):
    paths = {name: getattr(args, name) for name in ('routes', 'family', 'dossier')}
    if any(digest(path) != getattr(args, 'expected_' + name + '_sha256') for name, path in paths.items()):
        raise ValueError('qualified identifier receipt differs')
    target = args.private_output.resolve()
    if args.private_output.is_symlink() or target == REPO or REPO in target.parents or any(
            target == p.resolve() or p.resolve() in target.parents or target in p.resolve().parents for p in paths.values()):
        raise ValueError('identifier dossier must be outside repository and inputs')
    with os.fdopen(os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600), 'w') as output:
        report = inspect(*(read_rows(paths[n]) for n in ('routes', 'family', 'dossier')),
            args.expected_forms, args.expected_rows, args.expected_preverbs, output)
    if any(digest(path) != getattr(args, 'expected_' + name + '_sha256') for name, path in paths.items()):
        raise ValueError('identifier diagnostic mutated evidence')
    report.update(input_sha256={name: digest(path) for name, path in paths.items()},
                  private_diagnostic_sha256=digest(target), inputs_unchanged=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('routes', 'family', 'dossier', 'private-output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('routes', 'family', 'dossier'):
        parser.add_argument('--expected-' + name + '-sha256', required=True)
    for name in ('forms', 'rows', 'preverbs'):
        parser.add_argument('--expected-' + name, type=int, required=True)
    previous = os.umask(0o077)
    try:
        report = prepare(parser.parse_args())
    finally:
        os.umask(previous)
    print(json.dumps({'latin_preverb_identifier_diagnostic': report}, sort_keys=True))


if __name__ == '__main__':
    main()
