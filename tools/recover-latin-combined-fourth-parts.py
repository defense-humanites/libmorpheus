#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Recover unhandled combined fourth-conjugation headers with explicit parts."""
import argparse
from collections import Counter, defaultdict
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re

spec = importlib.util.spec_from_file_location('alternates', Path(__file__).with_name('recover-latin-full-alternates.py'))
alternates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alternates)
first = alternates.first
TIERS = {'with-supine': ['u^i and i_vi', 'i_tum, 4'],
         'perfect-only': ['i_vi or u^i', '4']}


def proof(row, tier):
    if tier not in TIERS:
        raise ValueError('unsupported recovery tier')
    if row.get('projection_error') is not None:
        return None
    fields = row['fields']
    types = [f['projection'] for f in fields if f['name']=='itype']
    positions = [i for i,f in enumerate(fields) if f['name']=='itype']
    pos = [f['projection'] for f in fields if f['name']=='pos']
    orths = [f for f in fields if f['name']=='orth']
    if (types != TIERS[tier] or len(positions)!=2 or positions[1]!=positions[0]+1 or
            pos not in [['v. a.'], ['v. n.']] or len(orths)!=2 or
            any(f['name'] not in {'orth','itype','pos'} for f in fields)):
        return None
    head = re.sub(r'#[1-9]$', '', row['headword'])
    alts = row.get('full_alternates', [])
    if len(alts)!=1 or not all(re.fullmatch(r'[A-Za-z_^]+(?:-[A-Za-z_^]+)*i[_^]?o', h) for h in [head,alts[0]]):
        return None
    roots = [re.sub(r'i[_^]?o$', '', h).encode() for h in [head,alts[0]]]
    if roots[0].translate(None,b'_^-' )==roots[1].translate(None,b'_^-' ):
        return None
    lemma = row['headword'].translate(str.maketrans('', '', '_^-')).encode()
    records = [b':le:'+lemma+b'\n']
    perfects = [b'u^',b'i_v'] if tier=='with-supine' else [b'i_v',b'u^']
    for index,root in enumerate(roots):
        flags = b' orth' if index else b''
        records.append(b':vs:'+root+b'\tconj4'+flags+b'\n')
        for ending in perfects:
            records.append(b':vs:'+root+ending+b' perfstem'+flags+b'\n')
        if tier=='with-supine':
            records.append(b':vs:'+root+b'i_t pp4'+flags+b'\n')
    # The historical chain joins these adjacent fields and normalizes the
    # perfect-only disjunction comma; no source field is moved.
    joined = copy.deepcopy(row)
    first_type = types[0] if tier=='with-supine' else 'i_vi, or u^i'
    joined['fields'][positions[0]]['projection'] = first_type+', '+types[1]
    del joined['fields'][positions[1]]
    raw = first.compound.recovery.render(joined).encode()
    return lemma, raw, b''.join(records), len(records)-1


def transform(candidate, rows, tier='with-supine'):
    if tier not in TIERS:
        raise ValueError('unsupported recovery tier')
    proofs = defaultdict(list)
    for row in rows:
        result = proof(row,tier)
        if result:
            proofs[result[0]].append(result)
    lemmas = {line[4:].strip() for line in candidate.splitlines() if line.startswith(b':le:')}
    lines = candidate.splitlines(keepends=True)
    additions = {}; counts = Counter()
    for lemma,choices in proofs.items():
        if len(choices)!=1:
            counts['withheld_ambiguous_source'] += 1; continue
        _,raw,records,n = choices[0]
        if lemma in lemmas:
            counts['withheld_existing_lemma'] += 1; continue
        if lines.count(raw)!=1:
            counts['withheld_missing_or_duplicate_header'] += 1; continue
        additions[raw] = records
        counts['recovered_headers'] += 1
        counts['added_stem_records'] += n
    return b''.join(line+additions.get(line,b'') for line in lines),dict(sorted(counts.items()))


def prepare(candidate,headers,lexica,output,expected=None,tier='with-supine'):
    target = first.private_target(candidate,headers,lexica,output)
    rows,source,revision = alternates.source_alternates(headers,lexica)
    data,counts = transform(candidate.read_bytes(),rows,tier)
    if expected is not None and counts.get('recovered_headers',0)!=expected:
        raise ValueError('unexpected recovered header count')
    report = {'schema':1,'scope':'exact adjacent combined fourth-conjugation fields and complete alternate',
              'tier':tier,'source_revision':revision,'counts':counts,
              'input_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (candidate,headers,source)},
              'output_sha256':hashlib.sha256(data).hexdigest()}
    first.write_private(target,data)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate','headers','lexica','private-output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--expected',type=int)
    parser.add_argument('--tier',choices=list(TIERS),default='with-supine')
    args = parser.parse_args()
    print(json.dumps(prepare(args.candidate,args.headers,args.lexica,args.private_output,args.expected,args.tier),sort_keys=True))


if __name__=='__main__':
    main()
