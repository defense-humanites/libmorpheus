#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Qualify the combined Latin candidate natively; lexical evidence stays private."""
import argparse
from collections import Counter
import importlib.util
import json
import os
from pathlib import Path
import re

spec=importlib.util.spec_from_file_location('prefix',Path(__file__).with_name('qualify-latin-prefix-alternates.py'))
prefix=importlib.util.module_from_spec(spec);spec.loader.exec_module(prefix)
spec=importlib.util.spec_from_file_location('combine',Path(__file__).with_name('reconstruct-latin-combined-candidate.py'))
combine=importlib.util.module_from_spec(spec);spec.loader.exec_module(combine)
primary=prefix.primary;changed=prefix.changed;review=prefix.review;native=prefix.native;supines=prefix.supines
COMBINED_SHA='f719a4e118195bc0d7696c30121a11495fac21cdfadb70ad95dd378443812463'
STAGE_SHA={
           'editor-attributions': '46e06edb3f4401c1ce0f921f53c11d602ff0fa44a8222e982e13d33dec992dde',
           'itype-tag-leak': 'd7bfa6ee9ee56252d62c82b31875cb9ec844ac8f0e0e8333751211fd6c142487',
           'velar-short-suffix': 'c99b856d4d02c99fe71be3ce3bb63f9f46d03dedd8b482eac9f448ea7209c3fd',
           'prefix-alternates': '62ce8fac2f576459f92fd6f5649f0031d98a21b7ddb4ea827ccd80155d56478b',
           'backlinked-presents': 'ff777b66170685f5d240f805a083976fe16841d8fccfbfbcb9ef366653b91626',
           'quoted-presents': 'f719a4e118195bc0d7696c30121a11495fac21cdfadb70ad95dd378443812463',
           'jicio-parts': 'f719a4e118195bc0d7696c30121a11495fac21cdfadb70ad95dd378443812463'
}


def record_delta(before,after):
    old=review.probe.definitions(before);new=review.probe.definitions(after)
    parse=lambda counter:[(lemma,line.split()[0][4:],line.split()[1],tuple(line.split()[2:]))
                          for (lemma,line),count in sorted(counter.items()) for _ in range(count)]
    return parse(Counter(old-new)),parse(Counter(new-old))


def classify_removed(gone):
    classes=Counter()
    for lemma,stem,kind,flags in gone:
        if re.search(rb'[A-Z]',stem):classes['attribution_stem']+=1
        elif stem.endswith(b'/ityp'):classes['leaked_tag_stem']+=1
        elif kind==b'conj1' and not flags:classes['reclassed_conj1_present']+=1
        else:classes['replaced_'+kind.decode()]+=1
    return dict(classes)


def prepare(args):
    paths={n:getattr(args,n) for n in ('report','candidate','headers','tei')}
    receipts={'report':primary.REPORT_SHA,'candidate':changed.reproduction.candidate.CANDIDATE_SHA,
              'headers':review.RECEIPTS['headers'],'tei':review.RECEIPTS['tei']}
    if args.forms is not None:paths['forms']=args.forms;receipts['forms']=prefix.FORMS_SHA
    if any(native.digest(p)!=receipts[n] for n,p in paths.items()):
        raise ValueError('combined candidate input receipt differs')
    report=json.loads(args.report.read_bytes())
    if report['changed_definition_source_review']['changed_definition_lemmas']!=59:
        raise ValueError('combined candidate report scope differs')
    target=changed.loss.private_target(args.output,[*paths.values(),args.native,args.library,args.baseline,args.tools,args.filters])
    target.mkdir(mode=0o700)
    baseline_indexes={n:native.digest(args.baseline/'Latin/steminds'/n) for n in changed.reproduction.candidate.INDEXES}
    indexes={n:native.digest(args.native/'Latin/steminds'/n) for n in baseline_indexes}
    if indexes!=changed.reproduction.candidate.INDEXES:
        raise ValueError('combined candidate original native receipt differs')
    combination=combine.prepare(args.candidate,args.headers,args.tei,args.filters,target/'combination')
    if combination['output_sha256']!=COMBINED_SHA or any(
            s['output_sha256']!=STAGE_SHA[s['stage']] for s in combination['stages']):
        raise ValueError('combined candidate stages differ from the qualified sequence')
    stems=target/'combination/combined.stems'
    before=args.candidate.read_bytes();after=stems.read_bytes()
    gone,came=record_delta(before,after)
    trial_indexes=native.build_trial(args.baseline,stems,args.tools,target/'trial')
    if any(trial_indexes[n]!=indexes[n] for n in ('nomind','nomind.lindex')):
        raise ValueError('combined candidate changes nominal indexes')
    cells,classes=prefix.family_cells(came)
    forms=sorted({c[0] for c in cells})
    native.write_private(target/'forms',b''.join(f+b'\n' for f in forms))
    first=review.sibling('repair-latin-first-conjugation')
    rows,_,_=first.source_rows(args.headers,args.tei)
    headers={review.probe.digest(json.dumps(r,sort_keys=True).encode()):r for r in rows}
    changed_lemmas={lemma for lemma,_,_,_ in came}|{lemma for lemma,_,_,_ in gone}
    dossier=[(i,c,review.source_key(headers[c['source_header_sha256']]))
             for i,c in enumerate(report['changed_definition_source_review']['anonymous_cases'])
             if 'source_header_sha256' in c and review.source_key(headers[c['source_header_sha256']]) in changed_lemmas]
    readers={};sixteen=Counter();restored=Counter();private=[];added_lemmas=Counter()
    try:
        for label,root in (('before',args.native),('after',target/'trial'),('baseline',args.baseline)):
            readers[label]=supines.direct.StrictRows(args.library,root)
        before_counts,covered_before=prefix.check_cells(readers['before'],cells)
        after_counts,covered_after=prefix.check_cells(readers['after'],cells)
        if covered_before-covered_after:raise ValueError('combined candidate loses a covered added record')
        for form in forms:
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
                raise ValueError('combined candidate global scope differs or loses recognized forms')
            displacement=prefix.displacement_review(target/'global-delta.jsonl',readers['after'])
            # The controlled rebuilt baseline against the original and the combined
            # candidate: readings the combination restores are those removed by the
            # original candidate and no longer removed by the combined one.
            baseline_original=supines.direct.audit.audit(args.forms,readers['baseline'],readers['before'],target/'baseline-original.jsonl')
            baseline_combined=supines.direct.audit.audit(args.forms,readers['baseline'],readers['after'],target/'baseline-combined.jsonl')
            global_report={'control':global_control,'comparison':global_delta,'removed_reading_displacement':displacement,
                           'controlled_baseline_to_original':{k:baseline_original[k] for k in ('counts','analysis_rows','global_eleven_field_multisets','changed_analysis_counts','lost_forms_diagnostic')},
                           'controlled_baseline_to_combined':{k:baseline_combined[k] for k in ('counts','analysis_rows','global_eleven_field_multisets','changed_analysis_counts','lost_forms_diagnostic')},
                           'historical_readings_no_longer_removed':baseline_original['global_eleven_field_multisets']['removed_rows']-baseline_combined['global_eleven_field_multisets']['removed_rows'],
                           'completely_lost_forms_no_longer_lost':baseline_original['lost_forms_diagnostic']['forms']-baseline_combined['lost_forms_diagnostic']['forms']}
    finally:
        for reader in readers.values():reader.close()
    native.write_private(target/'family-evidence.jsonl',b''.join((json.dumps(r,sort_keys=True)+'\n').encode() for r in private))
    if any(native.digest(p)!=receipts[n] for n,p in paths.items()) or any(
            native.digest(args.native/'Latin/steminds'/n)!=indexes[n] or
            native.digest(args.baseline/'Latin/steminds'/n)!=baseline_indexes[n] for n in indexes):
        raise ValueError('combined candidate qualification changed an input')
    return {'schema':1,
            'scope':'the six separately qualified trials and the earlier -jicio repair combined in sequence on one private candidate; family cells of every added record, LISTALL comparison against the original candidate and against the controlled rebuilt baseline; no production promotion',
            'native_scope':'engine-generated cells of each added record under its exact lemma and class; historical restoration on those forms and, with LISTALL, globally against the controlled rebuilt baseline; no independent form attestation',
            'combination':combination,'added_record_classes':classes,'removed_record_classes':classify_removed(gone),
            'added_records':len(came),'removed_records':len(gone),'input_sha256':receipts,
            'combined_source_sha256':native.digest(stems),
            'original_indexes_sha256':indexes,'trial_indexes_sha256':trial_indexes,
            'native_family_before':before_counts,'native_family_after':after_counts,
            'records_without_covered_cell_after':len(came)-len(covered_after),
            'distinct_family_forms':len(forms),'family_sixteen_field_multisets':dict(sixteen),
            'historical_restoration_on_family_forms':dict(restored),
            'changed_definition_loss_cases':per_case,'family_comparison':delta,'identical_root_control':control,
            'global_listall':global_report,'private_family_evidence_sha256':native.digest(target/'family-evidence.jsonl'),
            'original_inputs_unchanged':True}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('report','candidate','headers','tei','native','library','baseline','tools','filters','output'):
        p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--forms',type=Path)
    args=p.parse_args()
    previous=os.umask(0o077)
    try:result=prepare(args)
    finally:os.umask(previous)
    print(json.dumps({'latin_combined_candidate':result},sort_keys=True))


if __name__=='__main__':main()
