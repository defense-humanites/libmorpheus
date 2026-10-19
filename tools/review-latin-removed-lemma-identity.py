#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Review removed LISTALL readings for readings that differ by lemma only.

The eleven-field comparison against the controlled rebuilt baseline counts a
reading as removed when any field differs, the lemma included. The curated
witness kept voice variants, alternate spellings and homograph numberings as
lemmas of their own; a candidate that recognizes the same form with the same
grammar under the dictionary's article still shows a removed reading under
the witness's lemma, whether the article's reading is new or was already in
the baseline beside the witness's. This review re-reads a private per-form
difference file and, for each removed reading, asks the candidate for the
form's analyses after the change: a reading agrees at ten fields when only
the lemma differs (the workword compared without vowel-length notation,
which belongs to the stem spelling), at nine fields when the voice differs
as well, as for an active witness lemma whose article is deponent. The
relation between the two lemma spellings is classified by shape; no
spelling is read against the source. Readings on forms the candidate no
longer recognizes at all cannot agree with anything and are counted apart.
Only counts, categories and SHA-256 values are published; the pairs stay in
a private file.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[1]
NOTATION = str.maketrans('', '', '_^-')
LEMMA, VOICE = 1, 9
RANK = ('homograph_numbering', 'active_lemma_matched_by_deponent', 'deponent_lemma_matched_by_active',
        'native_composition_for_lemma', 'lemma_for_native_composition', 'assimilated_native_composition_for_lemma',
        'lemma_for_assimilated_native_composition', 'single_letter_spelling', 'other_lemma')


def base(lemma):
    return re.sub(r'#\d+$', '', lemma).translate(str.maketrans('', '', '_^'))


def single_edit(left, right):
    if left == right:
        return False
    if len(left) == len(right):
        return sum(a != b for a, b in zip(left, right)) == 1
    short, long = sorted((left, right), key=len)
    if len(long) - len(short) != 1:
        return False
    return any(long[:i] + long[i + 1:] == short for i in range(len(long)))


def relation(removed, added):
    """Mechanical relation between the witness's lemma and the candidate's."""
    left, right = base(removed), base(added)
    if left == right:
        return 'homograph_numbering'
    if '-' in right and right.replace('-', '') == left:
        return 'native_composition_for_lemma'
    if '-' in left and left.replace('-', '') == right:
        return 'lemma_for_native_composition'
    if '-' in right and single_edit(right.replace('-', ''), left):
        return 'assimilated_native_composition_for_lemma'
    if '-' in left and single_edit(left.replace('-', ''), right):
        return 'lemma_for_assimilated_native_composition'
    if left.endswith('o') and right == left[:-1] + 'or':
        return 'active_lemma_matched_by_deponent'
    if left.endswith('or') and right == left[:-2] + 'o':
        return 'deponent_lemma_matched_by_active'
    if single_edit(left, right):
        return 'single_letter_spelling'
    return 'other_lemma'


def ten(signature):
    return (signature[0].translate(NOTATION),) + tuple(signature[LEMMA + 1:])


def nine(signature):
    return (signature[0].translate(NOTATION),) + tuple(signature[LEMMA + 1:VOICE]) + tuple(signature[VOICE + 1:])


def match(removed, after):
    """The closest after-reading agreeing with a removed reading, by tier and relation rank."""
    for tier, key in (('ten', ten), ('nine', nine)):
        wanted = key(removed)
        found = [(RANK.index(relation(removed[LEMMA], a[LEMMA])), a) for a in after
                 if a[LEMMA] != removed[LEMMA] and key(a) == wanted]
        if found:
            rank, chosen = min(found, key=lambda f: (f[0], f[1]))
            return tier, RANK[rank], chosen
    return None, None, None


def review(delta_path, after_signatures, private_output):
    """after_signatures(form) returns the candidate's eleven-field readings as text tuples."""
    if private_output.is_symlink():
        raise FileExistsError('private lemma-identity output is a symlink')
    target = private_output.resolve()
    if target == REPO or REPO in target.parents:
        raise ValueError('private lemma-identity output must be outside the repository')
    counts = Counter(); relations = {'ten': Counter(), 'nine': Counter()}; voices = Counter()
    by_pos = Counter(); per_lemma = defaultdict(Counter); origin = Counter()
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
    with os.fdopen(os.open(target, flags, 0o600), 'w') as output:
        for line in delta_path.read_bytes().splitlines():
            row = json.loads(line)
            removed = Counter({tuple(r['signature']): r['multiplicity'] for r in row['removed']})
            if not removed:
                continue
            total = sum(removed.values())
            counts['forms_with_removed_readings'] += 1; counts['removed_readings'] += total
            for signature, count in removed.items():
                per_lemma[signature[LEMMA]]['removed'] += count
            if row['rebuilt_count'] == 0:
                counts['removed_readings_on_completely_lost_forms'] += total
                continue
            after = [tuple(s) for s in after_signatures(row['form'])]
            if len(after) != row['rebuilt_count']:
                raise ValueError('candidate readings differ from the difference file')
            added = Counter({tuple(r['signature']): r['multiplicity'] for r in row['added']})
            pairs = []
            for signature, count in sorted(removed.items()):
                tier, kind, chosen = match(signature, after)
                if tier is None:
                    counts['removed_readings_without_lemma_match'] += count; continue
                counts['removed_readings_matched_at_%s_fields' % tier] += count
                relations[tier][kind] += count; by_pos[str(signature[2])] += count
                per_lemma[signature[LEMMA]]['matched'] += count
                origin['added_reading' if chosen in added else 'retained_reading'] += count
                if tier == 'nine':
                    voices['%s>%s' % (signature[VOICE], chosen[VOICE])] += count
                if signature[0] != chosen[0]:
                    counts['matched_readings_with_workword_notation_differing'] += count
                pairs.append({'removed_lemma': signature[LEMMA], 'matched_lemma': chosen[LEMMA], 'fields': tier,
                              'relation': kind, 'multiplicity': count})
            if pairs:
                counts['forms_with_lemma_matches'] += 1
                output.write(json.dumps({'form': row['form'], 'pairs': pairs}, sort_keys=True) + '\n')
    lemmas = Counter()
    for lemma, tally in per_lemma.items():
        lemmas['fully_matched' if tally['matched'] == tally['removed'] else
               'partly_matched' if tally['matched'] else 'unmatched'] += 1
    return {'scope': 'removed eleven-field readings matched against the candidate readings of the same form that differ by lemma only (ten fields, workword notation disregarded) or by lemma and voice only (nine fields); relation of the two lemma spellings by shape; completely lost forms counted apart; no lexical value published',
            'counts': dict(sorted(counts.items())),
            'ten_field_matches_by_relation': dict(sorted(relations['ten'].items())),
            'nine_field_matches_by_relation': dict(sorted(relations['nine'].items())),
            'nine_field_voice_pairs': dict(sorted(voices.items())),
            'matched_reading_origin': dict(sorted(origin.items())),
            'matched_readings_by_part_of_speech': dict(sorted(by_pos.items())),
            'removed_lemmas': {'total': len(per_lemma), **dict(sorted(lemmas.items()))},
            'private_pairs_sha256': hashlib.sha256(target.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delta', type=Path, required=True, help='private per-form difference file of an audit')
    parser.add_argument('--readings', type=Path, required=True,
                        help='JSON lines of {"form", "readings"}: the candidate readings of each form')
    parser.add_argument('--private-output', type=Path, required=True)
    args = parser.parse_args()
    table = {}
    for line in args.readings.read_bytes().splitlines():
        row = json.loads(line); table[row['form']] = row['readings']
    previous = os.umask(0o077)
    try:
        report = review(args.delta, lambda form: table.get(form, []), args.private_output)
    finally:
        os.umask(previous)
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
