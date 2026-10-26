#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Qualify isolated source supine alternatives; lexical values stay private."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path

import importlib.util
spec=importlib.util.spec_from_file_location('review',Path(__file__).with_name('review-latin-historical-filter-delta.py'))
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
direct=review.sibling('qualify-latin-direct-present-control')
native=direct.native
REVIEW_SHA='10d79072c4df8923acbb85fbd0cd28ec4a3e49b8a05cc2962ddb37cb03983023'
# These are the engine's pp4 table codes, including historical supine
# nominative/dative labels. They are not a philological case correction.
CELLS=(('um',0,9,0,8,16),('u_',0,9,0,8,4),
       ('us',5,7,2,4,16),('um',5,7,2,8,16),
       ('urus',3,7,1,4,16),('urum',3,7,1,8,16))


def expectations(dossier,data):
    row=dossier['source_header'];lemma=review.source_key(row)
    if lemma is None or lemma.decode()!=dossier['lemma']:
        raise ValueError('source lemma join differs')
    branch,expected=review.source_expectations(row)
    if branch!='explicit_compound_two_perfects_two_supines' or sum(expected.values())!=5:
        raise ValueError('source alternatives differ from qualified recipe')
    selected=Counter()
    for (key,line),count in review.probe.definitions(data).items():
        if key==lemma:selected[tuple(line.split())]+=count
    declared=Counter({tuple(r['directive'].encode().split()):r['multiplicity'] for r in dossier['after']})
    missing=expected-selected
    if selected!=declared or selected-expected or sum(missing.values())!=1 or any(
            tokens[1:]!=(b'pp4',) for tokens in missing):
        raise ValueError('trial must insert exactly one missing source supine')
    return lemma,selected,expected


def payload(lemma,records):
    return b':le:'+lemma+b'\n'+b''.join(b' '.join(tokens)+b'\n' for tokens,count in sorted(records.items()) for _ in range(count))


def family_cells(expected):
    cells=[]
    for tokens,count in expected.items():
        if tokens[1:]!=(b'pp4',):continue
        if count!=1:raise ValueError('duplicated source supine')
        # Strip separators and quantity only for analysis input, never stems.
        stem=tokens[0][4:]
        for ending,tense,mood,voice,gender,case in CELLS:
            form=(stem+ending.encode()).translate(None,b'_^-' )
            cells.append((form,(2,0,1,gender,case,tense,mood,voice,0)))
    if len(cells)!=12:raise ValueError('expected two supine families')
    return cells


def cell_signature(row):
    return tuple(getattr(row,name) for name in ('part_of_speech','person','number','gender',
        'grammatical_case','tense','mood','voice','degree'))


def compare_family(lemma,cells,before,after,target):
    totals=Counter();evidence=[]
    for form,signature in cells:
        old=before.analyses(form,require_untruncated=True)
        new=after.analyses(form,require_untruncated=True)
        matches=lambda rows:sum(r.lemma==lemma and not r.preverb and cell_signature(r)==signature for r in rows)
        old_count,new_count=matches(old),matches(new)
        if not new_count:raise ValueError('source supine family expectation missing')
        totals['expected_cells']+=1;totals['covered_before']+=bool(old_count)
        totals['covered_after']+=bool(new_count);totals['expected_readings_before']+=old_count
        totals['expected_readings_after']+=new_count
        evidence.append({'form':form.decode(),'signature':signature,'before':old_count,'after':new_count})
    forms=sorted({form for form,_ in cells})
    counts=Counter()
    for form in forms:
        old=Counter(map(direct.route,before.analyses(form,require_untruncated=True)))
        new=Counter(map(direct.route,after.analyses(form,require_untruncated=True)))
        counts['retained_rows']+=sum((old&new).values());counts['removed_rows']+=sum((old-new).values())
        counts['added_rows']+=sum((new-old).values());counts['changed_forms']+=bool(old-new or new-old)
    native.write_private(target/'family.jsonl',b''.join((json.dumps(r,sort_keys=True)+'\n').encode() for r in evidence))
    native.write_private(target/'forms',b''.join(f+b'\n' for f in forms))
    return {'source_cells':dict(totals),'distinct_forms':len(forms),
        'sixteen_field_multisets':dict(counts),'private_family_sha256':native.digest(target/'family.jsonl')}


def prepare(args):
    original={name:getattr(args,name).read_bytes() for name in ('review','diagnostic')}
    if (review.probe.digest(original['review'])!=REVIEW_SHA or
            review.probe.digest(original['diagnostic'])!=review.RECEIPTS['diagnostic']):
        raise ValueError('source supine qualification receipt differs')
    dossier=json.loads(original['review']);lemma,before,after=expectations(dossier,original['diagnostic'])
    first=review.sibling('repair-latin-first-conjugation')
    target=first.private_target(args.diagnostic,args.review,args.library,args.output)
    target.mkdir(mode=0o700)
    indexes={};sources={};readers={}
    names=('nomind','nomind.lindex','vbind','vbind.lindex')
    baseline={n:native.digest(args.baseline/'Latin/steminds'/n) for n in names}
    try:
        for label,records in (('before',before),('after',after)):
            source=target/(label+'.stems');native.write_private(source,payload(lemma,records))
            sources[label]=native.digest(source)
            indexes[label]=native.build_trial(args.baseline,source,args.tools,target/label)
            if any(indexes[label][n]!=baseline[n] for n in names[:2]):
                raise ValueError('supine trial changes nominal indexes')
            readers[label]=direct.StrictRows(args.library,target/label)
        cells=family_cells(after)
        family=compare_family(lemma,cells,readers['before'],readers['after'],target)
        control=direct.audit.audit(target/'forms',readers['after'],readers['after'],target/'control.jsonl',require_identical=True)
        delta=direct.audit.audit(target/'forms',readers['before'],readers['after'],target/'differences.jsonl')
    finally:
        for reader in readers.values():reader.close()
    if any(getattr(args,n).read_bytes()!=data for n,data in original.items()) or any(
            native.digest(args.baseline/'Latin/steminds'/n)!=baseline[n] for n in names):
        raise ValueError('source supine trial changed an original input')
    return {'schema':1,'scope':'isolated one-lemma source-supine families only; no full candidate or LISTALL qualification, no production promotion',
        'engine_supine_case_codes':'historical pp4 table nominative/dative; no philological case correction',
        'input_sha256':{n:review.probe.digest(data) for n,data in original.items()},
        'source_sha256':sources,'indexes_sha256':indexes,'family':family,
        'identical_root_control':control,'family_comparison':delta,'original_inputs_unchanged':True}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('review','diagnostic','baseline','tools','library','output'):
        p.add_argument('--'+name,type=Path,required=True)
    previous=os.umask(0o077)
    try:report=prepare(p.parse_args())
    finally:os.umask(previous)
    print(json.dumps({'latin_historical_source_supine_families':report},sort_keys=True))


if __name__=='__main__':main()
