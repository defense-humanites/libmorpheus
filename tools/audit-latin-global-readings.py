#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare every LISTALL grammatical multiset; publish aggregate diagnostics."""
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SIGNATURE = ('workword', 'lemma', 'part_of_speech', 'person', 'number', 'gender',
             'grammatical_case', 'tense', 'mood', 'voice', 'degree')


def source_lemmas(path):
    return {line[4:].strip() for line in path.read_bytes().splitlines() if line.startswith(b':le:')}


def provenance(rows):
    groups = defaultdict(set)
    for signature, preverb in rows:
        groups[signature].add(bool(preverb))
    return {signature: ('mixed' if len(values) == 2 else 'native_preverb' if True in values else 'direct')
            for signature, values in groups.items()}


def serialized(delta):
    records = []
    for signature, count in sorted(delta.items()):
        try:
            values = [v.decode('utf-8') if isinstance(v, bytes) else v for v in signature]
        except UnicodeDecodeError:
            raise ValueError('native grammatical signature text is not UTF-8') from None
        records.append({'signature': values, 'multiplicity': count})
    return records


def grouped(counter, fields):
    return [dict(zip(fields, key), rows=count) for key, count in sorted(counter.items())]


def audit(forms, curated, rebuilt, private_output, candidate_lemmas=None, require_identical=False):
    if private_output.is_symlink():
        raise FileExistsError('private grammatical output is a symlink')
    target = private_output.resolve()
    if (target == REPO or REPO in target.parents or target == forms.resolve() or
            target in forms.resolve().parents):
        raise ValueError('private grammatical output must be outside repository and input')
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
    seen, counts, totals = set(), Counter(), Counter()
    changes = Counter()
    row_totals = {'curated': 0, 'rebuilt': 0}
    delta_groups = {'removed': Counter(), 'added': Counter()}
    loss_groups, lost_lemmas = Counter(), defaultdict(set)
    digest = hashlib.sha256()
    with os.fdopen(os.open(target, flags, 0o600), 'w') as output:
        with forms.open('rb') as source:
            for raw in source:
                digest.update(raw)
                counts['input_lines'] += 1
                word = raw.rstrip(b'\r\n')
                if not word:
                    counts['blank_lines'] += 1
                    continue
                if any(byte < 33 or byte > 126 for byte in word):
                    raise ValueError('non-ASCII or whitespace in grammatical input')
                if word in seen:
                    counts['duplicate_lines'] += 1
                    continue
                seen.add(word)
                counts['distinct_forms'] += 1
                old, new = curated.rows(word), rebuilt.rows(word)
                left, right = Counter(row for row, _ in old), Counter(row for row, _ in new)
                removed, added = left-right, right-left
                for key, rows in [('curated', old), ('rebuilt', new)]:
                    row_totals[key] += len(rows)
                cell = ('recognized' if old else 'absent') + '_curated__' + ('recognized' if new else 'absent') + '_rebuilt'
                counts[cell] += 1
                totals['retained_rows'] += sum((left & right).values())
                totals['removed_rows'] += sum(removed.values())
                totals['added_rows'] += sum(added.values())
                if len(old) != len(new):
                    changes['changed_analysis_counts'] += 1
                if removed or added:
                    changes['changed_grammatical_multisets'] += 1
                    if len(old) == len(new):
                        changes['changed_multisets_at_equal_counts'] += 1
                    if require_identical:
                        raise ValueError('identical-root grammatical control differs')
                    for name, delta, rows in [('removed', removed, old), ('added', added, new)]:
                        origins = provenance(rows)
                        for signature, multiplicity in delta.items():
                            pos, tense, origin = signature[2], signature[7], origins[signature]
                            delta_groups[name][(pos, tense, origin)] += multiplicity
                            if old and not new and name == 'removed':
                                membership = ('not_applicable' if pos != 2 or candidate_lemmas is None else
                                    'in_substituted_verbal_source' if signature[1] in candidate_lemmas else
                                    'outside_substituted_verbal_source')
                                loss_groups[(pos, tense, origin, membership)] += multiplicity
                                lost_lemmas[pos].add(signature[1])
                    output.write(json.dumps({'form': word.decode('ascii'), 'curated_count': len(old),
                        'rebuilt_count': len(new), 'retained_rows': sum((left & right).values()),
                        'removed': serialized(removed), 'added': serialized(added)}, sort_keys=True)+'\n')
    return {'schema': 1, 'mode': 'literal ASCII forms; native options 0',
            'scope': 'all eleven-field multisets, including equal-count forms; aggregate diagnostic, not equivalence approval',
            'identical_root_control': require_identical, 'signature_fields': list(SIGNATURE),
            'input_sha256': digest.hexdigest(), 'counts': dict(sorted(counts.items())),
            'status_pairs': {'0,0': counts['distinct_forms']}, 'analysis_rows': row_totals,
            **{key: changes[key] for key in ('changed_analysis_counts', 'changed_grammatical_multisets', 'changed_multisets_at_equal_counts')},
            'global_eleven_field_multisets': dict(sorted(totals.items())),
            'delta_rows_by_pos_tense_provenance': {name: grouped(counter, ('part_of_speech', 'tense', 'provenance'))
                                                   for name, counter in delta_groups.items()},
            'lost_forms_diagnostic': {
                'forms': counts['recognized_curated__absent_rebuilt'],
                'rows_by_pos_tense_provenance_source_membership': grouped(loss_groups,
                    ('part_of_speech', 'tense', 'provenance', 'lemma_membership')),
                'distinct_lemmas_by_pos': {str(pos): len(lemmas) for pos, lemmas in sorted(lost_lemmas.items())},
                'membership_scope': 'exact lemma bytes in the substituted verbal input only; excludes retained verbal inputs; no source approval'},
            'private_difference_sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
