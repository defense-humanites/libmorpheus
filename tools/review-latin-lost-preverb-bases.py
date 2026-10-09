#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Review lost native composition identifiers and their literal base peers."""
import argparse
from collections import Counter, defaultdict
import importlib.util
import json
import os
from pathlib import Path
import re

spec=importlib.util.spec_from_file_location('changed',Path(__file__).with_name('review-latin-changed-definition-losses.py'))
changed=importlib.util.module_from_spec(spec);spec.loader.exec_module(changed)
loss=changed.loss
native=changed.reproduction.native


def literal_base(lemma,preverb):
    if not preverb or not lemma.startswith(preverb+'-') or len(lemma)<=len(preverb)+1:return None
    return lemma[len(preverb)+1:]


def decomposition_form(reading):
    value=''.join(reading[n] for n in ('stem','suffix','ending'))
    if not re.fullmatch(r'[A-Za-z_^\-]+',value):return None
    result=value.translate(str.maketrans('','','_^-')).encode('ascii')
    return result if result else None


def peer_count(reader,form,base,reading):
    expected=tuple(reading['signature'][2:11])+(reading['stem'].encode(),reading['suffix'].encode(),reading['ending'].encode())
    return sum(not row.preverb and row.lemma==base.encode('ascii') and
        tuple(getattr(row,n) for n in ('part_of_speech','person','number','gender','grammatical_case','tense','mood','voice','degree','stem','suffix','ending'))==expected
        for row in reader.analyses(form,require_untruncated=True))


def inspect(rows,dossiers,old_defs,new_defs,old_reader,new_reader,sources):
    selected={key:row for key,row in dossiers.items() if row['definition_state']=='no_definitions_in_either'}
    counts=Counter();groups=Counter();case_counts=defaultdict(Counter);private=[];base_sets=defaultdict(set)
    for row in rows:
        for reading in row['readings']:
            lemma=reading['signature'][1]
            if lemma not in selected:continue
            if not reading['preverb']:raise ValueError('definition-free loss must be native composition')
            base=literal_base(lemma,reading['preverb']);form=decomposition_form(reading)
            relation='literal_preverb_base_identifier' if base is not None else 'unclassified_identifier'
            state=loss.definition_state(old_defs.get(base.encode(),Counter()),new_defs.get(base.encode(),Counter())) if base is not None else 'not_evaluated'
            old_peers=new_peers=0
            if base is not None and form is not None:
                old_peers=peer_count(old_reader,form,base,reading);new_peers=peer_count(new_reader,form,base,reading)
            peer=('baseline_and_final_direct_peer' if old_peers and new_peers else
                  'baseline_direct_peer_only' if old_peers else
                  'final_direct_peer_only' if new_peers else 'no_direct_peer_in_reconstructed_form')
            base_loss=dossiers.get(base,{}).get('definition_state','not_in_complete_loss_dossier')
            choices=sources.get(base.encode(),{}) if base is not None else {}
            join='unique_article' if len(choices)==1 else 'ambiguous_articles' if choices else 'no_article_join'
            counts['readings']+=1;counts[relation]+=1;counts[peer]+=1
            groups[(relation,state,base_loss,peer,join)]+=1;case_counts[lemma][(state,base_loss,peer,join)]+=1
            if base is not None:base_sets[lemma].add(base)
            private.append({'form':row['form'],'reading':reading,'base':base,'decomposition_form':form.decode() if form else None,
                'identifier_relation':relation,'base_definition_state':state,'base_complete_loss_state':base_loss,
                'before_direct_peer_readings':old_peers,'after_direct_peer_readings':new_peers,'source_join':join})
    cases=[]
    for lemma,case in sorted(case_counts.items()):
        base_headers=[]
        for base in sorted(base_sets[lemma]):
            choices=sources.get(base.encode(),{})
            if len(choices)==1:
                row=next(iter(choices.values()))['row']
                base_headers.append(changed.review.probe.digest(json.dumps(row,sort_keys=True).encode()))
        cases.append({'readings':sum(case.values()),'distinct_literal_bases':len(base_sets[lemma]),
            'base_source_header_sha256':sorted(set(base_headers)),
            'groups':loss.grouped(case,('base_definition_state','base_complete_loss_state','peer_state','base_source_join'))})
    return {'counts':dict(counts),'distinct_native_identifiers':len(case_counts),
        'distinct_literal_bases':len(set().union(*base_sets.values())) if base_sets else 0,
        'groups':loss.grouped(groups,('identifier_relation','base_definition_state','base_complete_loss_state','peer_state','base_source_join')),
        'anonymous_cases':cases},private


def prepare(args):
    paths={n:getattr(args,n) for n in ('dossier','baseline_expanded','final_expanded','headers','tei')}
    receipts={'dossier':changed.reproduction.DOSSIER_SHA,'baseline_expanded':'f64a9c551a1c56013c645628408e79a02bb6b9672bc98585f8c0edd7038836c3',
        'final_expanded':'83e4157c96bc029fa6950c589c5a26f4f1c55eef07a2654d7cc771ceeafa0940',
        'headers':changed.review.RECEIPTS['headers'],'tei':changed.review.RECEIPTS['tei']}
    if any(native.digest(p)!=receipts[n] for n,p in paths.items()):raise ValueError('lost-preverb review receipt differs')
    all_rows=[json.loads(line) for line in args.dossier.read_bytes().splitlines()]
    forms=[r for r in all_rows if r['kind']=='lost_form'];dossiers={r['lemma']:r for r in all_rows if r['kind']=='lemma_review'}
    first=changed.review.sibling('repair-latin-first-conjugation')
    rows,_,_=first.source_rows(args.headers,args.tei);entries,_,_=first.review.load_entries(args.tei)
    sources=loss.source_index(rows,entries,first.review.partition.classify)
    target=loss.private_target(args.output,[*paths.values(),args.baseline,args.candidate,args.library]);target.mkdir(mode=0o700)
    readers={}
    indexes={label:{n:native.digest(root/'Latin/steminds'/n) for n in changed.reproduction.candidate.INDEXES}
        for label,root in (('baseline',args.baseline),('candidate',args.candidate))}
    if indexes['candidate']!=changed.reproduction.candidate.INDEXES:raise ValueError('lost-preverb candidate indexes differ')
    try:
        for label,root in (('baseline',args.baseline),('candidate',args.candidate)):
            readers[label]=changed.reproduction.candidate.supines.direct.StrictRows(args.library,root)
        report,private=inspect(forms,dossiers,loss.definitions(args.baseline_expanded),loss.definitions(args.final_expanded),
            readers['baseline'],readers['candidate'],sources)
    finally:
        for reader in readers.values():reader.close()
    if report['distinct_native_identifiers']!=44 or report['counts']['readings']!=2786:
        raise ValueError('lost-preverb review scope differs')
    payload=b''.join((json.dumps(row,sort_keys=True)+'\n').encode() for row in private)
    changed.review.probe.write_private(target/'base-review.jsonl',payload)
    if any(native.digest(p)!=receipts[n] for n,p in paths.items()) or any(
        native.digest(root/'Latin/steminds'/n)!=indexes[label][n] for label,root in (('baseline',args.baseline),('candidate',args.candidate)) for n in indexes[label]):
        raise ValueError('lost-preverb review changed an input')
    return {'schema':1,'scope':'44 definition-free native composition losses; literal base and direct-peer diagnostics, no lexical identity or repair approval',
        'input_sha256':receipts,**report,
        'decomposition_scope':'quantity/separator removal for diagnostic reanalysis only; no source-form attestation; failure to find a peer is not absence proof',
        'private_base_review_sha256':changed.review.probe.digest(payload),'original_inputs_unchanged':True}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('dossier','baseline-expanded','final-expanded','headers','tei','baseline','candidate','library','output'):
        p.add_argument('--'+n,type=Path,required=True)
    previous=os.umask(0o077)
    try:report=prepare(p.parse_args())
    finally:os.umask(previous)
    print(json.dumps({'latin_lost_preverb_base_review':report},sort_keys=True))


if __name__=='__main__':main()
