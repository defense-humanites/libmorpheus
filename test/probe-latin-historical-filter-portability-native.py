#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

spec = importlib.util.spec_from_file_location('probe', Path(__file__).resolve().parents[1] /
                                           'tools/probe-latin-historical-filter-portability.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class NativeTruncation(unittest.TestCase):
    def test_bounded_suffix_selection_preserves_historical_flags(self):
        code='''#include <string.h>
#include <assert.h>
char stem[32]; int sawi, sawpass;
int select_suffix(void) {
''' + m.LEMMA_SUFFIXES + '''
    return 0;
}
int main(void) {
    const char *suffixes[]={"i^or","e^or","i^o","e^o","ior","eor","or","eo","it","et","io"};
    int i;
    for(i=0;i<11;i++) {
        strcpy(stem,"zz"); strcat(stem,suffixes[i]); sawi=sawpass=0;
        select_suffix(); assert(!strcmp(stem,"zz"));
        assert(sawi==(i==0||i==2||i==4||i==10));
        assert(sawpass==(i==1||i==4||i==5||i==6));
    }
    strcpy(stem,"zo"); sawi=sawpass=0; select_suffix(); assert(!strcmp(stem,"z"));
    assert(!sawi&&!sawpass);
    strcpy(stem,""); select_suffix(); assert(!strcmp(stem,""));
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as directory:
            r=Path(directory);source=r/'synthetic.c';binary=r/'synthetic';source.write_text(code)
            p=subprocess.run(['cc','-std=gnu89','-g','-fsanitize=address,undefined',
                '-fno-sanitize-recover=all',str(source),'-o',str(binary)],capture_output=True)
            self.assertEqual(p.returncode,0,p.stderr.decode())
            p=subprocess.run([str(binary)],capture_output=True)
            self.assertEqual(p.returncode,0,p.stderr.decode());self.assertEqual(p.stderr,b'')

    def test_short_lemmas_and_suffix_flags_in_complete_lexer(self):
        lexer=Path(__file__).resolve().parents[1]/'src/gkdict/latvb.l'
        with tempfile.TemporaryDirectory() as directory:
            r=Path(directory);source=r/'synthetic';reference=r/'reference'
            source.write_bytes(b'zoo\t<itype>e_gi, actum, 3</itype>\n'
                               b'zo\t<itype>e_gi, actum, 3</itype>\n')
            reference.write_bytes(b'')
            args=SimpleNamespace(lexer=lexer,input=source,reference=reference,output=r/'control',
                                 expected_reference_sha256=m.digest(b''))
            report=m.prepare(args)
            self.assertEqual(report['sanitizer_process_exit'],0)
            records=m.definitions((args.output/'filter.stdout').read_bytes())
            self.assertEqual({key[0] for key in records},{b'zo',b'zoo'})
            self.assertEqual(sum(records.values()),6)
            self.assertEqual((args.output/'filter.stderr').read_bytes(),b'')

    def test_pinned_lexer_with_synthetic_notation_and_alternative_perfects(self):
        lexer = Path(__file__).resolve().parents[1] / 'src/gkdict/latvb.l'
        original = lexer.read_bytes()
        patched = m.diagnostic_source(original)
        self.assertEqual(patched.count(b'memmove('), 3)
        with tempfile.TemporaryDirectory() as directory:
            r=Path(directory); source=r/'synthetic.input'; reference=r/'reference'
            source.write_bytes(b'zz^zo\t<itype>i_vi, or i^i, i_tum, 4</itype>\n')
            reference.write_bytes(b'')
            args=SimpleNamespace(lexer=lexer,input=source,reference=reference,output=r/'control',
                                 expected_reference_sha256=m.digest(b''))
            report=m.prepare(args)
            self.assertEqual(report['sanitizer_process_exit'],0)
            self.assertTrue(report['original_inputs_unchanged'])
            self.assertEqual(report['definition_multisets']['after_rows'],4)
            self.assertEqual(lexer.read_bytes(),original)
            self.assertEqual((args.output/'filter.stderr').read_bytes(),b'')

    def test_short_and_absent_stems_under_sanitizers(self):
        code = '''#include <ctype.h>
#include <string.h>
#include <assert.h>
''' + m.TRUNCSTEM + '''
static void check(const char *source, int trim, const char *expected) {
    char buffer[32];
    strcpy(buffer,source);
    truncstem(buffer,trim);
    assert(!strcmp(buffer,expected));
}
int main(void) {
    check("",1,""); check("",'s',"");
    check("z",1,""); check("z",'s',"z");
    check("zzct",1,"zz"); check("zzxy",1,"zzx");
    check("zzd",'s',"zz"); check("zzq",'s',"zz");
    check("zzs",'s',"zz"); check("zzabcd",'b',"zza");
    check("zzabc",'x',"zzabc"); check("zzabc",0,"zzabc");
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as directory:
            r = Path(directory); source=r/'synthetic.c'; binary=r/'synthetic'
            source.write_text(code)
            result = subprocess.run(['cc','-std=gnu89','-g','-fsanitize=address,undefined',
                '-fno-sanitize-recover=all','-fno-omit-frame-pointer',str(source),'-o',str(binary)], capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr.decode())
            result = subprocess.run([str(binary)],capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr.decode())
            self.assertEqual(result.stderr,b'')


if __name__ == '__main__':
    unittest.main()
