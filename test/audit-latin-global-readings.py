#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/audit-latin-global-readings.py'
spec = importlib.util.spec_from_file_location('global_readings', SCRIPT)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


def row(lemma=b'synthetic', pos=2, tense=1, person=1, preverb=b''):
    return ((b'workword', lemma, pos, person, 1, 0, 0, tense, 4, 1, 0), preverb)


class Analyzer:
    def __init__(self, rows): self.values, self.calls = rows, []
    def rows(self, word):
        self.calls.append(word)
        value = self.values.get(word, [])
        if isinstance(value, Exception): raise value
        return value


class GlobalReadings(unittest.TestCase):
    def test_full_matrix_equal_count_changes_multiplicities_and_loss_groups(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory); forms=p/'forms'; forms.write_bytes(b'a\nb\nc\nd\ne\n')
            direct=row(b'source', tense=5); prefix=row(b'other', preverb=b'ex')
            old=Analyzer({b'a':[direct,direct,prefix], b'b':[row()], b'c':[row(pos=1)]})
            new=Analyzer({b'b':[row(),row(person=2)], b'c':[row(b'changed',pos=1)], b'd':[row(pos=1)]})
            report=g.audit(forms,old,new,p/'private',{b'source'})
            self.assertEqual(report['counts'], {'absent_curated__absent_rebuilt':1,
                'absent_curated__recognized_rebuilt':1,'distinct_forms':5,'input_lines':5,
                'recognized_curated__absent_rebuilt':1,'recognized_curated__recognized_rebuilt':2})
            self.assertEqual(report['analysis_rows'], {'curated':5,'rebuilt':4})
            self.assertEqual(report['global_eleven_field_multisets'], {'added_rows':3,'removed_rows':4,'retained_rows':1})
            self.assertEqual(report['changed_analysis_counts'],3)
            self.assertEqual(report['changed_grammatical_multisets'],4)
            self.assertEqual(report['changed_multisets_at_equal_counts'],1)
            self.assertEqual(report['lost_forms_diagnostic']['distinct_lemmas_by_pos'],{'2':2})
            groups=report['lost_forms_diagnostic']['rows_by_pos_tense_provenance_source_membership']
            self.assertEqual(sum(r['rows'] for r in groups),3)
            self.assertEqual({r['lemma_membership']:r['rows'] for r in groups},
                {'in_substituted_verbal_source':2,'outside_substituted_verbal_source':1})
            records=[json.loads(l) for l in (p/'private').read_text().splitlines()]
            self.assertEqual(len(records),4)
            self.assertEqual(records[2]['curated_count'],records[2]['rebuilt_count'])
            self.assertNotIn('synthetic',json.dumps(report)); self.assertNotIn('changed',json.dumps(report['lost_forms_diagnostic']))
            self.assertEqual((p/'private').stat().st_mode & 0o777,0o600)

    def test_control_compares_multisets_without_dependence_on_order(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory); forms=p/'forms'; forms.write_bytes(b'x\n')
            a,b=row(),row(person=2)
            report=g.audit(forms,Analyzer({b'x':[a,a,b]}),Analyzer({b'x':[b,a,a]}),p/'private',require_identical=True)
            self.assertEqual(report['changed_grammatical_multisets'],0)
            self.assertEqual(report['global_eleven_field_multisets'],{'added_rows':0,'removed_rows':0,'retained_rows':3})
            self.assertEqual((p/'private').read_bytes(),b'')

    def test_control_rejects_replaced_readings_even_when_count_is_equal(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory); forms=p/'forms'; forms.write_bytes(b'x\n')
            with self.assertRaisesRegex(ValueError,'control differs'):
                g.audit(forms,Analyzer({b'x':[row()]}),Analyzer({b'x':[row(person=2)]}),p/'private',require_identical=True)

    def test_mixed_preverb_provenance_does_not_assign_unmatched_occurrences(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory); forms=p/'forms'; forms.write_bytes(b'x\n')
            report=g.audit(forms,Analyzer({b'x':[row(),row(preverb=b'ex')]}),Analyzer({b'x':[row()]}),p/'private',set())
            removed=report['delta_rows_by_pos_tense_provenance']['removed']
            self.assertEqual(removed,[{'part_of_speech':2,'tense':1,'provenance':'mixed','rows':1}])

    def test_blank_duplicate_literal_input_and_input_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory); forms=p/'forms'; data=b'x\r\n\nx\ny\n'; forms.write_bytes(data)
            left,right=Analyzer({}),Analyzer({})
            report=g.audit(forms,left,right,p/'private')
            self.assertEqual(report['counts']['input_lines'],4)
            self.assertEqual(report['counts']['distinct_forms'],2)
            self.assertEqual(report['counts']['blank_lines'],1)
            self.assertEqual(report['counts']['duplicate_lines'],1)
            self.assertEqual(report['input_sha256'],g.hashlib.sha256(data).hexdigest())
            self.assertEqual(left.calls,[b'x',b'y']); self.assertEqual(right.calls,left.calls)

    def test_bad_input_and_native_errors_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory); forms=p/'forms'
            for i,data in enumerate((b'x y\n',b'\xc3\xa9\n',b'x\n')):
                forms.write_bytes(data)
                with self.assertRaises(ValueError):
                    g.audit(forms,Analyzer({b'x':ValueError('native error')}),Analyzer({}),p/str(i))

    def test_private_repository_input_alias_no_overwrite_and_symlink_guards(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory); forms=p/'forms'; forms.write_bytes(b'x\n'); target=p/'private'
            for invalid in (forms, SCRIPT.parent/'private'):
                with self.assertRaises(ValueError): g.audit(forms,Analyzer({}),Analyzer({}),invalid)
            target.write_bytes(b'keep')
            with self.assertRaises(FileExistsError): g.audit(forms,Analyzer({}),Analyzer({}),target)
            self.assertEqual(target.read_bytes(),b'keep')
            link=p/'link'; link.symlink_to(target)
            with self.assertRaises(FileExistsError): g.audit(forms,Analyzer({}),Analyzer({}),link)
            self.assertEqual(target.read_bytes(),b'keep')
            dangling=p/'dangling'; destination=p/'absent'; dangling.symlink_to(destination)
            with self.assertRaises(FileExistsError): g.audit(forms,Analyzer({}),Analyzer({}),dangling)
            self.assertFalse(destination.exists())

    def test_source_membership_preserves_exact_lemma_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'source'
            path.write_bytes(b':le:synthetic#2\n:vs:old conj3\n:le:other\n')
            self.assertEqual(g.source_lemmas(path),{b'synthetic#2',b'other'})


if __name__=='__main__': unittest.main()
