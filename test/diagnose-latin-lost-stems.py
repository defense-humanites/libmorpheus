#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/diagnose-latin-lost-stems.py'
spec = importlib.util.spec_from_file_location('losses', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def reading(lemma=b'zzlemma', stem=b'zzstem', preverb=b'', pos=2, tense=1):
    return SimpleNamespace(workword=b'zzform', lemma=lemma, part_of_speech=pos,
        person=1, number=1, gender=0, grammatical_case=0, tense=tense, mood=4, voice=1,
        degree=0, stem=stem, suffix=b'', ending=b'o', preverb=preverb, raw_preverb=preverb)


def loss(form, rows):
    signatures=m.Counter(m.signature(r) for r in rows)
    return {'form':form, 'curated_count':len(rows), 'rebuilt_count':0, 'retained_rows':0, 'added':[],
            'removed':[{'signature':[m.decoded(v) for v in sig], 'multiplicity':n} for sig,n in signatures.items()]}


class Analyzer:
    def __init__(self, values): self.values, self.calls = values, []
    def analyses(self, word, require_untruncated=False):
        if not require_untruncated: raise AssertionError('must check diagnostic text truncation')
        self.calls.append(word)
        value=self.values.get(word, [])
        if isinstance(value, Exception): raise value
        return value


class LossDiagnostics(unittest.TestCase):
    def test_full_losses_reprobe_multiplicity_membership_and_private_dossiers(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory); diff=p/'differences'
            a=reading(); b=reading(b'zzother', b'zzroot', b'ex', tense=5)
            diff.write_text(json.dumps(loss('zzform',[a,a,b]))+'\n'+json.dumps(
                {'form':'unchanged_count', 'curated_count':1, 'rebuilt_count':1})+'\n')
            old={b'zzlemma':m.Counter({b':vs:zzstem conj3':2}), b'zzother':m.Counter({b':vs:zzroot perfstem':1})}
            new={b'zzlemma':m.Counter({b':vs:zzstem conj3':1})}
            source={b'zzlemma':{'entry1':{'id':'entry1'}, 'entry2':{'id':'entry2'}},
                    b'zzother':{'entry3':{'id':'entry3','partition':'verbal'}}}
            left,right=Analyzer({b'zzform':[a,a,b]}),Analyzer({})
            output=io.StringIO()
            report=m.diagnose(diff,left,right,old,new,{b'zzlemma'}, {b'zzother'},source,output,lambda x:x)
            self.assertEqual(report['counts'], {'forms':1,'readings':3,'distinct_lemmas':2,'nonverbal_readings':0})
            self.assertEqual(report['definition_states']['readings'], {'changed_definition_multisets':2,'no_final_definitions':1})
            self.assertEqual(report['stem_matches_by_readings'], {'baseline_exact__final_exact':2,'baseline_exact__final_no_exact':1})
            self.assertEqual(report['source_joins']['readings'],{'ambiguous_articles':2,'unique_article':1})
            self.assertEqual(report['source_partitions']['readings'],{'ambiguous_articles':2,'verbal':1})
            self.assertEqual(sum(r['rows'] for r in report['reading_groups']),3)
            self.assertEqual(left.calls,[b'zzform']); self.assertEqual(right.calls,left.calls)
            public=json.dumps(report)
            for value in ('zzform','zzlemma','zzstem','entry1'): self.assertNotIn(value,public)
            dossiers=[json.loads(l) for l in output.getvalue().splitlines()]
            self.assertEqual(len(dossiers),3)
            self.assertEqual(len(dossiers[0]['readings']),3)
            self.assertEqual(dossiers[1]['baseline_definitions'][0]['multiplicity'],2)
            self.assertEqual(len(dossiers[1]['articles']),2)

    def test_stem_matching_distinguishes_exact_notation_lead_and_unmatched(self):
        old=m.Counter({b':vs:zz-st_e^m conj3':1, b':de:zzroot are_vb':1})
        new=m.Counter({b':vs:zzstem conj3':1})
        self.assertEqual(m.stem_match(b'zzstem',old,new),'baseline_notation_lead__final_notation_lead')
        self.assertEqual(m.stem_match(b'zzroot',old,new),'baseline_exact__final_no_exact')
        self.assertEqual(m.stem_match(b'zzmissing',old,new),'baseline_stem_unmatched')
        self.assertEqual(m.definition_state(m.Counter(),m.Counter()),'no_definitions_in_either')
        self.assertEqual(m.definition_state(old,old),'equal_definition_multisets')

    def test_literal_definitions_preserve_homographs_flags_whitespace_and_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'source'
            source.write_bytes(b'# preamble\n:vs:ignored conj3\n:le:zzlemma#2\r\n:vs:zzroot\tconj3 orth\r\n'
                b':vs:zzroot\tconj3 orth\n:vs:zzroot conj3\n@ extra flags\n:le:zzlemma\n')
            records=m.definitions(source)
            self.assertEqual(set(records),{b'zzlemma#2',b'zzlemma'})
            self.assertEqual(records[b'zzlemma#2'][b':vs:zzroot\tconj3 orth'],2)
            self.assertEqual(sum(records[b'zzlemma#2'].values()),4)
            self.assertEqual(m.tokens(records[b'zzlemma#2']),{b'zzroot'})

    def test_source_routes_preserve_multiple_articles_and_homograph_identity(self):
        rows=[{'id':'one','lemma':'zzkey#2','headword':'zz-he_ad#2','projection_error':None},
              {'id':'two','lemma':'zzhead#2','headword':'zzother#2','projection_error':None},
              {'id':'bad','lemma':None,'headword':None,'projection_error':'unsupported'}]
        sources=m.source_index(rows,{'one':object(),'two':object()},lambda r:('nominal','synthetic'))
        self.assertEqual(set(sources[b'zzhead#2']),{'one','two'})
        self.assertNotIn(b'zzhead',sources)
        self.assertEqual(sources[b'zzkey#2']['one']['join_routes'],['projected_key'])
        self.assertEqual(sources[b'zzkey#2']['one']['partition'],'nominal')

    def test_changed_native_counts_signatures_api_errors_or_candidate_coverage_abort(self):
        with tempfile.TemporaryDirectory() as directory:
            diff=Path(directory)/'diff'; a=reading(); diff.write_text(json.dumps(loss('zzform',[a]))+'\n')
            for before,after in [([],[]),([reading(b'other')],[]),([a],[a]),(ValueError('native failed'),[])]:
                with self.assertRaises(ValueError):
                    m.diagnose(diff,Analyzer({b'zzform':before}),Analyzer({b'zzform':after}),{}, {},set(),set(),{},io.StringIO(),lambda x:x)

    def test_duplicate_or_inconsistent_lost_records_abort(self):
        with tempfile.TemporaryDirectory() as directory:
            diff=Path(directory)/'diff'; a=reading(); record=loss('zzform',[a])
            for records in ([record,record],[dict(record,retained_rows=1)],
                            [dict(record,removed=[dict(record['removed'][0],multiplicity=0)])]):
                diff.write_text(''.join(json.dumps(r)+'\n' for r in records))
                with self.assertRaises(ValueError):
                    m.diagnose(diff,Analyzer({b'zzform':[a]}),Analyzer({}),{}, {},set(),set(),{},io.StringIO(),lambda x:x)

    def test_private_repository_input_ancestor_and_symlink_guards(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory); source=p/'input'; source.mkdir()
            for target in (SCRIPT.parent/'private',source,source/'private',p):
                with self.assertRaises(ValueError): m.private_target(target,[source])
            link=p/'link'; link.symlink_to(p/'absent')
            with self.assertRaises(FileExistsError): m.private_target(link,[source])
            self.assertEqual(m.private_target(p/'private',[source]),(p/'private').resolve())

    def test_global_difference_receipt_is_required_before_source_or_native_loading(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory); (p/'baseline-to-final-global.jsonl').write_bytes(b'')
            (p/'report.json').write_text(json.dumps({'global_comparisons':{'baseline-to-final-global':{'private_difference_sha256':'wrong'}}}))
            with self.assertRaisesRegex(ValueError,'receipt differs'):
                m.prepare(SimpleNamespace(comparison_dir=p,baseline=p,candidate=p,expected_difference_sha256=None))


if __name__ == '__main__': unittest.main()
