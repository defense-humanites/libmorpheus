#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from collections import Counter
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

spec=importlib.util.spec_from_file_location('direct',Path(__file__).resolve().parents[1]/'tools/qualify-latin-direct-present-control.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
BUILD=Path(sys.argv.pop(1)).resolve()
LIBRARY=BUILD/('libmorpheus.dylib' if sys.platform=='darwin' else 'libmorpheus.so')


class NativeDirectControl(unittest.TestCase):
    def test_not_in_comp_preserves_thirteen_direct_cells_and_disables_composition(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); readers={}
            try:
                data=b':le:zzsyntheticzo#2\n:vs:zzsyntheticz conj1\n'
                for name,payload in (('open',data),('restricted',m.restricted_payload(data,b'zzsyntheticzo#2'))):
                    source=root/(name+'.stems'); source.write_bytes(payload)
                    m.native.build_trial(BUILD/'stemlib-production/latin',source,BUILD,root/name)
                    readers[name]=m.StrictRows(LIBRARY,root/name)
                forms=['zzsyntheticz'+s for s in ('o','as','at','amus','atis','ant','em','es','et','emus','etis','ent','are')]
                composed=0
                for word in forms:
                    left=readers['open'].analyses(word.encode(),require_untruncated=True)
                    right=readers['restricted'].analyses(word.encode(),require_untruncated=True)
                    self.assertTrue(left); self.assertEqual(Counter(map(m.route,left)),Counter(map(m.route,right)))
                    original=[r for r in readers['open'].analyses(('re'+word).encode(),require_untruncated=True)
                              if r.lemma==b're-zzsyntheticzo#2' and r.preverb==b're']
                    changed=[r for r in readers['restricted'].analyses(('re'+word).encode(),require_untruncated=True)
                             if r.lemma==b're-zzsyntheticzo#2' and r.preverb==b're']
                    composed+=len(original); self.assertEqual(changed,[])
                self.assertGreater(composed,0)
            finally:
                for reader in readers.values():reader.close()
            # Exercise rebuilding from an already built trial: the copied
            # intermediate files must not collide with exclusive writes.
            family=[]
            for i,word in enumerate(forms):
                family.append({'kind':'source_present_family','lemma':'zzsyntheticzo#2','form':word,
                    'person':i%6%3+1 if i<12 else 0,'number':1 if i%6<3 else 3,
                    'mood':4 if i<6 else 8 if i<12 else 5,'voice':1})
            family[-1]['number']=0
            family_path=root/'family.jsonl'; family_path.write_text(''.join(json.dumps(c)+'\n' for c in family))
            forms_path=root/'forms'; forms_path.write_text('\n'.join(sorted(forms+['re'+w for w in forms]))+'\n')
            candidate_source=root/'candidate.stems'; candidate_source.write_bytes(b'')
            inputs={'source':root/'open.stems','family':family_path,'forms':forms_path,'candidate_source':candidate_source}
            args=SimpleNamespace(**inputs,**{'expected_'+n+'_sha256':m.loss.digest(p) for n,p in inputs.items()},
                candidate=BUILD/'stemlib-production/latin',opened=root/'open',tools=BUILD,library=LIBRARY,
                output=root/'complete-control',expected_forms=26,
                expected_vbind_sha256=m.loss.digest(root/'open/Latin/steminds/vbind'),
                expected_vside_sha256=m.loss.digest(root/'open/Latin/steminds/vbind.lindex'))
            report=m.prepare(args)
            self.assertTrue(report['original_candidate_and_open_trial_unchanged'])
            self.assertEqual(report['source_family_control']['cells_unchanged'],13)
            self.assertEqual(report['global_comparisons']['candidate_to_restricted']['global_eleven_field_multisets'].get('removed_rows',0),0)
            self.assertEqual(report['global_comparisons']['open_to_restricted']['global_eleven_field_multisets']['removed_rows'],composed)


if __name__=='__main__':
    unittest.main()
