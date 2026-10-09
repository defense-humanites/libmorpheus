#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Qualify one source-alternative replacement in a separate full candidate."""
import argparse
from collections import Counter
import importlib.util
import json
import os
from pathlib import Path

spec=importlib.util.spec_from_file_location('supines',Path(__file__).with_name('qualify-latin-historical-source-supines.py'))
supines=importlib.util.module_from_spec(spec);spec.loader.exec_module(supines)
review=supines.review
native=supines.native
CANDIDATE_SHA='6caf089d03e62d745aebc94d1b1cc5cf06938626db4af8c794a2326ca7a94cd9'
FORMS_SHA='1df0800fb1443b2cfd64d787c257319aa72b69f453c3c37ec60c359c70cebd93'
INDEXES={'nomind':'106592a19b3b34a343c271fadcc559cdef10363c0d7f4ea024a71ae613e1bd54',
    'nomind.lindex':'e70bc11f301cbdf9765cb56b30109f0fc53539c19056168c2e09c05503d05210',
    'vbind':'d13367a683e0645adcbe83ab1b34ddc9a4444c8d22d2c9d83fcaf5e875f39ac4',
    'vbind.lindex':'486c8641cb83a5d1b8dd2184aae9204b7f7a77ce3293daadbe4a7c1b3b36e954'}


def records(rows):
    result=Counter()
    for row in rows:result[tuple(row['directive'].encode().split())]+=row['multiplicity']
    return result


def replace_selected(data,dossier):
    lemma=review.source_key(dossier['source_header'])
    if lemma is None or lemma.decode()!=dossier['lemma']:raise ValueError('candidate source join differs')
    branch,expected=review.source_expectations(dossier['source_header'])
    if branch!='explicit_compound_two_perfects_two_supines' or sum(expected.values())!=5:
        raise ValueError('candidate source recipe differs')
    selected=Counter()
    for (key,line),count in review.probe.definitions(data).items():
        if key==lemma:selected[tuple(line.split())]+=count
    if selected!=records(dossier['before']):
        raise ValueError('candidate selected directives differ from qualified historical review')
    out=[];current=None;blocks=0;inserted=False
    for line in data.splitlines(keepends=True):
        if line.startswith(b':le:'):
            current=line[4:].strip();blocks+=current==lemma
        if current==lemma and line.startswith(review.probe.STEM_PREFIXES):
            if not inserted:
                out.extend(b' '.join(tokens)+b'\n' for tokens,count in sorted(expected.items()) for _ in range(count))
                inserted=True
        else:out.append(line)
    if blocks!=1 or not inserted:raise ValueError('candidate needs one unique selected definition block')
    result=b''.join(out)
    old=review.probe.definitions(data);new=review.probe.definitions(result)
    if any(key!=lemma for key,_ in (old-new).keys()|(new-old).keys()):
        raise ValueError('candidate replacement changes another lemma')
    removed,added=selected-expected,expected-selected
    classes=lambda rows:dict(Counter({kind:sum(n for tokens,n in rows.items() if review.classify(b' '.join(tokens))==kind)
        for kind in {review.classify(b' '.join(t)) for t in rows}}))
    return lemma,expected,result,{'removed':classes(removed),'added':classes(added)}


def prepare(args):
    paths={n:getattr(args,n) for n in ('candidate','review','forms')}
    receipts={'candidate':CANDIDATE_SHA,'review':supines.REVIEW_SHA,'forms':FORMS_SHA}
    if any(native.digest(p)!=receipts[n] for n,p in paths.items()):raise ValueError('full candidate qualification receipt differs')
    data=args.candidate.read_bytes();dossier=json.loads(args.review.read_bytes())
    lemma,expected,modified,classes=replace_selected(data,dossier)
    first=review.sibling('repair-latin-first-conjugation')
    target=first.private_target(args.candidate,args.review,args.forms,args.output);target.mkdir(mode=0o700)
    before_baseline={n:native.digest(args.baseline/'Latin/steminds'/n) for n in INDEXES}
    readers={};indexes={};sources={}
    try:
        for label,payload in (('before',data),('after',modified)):
            source=target/(label+'.stems');native.write_private(source,payload);sources[label]=native.digest(source)
            indexes[label]=native.build_trial(args.baseline,source,args.tools,target/label)
            if (label=='before' and indexes[label]!=INDEXES) or any(indexes[label][n]!=INDEXES[n] for n in ('nomind','nomind.lindex')):
                raise ValueError('full candidate native reference or nominal indexes differ')
            readers[label]=supines.direct.StrictRows(args.library,target/label)
        family=supines.compare_family(lemma,supines.family_cells(expected),readers['before'],readers['after'],target)
        control=supines.direct.audit.audit(args.forms,readers['after'],readers['after'],target/'global-control.jsonl',require_identical=True)
        print(json.dumps({'latin_source_candidate_checkpoint':{'phase':'identical-control-complete',
            'forms':control['counts']['distinct_forms'],'report_is_partial':True}},sort_keys=True),flush=True)
        delta=supines.direct.audit.audit(args.forms,readers['before'],readers['after'],target/'global-differences.jsonl')
        if any(r['counts']['distinct_forms']!=1033579 or r['input_sha256']!=FORMS_SHA for r in (control,delta)):
            raise ValueError('full candidate LISTALL scope differs')
        if delta['analysis_rows']['curated']!=2100530:
            raise ValueError('full candidate original reading count differs')
    finally:
        for reader in readers.values():reader.close()
    if any(native.digest(p)!=receipts[n] for n,p in paths.items()) or any(
        native.digest(args.baseline/'Latin/steminds'/n)!=before_baseline[n] for n in INDEXES):
        raise ValueError('full candidate qualification changed an original input')
    report={'schema':1,'scope':'one source-alternative replacement in a separate full candidate; aggregate qualification, no production promotion',
        'input_sha256':receipts,'source_sha256':sources,'source_delta_classes':classes,'indexes_sha256':indexes,
        'supine_family':family,'global_identical_control':control,'candidate_to_source_trial':delta,'original_inputs_unchanged':True}
    native.write_private(target/'report.json',(json.dumps(report,sort_keys=True)+'\n').encode())
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('candidate','review','forms','baseline','tools','library','output'):p.add_argument('--'+n,type=Path,required=True)
    previous=os.umask(0o077)
    try:report=prepare(p.parse_args())
    finally:os.umask(previous)
    print(json.dumps({'latin_historical_source_full_candidate':report},sort_keys=True))


if __name__=='__main__':main()
