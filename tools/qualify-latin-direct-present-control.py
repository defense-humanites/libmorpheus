#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Qualify a not_in_comp counterfactual copy of one source-present trial.

The flag is a diagnostic intervention, never a claimed source property.
"""
import argparse
from collections import Counter
import importlib.util
import json
import os
from pathlib import Path
import shutil

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('loss', REPO / 'tools/diagnose-latin-lost-stems.py')
loss = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loss)
native = loss.sibling('qualify-latin-present-stages')
audit = loss.sibling('audit-latin-global-readings')


class StrictRows(native.NativeRows):
    def rows(self, word):
        return [(loss.signature(r), r.preverb) for r in self.analyses(word, require_untruncated=True)]


def restricted_payload(data, lemma):
    current, changed, out = None, 0, []
    for line in data.splitlines(keepends=True):
        if line.startswith(b':le:'):
            current = line[4:].strip()
        if current == lemma and line.startswith(loss.STEM_PREFIXES):
            if not line.startswith(b':vs:') or line.split()[1:] != [b'conj1']:
                raise ValueError('selected present directive differs from qualified class')
            newline = b'\r\n' if line.endswith(b'\r\n') else b'\n' if line.endswith(b'\n') else b''
            line = line[:len(line)-len(newline)] if newline else line
            line += b' not_in_comp' + newline
            changed += 1
        out.append(line)
    if changed != 1:
        raise ValueError('restriction needs exactly one qualified present directive')
    return b''.join(out)


def route(r):
    return loss.signature(r) + (r.preverb, r.raw_preverb, r.stem, r.suffix, r.ending)


def family_control(cells, opened, restricted):
    counts = Counter()
    for cell in cells:
        word = cell['form'].encode('ascii'); lemma = cell['lemma'].encode('ascii')
        left = opened.analyses(word, require_untruncated=True)
        right = restricted.analyses(word, require_untruncated=True)
        if Counter(map(route, left)) != Counter(map(route, right)):
            raise ValueError('restriction changes a qualified present-family multiset')
        expected = sum(not r.preverb and r.lemma == lemma and
            (r.part_of_speech, r.person, r.number, r.tense, r.mood, r.voice) ==
            (2, cell['person'], cell['number'], 1, cell['mood'], cell['voice']) for r in right)
        if not expected:
            raise ValueError('restricted source-present expectation missing')
        counts['cells_unchanged'] += 1; counts['expected_readings'] += expected
    return dict(counts)


def prepare(args):
    inputs = {name: getattr(args, name) for name in ('source', 'family', 'forms', 'candidate_source')}
    if any(loss.digest(path) != getattr(args, 'expected_' + name + '_sha256') for name, path in inputs.items()):
        raise ValueError('direct-present input receipt differs')
    cells = [json.loads(line) for line in args.family.read_text().splitlines()]
    lemmas = {c['lemma'] for c in cells}
    if len(cells) != 13 or len(lemmas) != 1 or any(c['kind'] != 'source_present_family' for c in cells):
        raise ValueError('qualified family inventory differs')
    lemma = next(iter(lemmas)).encode('ascii')
    if loss.definitions(args.candidate_source).get(lemma):
        raise ValueError('selected lemma already has original candidate definitions')
    names = ('nomind', 'nomind.lindex', 'vbind', 'vbind.lindex')
    original = {name: loss.digest(args.candidate / 'Latin/steminds' / name) for name in names}
    opened_hashes = {name: loss.digest(args.opened / 'Latin/steminds' / name) for name in names}
    if (opened_hashes['vbind'] != args.expected_vbind_sha256 or
            opened_hashes['vbind.lindex'] != args.expected_vside_sha256 or
            any(opened_hashes[n] != original[n] for n in names[:2])):
        raise ValueError('qualified open-trial index receipt differs')
    target = loss.private_target(args.output, [*inputs.values(), args.candidate, args.opened, args.tools, args.library])
    target.mkdir(mode=0o700)
    source = target / 'restricted.stems'
    native.write_private(source, restricted_payload(args.source.read_bytes(), lemma))
    # A qualified trial already contains build logs and intermediate inputs.
    # Clean only their copied versions so exclusive private writes stay valid.
    template = target / 'template'
    shutil.copytree(args.opened, template)
    for name in ('input', 'expanded', 'oddkeys', 'do_conj.log', 'indexvbs.log'):
        (template / 'Latin/lexical' / ('present-trial.' + name if name in ('input', 'expanded', 'oddkeys') else
                                      'present-trial-' + name)).unlink(missing_ok=True)
    hashes = native.build_trial(template, source, args.tools, target / 'native')
    if any(hashes[n] != original[n] for n in names[:2]):
        raise ValueError('restriction changes nominal indexes')
    readers = {}
    try:
        readers['candidate'] = StrictRows(args.library, args.candidate)
        readers['opened'] = StrictRows(args.library, args.opened)
        readers['restricted'] = StrictRows(args.library, target / 'native')
        family = family_control(cells, readers['opened'], readers['restricted'])
        comparisons = {}
        for label, left, right, identical in (
            ('restricted_global_control', 'restricted', 'restricted', True),
            ('candidate_to_restricted', 'candidate', 'restricted', False),
            ('open_to_restricted', 'opened', 'restricted', False)):
            report = audit.audit(args.forms, readers[left], readers[right], target / (label + '.jsonl'),
                                 require_identical=identical)
            if report['counts']['distinct_forms'] != args.expected_forms or report['input_sha256'] != args.expected_forms_sha256:
                raise ValueError('restriction global form scope differs')
            comparisons[label] = report
    finally:
        for reader in readers.values():
            reader.close()
    if any(loss.digest(args.candidate / 'Latin/steminds' / n) != original[n] or
           loss.digest(args.opened / 'Latin/steminds' / n) != opened_hashes[n] for n in names) or any(
           loss.digest(p) != getattr(args, 'expected_' + n + '_sha256') for n, p in inputs.items()):
        raise ValueError('direct-present counterfactual changed an original input')
    return {'schema': 1, 'scope': 'not_in_comp counterfactual only; no source annotation, repair promotion or production change',
        'source_family_control': family, 'global_comparisons': comparisons,
        'original_candidate_and_open_trial_unchanged': True, 'indexes_sha256': hashes,
        'restricted_source_sha256': loss.digest(source), 'input_sha256': {n: loss.digest(p) for n, p in inputs.items()}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ('source', 'family', 'forms', 'candidate-source', 'candidate', 'opened', 'tools', 'library', 'output'):
        p.add_argument('--' + n, type=Path, required=True)
    for n in ('source', 'family', 'forms', 'candidate-source', 'vbind', 'vside'):
        p.add_argument('--expected-' + n + '-sha256', required=True)
    p.add_argument('--expected-forms', type=int, required=True)
    previous = os.umask(0o077)
    try:
        report = prepare(p.parse_args())
    finally:
        os.umask(previous)
    print(json.dumps({'latin_direct_present_control': report}, sort_keys=True))


if __name__ == '__main__':
    main()
