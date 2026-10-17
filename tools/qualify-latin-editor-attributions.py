#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Qualify the editor-attribution replay natively; lexical evidence stays private."""
import argparse
from collections import Counter
import importlib.util
import json
import os
from pathlib import Path
import re

spec=importlib.util.spec_from_file_location('prefix',Path(__file__).with_name('qualify-latin-prefix-alternates.py'))
prefix=importlib.util.module_from_spec(spec);spec.loader.exec_module(prefix)
spec=importlib.util.spec_from_file_location('recover',Path(__file__).with_name('recover-latin-editor-attributions.py'))
recover=importlib.util.module_from_spec(spec);spec.loader.exec_module(recover)
primary=prefix.primary;changed=prefix.changed;review=prefix.review;native=prefix.native;supines=prefix.supines
EXPECTED_COUNTS={'replaced_lemma_blocks':12,'reclassed_intact_records':8}


def replaced_records(before,after):
    """Removed records are capitalized attribution stems or reclassed presents; added ones are lowercase."""
    old=review.probe.definitions(before);new=review.probe.definitions(after)
    parse=lambda counter:[(lemma,line.split()[0][4:],line.split()[1],tuple(line.split()[2:]))
                          for (lemma,line),count in sorted(counter.items()) for _ in range(count)]
    gone,came=parse(Counter(old-new)),parse(Counter(new-old))
    if any(re.search(rb'[A-Z]',stem) for _,stem,_,_ in came):
        raise ValueError('editor attribution replay adds a capitalized stem')
    junk=[r for r in gone if re.search(rb'[A-Z]',r[1])]
    reclassed=[r for r in gone if not re.search(rb'[A-Z]',r[1])]
    if any(kind!=b'perfstem' for _,_,kind,_ in junk):
        raise ValueError('attribution stems are not all historical perfect records')
    added_stems={(lemma,stem) for lemma,stem,_,_ in came}
    if any((lemma,stem) not in added_stems for lemma,stem,_,_ in reclassed):
        raise ValueError('a reclassed present lost its stem')
    if {lemma for lemma,_,_,_ in came}-{lemma for lemma,_,_,_ in gone}:
        raise ValueError('editor attribution replay touches a block without an attribution stem')
    return gone,came,junk,reclassed


def prepare(args):
    paths={n:getattr(args,n) for n in ('report','candidate','headers','tei')}
    receipts={'report':primary.REPORT_SHA,'candidate':changed.reproduction.candidate.CANDIDATE_SHA,
              'headers':review.RECEIPTS['headers'],'tei':review.RECEIPTS['tei']}
    if args.forms is not None:paths['forms']=args.forms;receipts['forms']=prefix.FORMS_SHA
    if any(native.digest(p)!=receipts[n] for n,p in paths.items()):
        raise ValueError('editor attribution input receipt differs')
    report=json.loads(args.report.read_bytes())
    if report['changed_definition_source_review']['changed_definition_lemmas']!=59:
        raise ValueError('editor attribution report scope differs')
    target=changed.loss.private_target(args.output,[*paths.values(),args.native,args.library,args.baseline,args.tools,args.filters])
    target.mkdir(mode=0o700)
    baseline_indexes={n:native.digest(args.baseline/'Latin/steminds'/n) for n in changed.reproduction.candidate.INDEXES}
    indexes={n:native.digest(args.native/'Latin/steminds'/n) for n in baseline_indexes}
    if indexes!=changed.reproduction.candidate.INDEXES:
        raise ValueError('editor attribution original native receipt differs')
    recovery=recover.prepare(args.candidate,args.headers,args.tei,args.filters,target/'recovery')
    if any(recovery['counts'].get(k)!=v for k,v in EXPECTED_COUNTS.items()):
        raise ValueError('editor attribution counts differ from the qualified trial')
    stems=target/'recovery/after.stems'
    before=args.candidate.read_bytes();after=stems.read_bytes()
    gone,came,junk,reclassed=replaced_records(before,after)
    trial_indexes=native.build_trial(args.baseline,stems,args.tools,target/'trial')
    if any(trial_indexes[n]!=indexes[n] for n in ('nomind','nomind.lindex')):
        raise ValueError('editor attribution replay changes nominal indexes')
    cells,classes=prefix.family_cells(came)
    reclassed_cells,_=prefix.family_cells(reclassed)
    forms=sorted({c[0] for c in cells});reclassed_forms=sorted({c[0] for c in reclassed_cells})
    all_forms=sorted(set(forms)|set(reclassed_forms))
    native.write_private(target/'forms',b''.join(f+b'\n' for f in all_forms))
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
        if covered_before-covered_after:raise ValueError('editor attribution replay loses a covered added record')
        reclassed_before,_=prefix.check_cells(readers['before'],reclassed_cells)
        reclassed_after,_=prefix.check_cells(readers['after'],reclassed_cells)
        if reclassed_after.get('covered_cells',0)<reclassed_before.get('covered_cells',0):
            raise ValueError('reclassing a present loses a covered cell')
        for form in all_forms:
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
        if restored['forms_no_longer_recognized']:
            raise ValueError('editor attribution replay loses a recognized family form')
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
                raise ValueError('editor attribution global scope differs or loses recognized forms')
            global_report={'control':global_control,'comparison':global_delta,
                           'removed_reading_displacement':prefix.displacement_review(target/'global-delta.jsonl',readers['after'])}
    finally:
        for reader in readers.values():reader.close()
    native.write_private(target/'family-evidence.jsonl',b''.join((json.dumps(r,sort_keys=True)+'\n').encode() for r in private))
    if any(native.digest(p)!=receipts[n] for n,p in paths.items()) or any(
            native.digest(args.native/'Latin/steminds'/n)!=indexes[n] or
            native.digest(args.baseline/'Latin/steminds'/n)!=baseline_indexes[n] for n in indexes):
        raise ValueError('editor attribution qualification changed an input')
    return {'schema':1,
            'scope':'headers whose capitalized <itype> attribution precedes the written parts, replayed through the unchanged historical filters without that field; separate trial; family cells and optional LISTALL diagnostic; no production promotion',
            'native_scope':'engine-generated cells of each added record and of each reclassed present under its exact lemma; historical restoration measured against the controlled rebuilt baseline on those forms only',
            'historical_defect':'latvb reads the first <itype> after the headword as the perfect; an editor name or citation tagged <itype> is concatenated to the stem and the written parts are ignored',
            'recovery':recovery,'replaced_record_classes':classes,
            'removed_attribution_records':len(junk),'reclassed_present_records':len(reclassed),
            'input_sha256':receipts,'trial_source_sha256':native.digest(stems),
            'original_indexes_sha256':indexes,'trial_indexes_sha256':trial_indexes,
            'native_family_before':before_counts,'native_family_after':after_counts,
            'reclassed_present_cells_before':reclassed_before,'reclassed_present_cells_after':reclassed_after,
            'records_without_covered_cell_after':len(came)-len(covered_after),
            'distinct_family_forms':len(all_forms),
            'family_sixteen_field_multisets':dict(sixteen),'historical_restoration_on_family_forms':dict(restored),
            'changed_definition_loss_cases':per_case,'family_comparison':delta,'identical_root_control':control,
            'global_listall':global_report,'private_family_evidence_sha256':native.digest(target/'family-evidence.jsonl'),
            'original_inputs_unchanged':True}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('report','candidate','headers','tei','native','library','baseline','tools','filters','output'):
        p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--forms',type=Path)
    previous=os.umask(0o077)
    try:result=prepare(p.parse_args())
    finally:os.umask(previous)
    print(json.dumps({'latin_editor_attributions':result},sort_keys=True))


if __name__=='__main__':main()
