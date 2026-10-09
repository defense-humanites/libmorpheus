#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Attribute the qualified supine additions and compare historical readings."""
import argparse
from collections import Counter
import importlib.util
import json
import os
from pathlib import Path

spec=importlib.util.spec_from_file_location('trial',Path(__file__).with_name('qualify-latin-third-supine-alternatives.py'))
trial=importlib.util.module_from_spec(spec);spec.loader.exec_module(trial)
changed=trial.changed
loss=changed.loss
native=trial.native
supines=trial.supines
bases=loss.sibling('review-latin-lost-preverb-bases')
QUALIFICATION_SHA='42e7bba524ee6cc76d23981c38e2d697984344240c48652c5ddd82b0b9ad3aba'
BASELINE_EXPANDED_SHA='f64a9c551a1c56013c645628408e79a02bb6b9672bc98585f8c0edd7038836c3'
BASELINE_INDEXES={
    'nomind':'106592a19b3b34a343c271fadcc559cdef10363c0d7f4ea024a71ae613e1bd54',
    'nomind.lindex':'e70bc11f301cbdf9765cb56b30109f0fc53539c19056168c2e09c05503d05210',
    'vbind':'cda6088f50c2e5ba10ecafdd0ca261e126b3af7a143dec67d6c166a1f4558dcc',
    'vbind.lindex':'e0fac809eaa705bdba44f462a46d1696f4c54744ff3043cfcabb383193e30353'}


def decoded(value):
    return value.decode('utf-8') if isinstance(value,bytes) else value


def serialized(counter):
    return [{'signature':[decoded(v) for v in key],'multiplicity':n}
            for key,n in sorted(counter.items())]


def deserialized(records):
    result=Counter()
    for row in records:
        values=row['signature'];count=row['multiplicity']
        if len(values)!=11 or type(count) is not int or count<=0:
            raise ValueError('supine attribution signature scope differs')
        result[tuple(v.encode('utf-8') if isinstance(v,str) else v for v in values)]+=count
    return result


def compare(record,before,after,baseline,selected):
    old=Counter(map(loss.signature,before));new=Counter(map(loss.signature,after))
    added=new-old;removed=old-new
    if (len(before)!=record['curated_count'] or len(after)!=record['rebuilt_count']
            or sum((old&new).values())!=record['retained_rows']
            or added!=deserialized(record['added']) or removed!=deserialized(record['removed']) or removed):
        raise ValueError('supine attribution qualified multiset differs')
    old16=Counter(map(supines.direct.route,before));new16=Counter(map(supines.direct.route,after))
    if old16-new16:
        raise ValueError('supine attribution changes retained derivation fields')
    added16=new16-old16
    historical=Counter(map(loss.signature,baseline))-old
    matched=historical&added
    matched16=(Counter(map(supines.direct.route,baseline))-old16)&added16
    counts=Counter({'added_eleven_field_readings':sum(added.values()),
                    'added_sixteen_field_readings':sum(added16.values()),
                    'retained_sixteen_field_readings':sum((old16&new16).values()),
                    'historical_removed_readings_restored':sum(matched.values()),
                    'historical_sixteen_field_readings_restored':sum(matched16.values()),
                    'additions_beyond_historical_removed_multiset':sum((added-matched).values())})
    state='complete_form_loss' if not before else 'still_recognized_form_loss'
    counts['historical_readings_restored__'+state]+=sum(matched.values())
    selected11=Counter({key:n for key,n in matched.items() if key[1] in selected and key[2]==2}) if not before else Counter()
    selected16=Counter({key:n for key,n in matched16.items() if key[1] in selected and key[2]==2}) if not before else Counter()
    counts['selected_old_complete_loss_readings_restored_eleven_fields']+=sum(selected11.values())
    counts['selected_old_complete_loss_readings_restored_sixteen_fields']+=sum(selected16.values())
    per_case=Counter()
    for key,n in selected11.items():per_case[(key[1],'eleven_fields')]+=n
    for key,n in selected16.items():per_case[(key[1],'sixteen_fields')]+=n
    rows={supines.direct.route(row):row for row in after}
    additions=[(rows[key],n) for key,n in sorted(added16.items())]
    evidence={'form':record['form'],'original_absent':not before,
              'historical_eleven_field_matches':serialized(matched),
              'historical_sixteen_field_matches':serialized(matched16)}
    return counts,per_case,additions,evidence


def reading_record(row):
    return {'signature':[decoded(v) for v in loss.signature(row)],
            **{n:decoded(getattr(row,n)) for n in ('stem','suffix','ending','preverb','raw_preverb')}}


def peer_state(before,after):
    return ('before_and_after_direct_peer' if before and after else
            'after_direct_peer_only' if after else 'before_direct_peer_only' if before else 'no_direct_peer')


def inspect_dependency(row,readers,selected):
    reading=reading_record(row)
    base=bases.literal_base(reading['signature'][1],reading['preverb'])
    form=bases.decomposition_form(reading)
    peers={label:0 for label in ('baseline','original','trial','reference')}
    if base is not None and form is not None:
        peers={label:bases.peer_count(reader,form,base,reading) for label,reader in readers.items()}
    scope='selected_source_base' if base is not None and base.encode() in selected else 'other_base' if base else 'unclassified_identifier'
    group=(scope,peer_state(peers['original'],peers['trial']),bool(peers['reference']),bool(peers['baseline']))
    private={'reading':reading,'literal_base':base,'decomposition_form':form.decode() if form else None,
             'base_scope':scope,'exact_direct_peers':peers}
    return group,base,private


def source_cases(evidence,report):
    old={c['source_header_sha256']:c for c in report['changed_definition_source_review']['anonymous_cases']}
    selected={};groups=Counter()
    for item in evidence:
        if 'source_header' not in item:continue
        row=item['source_header'];key=trial.review.probe.digest(json.dumps(row,sort_keys=True).encode())
        case=old.get(key);branch,expected=trial.recipe(row)
        lemma=trial.review.source_key(row)
        if (case is None or case.get('source_partition')!='verbal' or not case.get('literal_headword_identity')
                or not expected or lemma in selected or item['lemma'].encode()!=lemma):
            raise ValueError('supine attribution source join differs')
        selected[lemma]={'source_header_sha256':key,'old_complete_loss_readings':sum(case['readings'].values())}
        groups[branch]+=1
    if len(selected)!=2 or sum(c['old_complete_loss_readings'] for c in selected.values())!=119:
        raise ValueError('supine attribution historical case scope differs')
    return selected,groups


def prepare(args):
    if native.digest(args.qualification)!=QUALIFICATION_SHA or native.digest(args.source_report)!=trial.primary.REPORT_SHA:
        raise ValueError('supine attribution public receipts differ')
    qualification=json.loads(args.qualification.read_bytes())['qualification']
    paths={'qualification':args.qualification,'source_report':args.source_report,
           'delta':args.trial/'global-delta.jsonl','evidence':args.trial/'source-evidence.jsonl',
           'source':args.trial/'after.stems','reference_source':args.trial/'reference.stems',
           'baseline_expanded':args.baseline/'Latin/lexical/verb.expanded'}
    receipts={'qualification':QUALIFICATION_SHA,'source_report':trial.primary.REPORT_SHA,
              'delta':qualification['global_listall']['comparison']['private_difference_sha256'],
              'evidence':qualification['private_source_evidence_sha256'],
              'source':qualification['trial_source_sha256'],
              'reference_source':qualification['source_reference_sha256'],
              'baseline_expanded':BASELINE_EXPANDED_SHA}
    if any(native.digest(p)!=receipts[n] for n,p in paths.items()):
        raise ValueError('supine attribution private input receipt differs')
    selected,recipes=source_cases([json.loads(l) for l in paths['evidence'].read_bytes().splitlines()],json.loads(args.source_report.read_bytes()))
    records=[json.loads(l) for l in paths['delta'].read_bytes().splitlines()]
    forms=[r['form'].encode('ascii') for r in records]
    if len(forms)!=245 or len(set(forms))!=245 or any(not f or any(c<33 or c>126 for c in f) for f in forms):
        raise ValueError('supine attribution changed-form scope differs')
    roots={'baseline':args.baseline,'original':args.original,'trial':args.trial/'trial','reference':args.trial/'reference'}
    indexes={label:{n:native.digest(root/'Latin/steminds'/n) for n in BASELINE_INDEXES} for label,root in roots.items()}
    if (indexes['baseline']!=BASELINE_INDEXES or indexes['original']!=qualification['original_indexes_sha256']
            or indexes['trial']!=qualification['trial_indexes_sha256'] or indexes['reference']!=qualification['source_reference_indexes_sha256']):
        raise ValueError('supine attribution native indexes differ')
    target=loss.private_target(args.output,[*paths.values(),*roots.values(),args.library]);target.mkdir(mode=0o700)
    readers={};totals=Counter();cases=Counter();dependencies=Counter();identifiers=set();base_set=set();private=[]
    try:
        for label,root in roots.items():readers[label]=supines.direct.StrictRows(args.library,root)
        for record,form in zip(records,forms):
            snapshots={label:readers[label].analyses(form,require_untruncated=True) for label in ('baseline','original','trial')}
            counts,case_counts,additions,evidence=compare(record,snapshots['original'],snapshots['trial'],snapshots['baseline'],selected)
            totals.update(counts);cases.update(case_counts);private.append(evidence)
            for row,n in additions:
                if not row.preverb:totals['added_direct_readings']+=n;continue
                totals['added_native_preverb_readings']+=n;identifiers.add(row.lemma)
                group,base,evidence=inspect_dependency(row,readers,selected)
                dependencies[group]+=n
                if base is not None:base_set.add(base)
                private.append({'kind':'native_dependency','form':record['form'],'multiplicity':n,**evidence})
        native.write_private(target/'forms',b''.join(f+b'\n' for f in sorted(forms)))
        control=supines.direct.audit.audit(target/'forms',readers['trial'],readers['trial'],target/'control.jsonl',require_identical=True)
    finally:
        for reader in readers.values():reader.close()
    if (totals['added_eleven_field_readings']!=649 or totals['added_sixteen_field_readings']!=649
            or totals['added_direct_readings']!=215 or totals['added_native_preverb_readings']!=434
            or totals['selected_old_complete_loss_readings_restored_eleven_fields']>119):
        raise ValueError('supine attribution addition or historical scope differs')
    anonymous=[]
    for lemma,case in sorted(selected.items()):
        restored=cases[(lemma,'eleven_fields')]
        if restored>case['old_complete_loss_readings']:raise ValueError('supine attribution exceeds an old case')
        anonymous.append({**case,'restored_eleven_fields':restored,'restored_sixteen_fields':cases[(lemma,'sixteen_fields')],
                          'remaining_old_eleven_field_readings':case['old_complete_loss_readings']-restored})
    payload=b''.join((json.dumps(r,sort_keys=True)+'\n').encode() for r in private)
    native.write_private(target/'attribution.jsonl',payload)
    if any(native.digest(p)!=receipts[n] for n,p in paths.items()) or any(
            native.digest(root/'Latin/steminds'/n)!=indexes[label][n] for label,root in roots.items() for n in BASELINE_INDEXES):
        raise ValueError('supine attribution changed an input')
    return {'schema':1,'scope':'245 changed forms in the qualified separate supine trial; historical reading attribution and literal native base dependencies only',
            'input_sha256':receipts,'native_indexes_sha256':indexes,'counts':dict(totals),
            'source_recipes':dict(recipes),'old_selected_complete_loss_readings':119,'anonymous_source_cases':anonymous,
            'native_dependency_groups':loss.grouped(dependencies,('base_scope','direct_peer_state','source_reference_peer','baseline_peer')),
            'distinct_added_native_identifiers':len(identifiers),'distinct_literal_bases':len(base_set),
            'identical_root_changed_form_control':control,'private_attribution_sha256':native.digest(target/'attribution.jsonl'),
            'historical_scope':'baseline-minus-original intersections with added multisets; complete losses require original analyses empty; no extrapolation outside 245 changed forms',
            'dependency_scope':'literal recorded preverb boundary and nine grammatical plus three derivation fields; quantity/separator removal for diagnostic inputs only; no compound source identity or independent form attestation',
            'original_inputs_unchanged':True}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('qualification','source-report','trial','baseline','original','library','output'):
        p.add_argument('--'+name,type=Path,required=True)
    previous=os.umask(0o077)
    try:report=prepare(p.parse_args())
    finally:os.umask(previous)
    print(json.dumps({'latin_third_supine_recovery_attribution':report},sort_keys=True))


if __name__=='__main__':main()
