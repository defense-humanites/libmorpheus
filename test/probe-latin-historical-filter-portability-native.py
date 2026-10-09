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
