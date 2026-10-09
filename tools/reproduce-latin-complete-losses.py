#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reproduce the pinned global loss dossier without other research trials."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

spec=importlib.util.spec_from_file_location('candidate',Path(__file__).with_name('qualify-latin-historical-source-candidate.py'))
candidate=importlib.util.module_from_spec(spec);spec.loader.exec_module(candidate)
native=candidate.native
loss=candidate.review.sibling('diagnose-latin-lost-stems')
DIFFERENCE_SHA='08f0aca20f35eecf95f24a50690ad91a35a139663f558570d9ea86ea07f8bd52'
DOSSIER_SHA='a4be9ccc97383f48f4ba94bc4e23092e17b729a685eb01c5242d2bfac9c4ba1a'


def prepare(args):
    if native.digest(args.candidate)!=candidate.CANDIDATE_SHA or native.digest(args.forms)!=candidate.FORMS_SHA:
        raise ValueError('complete-loss reproduction input receipt differs')
    target=loss.private_target(args.output,[args.candidate,args.forms,args.baseline,args.headers,args.tei,args.library,args.tools])
    target.mkdir(mode=0o700)
    baseline={n:native.digest(args.baseline/'Latin/steminds'/n) for n in candidate.INDEXES}
    indexes=native.build_trial(args.baseline,args.candidate,args.tools,target/'candidate')
    if indexes!=candidate.INDEXES:raise ValueError('complete-loss candidate indexes differ')
    readers={}
    try:
        readers['baseline']=candidate.supines.direct.StrictRows(args.library,args.baseline)
        readers['candidate']=candidate.supines.direct.StrictRows(args.library,target/'candidate')
        report=candidate.supines.direct.audit.audit(args.forms,readers['baseline'],readers['candidate'],
            target/'baseline-to-final-global.jsonl',candidate.supines.direct.audit.source_lemmas(args.candidate))
    finally:
        for reader in readers.values():reader.close()
    if (report['private_difference_sha256']!=DIFFERENCE_SHA or report['counts']['distinct_forms']!=1033579 or
        report['analysis_rows']!={'curated':2048328,'rebuilt':2100530}):
        raise ValueError('complete-loss global reproduction differs')
    native.write_private(target/'report.json',(json.dumps({'global_comparisons':{'baseline-to-final-global':report},
        'input_sha256':{'bounded-present':candidate.CANDIDATE_SHA}},sort_keys=True)+'\n').encode())
    dossier=target/'loss-dossier.jsonl'
    diagnostic=loss.prepare(SimpleNamespace(comparison_dir=target,baseline=args.baseline,candidate=target/'candidate',
        candidate_source=args.candidate,headers=args.headers,lexica=args.tei,library=args.library,private_output=dossier,
        expected_forms=6789,expected_lemmas=133,expected_rows=11005,expected_difference_sha256=DIFFERENCE_SHA))
    if native.digest(dossier)!=DOSSIER_SHA:raise ValueError('complete-loss source dossier differs')
    if any(native.digest(args.baseline/'Latin/steminds'/n)!=baseline[n] for n in baseline) or native.digest(args.candidate)!=candidate.CANDIDATE_SHA:
        raise ValueError('complete-loss reproduction changed an input')
    return {'schema':1,'scope':'exact reproduction of original complete losses; no source repair or promotion',
        'global_comparison':report,'loss_diagnostic':diagnostic,'original_inputs_unchanged':True}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('candidate','forms','baseline','headers','tei','library','tools','output'):p.add_argument('--'+n,type=Path,required=True)
    previous=os.umask(0o077)
    try:report=prepare(p.parse_args())
    finally:os.umask(previous)
    print(json.dumps({'latin_complete_loss_reproduction':report},sort_keys=True))


if __name__=='__main__':main()
