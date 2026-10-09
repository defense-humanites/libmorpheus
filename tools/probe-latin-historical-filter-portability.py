#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare a private sanitizer-built latvb copy with a pinned historical output.

This diagnostic never replaces a lexer, candidate or runtime index.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

LEXER_SHA256 = '27765fb0e13ba200f432c98218e1bb53126acedb391bf1d8c5cabe1fe30dd231'
TRUNCSTEM = '''truncstem(char * workstem, int trimn)
{
    size_t n = strlen(workstem);
    if (trimn == 1) {
        if (n >= 2 && !strcmp("ct",workstem+n-2)) workstem[n-2] = 0;
        else if (n) workstem[n-1] = 0;
    } else if (isalpha(trimn)) {
        while (n) {
            n--;
            if ((trimn == 's' && (workstem[n] == 'd' || workstem[n] == 'q')) || workstem[n] == trimn) {
                workstem[n] = 0;
                break;
            }
        }
    }
    return 0;
}
'''
STEM_PREFIXES = (b':vs:', b':de:', b':vb:', b':wd:')
ASAN_CATEGORIES = {'strcpy-param-overlap', 'stack-buffer-overflow', 'global-buffer-overflow',
                   'heap-buffer-overflow', 'stack-buffer-underflow', 'heap-use-after-free',
                   'stack-use-after-return', 'stack-use-after-scope', 'SEGV', 'DEADLYSIGNAL'}
FUNCTIONS = {'set_lemma', 'set_orth', 'do_vstems', 'truncstem', 'do_itype',
             'doverb', 'doderiv', 'is_spectype', 'yylex', 'main'}


class DiagnosticProcessError(ValueError):
    def __init__(self, summary):
        super().__init__('private diagnostic process failed; detailed logs remain private')
        self.summary = summary


def failure_summary(name, returncode, stderr):
    """Reconstruct only allowlisted categories/locations; never copy log lines."""
    text = stderr.decode('utf-8', errors='replace')
    candidates = re.findall(r'AddressSanitizer: ([A-Za-z_-]+)', text)
    categories = sorted(set(candidates) & ASAN_CATEGORIES)
    if 'runtime error:' in text:
        categories.append('undefined-behavior')
    lines = sorted({int(n) for n in re.findall(r'/latvb\.[lc]:([0-9]+)', text)})
    functions = sorted(set(re.findall(r'\bin ([A-Za-z_][A-Za-z_0-9]*)', text)) & FUNCTIONS)
    return {'schema': 1, 'scope': 'failed diagnostic process; no output comparison qualified',
            'operation': name if name in {'flex', 'cc', 'filter'} else 'unknown',
            'returncode': returncode, 'categories': categories,
            'lexer_or_generated_source_lines': lines, 'functions': functions}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def diagnostic_source(data):
    if digest(data) != LEXER_SHA256:
        raise ValueError('historical lexer receipt differs')
    text = data.decode('ascii')
    for old, new, count in (
        ('strcpy(t,t+1);', 'memmove(t,t+1,strlen((const char *)t+1)+1);', 1),
        ('strcpy(perfsuff,t);', 'memmove(perfsuff,t,strlen((const char *)t)+1);', 2)):
        if text.count(old) != count:
            raise ValueError('diagnostic copy site inventory differs')
        text = text.replace(old, new)
    marker = 'truncstem(char * workstem, int trimn)\n{'
    if text.count(marker) != 1:
        raise ValueError('diagnostic truncation site inventory differs')
    # This pinned lexer ends with this function; the source receipt binds its tail.
    return (text[:text.index(marker)] + TRUNCSTEM).encode('ascii')


def definitions(data):
    lemma, records = None, Counter()
    for line in data.splitlines():
        if line.startswith(b':le:'):
            lemma = line[4:].strip()
            if not lemma or any(c < 33 or c > 126 for c in lemma):
                raise ValueError('invalid historical lemma record')
        elif line.startswith(STEM_PREFIXES):
            if lemma is None or not line[4:].split():
                raise ValueError('unbound historical stem record')
            records[lemma, line] += 1
    return records


def compare(before, after):
    left, right = definitions(before), definitions(after)
    lemmas = {k[0] for k in left | right}
    changed = {lemma for lemma, _ in (left - right) | (right - left)}
    return {
        'before_rows': sum(left.values()), 'after_rows': sum(right.values()),
        'retained_rows': sum((left & right).values()),
        'removed_rows': sum((left - right).values()), 'added_rows': sum((right - left).values()),
        'union_lemmas': len(lemmas), 'changed_lemma_multisets': len(changed),
        'unchanged_lemma_multisets': len(lemmas - changed)}, left, right


def write_private(path, data):
    with path.open('xb') as stream:
        os.chmod(path, 0o600)
        stream.write(data)


def run_private(command, target, name, data=None):
    try:
        result = subprocess.run(command, input=data, capture_output=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        raise ValueError('private diagnostic process could not complete') from None
    write_private(target / (name + '.stdout'), result.stdout)
    write_private(target / (name + '.stderr'), result.stderr)
    if result.returncode:
        raise DiagnosticProcessError(failure_summary(name, result.returncode, result.stderr))
    return result.stdout


def prepare(args):
    paths = {'lexer': args.lexer, 'input': args.input, 'reference': args.reference}
    original = {n: p.read_bytes() for n, p in paths.items()}
    if digest(original['reference']) != args.expected_reference_sha256:
        raise ValueError('historical reference receipt differs')
    modified = diagnostic_source(original['lexer'])
    target = args.output.resolve()
    target.mkdir(mode=0o700)
    lexer, generated, binary = target / 'latvb.l', target / 'latvb.c', target / 'latvb'
    write_private(lexer, modified)
    run_private(['flex', '-o', str(generated), str(lexer)], target, 'flex')
    options = ['-std=gnu89', '-w', '-g', '-fsanitize=address,undefined',
               '-fno-sanitize-recover=all', '-fno-omit-frame-pointer']
    if sys.platform == 'darwin':
        options.append('-Wno-return-mismatch')
    run_private(['cc', *options, str(generated), '-o', str(binary),
                 '-ll' if sys.platform == 'darwin' else '-lfl'], target, 'cc')
    result = run_private([str(binary)], target, 'filter', original['input'])
    metrics, left, right = compare(original['reference'], result)
    changes = []
    for label, records in (('removed', left - right), ('added', right - left)):
        for (lemma, line), count in sorted(records.items()):
            changes.append(json.dumps({'change': label, 'lemma': lemma.decode('ascii'),
                                       'directive': line.decode('ascii'), 'multiplicity': count}, sort_keys=True))
    private_delta = ('\n'.join(changes) + ('\n' if changes else '')).encode()
    write_private(target / 'differences.jsonl', private_delta)
    if any(p.read_bytes() != original[n] for n, p in paths.items()):
        raise ValueError('historical control changed an original input')
    return {'schema': 1, 'scope': 'diagnostic lexer copy only; no candidate or production substitution',
            'platform': sys.platform, 'instrumentation': 'address,undefined; no recovery',
            'input_sha256': {n: digest(d) for n, d in original.items()},
            'diagnostic_lexer_sha256': digest(modified), 'output_sha256': digest(result),
            'raw_output_equal': result == original['reference'], 'definition_multisets': metrics,
            'private_delta_sha256': digest(private_delta), 'sanitizer_process_exit': 0,
            'original_inputs_unchanged': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for n in ('lexer', 'input', 'reference', 'output'):
        parser.add_argument('--' + n, type=Path, required=True)
    parser.add_argument('--expected-reference-sha256', required=True)
    previous = os.umask(0o077)
    try:
        try:
            report = prepare(parser.parse_args())
        except DiagnosticProcessError as error:
            print(json.dumps({'latin_historical_filter_failure': error.summary}, sort_keys=True), flush=True)
            raise ValueError(str(error)) from None
    finally:
        os.umask(previous)
    print(json.dumps({'latin_historical_filter_portability': report}, sort_keys=True))


if __name__ == '__main__':
    main()
