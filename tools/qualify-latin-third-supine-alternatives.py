#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Trial literal coordinated third-conjugation supines; lexical evidence stays private."""
import argparse
from collections import Counter
import importlib.util
import json
import os
from pathlib import Path
import re

spec=importlib.util.spec_from_file_location('primary',Path(__file__).with_name('qualify-latin-loss-primary-source.py'))
primary=importlib.util.module_from_spec(spec);spec.loader.exec_module(primary)
changed=primary.changed
review=primary.review
native=primary.native
supines=primary.supines

def plain(value):
    return value.translate(str.maketrans('','','_^'))

def recipe(row):
    head=row.get('headword','')
    if row.get('projection_error') is not None or not re.fullmatch(r'[a-z_^]+(?:#[1-9])?',head):
        return 'unclassified',Counter()
    head=re.sub(r'#[1-9]$','',head)
    fields=[(i,f['projection']) for i,f in enumerate(row['fields']) if f['name']=='itype']
    if not fields or any(b[0]!=a[0]+1 for a,b in zip(fields,fields[1:])):
        return 'unclassified',Counter()
    grammar=', '.join(v for _,v in fields)
    triple=re.fullmatch(r'([a-z_^]+i), ([a-z_^]+um), ([a-z_^]+um) and ([a-z_^]+um), 3',grammar)
    dual=re.fullmatch(r'([a-z_^]+i), ([a-z_^]+um), and ([a-z_^]+um), 3',grammar)
    if triple and head.endswith('o') and not head.endswith(('io','i^o')):
        root=head[:-1];parts=triple.groups();branch='literal_triple_supines'
        if len(plain(root))<3 or plain(parts[0][:-1])!=plain(root):
            return 'unclassified',Counter()
        kind=b'conj3'
    elif dual and head.endswith('i^o'):
        root=head[:-3];parts=dual.groups();branch='literal_dual_supines_reduplicated_perfect'
        base=plain(root)
        # This is a bound on an explicitly written word, not a generated perfect.
        if (len(base)!=3 or base[0] in 'aeiou' or base[1] not in 'aeiou'
                or base[2] in 'aeiou' or plain(parts[0][:-1])!=base[0]+'e'+base[0]+'e'+base[2]):
            return 'unclassified',Counter()
        kind=b'conj3_io'
    else:
        return 'unclassified',Counter()
    stems=[p[:-2] for p in parts[1:]]
    if (any(not plain(s).startswith(plain(root)) for s in stems)
            or len(set(stems))!=len(stems) or root[0] in 'aeiou'):
        return 'unclassified',Counter()
    expected=Counter({((':vs:'+root).encode(),kind):1,
                      ((':vs:'+parts[0][:-1]).encode(),b'perfstem'):1})
    expected.update(((':vs:'+s).encode(),b'pp4') for s in stems)
    return branch,expected

def shape(row):
    fields=[f['projection'] for f in row['fields'] if f['name']=='itype']
    grammar=', '.join(fields)
    head=re.sub(r'#[1-9]$','',row.get('headword',''))
    parts=[p.strip() for p in re.split(r', | and ',grammar) if p.strip() not in ('3','and')]
    root=head[:-3] if head.endswith('i^o') else head[:-1]
    return {'grammar_shape':re.sub(r'[A-Za-z_^]+','PART',grammar),
        'head_plain_length':len(plain(head)),'head_ascii_lower':bool(re.fullmatch(r'[a-z_^]+',head)),
        'head_plain_o':head.endswith('o'),'head_io':head.endswith(('io','i^o')),
        'parts_plain_lengths':[len(plain(p)) for p in parts],
        'perfect_matches_present':bool(parts and plain(parts[0][:-1])==plain(root)),
        'supines_start_present':[plain(p[:-2]).startswith(plain(root)) for p in parts[1:]],
        'supines_end_um':[p.endswith('um') for p in parts[1:]],
        'parts_ascii_lower':[bool(re.fullmatch(r'[a-z_^]+',p)) for p in parts],
        'adjacent_itypes':all(b==a+1 for a,b in zip(
            [i for i,f in enumerate(row['fields']) if f['name']=='itype'],
            [i for i,f in enumerate(row['fields']) if f['name']=='itype'][1:]))}

def anchors(actual,expected):
    missing=expected-actual
    if (sum(actual.values())!=3 or actual-expected or sum(missing.values()) not in (1,2)
            or any(tokens[1:]!=(b'pp4',) for tokens in missing)
            or sum(n for tokens,n in actual.items() if tokens[1:]==(b'pp4',))!=1):
        raise ValueError('coordinated supine anchor scope differs')
    return missing

def append_missing(data,additions):
    lines=data.splitlines(keepends=True);result=[];lemma=None;seen=Counter()
    def emit(key):
        if key in additions:
            seen[key]+=1
            if result and not result[-1].endswith(b'\n'):
                raise ValueError('coordinated supine block has no terminal newline')
            result.extend(b' '.join(t)+b'\n' for t,n in sorted(additions[key].items()) for _ in range(n))
    for line in lines:
        if line.startswith(b':le:'):
            emit(lemma);lemma=line[4:].strip()
        result.append(line)
    emit(lemma)
    if seen!=Counter({k:1 for k in additions}):
        raise ValueError('coordinated supine block identity differs')
    after=b''.join(result)
    old=review.probe.definitions(data);new=review.probe.definitions(after)
    # The definition parser retains directive bytes; normalize whitespace for comparison.
    def normalized(definitions):
        result=Counter()
        for (key,line),n in definitions.items():result[(key,tuple(line.split()))]+=n
        return result
    expected=Counter({(key,t):n for key,records in additions.items() for t,n in records.items()})
    if normalized(old)-normalized(new) or normalized(new)-normalized(old)!=expected:
        raise ValueError('coordinated supine trial definition delta differs')
    return after

def prepare(args):
    paths={n:getattr(args,n) for n in ('report','candidate','headers','tei')}
    if args.forms is not None:
        paths['forms']=args.forms
    receipts={'report':primary.REPORT_SHA,'candidate':changed.reproduction.candidate.CANDIDATE_SHA,
              'headers':review.RECEIPTS['headers'],'tei':review.RECEIPTS['tei']}
    if args.forms is not None:
        receipts['forms']='1df0800fb1443b2cfd64d787c257319aa72b69f453c3c37ec60c359c70cebd93'
    if any(native.digest(p)!=receipts[n] for n,p in paths.items()):
        raise ValueError('coordinated supine input receipt differs')
    report=json.loads(args.report.read_bytes())
    if report['changed_definition_source_review']['changed_definition_lemmas']!=59:
        raise ValueError('coordinated supine report scope differs')
    first=review.sibling('repair-latin-first-conjugation')
    rows,_,_=first.source_rows(args.headers,args.tei)
    headers={review.probe.digest(json.dumps(r,sort_keys=True).encode()):r for r in rows}
    selected=[];groups=Counter();screened=0;private=[];additions={};coordinated_shapes=[]
    data=args.candidate.read_bytes();definitions=review.probe.definitions(data)
    for case in report['changed_definition_source_review']['anonymous_cases']:
        if case.get('source_partition')!='verbal':continue
        row=headers.get(case['source_header_sha256'])
        if row is None:raise ValueError('coordinated supine header join missing')
        fields=[f['projection'] for f in row['fields'] if f['name']=='itype']
        if not fields or not re.search(r'(?:^|, )3$',', '.join(fields)):continue
        if primary.source_recipe(row)[1]:continue
        screened+=1
        branch,expected=recipe(row)
        if ' and ' in ', '.join(fields):coordinated_shapes.append(shape(row))
        groups[branch]+=1
        if not expected:continue
        if not case.get('literal_headword_identity'):
            raise ValueError('coordinated supine literal identity differs')
        lemma=review.source_key(row)
        actual=changed.selected_tokens(definitions,lemma)
        missing=anchors(actual,expected)
        if lemma in additions:raise ValueError('coordinated supine duplicate lemma')
        additions[lemma]=missing;selected.append((lemma,expected,case))
        private.append({'source_header':row,'lemma':lemma.decode(),'recipe':branch,
                        'missing':[[t.decode() for t in tokens] for tokens in missing]})
    print(json.dumps({'latin_third_supine_screen':{'screened':screened,'groups':dict(groups),
          'coordinated_shapes':coordinated_shapes,'selected':len(selected),'missing_directives':sum(sum(c.values()) for c in additions.values())}},sort_keys=True),flush=True)
    if screened!=27 or len(selected)!=2 or sum(sum(c.values()) for c in additions.values())!=3:
        raise ValueError('coordinated supine bounded selection differs')
    target=changed.loss.private_target(args.output,[*paths.values(),args.native,args.library,args.baseline,args.tools])
    target.mkdir(mode=0o700)
    baseline_indexes={n:native.digest(args.baseline/'Latin/steminds'/n) for n in changed.reproduction.candidate.INDEXES}
    indexes={n:native.digest(args.native/'Latin/steminds'/n) for n in baseline_indexes}
    if indexes!=changed.reproduction.candidate.INDEXES:
        raise ValueError('coordinated supine original native receipt differs')
    after=append_missing(data,additions)
    native.write_private(target/'after.stems',after)
    native.write_private(target/'reference.stems',b''.join(supines.payload(lemma,expected) for lemma,expected,_ in selected))
    trial_indexes=native.build_trial(args.baseline,target/'after.stems',args.tools,target/'trial')
    ref_indexes=native.build_trial(args.baseline,target/'reference.stems',args.tools,target/'reference')
    if any(index[n]!=indexes[n] for index in (trial_indexes,ref_indexes) for n in ('nomind','nomind.lindex')):
        raise ValueError('coordinated supine nominal indexes changed')
    readers={}
    totals_before=Counter();totals_after=Counter();forms=set();sixteen=Counter();global_report=None
    try:
        for label,root in (('before',args.native),('after',target/'trial'),('reference',target/'reference')):
            readers[label]=supines.direct.StrictRows(args.library,root)
        for lemma,expected,case in selected:
            sup=Counter({t:n for t,n in expected.items() if t[1:]==(b'pp4',)})
            cells=primary.family_cells(sup)
            before,evidence_before=primary.check_cells(readers['before'],lemma,cells,readers['reference'])
            after_counts,evidence_after=primary.check_cells(readers['after'],lemma,cells,readers['reference'])
            totals_before.update(before);totals_after.update(after_counts)
            forms.update(f for f,_,_ in cells)
            private.append({'lemma':lemma.decode(),'before':evidence_before,'after':evidence_after})
        for form in sorted(forms):
            old=Counter(map(supines.direct.route,readers['before'].analyses(form,require_untruncated=True)))
            new=Counter(map(supines.direct.route,readers['after'].analyses(form,require_untruncated=True)))
            sixteen['retained_rows']+=sum((old&new).values())
            sixteen['removed_rows']+=sum((old-new).values())
            sixteen['added_rows']+=sum((new-old).values())
            sixteen['changed_forms']+=bool(old-new or new-old)
        if sixteen['removed_rows']:
            raise ValueError('coordinated supine family removes native readings')
        native.write_private(target/'forms',b''.join(f+b'\n' for f in sorted(forms)))
        control=supines.direct.audit.audit(target/'forms',readers['after'],readers['after'],target/'control.jsonl',require_identical=True)
        delta=supines.direct.audit.audit(target/'forms',readers['before'],readers['after'],target/'delta.jsonl')
        if (totals_before['covered_cells']!=12 or totals_after['expected_cells']!=30 or totals_after['covered_cells']!=30
                or totals_after['reference_covered_cells']!=30 or totals_after['missing_reference_readings']):
            raise ValueError('coordinated supine reference family differs')
        if args.forms is not None:
            global_control=supines.direct.audit.audit(args.forms,readers['after'],readers['after'],target/'global-control.jsonl',require_identical=True)
            global_delta=supines.direct.audit.audit(args.forms,readers['before'],readers['after'],target/'global-delta.jsonl')
            if (global_delta['counts']['distinct_forms']!=1033579
                    or global_delta['analysis_rows']['curated']!=2100530
                    or global_delta['global_eleven_field_multisets']['removed_rows']):
                raise ValueError('coordinated supine global scope or retained readings differ')
            global_report={'control':global_control,'comparison':global_delta}
    finally:
        for reader in readers.values():reader.close()
    evidence=b''.join((json.dumps(r,sort_keys=True)+'\n').encode() for r in private)
    native.write_private(target/'source-evidence.jsonl',evidence)
    if any(native.digest(p)!=receipts[n] for n,p in paths.items()) or any(
            native.digest(args.native/'Latin/steminds'/n)!=indexes[n] or
            native.digest(args.baseline/'Latin/steminds'/n)!=baseline_indexes[n] for n in indexes):
        raise ValueError('coordinated supine changed an input')
    return {'schema':1,'scope':'two literal coordinated supine source families in a separate full-source trial; optional LISTALL diagnostic; no production promotion',
            'native_scope':'source generated diagnostic forms; exact literal lemma and sixteen native fields against isolated source reference; no independent form attestation',
            'engine_supine_case_codes':'historical pp4 table nominative/dative; no philological case correction',
            'screened_third_cases':screened,'recipe_groups':dict(groups),'selected_lemmas':len(selected),
            'added_pp4_directives':3,'removed_directives':0,'input_sha256':receipts,
            'trial_source_sha256':native.digest(target/'after.stems'),
            'original_indexes_sha256':indexes,'trial_indexes_sha256':trial_indexes,
            'source_reference_indexes_sha256':ref_indexes,'source_reference_sha256':native.digest(target/'reference.stems'),
            'native_family_before':dict(totals_before),'native_family_after':dict(totals_after),
            'distinct_family_forms':len(forms),'family_sixteen_field_multisets':dict(sixteen),'global_listall':global_report,'family_comparison':delta,'identical_root_control':control,
            'private_source_evidence_sha256':native.digest(target/'source-evidence.jsonl'),'original_inputs_unchanged':True}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('report','candidate','headers','tei','native','library','baseline','tools','output'):
        p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--forms',type=Path)
    previous=os.umask(0o077)
    try:result=prepare(p.parse_args())
    finally:os.umask(previous)
    print(json.dumps({'latin_third_supine_alternatives':result},sort_keys=True))

if __name__=='__main__':main()
