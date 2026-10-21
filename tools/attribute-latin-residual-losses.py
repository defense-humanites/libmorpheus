#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Attribute the residual LISTALL losses of the combined candidate to decisions.

After the combined candidate and the lemma-identity review, two residues
remain against the controlled rebuilt baseline: the readings on the forms the
candidate no longer recognizes at all, and the removed readings on recognized
forms that agree with no candidate reading at ten or nine fields. This
diagnostic attributes both to the categories the open decisions are phrased
in. A lost reading is attributed by its lemma: a native preverb identifier
(composed identity), a curated verbal lemma that still has a definition in
the candidate (a changed-definition dossier), a curated verbal lemma without
one (by the category of the witness backlog screen: voice variant, alternate
spelling, homograph numbering, no projected header, or the shape of the
unreadable grammar string), a lemma outside the curated verbal witness, or a
non-verbal reading. An unmatched reading on a recognized form is attributed
in addition by the smallest set of fields on which it differs from a
candidate reading of the same form, so that a reading lost to a tense, a
mood or a class differs visibly from one lost with its whole lemma. The
witness supplies lemma membership only; nothing is labelled with its stems.
Only counts, categories and SHA-256 values are published.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent


def sibling(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


screen = sibling('screen-latin-witness-backlog')
identity = sibling('review-latin-removed-lemma-identity')
FIELDS = ('workword', 'lemma', 'part_of_speech', 'person', 'number', 'gender',
          'grammatical_case', 'tense', 'mood', 'voice', 'degree')
NOTATION = str.maketrans('', '', '_^-')


def lemma_category(lemma, pos, categories, candidate_blocks):
    """Decision category of one removed reading, from its lemma and part of speech."""
    if pos != 2:
        return 'non_verbal_reading:pos_%s' % pos
    key = lemma.encode('ascii', 'replace')
    if '-' in re.sub(r'#\d+$', '', lemma):
        return 'native_preverb_identifier'
    category = categories.get(key)
    if category == 'with_candidate_definitions':
        return 'curated_lemma_with_candidate_definition'
    if category is not None:
        return 'curated_lemma_without_definition:' + category
    if candidate_blocks.get(key):
        return 'candidate_lemma_outside_curated_witness'
    return 'lemma_outside_curated_witness_and_candidate'


def differing_fields(removed, after):
    """The smallest set of fields on which a removed reading differs from a candidate reading of the form."""
    best = None
    for candidate in after:
        fields = [name for name, left, right in zip(FIELDS, removed, candidate)
                  if (left.translate(NOTATION) != right.translate(NOTATION) if name == 'workword' else left != right)]
        if best is None or len(fields) < len(best):
            best = fields
    return '+'.join(best) if best else 'no_candidate_reading'


def difference_size(fields):
    """Coarse size of a difference: how many grammatical fields, and whether the lemma differs too."""
    if fields == 'no_candidate_reading':
        return fields
    names = fields.split('+'); grammatical = [n for n in names if n not in ('workword', 'lemma')]
    size = ('one_grammatical_field' if len(grammatical) == 1 else 'two_or_three_grammatical_fields'
            if len(grammatical) <= 3 else 'four_or_more_grammatical_fields')
    return size + ('_and_lemma' if 'lemma' in names else '')


def attribute(delta_path, after_signatures, categories, candidate_blocks):
    lost = {'readings': Counter(), 'forms': Counter(), 'lemmas': {}}
    unmatched = {'readings': Counter(), 'lemmas': {}}
    by_fields = Counter(); fields_by_category = Counter(); by_size = Counter(); counts = Counter()
    for line in delta_path.read_bytes().splitlines():
        row = json.loads(line)
        removed = Counter({tuple(r['signature']): r['multiplicity'] for r in row['removed']})
        if not removed:
            continue
        if row['rebuilt_count'] == 0:
            counts['completely_lost_forms'] += 1
            seen = set()
            for signature, count in removed.items():
                category = lemma_category(signature[1], signature[2], categories, candidate_blocks)
                lost['readings'][category] += count; counts['readings_on_completely_lost_forms'] += count
                lost['lemmas'].setdefault(category, set()).add(signature[1])
                if category not in seen:
                    lost['forms'][category] += 1; seen.add(category)
            continue
        after = [tuple(s) for s in after_signatures(row['form'])]
        if len(after) != row['rebuilt_count']:
            raise ValueError('candidate readings differ from the difference file')
        for signature, count in sorted(removed.items()):
            tier, _, _ = identity.match(signature, after)
            if tier is not None:
                counts['removed_readings_matched_by_lemma_identity'] += count; continue
            counts['unmatched_readings_on_recognized_forms'] += count
            category = lemma_category(signature[1], signature[2], categories, candidate_blocks)
            unmatched['readings'][category] += count
            unmatched['lemmas'].setdefault(category, set()).add(signature[1])
            fields = differing_fields(signature, after)
            by_fields[fields] += count; fields_by_category[(category, fields)] += count
            by_size[difference_size(fields)] += count
    def table(part):
        return {c: {'readings': part['readings'][c], **({'forms': part['forms'][c]} if 'forms' in part else {}),
                    'lemmas': len(part['lemmas'][c])} for c in sorted(part['readings'])}
    return {'counts': dict(sorted(counts.items())),
            'completely_lost_forms_by_lemma_category': table(lost),
            'unmatched_readings_by_lemma_category': table(unmatched),
            'unmatched_readings_by_difference_size': dict(sorted(by_size.items())),
            'unmatched_readings_by_differing_fields': dict(sorted(by_fields.items(), key=lambda i: (-i[1], i[0]))),
            'unmatched_readings_by_category_and_fields': [
                {'lemma_category': c, 'differing_fields': f, 'readings': n}
                for (c, f), n in sorted(fields_by_category.items(), key=lambda i: (-i[1], i[0]))]}


def prepare(args):
    prefix = sibling('qualify-latin-prefix-alternates'); combined = sibling('qualify-latin-combined-candidate')
    primary = prefix.primary; changed = prefix.changed; review = prefix.review; native = prefix.native; supines = prefix.supines
    paths = {'candidate': args.candidate, 'headers': args.headers, 'tei': args.tei, 'forms': args.forms}
    receipts = {'candidate': changed.reproduction.candidate.CANDIDATE_SHA, 'headers': review.RECEIPTS['headers'],
                'tei': review.RECEIPTS['tei'], 'forms': prefix.FORMS_SHA}
    if any(native.digest(p) != receipts[n] for n, p in paths.items()):
        raise ValueError('residual loss attribution input receipt differs')
    target = changed.loss.private_target(args.output, [*paths.values(), args.library, args.baseline, args.tools, args.filters, args.witness])
    target.mkdir(mode=0o700)
    baseline_indexes = {n: native.digest(args.baseline / 'Latin/steminds' / n) for n in changed.reproduction.candidate.INDEXES}
    combination = combined.combine.prepare(args.candidate, args.headers, args.tei, args.filters, target / 'combination')
    if combination['output_sha256'] != combined.COMBINED_SHA:
        raise ValueError('residual loss attribution combined candidate differs from the qualified one')
    stems = target / 'combination/combined.stems'
    trial_indexes = native.build_trial(args.baseline, stems, args.tools, target / 'trial')
    rows, _, _ = screen.alternates.source_alternates(args.headers, args.tei)
    categories = screen.classify(stems.read_bytes(), args.witness.read_bytes(), rows)
    candidate_blocks = screen.blocks(stems.read_bytes())
    readers = {}
    try:
        readers['baseline'] = supines.direct.StrictRows(args.library, args.baseline)
        readers['after'] = supines.direct.StrictRows(args.library, target / 'trial')
        comparison = supines.direct.audit.audit(args.forms, readers['baseline'], readers['after'], target / 'baseline-combined.jsonl')
        expected = {'removed_rows': 38066, 'forms': 5766}
        if (comparison['global_eleven_field_multisets']['removed_rows'] != expected['removed_rows']
                or comparison['lost_forms_diagnostic']['forms'] != expected['forms']):
            raise ValueError('residual loss attribution baseline comparison differs from the qualified receipt')
        report = attribute(target / 'baseline-combined.jsonl', combined.text_readings(readers['after']), categories, candidate_blocks)
    finally:
        for reader in readers.values():
            reader.close()
    if any(native.digest(p) != receipts[n] for n, p in paths.items()) or any(
            native.digest(args.baseline / 'Latin/steminds' / n) != baseline_indexes[n] for n in baseline_indexes):
        raise ValueError('residual loss attribution changed an input')
    return {'schema': 1,
            'scope': 'readings of the controlled rebuilt baseline that the combined candidate removes on LISTALL and that lemma identity does not explain, attributed by lemma category of the open decisions and by differing fields; witness used for membership only; no candidate changed, no production promotion',
            'input_sha256': receipts, 'witness_sha256': native.digest(args.witness),
            'combined_source_sha256': native.digest(stems), 'trial_indexes_sha256': trial_indexes,
            'baseline_comparison': {k: comparison[k] for k in ('counts', 'global_eleven_field_multisets')},
            'lemma_categories': dict(sorted(Counter(categories.values()).items())),
            **report, 'original_inputs_unchanged': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate', 'headers', 'tei', 'library', 'baseline', 'tools', 'filters', 'forms', 'witness', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    previous = os.umask(0o077)
    try:
        result = prepare(args)
    finally:
        os.umask(previous)
    print(json.dumps({'latin_residual_loss_attribution': result}, sort_keys=True))


if __name__ == '__main__':
    main()
