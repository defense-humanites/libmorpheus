#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Combine the separately qualified Latin trials into one private candidate.

Each trial so far was staged and measured on the unchanged full source
candidate. This tool applies the same bounded recipes in a fixed order, each
on the output of the previous one, and records every stage's counts and
SHA-256. The order lets later recipes see earlier repairs: the attribution
replay and the deletions come first, the labiovelar, anchor, sigmatic and
residual attachment replacements next, then the same attachment repairs on
the headers whose itype fields combitype joins, the prefix alternates copy
the repaired records, the
backlinked and quoted presents follow, and the earlier -jicio repair closes
the chain for the block the attribution replay unblocks. No recipe is changed; lexical values
stay private.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sibling(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STAGES = (
    ('editor-attributions', 'recover-latin-editor-attributions'),
    ('itype-tag-leak', 'repair-latin-itype-tag-leak'),
    ('velar-short-suffix', 'repair-latin-velar-short-suffix'),
    ('anchor-duplication', 'repair-latin-anchor-duplication'),
    ('sigmatic-suffix', 'repair-latin-sigmatic-suffix'),
    ('residual-attachments', 'repair-latin-residual-attachments'),
    ('joined-itypes', 'repair-latin-joined-itypes'),
    ('prefix-alternates', 'recover-latin-prefix-alternates'),
    ('backlinked-presents', 'recover-latin-backlinked-present-classes'),
    ('quoted-presents', 'recover-latin-backlinked-present-classes'),
    ('jicio-parts', 'repair-latin-jicio-parts'),
)


def run_stage(name, tool, candidate, headers, lexica, filters, target):
    module = sibling(tool)
    output = target / (name + '.stems')
    if name == 'editor-attributions':
        report = module.prepare(candidate, headers, lexica, filters, target / name)
        output = target / name / 'after.stems'
    elif name == 'backlinked-presents':
        report = module.prepare(candidate, headers, lexica, output, None, 'backlink')
    elif name == 'quoted-presents':
        report = module.prepare(candidate, headers, lexica, output, None, 'quotation')
    else:
        report = module.prepare(candidate, headers, lexica, output)
    return output, report


def prepare(candidate, headers, lexica, filters, output):
    first = sibling('repair-latin-first-conjugation')
    target = first.private_target(candidate, headers, lexica, output)
    target.mkdir(mode=0o700)
    stages = []
    current = candidate
    for name, tool in STAGES:
        current, report = run_stage(name, tool, current, headers, lexica, filters, target)
        stages.append({'stage': name, 'tool': tool + '.py', 'counts': report['counts'],
                       'input_sha256': hashlib.sha256(candidate.read_bytes()).hexdigest() if not stages else stages[-1]['output_sha256'],
                       'output_sha256': report['output_sha256']})
    final = target / 'combined.stems'
    first.write_private(final, current.read_bytes())
    return {'schema': 1,
            'scope': 'the nine separately qualified trials, the joined-itype extension of the attachment repairs and the earlier -jicio repair applied in sequence on one private candidate; per-stage counts and hashes; no production promotion',
            'source_revision': stages and sibling('recover-latin-initial-sense').review.REVISION,
            'input_sha256': hashlib.sha256(candidate.read_bytes()).hexdigest(),
            'stages': stages, 'output_sha256': hashlib.sha256(final.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate', 'headers', 'lexica', 'filters', 'private-output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    previous = os.umask(0o077)
    try:
        report = prepare(args.candidate, args.headers, args.lexica, args.filters, args.private_output)
    finally:
        os.umask(previous)
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
