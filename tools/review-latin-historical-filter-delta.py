#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Review the pinned one-lemma lexer delta privately; print categories only."""
import argparse
from collections import Counter
import importlib.util
import json
import os
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[1]


def sibling(name):
    spec=importlib.util.spec_from_file_location(name,REPO/'tools'/(name+'.py'))
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj


probe=sibling('probe-latin-historical-filter-portability')
RECEIPTS={
    'reference':'22196e561a802c607249597b767652b3c0f9ad797b3155a22ec11c61875c8479',
    'diagnostic':'8f234062ffeaf58e15ceabe3c8a8f5ff2ea37ef0c62d90659ea5db581a5c85de',
    'delta':'258e211210c33e223fe3055c7c21e3a9c834f51d5e27e1ff4332d900dd2d4622',
    'headers':'85658956fa68024d032f944f7920d38fa8b424318be6454eebdb6bd74c76cc34',
    'tei':'ccbd2f79db1006edc607fe51227babab6872fbdaa4e925f4c1999a3b978041ee'}


def classify(line):
    tokens=line.split(); prefix=tokens[0][:4]; fields=set(tokens[1:])
    if prefix==b':de:':return 'derivation'
    if prefix==b':vb:':return 'literal_verbal_word'
    if prefix==b':wd:':return 'literal_word'
    kinds=[]
    if fields & {b'conj1',b'conj2',b'conj3',b'conj3_io',b'conj4'}:kinds.append('present')
    if fields & {b'perfstem',b'avperf',b'evperf',b'ivperf'}:kinds.append('perfect')
    if b'pp4' in fields:kinds.append('supine')
    return kinds[0] if len(kinds)==1 else 'conflicting' if kinds else 'unclassified'


def source_key(row):
    head=row.get('headword','')
    if row.get('projection_error') is not None or not re.fullmatch(r'[A-Za-z_^#0-9-]+',head):
        return None
    # Exact historical lemma spelling: remove notation, preserve case and digits.
    return head.translate(str.maketrans('','','_^-')).encode('ascii')


def source_expectations(row):
    fields=[(i,f['projection']) for i,f in enumerate(row['fields']) if f['name']=='itype']
    if not fields or any(b[0]!=a[0]+1 for a,b in zip(fields,fields[1:])):
        return 'unclassified',Counter()
    # combitype joins only adjacent itype fields. Preserve all source quantities.
    grammar=', '.join(value for _,value in fields)
    # A literal compound boundary supplies the prefix; do not infer it from
    # the historical backwards search for a consonant. Both alternatives in
    # each principal-part slot remain source expectations.
    compound=re.fullmatch(r'([A-Za-z_^]+)-([A-Za-z_^]+)o',row['headword'])
    alternatives=re.fullmatch(r'([A-Za-z_^]+i) or ([A-Za-z_^]+i), ([A-Za-z_^]+um) or ([A-Za-z_^]+um), 3',grammar)
    if compound and alternatives:
        parts=alternatives.groups();base=compound[2];prefix=compound[1]+'-'
        if (all(part[0]==base[0] for part in parts) and base[0] not in 'aeioux'
                and parts[0]!=parts[1] and parts[2]!=parts[3]):
            expected=[((':vs:'+prefix+base).encode(),b'conj3')]
            expected.extend(((':vs:'+prefix+part[:-1]).encode(),b'perfstem') for part in parts[:2])
            expected.extend(((':vs:'+prefix+part[:-2]).encode(),b'pp4') for part in parts[2:])
            return 'explicit_compound_two_perfects_two_supines',Counter(expected)
    match=re.fullmatch(r'(i_vi|i\^i|ii),? (?:or|and) (i_vi|i\^i|ii), (?:(i_tum|i\^tum), )?(?:4|i_re)',grammar)
    if not match or match[1]==match[2] or 'i_vi' not in (match[1],match[2]):
        return 'unclassified',Counter()
    head=row['headword'].split('#')[0]
    if not head or head[-1].isdigit():return 'unclassified',Counter()
    stem=None
    for suffix in ('i^or','e^or','i^o','e^o','ior','eor','or','eo','it','et','io'):
        if head.endswith(suffix):stem=head[:-len(suffix)];break
    if stem is None:stem=head[:-1]
    expected=[((':vs:'+stem).encode(),b'conj4')]
    expected.extend(((':vs:'+stem+part[:-1]).encode(),b'perfstem') for part in (match[1],match[2]))
    if match[3]:expected.append(((':vs:'+stem+match[3][:-2]).encode(),b'pp4'))
    return 'alternative_perfect_with_supine' if match[3] else 'alternative_perfect_without_supine',Counter(expected)


def quantity_only_pairs(missing,extra):
    def key(tokens):
        return (tokens[0].translate(None,b'_^'),)+tokens[1:]
    left,right=Counter(),Counter()
    for tokens,n in missing.items():left[key(tokens)]+=n
    for tokens,n in extra.items():right[key(tokens)]+=n
    return sum((left&right).values())


def source_grammar_shape(row):
    """Only fixed structural categories and a receipt, never source tokens."""
    fields=[f['projection'] for f in row['fields'] if f['name']=='itype']
    grammar=', '.join(fields)
    parts=re.split(r',\s*|\s+(?:or|and)\s+',grammar)
    return {
        'itype_fields':len(fields),
        'bare_fourth_conjugation_fields':sum(v in {'4','i_re','i_re, 4'} for v in fields),
        'fields_with_alternative_connector':sum(bool(re.search(r'\b(?:or|and)\b',v)) for v in fields),
        'grammar_sha256':probe.digest(grammar.encode('utf-8')),
        'comma_separated_segments':len(grammar.split(',')),
        'principal_part_like_tokens':sum(bool(re.fullmatch(r'[A-Za-z_^]+',v)) for v in parts),
        'tokens_with_quantity_marks':sum(bool(re.search(r'[_^]',v)) for v in parts),
        'terminal_conjugation_digit':int(grammar[-1]) if re.search(r'(?:^|,\s*)[1-4]$',grammar) else None,
    }


def isolated_replay(row,lemma,filters,diagnostic_filter,target):
    recovery=sibling('recover-latin-initial-sense')
    data=recovery.render(row).encode('utf-8')
    known_types={b'i_vi, or i^i, i_tum, 4',b'i_vi, or i^i, 4'}
    for name in ('combitype','splitlat','conj1'):
        data=probe.run_private([str(filters/name)],target,'replay-'+name,data)
    branch_rows=sum(value in known_types for value in re.findall(rb'<itype>([^<]+)</itype>',data))
    data=probe.run_private([str(diagnostic_filter)],target,'replay-latvb',data)
    selected=Counter()
    for (key,line),n in probe.definitions(data).items():
        if key==lemma:selected[tuple(line.split())]+=n
    return selected,branch_rows


def validate_delta(data,left,right):
    records={'removed':Counter(),'added':Counter()}
    for line in data.splitlines():
        row=json.loads(line)
        if (set(row)!={'change','lemma','directive','multiplicity'} or row['change'] not in records or
                type(row['multiplicity']) is not int or row['multiplicity']<=0):
            raise ValueError('invalid private delta record')
        key=(row['lemma'].encode('ascii'),row['directive'].encode('ascii'))
        if key in records[row['change']]:raise ValueError('duplicate private delta record')
        records[row['change']][key]=row['multiplicity']
    if records['removed']!=left-right or records['added']!=right-left:
        raise ValueError('private delta differs from received raw outputs')
    return records


def prepare(args):
    paths={n:getattr(args,n) for n in RECEIPTS}
    original={n:p.read_bytes() for n,p in paths.items()}
    if any(probe.digest(data)!=RECEIPTS[n] for n,data in original.items()):
        raise ValueError('historical delta review receipt differs')
    metrics,left,right=probe.compare(original['reference'],original['diagnostic'])
    delta=validate_delta(original['delta'],left,right)
    changed={lemma for records in delta.values() for lemma,_ in records}
    if len(changed)!=1 or metrics['removed_rows']!=1 or metrics['added_rows']!=2:
        raise ValueError('historical delta inventory differs')
    first=sibling('repair-latin-first-conjugation')
    rows,_,_=first.source_rows(args.headers,args.tei) # Revalidate against the actual pinned TEI.
    lemma=next(iter(changed));matches=[r for r in rows if source_key(r)==lemma]
    if len(matches)!=1:raise ValueError('changed lemma needs one literal source join')
    row=matches[0];branch,expected=source_expectations(row)
    after=Counter()
    for (key,line),n in right.items():
        if key==lemma:after[tuple(line.split())]+=n
    missing=expected-after;extra=after-expected if expected else after
    classes={}
    for label,records in delta.items():
        counts=Counter()
        for (_,line),n in records.items():counts[classify(line)]+=n
        classes[label]=dict(sorted(counts.items()))
    target=first.private_target(args.reference,args.headers,args.tei,args.output)
    target.mkdir(mode=0o700)
    replayed,backend_branches=isolated_replay(row,lemma,args.filters,args.diagnostic_filter,target)
    dossier={'lemma':lemma.decode(),'source_header':row,'source_branch':branch,
             'before':[{'directive':line.decode(),'multiplicity':n} for (key,line),n in sorted(left.items()) if key==lemma],
             'after':[{'directive':line.decode(),'multiplicity':n} for (key,line),n in sorted(right.items()) if key==lemma],
             'expected':[{'tokens':[t.decode() for t in tokens],'multiplicity':n} for tokens,n in sorted(expected.items())]}
    payload=(json.dumps(dossier,sort_keys=True)+'\n').encode()
    probe.write_private(target/'source-review.jsonl',payload)
    if any(p.read_bytes()!=original[n] for n,p in paths.items()):raise ValueError('source review changed an input')
    return {'schema':1,'scope':'one-lemma source consistency review; no lexical promotion or candidate substitution',
        'input_sha256':{n:probe.digest(v) for n,v in original.items()},'changed_lemmas':1,
        'delta_classes':classes,'literal_source_header_matches':1,'source_branch':branch,
        'expected_source_directives':sum(expected.values()),'missing_source_directives':sum(missing.values()),
        'extra_diagnostic_directives':sum(extra.values()),
        'source_quantity_only_difference_pairs':quantity_only_pairs(missing,extra),
        'source_header_shape':source_grammar_shape(row),
        'isolated_source_backend_alternative_type_rows':backend_branches,
        'isolated_source_selected_directives':sum(replayed.values()),
        'isolated_source_reproduces_full_diagnostic_multiset':replayed==after,
        'diagnostic_matches_bounded_source_recipe':bool(expected) and not missing and not extra,
        'private_source_review_sha256':probe.digest(payload),'original_inputs_unchanged':True}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in (*RECEIPTS,'output','filters','diagnostic-filter'):p.add_argument('--'+n,type=Path,required=True)
    previous=os.umask(0o077)
    try:report=prepare(p.parse_args())
    finally:os.umask(previous)
    print(json.dumps({'latin_historical_filter_source_review':report},sort_keys=True))


if __name__=='__main__':main()
