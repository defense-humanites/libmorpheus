#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check bounded primary source recipes in the changed-loss group, without edits."""
import argparse
from collections import Counter
import importlib.util
import json
import os
from pathlib import Path
import re

spec=importlib.util.spec_from_file_location('changed',Path(__file__).with_name('review-latin-changed-definition-losses.py'))
changed=importlib.util.module_from_spec(spec);spec.loader.exec_module(changed)
review=changed.review
native=changed.reproduction.native
supines=changed.reproduction.candidate.supines
REPORT_SHA='35adc3a8abd1b570c3eb957dbb1cbfafdc8545a333fd07f131fd4863383dddd7'


def source_recipe(row):
    """Literal quantities/boundaries; regular slots only, no inferred prefix."""
    head=row.get('headword','')
    if row.get('projection_error') is not None or not re.fullmatch(r'[A-Za-z_^]+(?:-[A-Za-z_^]+)?(?:#[1-9])?',head):
        return 'unclassified',Counter()
    fields=[(i,f['projection']) for i,f in enumerate(row['fields']) if f['name']=='itype']
    if not fields or any(b[0]!=a[0]+1 for a,b in zip(fields,fields[1:])):
        return 'unclassified',Counter()
    grammar=', '.join(v for _,v in fields)
    head=re.sub(r'#[1-9]$','',head)
    active={'a_re','a_re, 1','a_vi, 1','a_vi, a_tum, 1'}
    if grammar in active and head.endswith('o') and not head.endswith('or'):
        return 'regular_first_active_primary',Counter({((':de:'+head[:-1]).encode(),b'are_vb'):1})
    if grammar=='a_tus, 1' and head.endswith('or'):
        return 'regular_first_deponent_primary',Counter({((':de:'+head[:-2]).encode(),b'are_vb',b'dep'):1})
    compound=re.fullmatch(r'([A-Za-z_^]+)-([A-Za-z_^]+)o',head)
    parts=re.fullmatch(r'([A-Za-z_^]+i), ([A-Za-z_^]+um), 3',grammar)
    if compound and parts and not head.endswith(('io','i^o')):
        prefix,base=compound.groups();perfect,supine=parts.groups()
        plain=lambda value:value.translate(str.maketrans('','','_^'))
        # The perfect explicitly spells the complete present component.
        # Short suffixes and changing/suppletive components need other proofs.
        if (base[0] not in 'aeioux' and perfect[0]==supine[0]==base[0]
                and len(plain(base))>=3 and plain(perfect[:-1])==plain(base)
                and len(plain(supine[:-2]))>=len(plain(base))):
            boundary=prefix+'-'
            return 'explicit_compound_single_perfect_supine',Counter({
                ((':vs:'+boundary+base).encode(),b'conj3'):1,
                ((':vs:'+boundary+perfect[:-1]).encode(),b'perfstem'):1,
                ((':vs:'+boundary+supine[:-2]).encode(),b'pp4'):1})
    if grammar=='i_vi, 4' and head.endswith('i^o'):
        root=head[:-3]
        if root:
            return 'explicit_fourth_perfect_without_supine',Counter({
                ((':vs:'+root).encode(),b'conj4'):1,
                ((':vs:'+root+'i_v').encode(),b'perfstem'):1})
    return 'unclassified',Counter()


def inventory(report):
    section=report['changed_definition_source_review']
    if section['changed_definition_lemmas']!=59 or section['lost_readings']!=5547:
        raise ValueError('primary source report scope differs')
    selected=[c for c in section['anonymous_cases'] if c.get('source_partition')=='verbal'
              and c.get('isolated_matches_raw_candidate_multiset') is False]
    hashes=[c['source_header_sha256'] for c in selected]
    if len(selected)!=9 or len(set(hashes))!=9 or sum(sum(c['readings'].values()) for c in selected)!=559:
        raise ValueError('primary source selected scope differs')
    if any(not c['isolated_matches_full_diagnostic_multiset'] or not c['literal_headword_identity'] for c in selected):
        raise ValueError('primary source selected join differs')
    return selected


def primary(records):
    return Counter({tokens:n for tokens,n in records.items() if b'orth' not in tokens[1:]})


def family_cells(expected):
    cells=[]
    active={b'are_vb':('o','as','at','amus','atis','ant'),
            b'conj3':('o','is','it','imus','itis','unt'),
            b'conj4':('io','is','it','imus','itis','iunt'),
            b'perfstem':('i','isti','it','imus','istis','erunt')}
    passive=('or','aris','atur','amur','amini','antur')
    for tokens,count in expected.items():
        if count!=1:raise ValueError('primary source duplicate expectation')
        stem=tokens[0][4:];kind=tokens[1];dep=tokens[2:]==(b'dep',)
        if kind==b'pp4':
            if tokens[2:]:raise ValueError('primary source supine flags differ')
            endings=[(e,(2,0,1,g,c,t,m,v,0)) for e,t,m,v,g,c in supines.CELLS]
        elif kind in active and (not tokens[2:] or kind==b'are_vb' and dep):
            suffixes=passive if dep else active[kind]
            endings=[(e,(2,(i%3)+1,1 if i<3 else 3,0,0,5 if kind==b'perfstem' else 1,4,2 if dep else 1,0))
                     for i,e in enumerate(suffixes)]
        else:raise ValueError('primary source family class differs')
        for ending,signature in endings:
            form=(stem+ending.encode()).translate(None,b'_^-' )
            cells.append((form,signature,stem))
    return cells


def check_cells(reader,lemma,cells,reference):
    counts=Counter();evidence=[]
    for form,signature,stem in cells:
        rows=reader.analyses(form,require_untruncated=True)
        expected=Counter(supines.direct.route(r) for r in reference.analyses(form,require_untruncated=True)
                         if r.lemma==lemma and not r.preverb and supines.cell_signature(r)==signature)
        actual=Counter(supines.direct.route(r) for r in rows
                       if r.lemma==lemma and not r.preverb and supines.cell_signature(r)==signature)
        matches=sum((expected&actual).values())
        counts['expected_cells']+=1;counts['covered_cells']+=bool(matches)
        counts['reference_covered_cells']+=bool(expected)
        counts['missing_reference_readings']+=sum((expected-actual).values())
        counts['matching_direct_readings']+=matches
        evidence.append({'form':form.decode(),'signature':signature,'source_stem':stem.decode(),'matching_readings':matches})
    return dict(counts),evidence


def prepare(args):
    paths={'report':args.report,'candidate':args.candidate,'diagnostic':args.diagnostic,'headers':args.headers,'tei':args.tei}
    receipts={'report':REPORT_SHA,'candidate':changed.reproduction.candidate.CANDIDATE_SHA,
              'diagnostic':review.RECEIPTS['diagnostic'],'headers':review.RECEIPTS['headers'],'tei':review.RECEIPTS['tei']}
    if any(native.digest(p)!=receipts[n] for n,p in paths.items()):
        raise ValueError('primary source input receipt differs')
    report=json.loads(args.report.read_bytes())
    focused=inventory(report)
    focus_hashes={c['source_header_sha256'] for c in focused}
    indexes={n:native.digest(args.native/'Latin/steminds'/n) for n in changed.reproduction.candidate.INDEXES}
    if indexes!=changed.reproduction.candidate.INDEXES:raise ValueError('primary source native indexes differ')
    first=review.sibling('repair-latin-first-conjugation')
    rows,_,_=first.source_rows(args.headers,args.tei)
    headers={}
    for row in rows:
        key=review.probe.digest(json.dumps(row,sort_keys=True).encode())
        if key in headers:raise ValueError('primary source duplicate header')
        headers[key]=row
    selected=[]
    for case in report['changed_definition_source_review']['anonymous_cases']:
        if case.get('source_partition')!='verbal':continue
        row=headers.get(case['source_header_sha256'])
        if row is None:raise ValueError('primary source header missing')
        if source_recipe(row)[1]:selected.append(case)
    if len(selected)!=17 or not focus_hashes.issubset({c['source_header_sha256'] for c in selected}):
        raise ValueError('primary source extended scope differs')
    baseline_indexes={n:native.digest(args.baseline/'Latin/steminds'/n) for n in indexes}
    target=changed.loss.private_target(args.output,[*paths.values(),args.native,args.library,args.baseline,args.tools]);target.mkdir(mode=0o700)
    raw=review.probe.definitions(args.candidate.read_bytes());diagnostic=review.probe.definitions(args.diagnostic.read_bytes())
    source_payload=[]
    for case in selected:
        row=headers.get(case['source_header_sha256'])
        if row is None:raise ValueError('primary source header missing')
        lemma=review.source_key(row);branch,expected=source_recipe(row)
        if not expected:raise ValueError('primary source recipe unclassified')
        source_payload.append(supines.payload(lemma,expected))
    native.write_private(target/'source-primary.stems',b''.join(source_payload))
    reference_indexes=native.build_trial(args.baseline,target/'source-primary.stems',args.tools,target/'reference')
    if any(reference_indexes[n]!=indexes[n] for n in ('nomind','nomind.lindex')):
        raise ValueError('primary source reference changes nominal indexes')
    reader=supines.direct.StrictRows(args.library,args.native)
    reference=supines.direct.StrictRows(args.library,target/'reference')
    totals=Counter();groups=Counter();cases=[];private=[];forms=set();native_totals=Counter()
    try:
        for case in selected:
            key=case['source_header_sha256']
            if key not in headers:raise ValueError('primary source header missing')
            row=headers[key];lemma=review.source_key(row);branch,expected=source_recipe(row)
            if not expected:raise ValueError('primary source recipe unclassified')
            actual=changed.selected_tokens(raw,lemma);replayed=changed.selected_tokens(diagnostic,lemma)
            missing=expected-primary(actual);extra=primary(actual)-expected
            if missing or extra:raise ValueError('primary source candidate directives differ')
            cells=family_cells(expected);coverage,evidence=check_cells(reader,lemma,cells,reference)
            native_totals.update(coverage);forms.update(form for form,_,_ in cells)
            orth=sum(n for tokens,n in actual.items() if b'orth' in tokens[1:])
            totals['lemmas']+=1;totals['expected_primary_directives']+=sum(expected.values())
            totals['candidate_matching_primary_directives']+=sum((expected&primary(actual)).values())
            totals['diagnostic_matching_primary_directives']+=sum((expected&primary(replayed)).values())
            totals['additional_orth_directives_withheld']+=orth
            totals['lost_readings_in_selected_cases']+=sum(case['readings'].values())
            if key in focus_hashes:
                totals['verbal_replay_difference_cases']+=1
                totals['lost_readings_in_verbal_replay_differences']+=sum(case['readings'].values())
            groups[branch]+=1
            cases.append({'source_header_sha256':key,'recipe':branch,'in_nine_verbal_replay_differences':key in focus_hashes,
                'expected_primary_directives':sum(expected.values()),
                'candidate_matches_primary_recipe':not missing and not extra,
                'diagnostic_matches_primary_recipe':primary(replayed)==expected,
                'additional_orth_directives_withheld':orth,'native_family':coverage,'lost_readings':sum(case['readings'].values())})
            private.append({'source_header':row,'lemma':lemma.decode(),'recipe':branch,
                'expected':[{'tokens':[t.decode() for t in tokens],'multiplicity':n} for tokens,n in sorted(expected.items())],
                'candidate':[{'tokens':[t.decode() for t in tokens],'multiplicity':n} for tokens,n in sorted(actual.items())],
                'native_family':evidence})
        native.write_private(target/'forms',b''.join(form+b'\n' for form in sorted(forms)))
        control=supines.direct.audit.audit(target/'forms',reader,reader,target/'control.jsonl',require_identical=True)
    finally:
        reader.close();reference.close()
    if (native_totals['expected_cells']!=120 or native_totals['covered_cells']!=120 or
            native_totals['reference_covered_cells']!=120 or native_totals['missing_reference_readings']):
        raise ValueError('primary source native family coverage differs')
    payload=b''.join((json.dumps(row,sort_keys=True)+'\n').encode() for row in private)
    native.write_private(target/'source-primary-review.jsonl',payload)
    if any(native.digest(p)!=receipts[n] for n,p in paths.items()) or any(
            native.digest(args.native/'Latin/steminds'/n)!=indexes[n] or
            native.digest(args.baseline/'Latin/steminds'/n)!=baseline_indexes[n] for n in indexes):
        raise ValueError('primary source review changed an input')
    return {'schema':1,'scope':'bounded primary source review of changed-definition losses, including all nine verbal replay differences; no edit or recovery',
        'input_sha256':receipts,'native_indexes_sha256':indexes,'source_reference_indexes_sha256':reference_indexes,
        'source_reference_sha256':native.digest(target/'source-primary.stems'),'counts':dict(totals),
        'recipe_groups':[{'recipe':k,'lemmas':n} for k,n in sorted(groups.items())],
        'remaining_source_cases':{'unclassified_verbal':40,'nominal':1,'no_article_join':1},
        'native_family':dict(native_totals),'family_control':control,'anonymous_cases':cases,
        'orth_scope':'additional orth directives withheld from this primary source review; no deletion or approval',
        'native_scope':'source generated diagnostic forms; direct reference readings retained on all sixteen recorded fields; no independent form attestation',
        'private_source_primary_review_sha256':review.probe.digest(payload),'original_inputs_unchanged':True}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('report','candidate','diagnostic','headers','tei','native','library','baseline','tools','output'):p.add_argument('--'+n,type=Path,required=True)
    previous=os.umask(0o077)
    try:result=prepare(p.parse_args())
    finally:os.umask(previous)
    print(json.dumps({'latin_loss_primary_source_qualification':result},sort_keys=True))


if __name__=='__main__':main()
