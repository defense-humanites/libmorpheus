#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Review changed-definition losses against source and isolated lexer output."""
import argparse
from collections import Counter, defaultdict
import importlib.util
import json
import os
from pathlib import Path
import re

spec=importlib.util.spec_from_file_location('reproduction',Path(__file__).with_name('reproduce-latin-complete-losses.py'))
reproduction=importlib.util.module_from_spec(spec);spec.loader.exec_module(reproduction)
review=reproduction.candidate.review
loss=reproduction.loss


def language(node):
    while node is not None:
        value=node.get('{http://www.w3.org/XML/1998/namespace}lang') or node.get('lang')
        if value:return value
        node=node.getparent()
    return None


def surface_leads(entry,forms,normalize):
    """Exact surfaces/notation leads only; no lemma or grammar attribution."""
    result=defaultdict(set)
    for node in entry.iter():
        route=None
        if node.tag=='orth' and node.get('extent')=='full' and language(node) in (None,'la','lat'):
            route='full_orthography'
        elif node.tag=='quote' and language(node) in ('la','lat'):
            route='latin_citation'
        elif node.tag=='ref' and language(node) in (None,'la','lat'):
            route='whole_reference'
        if route is None:continue
        if any(language(child) not in (None,'la','lat') for child in node.iter()):continue
        text=normalize(' '.join(''.join(node.itertext()).split()),'Latin')
        if text is None:continue
        tokens=re.findall(r'[A-Za-z_^+-]+',text) if route=='latin_citation' else [text]
        for token in tokens:
            if not re.fullmatch(r'[A-Za-z_^+-]+',token):continue
            literal=token.encode('ascii');plain=literal.translate(None,b'_^-' )
            if literal in forms:result[(route,'literal')].add(literal)
            elif plain in forms:result[(route,'notation_removed_lead')].add(plain)
    return result


def dossier_inventory(path):
    dossiers={};forms=defaultdict(set);readings=defaultdict(Counter);seen=set()
    for line in path.read_bytes().splitlines():
        row=json.loads(line)
        if row['kind']=='lost_form':
            if row['form'] in seen:raise ValueError('duplicate loss form')
            seen.add(row['form'])
            for reading in row['readings']:
                signature=reading['signature']
                if len(signature)!=11:raise ValueError('loss signature differs')
                key=signature[1];forms[key].add(row['form'].encode('ascii'))
                readings[key]['native_preverb' if reading['preverb'] else 'direct']+=1
        elif row['kind']=='lemma_review':
            if row['lemma'] in dossiers:raise ValueError('duplicate loss lemma')
            dossiers[row['lemma']]=row
        else:raise ValueError('unknown loss record')
    if set(dossiers)!=set(readings):raise ValueError('loss inventories differ')
    selected={k:v for k,v in dossiers.items() if v['definition_state']=='changed_definition_multisets'}
    return selected,forms,readings


def token_records(rows):
    result=Counter()
    for row in rows:
        line=row['line'].encode('ascii')
        if line.startswith(review.probe.STEM_PREFIXES):result[tuple(line.split())]+=row['multiplicity']
    return result


def classes(records):
    result=Counter()
    for tokens,n in records.items():result[review.classify(b' '.join(tokens))]+=n
    return dict(sorted(result.items()))


def selected_tokens(definitions,lemma):
    result=Counter()
    for (key,line),n in definitions.items():
        if key==lemma:result[tuple(line.split())]+=n
    return result


def prepare(args):
    paths={'dossier':args.dossier,'headers':args.headers,'tei':args.tei,'candidate':args.candidate,'diagnostic':args.diagnostic}
    receipts={'dossier':reproduction.DOSSIER_SHA,'headers':review.RECEIPTS['headers'],'tei':review.RECEIPTS['tei'],
        'candidate':reproduction.candidate.CANDIDATE_SHA,'diagnostic':review.RECEIPTS['diagnostic']}
    if any(reproduction.native.digest(p)!=receipts[n] for n,p in paths.items()):
        raise ValueError('changed-definition review receipt differs')
    selected,forms,reading_counts=dossier_inventory(args.dossier)
    if len(selected)!=59 or sum(sum(reading_counts[k].values()) for k in selected)!=5547:
        raise ValueError('changed-definition loss scope differs')
    first=review.sibling('repair-latin-first-conjugation')
    rows,_,_=first.source_rows(args.headers,args.tei)
    entries,_,_=first.review.load_entries(args.tei)
    sources=loss.source_index(rows,entries,first.review.partition.classify)
    target=loss.private_target(args.output,[*paths.values(),args.filters,args.diagnostic_filter]);target.mkdir(mode=0o700)
    candidate=review.probe.definitions(args.candidate.read_bytes())
    diagnostic=review.probe.definitions(args.diagnostic.read_bytes())
    cases=[];private=[];groups=Counter();surface_totals=Counter()
    for number,(key,dossier) in enumerate(sorted(selected.items())):
        lemma=key.encode('ascii');choices=sources.get(lemma,{})
        before=token_records(dossier['baseline_definitions']);after=token_records(dossier['final_definitions'])
        case={'readings':dict(reading_counts[key]),'lost_forms':len(forms[key]),
            'removed_definition_classes':classes(before-after),'added_definition_classes':classes(after-before),
            'quantity_only_definition_pairs':review.quantity_only_pairs(before-after,after-before),
            'source_join':'unique_article' if len(choices)==1 else 'ambiguous_articles' if choices else 'no_article_join'}
        detail={'lemma':key,'baseline_definitions':dossier['baseline_definitions'],'final_definitions':dossier['final_definitions']}
        if len(choices)==1:
            choice=next(iter(choices.values()));row=choice['row'];entry=choice['entry']
            if dossier['articles'][0]['header']!=row:raise ValueError('loss source header differs')
            replay_target=target/('replay-'+str(number));replay_target.mkdir(mode=0o700)
            replayed,_=review.isolated_replay(row,lemma,args.filters,args.diagnostic_filter,replay_target)
            raw_final=selected_tokens(candidate,lemma);full_diagnostic=selected_tokens(diagnostic,lemma)
            identity=review.source_key(row)==lemma
            branch,expected=review.source_expectations(row) if identity else ('different_literal_headword',Counter())
            leads=surface_leads(entry,forms[key],first.review.projection.normalize)
            lead_counts=[{'route':route,'match':match,'forms':len(values)} for (route,match),values in sorted(leads.items())]
            for tag,values in leads.items():surface_totals[tag]+=len(values)
            case.update({'source_header_sha256':review.probe.digest(json.dumps(row,sort_keys=True).encode()),
                'source_partition':choice['partition'],'literal_headword_identity':identity,
                'source_grammar_shape':review.source_grammar_shape(row),'source_recipe':branch,
                'expected_source_directives':sum(expected.values()),
                'missing_recipe_directives_in_raw_candidate':sum((expected-raw_final).values()) if expected else None,
                'recipe_matches_raw_candidate':bool(expected) and expected==raw_final,
                'isolated_selected_directives':sum(replayed.values()),
                'isolated_matches_full_diagnostic_multiset':replayed==full_diagnostic,
                'isolated_matches_raw_candidate_multiset':replayed==raw_final,
                'surface_leads':lead_counts})
            detail.update({'source_header':row,'replayed':[{'tokens':[t.decode() for t in tokens],'multiplicity':n} for tokens,n in sorted(replayed.items())],
                'source_surface_leads':[{'route':route,'match':match,'forms':[f.decode() for f in sorted(values)]} for (route,match),values in sorted(leads.items())]})
        groups[(case['source_join'],case.get('source_partition','unclassified'),case.get('source_recipe','not_evaluated'))]+=1
        cases.append(case);private.append(detail)
    payload=b''.join((json.dumps(row,sort_keys=True)+'\n').encode() for row in private)
    review.probe.write_private(target/'source-review.jsonl',payload)
    if any(reproduction.native.digest(p)!=receipts[n] for n,p in paths.items()):raise ValueError('changed-definition review changed an input')
    return {'schema':1,'scope':'59 changed-definition complete-loss lemmas; source/replay and surface leads only, no automatic lexical repair',
        'input_sha256':receipts,'changed_definition_lemmas':59,'lost_readings':5547,
        'groups':loss.grouped(groups,('source_join','source_partition','source_recipe')),
        'surface_lead_counts':loss.grouped(surface_totals,('route','match')),
        'surface_scope':'whole full orthographies, Latin-labelled quotation tokens and whole references only; notation leads are not literal identity; citation occurrence is not lemma/grammar attribution',
        'anonymous_cases':cases,'private_source_review_sha256':review.probe.digest(payload),'original_inputs_unchanged':True}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('dossier','headers','tei','candidate','diagnostic','filters','diagnostic-filter','output'):p.add_argument('--'+n,type=Path,required=True)
    previous=os.umask(0o077)
    try:report=prepare(p.parse_args())
    finally:os.umask(previous)
    print(json.dumps({'latin_changed_definition_source_review':report},sort_keys=True))


if __name__=='__main__':main()
