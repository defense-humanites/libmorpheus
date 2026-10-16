#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Qualify the labiovelar short-suffix repair natively; lexical evidence stays private."""
import argparse
from collections import Counter
import importlib.util
import json
import os
from pathlib import Path

spec=importlib.util.spec_from_file_location('prefix',Path(__file__).with_name('qualify-latin-prefix-alternates.py'))
prefix=importlib.util.module_from_spec(spec);spec.loader.exec_module(prefix)
spec=importlib.util.spec_from_file_location('repair',Path(__file__).with_name('repair-latin-velar-short-suffix.py'))
repair=importlib.util.module_from_spec(spec);spec.loader.exec_module(repair)
primary=prefix.primary;changed=prefix.changed;review=prefix.review;native=prefix.native;supines=prefix.supines
EXPECTED_COUNTS={'repaired_records':16,'repaired_lemma_blocks':8}


def replaced_records(before,after):
    """Exactly paired perfstem/pp4 replacements under the same lemma; no other change."""
    old=review.probe.definitions(before);new=review.probe.definitions(after)
    removed=Counter(old-new);added=Counter(new-old)
    parse=lambda counter:[(lemma,line.split()[0][4:],line.split()[1],tuple(line.split()[2:]))
                          for (lemma,line),count in sorted(counter.items()) for _ in range(count)]
    gone,came=parse(removed),parse(added)
    if len(gone)!=len(came) or Counter((l,k) for l,_,k,_ in gone)!=Counter((l,k) for l,_,k,_ in came):
        raise ValueError('labiovelar repair replacement pairs differ')
    if any(k not in (b'perfstem',b'pp4') or f for _,_,k,f in gone+came):
        raise ValueError('labiovelar repair touches an unexpected record class')
    for lemma,stem,kind,_ in came:
        tail=b'x' if kind==b'perfstem' else b'ct'
        if not stem.endswith(tail) or (lemma,stem[:-len(tail)]+b'q'+tail,kind,())not in gone and (lemma,stem[:-len(tail)]+b'g'+tail,kind,())not in gone:
            raise ValueError('labiovelar repair stem does not pair with its defective record')
    return gone,came


def prepare(args):
    paths={n:getattr(args,n) for n in ('report','candidate','headers','tei')}
    receipts={'report':primary.REPORT_SHA,'candidate':changed.reproduction.candidate.CANDIDATE_SHA,
              'headers':review.RECEIPTS['headers'],'tei':review.RECEIPTS['tei']}
    if args.forms is not None:paths['forms']=args.forms;receipts['forms']=prefix.FORMS_SHA
    if any(native.digest(p)!=receipts[n] for n,p in paths.items()):
        raise ValueError('labiovelar repair input receipt differs')
    report=json.loads(args.report.read_bytes())
    if report['changed_definition_source_review']['changed_definition_lemmas']!=59:
        raise ValueError('labiovelar repair report scope differs')
    target=changed.loss.private_target(args.output,[*paths.values(),args.native,args.library,args.baseline,args.tools])
    target.mkdir(mode=0o700)
    baseline_indexes={n:native.digest(args.baseline/'Latin/steminds'/n) for n in changed.reproduction.candidate.INDEXES}
    indexes={n:native.digest(args.native/'Latin/steminds'/n) for n in baseline_indexes}
    if indexes!=changed.reproduction.candidate.INDEXES:
        raise ValueError('labiovelar repair original native receipt differs')
    recovery=repair.prepare(args.candidate,args.headers,args.tei,target/'after.stems')
    if any(recovery['counts'].get(k)!=v for k,v in EXPECTED_COUNTS.items()):
        raise ValueError('labiovelar repair counts differ from the qualified trial')
    before=args.candidate.read_bytes();after=(target/'after.stems').read_bytes()
    gone,came=replaced_records(before,after)
    trial_indexes=native.build_trial(args.baseline,target/'after.stems',args.tools,target/'trial')
    if any(trial_indexes[n]!=indexes[n] for n in ('nomind','nomind.lindex')):
        raise ValueError('labiovelar repair changes nominal indexes')
    cells,classes=prefix.family_cells(came)
    defective_cells,_=prefix.family_cells(gone)
    forms=sorted({c[0] for c in cells});defective_forms=sorted({c[0] for c in defective_cells})
    native.write_private(target/'forms',b''.join(f+b'\n' for f in forms+defective_forms))
    first=review.sibling('repair-latin-first-conjugation')
    rows,_,_=first.source_rows(args.headers,args.tei)
    headers={review.probe.digest(json.dumps(r,sort_keys=True).encode()):r for r in rows}
    changed_lemmas={lemma for lemma,_,_,_ in came}
    dossier=[(i,c,review.source_key(headers[c['source_header_sha256']]))
             for i,c in enumerate(report['changed_definition_source_review']['anonymous_cases'])
             if 'source_header_sha256' in c and review.source_key(headers[c['source_header_sha256']]) in changed_lemmas]
    readers={};sixteen=Counter();restored=Counter();private=[];added_lemmas=Counter()
    try:
        for label,root in (('before',args.native),('after',target/'trial'),('baseline',args.baseline)):
            readers[label]=supines.direct.StrictRows(args.library,root)
        before_counts,covered_before=prefix.check_cells(readers['before'],cells)
        after_counts,covered_after=prefix.check_cells(readers['after'],cells)
        defective_before,_=prefix.check_cells(readers['before'],defective_cells)
        if covered_before-covered_after:raise ValueError('labiovelar repair loses a covered record')
        for form in forms+defective_forms:
            old=Counter(map(supines.direct.route,readers['before'].analyses(form,require_untruncated=True)))
            new=Counter(map(supines.direct.route,readers['after'].analyses(form,require_untruncated=True)))
            hist=Counter(map(supines.direct.route,readers['baseline'].analyses(form,require_untruncated=True)))
            sixteen['retained_rows']+=sum((old&new).values());sixteen['removed_rows']+=sum((old-new).values())
            sixteen['added_rows']+=sum((new-old).values());sixteen['changed_forms']+=bool(old-new or new-old)
            gained=new-old
            restored['historical_sixteen_field_readings_restored']+=sum(((hist-old)&gained).values())
            restored['additions_beyond_historical_baseline']+=sum((gained-(hist-old)).values())
            restored['forms_newly_recognized']+=bool(new and not old)
            restored['forms_no_longer_recognized']+=bool(old and not new)
            for key,count in gained.items():added_lemmas[key[1]]+=count
            private.append({'form':form.decode(),'before':sum(old.values()),'after':sum(new.values()),
                            'historical':sum(hist.values()),'restored':sum(((hist-old)&gained).values())})
        per_case=[{'case_position':i,'source_header_sha256':c['source_header_sha256'],
                   'historical_lost_readings':sum(c['readings'].values()),
                   'family_readings_added_under_lemma':added_lemmas.get(l,0)} for i,c,l in dossier]
        control=supines.direct.audit.audit(target/'forms',readers['after'],readers['after'],target/'control.jsonl',require_identical=True)
        delta=supines.direct.audit.audit(target/'forms',readers['before'],readers['after'],target/'delta.jsonl')
        global_report=None
        if args.forms is not None:
            global_control=supines.direct.audit.audit(args.forms,readers['after'],readers['after'],target/'global-control.jsonl',require_identical=True)
            global_delta=supines.direct.audit.audit(args.forms,readers['before'],readers['after'],target/'global-delta.jsonl')
            if (global_delta['counts']['distinct_forms']!=1033579
                    or global_delta['analysis_rows']['curated']!=2100530
                    or global_delta['counts'].get('recognized_curated__absent_rebuilt',0)):
                raise ValueError('labiovelar repair global scope differs or loses recognized forms')
            global_report={'control':global_control,'comparison':global_delta}
    finally:
        for reader in readers.values():reader.close()
    native.write_private(target/'family-evidence.jsonl',b''.join((json.dumps(r,sort_keys=True)+'\n').encode() for r in private))
    if any(native.digest(p)!=receipts[n] for n,p in paths.items()) or any(
            native.digest(args.native/'Latin/steminds'/n)!=indexes[n] or
            native.digest(args.baseline/'Latin/steminds'/n)!=baseline_indexes[n] for n in indexes):
        raise ValueError('labiovelar repair qualification changed an input')
    return {'schema':1,
            'scope':'labiovelar -quo/-guo headwords with literal xi, ctum, 3 parts; exact defective perfstem/pp4 records replaced in a separate trial; family cells and optional LISTALL diagnostic; no production promotion',
            'native_scope':'engine-generated perfect and supine cells of each repaired record under its exact lemma, plus the cells of the removed defective stems; historical restoration measured against the controlled rebuilt baseline on those forms only',
            'historical_defect':'latvb conj3 trim removes only the final u of a qu/gu radical before appending the written xi/ctum suffix',
            'recovery':recovery,'replaced_record_classes':classes,'input_sha256':receipts,
            'trial_source_sha256':native.digest(target/'after.stems'),
            'original_indexes_sha256':indexes,'trial_indexes_sha256':trial_indexes,
            'native_family_before':before_counts,'native_family_after':after_counts,
            'defective_stem_cells_before':defective_before,
            'records_without_covered_cell_after':len(came)-len(covered_after),
            'distinct_family_forms':len(forms),'distinct_defective_forms':len(defective_forms),
            'family_sixteen_field_multisets':dict(sixteen),'historical_restoration_on_family_forms':dict(restored),
            'changed_definition_loss_cases':per_case,'family_comparison':delta,'identical_root_control':control,
            'global_listall':global_report,'private_family_evidence_sha256':native.digest(target/'family-evidence.jsonl'),
            'original_inputs_unchanged':True}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('report','candidate','headers','tei','native','library','baseline','tools','output'):
        p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--forms',type=Path)
    previous=os.umask(0o077)
    try:result=prepare(p.parse_args())
    finally:os.umask(previous)
    print(json.dumps({'latin_velar_short_suffix':result},sort_keys=True))


if __name__=='__main__':main()
