#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay the qualified letters-only stages privately from pinned raw output."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
spec=importlib.util.spec_from_file_location('review',Path(__file__).with_name('review-latin-historical-filter-delta.py'))
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
STEPS=[
  [
    "repair-latin-first-conjugation",
    "",
    50,
    [
      "--tier",
      "letters-only"
    ]
  ],
  [
    "repair-latin-principal-parts",
    "parts",
    2,
    []
  ],
  [
    "repair-latin-principal-parts",
    "allomorphs",
    20,
    [
      "--proof-tier",
      "source-allomorphs"
    ]
  ],
  [
    "recover-latin-ingo-parts",
    "ingo",
    1,
    []
  ],
  [
    "recover-latin-full-alternates",
    "alternates",
    131,
    []
  ],
  [
    "recover-latin-second-supines",
    "supines",
    4,
    []
  ],
  [
    "recover-latin-full-alternates",
    "fourth-alternates",
    2,
    [
      "--tier",
      "fourth-explicit-perfect"
    ]
  ],
  [
    "repair-latin-jicio-parts",
    "jicio",
    18,
    []
  ],
  [
    "recover-latin-regular-parts-alternates",
    "regular-alternates",
    18,
    []
  ],
  [
    "recover-latin-combined-fourth-parts",
    "combined-supine",
    1,
    []
  ],
  [
    "recover-latin-combined-fourth-parts",
    "combined-perfect",
    1,
    [
      "--tier",
      "perfect-only"
    ]
  ],
  [
    "recover-latin-regular-parts-alternates",
    "terminal-alternates",
    3,
    [
      "--tier",
      "terminal-delimiter"
    ]
  ],
  [
    "recover-latin-regular-parts-alternates",
    "present-alternates",
    4,
    [
      "--tier",
      "present-only"
    ]
  ],
  [
    "recover-latin-regular-parts-alternates",
    "inchoative-present",
    4,
    [
      "--tier",
      "inchoative-present"
    ]
  ],
  [
    "recover-latin-regular-parts-alternates",
    "velar-present",
    3,
    [
      "--tier",
      "velar-present"
    ]
  ],
  [
    "recover-latin-untagged-inchoative-present",
    "untagged-inchoative",
    1,
    []
  ],
  [
    "recover-latin-velar-suffix",
    "velar-suffix",
    1,
    []
  ],
  [
    "recover-latin-cited-present",
    "cited-present",
    11,
    []
  ],
  [
    "recover-latin-cited-present",
    "cited-future-imperative",
    4,
    [
      "--evidence",
      "future-imperative"
    ]
  ],
  [
    "recover-latin-boundary-present",
    "boundary-present",
    11,
    []
  ],
  [
    "recover-latin-vowel-present",
    "vowel-present",
    4,
    []
  ],
  [
    "recover-latin-backlinked-present",
    "backlinked-present",
    9,
    []
  ],
  [
    "recover-latin-coordinated-present",
    "coordinated-present",
    1,
    []
  ],
  [
    "recover-latin-bounded-present-spellings",
    "bounded-present",
    5,
    []
  ]
]

def prepare(args):
    paths={'reference':args.reference,'headers':args.headers,'tei':args.tei}
    if any(review.probe.digest(p.read_bytes())!=review.RECEIPTS[n] for n,p in paths.items()):
        raise ValueError('candidate reconstruction input receipt differs')
    first=review.sibling('repair-latin-first-conjugation')
    target=first.private_target(args.reference,args.headers,args.tei,args.output)
    target.mkdir(mode=0o700)
    current=args.reference;receipts=[]
    for number,(tool,suffix,expected,extra) in enumerate(STEPS):
        output=target/('stage-'+str(number)+'.stems')
        run=subprocess.run([sys.executable,str(Path(__file__).with_name(tool+'.py')),
            '--candidate',str(current),'--headers',str(args.headers),'--lexica',str(args.tei),
            '--private-output',str(output),'--expected',str(expected),*extra],capture_output=True)
        review.probe.write_private(target/('stage-'+str(number)+'.log'),run.stdout+run.stderr)
        if run.returncode:raise ValueError('private candidate reconstruction stage failed: '+str(number))
        receipts.append({'stage':number,'sha256':review.probe.digest(output.read_bytes())})
        current=output
    digest=review.probe.digest(current.read_bytes())
    if digest!='6caf089d03e62d745aebc94d1b1cc5cf06938626db4af8c794a2326ca7a94cd9':
        raise ValueError('reconstructed candidate differs from qualified source')
    review.probe.write_private(target/'candidate.stems',current.read_bytes())
    if any(review.probe.digest(p.read_bytes())!=review.RECEIPTS[n] for n,p in paths.items()):
        raise ValueError('candidate reconstruction changed an input')
    return {'schema':1,'stages':receipts,'candidate_source_sha256':digest,'original_inputs_unchanged':True}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('reference','headers','tei','output'):p.add_argument('--'+name,type=Path,required=True)
    previous=os.umask(0o077)
    try:report=prepare(p.parse_args())
    finally:os.umask(previous)
    print(json.dumps({'latin_qualified_candidate_reconstruction':report},sort_keys=True))
if __name__=='__main__':main()

