#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Qualify the abbreviated prefix alternate trial natively; lexical evidence stays private."""
import argparse
from collections import Counter
import importlib.util
import json
import os
from pathlib import Path
import re

spec=importlib.util.spec_from_file_location('primary',Path(__file__).with_name('qualify-latin-loss-primary-source.py'))
primary=importlib.util.module_from_spec(spec);spec.loader.exec_module(primary)
spec=importlib.util.spec_from_file_location('recover',Path(__file__).with_name('recover-latin-prefix-alternates.py'))
recover=importlib.util.module_from_spec(spec);spec.loader.exec_module(recover)
changed=primary.changed;review=primary.review;native=primary.native;supines=primary.supines
EXPECTED_COUNTS={'added_records':581,'changed_lemma_blocks':366,'accepted_alternate':1176}
FORMS_SHA='1df0800fb1443b2cfd64d787c257319aa72b69f453c3c37ec60c359c70cebd93'
# Engine present and perfect endings by stem class; the pp4 cells come from the
# historical supine table already used by the earlier source-family checks.
ACTIVE={b'are_vb':('o','as','at','amus','atis','ant'),b'conj1':('o','as','at','amus','atis','ant'),
        b'conj2':('eo','es','et','emus','etis','ent'),b'conj3':('o','is','it','imus','itis','unt'),
        b'conj3_io':('io','is','it','imus','itis','iunt'),b'conj4':('io','is','it','imus','itis','iunt'),
        b'ire_vb':('io','is','it','imus','itis','iunt'),b'perfstem':('i','isti','it','imus','istis','erunt')}
PASSIVE={b'are_vb':('or','aris','atur','amur','amini','antur'),b'conj1':('or','aris','atur','amur','amini','antur'),
         b'conj2':('eor','eris','etur','emur','emini','entur'),b'conj3':('or','eris','itur','imur','imini','untur'),
         b'conj3_io':('ior','eris','itur','imur','imini','iuntur'),b'conj4':('ior','iris','itur','imur','imini','iuntur'),
         b'ire_vb':('ior','iris','itur','imur','imini','iuntur')}


def added_records(before,after):
    """Records present after and absent before, keyed by lemma; exact lines."""
    old=review.probe.definitions(before);new=review.probe.definitions(after)
    if old-new:raise ValueError('prefix alternate trial removes a record')
    added=Counter(new-old)
    records=[]
    for (lemma,line),count in sorted(added.items()):
        tokens=line.split()
        if tokens[-1]!=b'orth' or count!=1:raise ValueError('prefix alternate addition shape differs')
        records.append((lemma,tokens[0][4:],tokens[1],tuple(tokens[2:-1])))
    return records


def family_cells(records):
    cells=[];classes=Counter()
    for lemma,stem,kind,flags in records:
        dep=b'dep' in flags
        if kind==b'pp4':
            classes['pp4']+=1
            endings=[(e,(2,0,1,g,c,t,m,v,0)) for e,t,m,v,g,c in supines.CELLS]
        elif kind in ACTIVE and (not dep or kind in PASSIVE):
            classes[kind.decode()+('_dep' if dep else '')]+=1
            suffixes=PASSIVE[kind] if dep else ACTIVE[kind]
            tense=5 if kind==b'perfstem' else 1
            endings=[(e,(2,(i%3)+1,1 if i<3 else 3,0,0,tense,4,2 if dep else 1,0)) for i,e in enumerate(suffixes)]
        else:
            classes['unsupported_'+kind.decode()]+=1;continue
        for ending,signature in endings:
            form=(stem+ending.encode()).translate(None,b'_^-')
            cells.append((form,signature,lemma,stem,kind))
    return cells,dict(classes)


# Latin enclitic retries of src/anal/checkstring.c LatinSuff; the analyzer tries
# them only while no direct analysis exists, so a new direct reading can
# displace a fallback reading on the same surface form.
ENCLITICS=(b'que',b'cumque',b'cunque',b'ne',b've',b'ue',b'libet',b'vis',b'piam',b'dem',b'dum',b'met')


def displacement_review(delta_path,after):
    """Explain removed readings as enclitic-retry fallbacks displaced by a direct analysis."""
    counts=Counter();by_enclitic=Counter()
    for line in delta_path.read_bytes().splitlines():
        row=json.loads(line)
        removed=Counter({tuple(v.encode() if isinstance(v,str) else v for v in r['signature']):r['multiplicity'] for r in row['removed']})
        if not removed:continue
        form=row['form'].encode('ascii');counts['forms_with_removed_readings']+=1
        counts['removed_readings']+=sum(removed.values())
        rows=after.analyses(form,require_untruncated=True)
        if any(r.preverb for r in rows) or not rows:
            counts['removed_readings_on_forms_without_direct_after_analysis']+=sum(removed.values());continue
        explained=False
        for enclitic in sorted(ENCLITICS,key=len,reverse=True):
            if not form.endswith(enclitic) or len(form)<=len(enclitic):continue
            stripped=Counter(map(supines.direct.loss.signature,after.analyses(form[:-len(enclitic)],require_untruncated=True)))
            if not removed-stripped:
                by_enclitic[enclitic.decode()]+=sum(removed.values());explained=True;break
        counts['removed_readings_reproduced_on_enclitic_stripped_input_after' if explained else 'removed_readings_unexplained']+=sum(removed.values())
    return {'scope':'removed eleven-field readings on forms recognized before and after; enclitic retry displaced by a new direct analysis; no lexical value published',
            'counts':dict(sorted(counts.items())),'reproduced_by_enclitic':dict(sorted(by_enclitic.items()))}


def check_cells(reader,cells):
    counts=Counter();covered=set()
    for form,signature,lemma,stem,kind in cells:
        rows=reader.analyses(form,require_untruncated=True)
        if any(r.lemma==lemma and not r.preverb and supines.cell_signature(r)==signature for r in rows):
            counts['covered_cells']+=1;covered.add((lemma,stem,kind))
        counts['expected_cells']+=1
    return dict(counts),covered


def prepare(args):
    paths={n:getattr(args,n) for n in ('report','candidate','headers','tei')}
    receipts={'report':primary.REPORT_SHA,'candidate':changed.reproduction.candidate.CANDIDATE_SHA,
              'headers':review.RECEIPTS['headers'],'tei':review.RECEIPTS['tei'],
              'preverb_table':native.digest(recover.PREVERB_TABLE)}
    if args.forms is not None:paths['forms']=args.forms;receipts['forms']=FORMS_SHA
    if any(native.digest(p)!=receipts[n] for n,p in paths.items()):
        raise ValueError('prefix alternate input receipt differs')
    report=json.loads(args.report.read_bytes())
    if report['changed_definition_source_review']['changed_definition_lemmas']!=59:
        raise ValueError('prefix alternate report scope differs')
    target=changed.loss.private_target(args.output,[*paths.values(),args.native,args.library,args.baseline,args.tools])
    target.mkdir(mode=0o700)
    baseline_indexes={n:native.digest(args.baseline/'Latin/steminds'/n) for n in changed.reproduction.candidate.INDEXES}
    indexes={n:native.digest(args.native/'Latin/steminds'/n) for n in baseline_indexes}
    if indexes!=changed.reproduction.candidate.INDEXES:
        raise ValueError('prefix alternate original native receipt differs')
    recovery=recover.prepare(args.candidate,args.headers,args.tei,target/'after.stems')
    if any(recovery['counts'].get(k)!=v for k,v in EXPECTED_COUNTS.items()):
        raise ValueError('prefix alternate recovery counts differ from the qualified trial')
    before=args.candidate.read_bytes();after=(target/'after.stems').read_bytes()
    records=added_records(before,after)
    if len(records)!=EXPECTED_COUNTS['added_records']:raise ValueError('prefix alternate record inventory differs')
    trial_indexes=native.build_trial(args.baseline,target/'after.stems',args.tools,target/'trial')
    if any(trial_indexes[n]!=indexes[n] for n in ('nomind','nomind.lindex')):
        raise ValueError('prefix alternate trial changes nominal indexes')
    cells,classes=family_cells(records)
    forms=sorted({c[0] for c in cells})
    native.write_private(target/'forms',b''.join(f+b'\n' for f in forms))
    # Loss-dossier lemmas whose block changes: exact source-header receipts only.
    first=review.sibling('repair-latin-first-conjugation')
    rows,_,_=first.source_rows(args.headers,args.tei)
    headers={review.probe.digest(json.dumps(r,sort_keys=True).encode()):r for r in rows}
    changed_lemmas={lemma for lemma,_,_,_ in records}
    dossier=[]
    for position,case in enumerate(report['changed_definition_source_review']['anonymous_cases']):
        if 'source_header_sha256' not in case:continue  # unjoined case: no source header
        row=headers.get(case['source_header_sha256'])
        if row is None:raise ValueError('prefix alternate header join missing')
        lemma=review.source_key(row)
        if lemma in changed_lemmas:
            dossier.append((position,case,lemma))
    readers={};sixteen=Counter();restored=Counter();per_case=[];private=[]
    try:
        for label,root in (('before',args.native),('after',target/'trial'),('baseline',args.baseline)):
            readers[label]=supines.direct.StrictRows(args.library,root)
        before_counts,covered_before=check_cells(readers['before'],cells)
        after_counts,covered_after=check_cells(readers['after'],cells)
        if covered_before-covered_after:raise ValueError('prefix alternate family loses a covered record')
        added_lemmas=Counter()
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
            for key,count in gained.items():added_lemmas[key[1]]+=count
            private.append({'form':form.decode(),'before':sum(old.values()),'after':sum(new.values()),
                            'historical':sum(hist.values()),'restored':sum(((hist-old)&gained).values())})
        if sixteen['removed_rows']:raise ValueError('prefix alternate family removes native readings')
        for position,case,lemma in dossier:
            per_case.append({'case_position':position,'source_header_sha256':case['source_header_sha256'],
                             'historical_lost_readings':sum(case['readings'].values()),
                             'family_readings_added_under_lemma':added_lemmas.get(lemma,0)})
        control=supines.direct.audit.audit(target/'forms',readers['after'],readers['after'],target/'control.jsonl',require_identical=True)
        delta=supines.direct.audit.audit(target/'forms',readers['before'],readers['after'],target/'delta.jsonl')
        global_report=None
        if args.forms is not None:
            global_control=supines.direct.audit.audit(args.forms,readers['after'],readers['after'],target/'global-control.jsonl',require_identical=True)
            global_delta=supines.direct.audit.audit(args.forms,readers['before'],readers['after'],target/'global-delta.jsonl')
            if (global_delta['counts']['distinct_forms']!=1033579
                    or global_delta['analysis_rows']['curated']!=2100530
                    or global_delta['counts'].get('recognized_curated__absent_rebuilt',0)):
                raise ValueError('prefix alternate global scope differs or loses recognized forms')
            global_report={'control':global_control,'comparison':global_delta,
                           'removed_reading_displacement':displacement_review(target/'global-delta.jsonl',readers['after'])}
    finally:
        for reader in readers.values():reader.close()
    evidence=b''.join((json.dumps(r,sort_keys=True)+'\n').encode() for r in private)
    native.write_private(target/'family-evidence.jsonl',evidence)
    if any(native.digest(p)!=receipts[n] for n,p in paths.items()) or any(
            native.digest(args.native/'Latin/steminds'/n)!=indexes[n] or
            native.digest(args.baseline/'Latin/steminds'/n)!=baseline_indexes[n] for n in indexes):
        raise ValueError('prefix alternate qualification changed an input')
    return {'schema':1,
            'scope':'abbreviated prefix alternates outside the four lexer-handled literals, staged over the full source candidate; family cells and optional LISTALL diagnostic; no production promotion',
            'native_scope':'engine-generated present, perfect and supine cells of each added record under its exact lemma and stem; historical restoration measured against the controlled rebuilt baseline on those forms only; no independent form attestation',
            'lexer_limit':'latvb.l set_orth() expands only adf-, adl-, adn-, ads- and discards other abbreviated alternates',
            'recovery':recovery,'added_record_classes':classes,'input_sha256':receipts,
            'trial_source_sha256':native.digest(target/'after.stems'),
            'original_indexes_sha256':indexes,'trial_indexes_sha256':trial_indexes,
            'native_family_before':before_counts,'native_family_after':after_counts,
            'records_without_covered_cell_after':len(records)-len(covered_after),
            'distinct_family_forms':len(forms),'family_sixteen_field_multisets':dict(sixteen),
            'historical_restoration_on_family_forms':dict(restored),
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
    print(json.dumps({'latin_prefix_alternates':result},sort_keys=True))


if __name__=='__main__':main()
