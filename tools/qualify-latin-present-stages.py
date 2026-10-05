#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay the last present trials with controlled nominals; print aggregates only."""

import argparse
from collections import Counter
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('listall', REPO / 'tools/audit-latin-listall.py')
listall = importlib.util.module_from_spec(spec)
spec.loader.exec_module(listall)
NUMERIC = ('part_of_speech', 'dialect', 'geographic_region', 'person', 'number',
           'gender', 'grammatical_case', 'tense', 'mood', 'voice', 'degree')
TEXT = ('raw', 'workword', 'lemma', 'preverb', 'augment', 'stem', 'suffix',
        'ending', 'crasis', 'dictionary_form', 'english_form', 'raw_preverb')
SIGNATURE = ('workword', 'lemma', 'part_of_speech', 'person', 'number', 'gender',
             'grammatical_case', 'tense', 'mood', 'voice', 'degree')


class Analysis(ctypes.Structure):
    _fields_ = ([('struct_size', ctypes.c_uint32)] +
                [(name, ctypes.c_uint32) for name in NUMERIC] +
                [(name, ctypes.c_char * 64) for name in TEXT] +
                [('domains', ctypes.c_char * 24), ('morph_flags', ctypes.c_uint8 * 11)])


class NativeRows(listall.NativeAnalyzer):
    def __init__(self, library, stemlib):
        super().__init__(library, stemlib)
        self.api.morpheus_analysis_size.restype = ctypes.c_size_t
        self.api.morpheus_result_get.argtypes = [ctypes.c_void_p, ctypes.c_size_t,
                                                ctypes.c_void_p, ctypes.c_size_t]
        self.api.morpheus_result_get.restype = ctypes.c_int
        if self.api.morpheus_analysis_size() != ctypes.sizeof(Analysis):
            self.close()
            raise ValueError('structured analysis size differs from ABI 2')

    def rows(self, word):
        result = ctypes.c_void_p()
        status = self.api.morpheus_analyze(self.context, word, len(word), 0, ctypes.byref(result))
        try:
            if status or not result:
                raise ValueError('native reading analysis failed')
            rows = []
            for index in range(self.api.morpheus_result_count(result)):
                row = Analysis()
                if self.api.morpheus_result_get(result, index, ctypes.byref(row), ctypes.sizeof(row)):
                    raise ValueError('native structured reading failed')
                fields = tuple(getattr(row, name) for name in SIGNATURE)
                rows.append((fields, row.preverb))
            return rows
        finally:
            if result:
                self.api.morpheus_result_free(result)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_private(path, data):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                          getattr(os, 'O_NOFOLLOW', 0), 0o600), 'wb') as stream:
        stream.write(data)


def additions(before, after, expected):
    """Require an insertion-only trial and bind every inserted row to its lemma."""
    old = iter(before.splitlines(keepends=True))
    pending = next(old, None)
    lemma = None
    inserted = []
    for line in after.splitlines(keepends=True):
        if line == pending:
            if line.startswith(b':le:'):
                lemma = line[4:].strip()
            pending = next(old, None)
        else:
            if not lemma or not line.startswith(b':vs:') or line.split()[1:] not in (
                    [b'conj3', b'orth'], [b'conj3_io', b'orth']):
                raise ValueError('trial is not a present-only insertion under an existing lemma')
            inserted.append((lemma, line))
    if pending is not None or len(inserted) != expected:
        raise ValueError('trial insertion count or unchanged source bytes differ')
    return {lemma for lemma, _ in inserted}


def build_trial(baseline, stems, tools, target):
    shutil.copytree(baseline, target)
    # A research substitution invalidates the production receipts in the copy.
    for receipt in target.glob('MORPHEUS-*'):
        receipt.unlink()
    root = target / 'Latin'
    work = root / 'lexical'
    inputs = []
    for line in (work / 'inputs.tsv').read_text().splitlines():
        if not line or line.startswith('#'):
            continue
        language, role, name, _ = line.split('\t')
        if language == 'Latin' and role in {'verb', 'irregular-verb-baseline'}:
            inputs.append(stems if name == 'stemsrc/vbs.latin' else root / name)
    if len(inputs) != 4 or stems not in inputs:
        raise ValueError('unexpected controlled verbal assembly inventory')
    source = work / 'present-trial.input'
    data = b''.join(path.read_bytes() for path in inputs)
    data = re.sub(rb'([a-z])([aei])_v[ \t]+perfstem', rb'\1\t\2vperf', data)
    write_private(source, data)
    expanded, oddkeys = work / 'present-trial.expanded', work / 'present-trial.oddkeys'
    for name in ('vbind', 'vbind.lindex'):
        (root / 'steminds' / name).unlink()
    env = dict(os.environ, MORPHLIB=str(target), LC_ALL='C', LANG='C', TZ='UTC')
    for name, args in [('do_conj', [source, expanded, oddkeys]),
                       ('indexvbs', [expanded, root / 'steminds/vbind'])]:
        run = subprocess.run([str(tools / name), '-L', *map(str, args)],
                             cwd=root, env=env, capture_output=True)
        write_private(work / ('present-trial-' + name + '.log'), run.stdout + run.stderr)
        if run.returncode:
            raise ValueError('private native index construction failed: ' + name)
    return {name: digest(root / 'steminds' / name)
            for name in ('nomind', 'nomind.lindex', 'vbind', 'vbind.lindex')}


def compare_rows(before, after, source_lemmas):
    left = Counter(row for row, _ in before)
    right = Counter(row for row, _ in after)
    removed, added = left - right, right - left
    provenance = Counter()
    for signature, count in added.items():
        matching = [preverb for row, preverb in after if row == signature]
        if any(matching) and not all(matching):
            provenance['ambiguous_provenance_review'] += count
        elif any(matching):
            provenance['native_preverb_review'] += count
        elif signature[1] in source_lemmas and signature[2] == 2:
            provenance['direct_source_verb'] += count
        else:
            provenance['other_review'] += count
    return {'retained_rows': sum((left & right).values()),
            'removed_rows': sum(removed.values()), 'added_rows': sum(added.values()),
            **provenance}


def comparison(forms, library, before, after, output, source_lemmas=None, identical=False):
    left = listall.NativeAnalyzer(library, before)
    try:
        right = listall.NativeAnalyzer(library, after)
        try:
            report = listall.audit(forms, left, right, output, identical)
        finally:
            right.close()
    finally:
        left.close()
    if report['counts'].get('error', 0):
        raise ValueError('full comparison has native errors')
    report['private_difference_sha256'] = digest(output)
    if source_lemmas is None:
        return report
    totals = Counter()
    left = NativeRows(library, before)
    try:
        right = NativeRows(library, after)
        try:
            with output.open() as stream:
                for raw in stream:
                    row = json.loads(raw)
                    if row['curated_count'] == row['rebuilt_count']:
                        continue
                    word = row['form'].encode('ascii')
                    old, new = left.rows(word), right.rows(word)
                    if len(old) != row['curated_count'] or len(new) != row['rebuilt_count']:
                        raise ValueError('private reading reanalysis differs from full counts')
                    totals['increased_forms' if len(new) > len(old) else 'decreased_forms'] += 1
                    totals.update(compare_rows(old, new, source_lemmas))
        finally:
            right.close()
    finally:
        left.close()
    report['changed_form_eleven_field_multisets'] = dict(sorted(totals.items()))
    report['signature_fields'] = list(SIGNATURE)
    return report


def qualify(forms, library, baseline, stage, tools, output, expected_forms=None, include_backlinked=False):
    forms, library, baseline, stage, tools = (p.resolve() for p in (forms, library, baseline, stage, tools))
    output = output.resolve()
    inputs = [p.resolve() for p in (forms, library, baseline, stage, tools)]
    if (output == REPO or REPO in output.parents or
            any(output == p or p in output.parents or output in p.parents for p in inputs)):
        raise ValueError('private work directory must be outside repository and inputs')
    names = ('cited-future-imperative', 'boundary-present', 'vowel-present')
    if include_backlinked:
        names += ('backlinked-present',)
    paths = {name: stage / ('verbal-letters-only-' + name + '.stems') for name in names}
    boundary_lemmas = additions(paths[names[0]].read_bytes(), paths[names[1]].read_bytes(), 11)
    vowel_lemmas = additions(paths[names[1]].read_bytes(), paths[names[2]].read_bytes(), 4)
    if include_backlinked:
        backlinked_lemmas = additions(paths[names[2]].read_bytes(), paths[names[3]].read_bytes(), 9)
    output.mkdir(mode=0o700)
    report = {'schema': 1, 'scope': 'verbal present trials with controlled rebuilt nominal witnesses',
              'nominal_policy': 'all baseline nominals unchanged; excludes five private reconstruction decisions',
              'input_sha256': {'forms': digest(forms), 'native_library': digest(library),
                               **{name: digest(path) for name, path in paths.items()}},
              'indexes': {}, 'comparisons': {}}
    for name in names:
        report['indexes'][name] = build_trial(baseline, paths[name], tools, output / name)
        print(json.dumps({'research_index': name, 'sha256': report['indexes'][name]}, sort_keys=True), flush=True)
    quantity = stage / 'verbal-all-vowel-present.stems'
    report['input_sha256']['all-quantity-vowel-present'] = digest(quantity)
    report['indexes']['all-quantity-vowel-present'] = build_trial(baseline, quantity, tools, output / 'all-quantity')
    if report['indexes'][names[2]] != report['indexes']['all-quantity-vowel-present']:
        raise ValueError('quantity treatments produce different indexes')
    if include_backlinked:
        quantity = stage / 'verbal-all-backlinked-present.stems'
        report['input_sha256']['all-quantity-backlinked-present'] = digest(quantity)
        report['indexes']['all-quantity-backlinked-present'] = build_trial(baseline, quantity, tools, output / 'all-quantity-backlinked')
        if report['indexes'][names[3]] != report['indexes']['all-quantity-backlinked-present']:
            raise ValueError('backlinked quantity treatments produce different indexes')
    for name in names:
        for nominal in ('nomind', 'nomind.lindex'):
            if report['indexes'][name][nominal] != digest(baseline / 'Latin/steminds' / nominal):
                raise ValueError('nominal witness changed')
    passes = [('boundary-control', names[1], names[1], None, True),
              ('vowel-control', names[2], names[2], None, True),
              ('boundary-step', names[0], names[1], boundary_lemmas, False),
              ('vowel-step', names[1], names[2], vowel_lemmas, False),
              ('baseline-to-vowel', None, names[2], None, False)]
    if include_backlinked:
        passes += [('backlinked-control', names[3], names[3], None, True),
                   ('backlinked-step', names[2], names[3], backlinked_lemmas, False)]
    for label, old, new, lemmas, identical in passes:
        result = comparison(forms, library, baseline if old is None else output / old,
                            output / new, output / (label + '.jsonl'), lemmas, identical)
        if expected_forms is not None and result['counts']['distinct_forms'] != expected_forms:
            raise ValueError('full comparison form count differs')
        if label == 'backlinked-step' and result['changed_form_eleven_field_multisets'].get('removed_rows', 0):
            raise ValueError('backlinked trial removes previous grammatical readings')
        report['comparisons'][label] = result
        print(json.dumps({'research_comparison': label, 'report': result}, sort_keys=True), flush=True)
    write_private(output / 'report.json', (json.dumps(report, sort_keys=True, indent=2) + '\n').encode())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('forms', 'library', 'baseline', 'stage', 'tools', 'private-output'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--expected-forms', type=int)
    parser.add_argument('--include-backlinked', action='store_true')
    args = parser.parse_args()
    qualify(args.forms, args.library, args.baseline, args.stage, args.tools,
            args.private_output, args.expected_forms, args.include_backlinked)


if __name__ == '__main__':
    main()
