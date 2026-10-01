"""Independent native acceptance checks for engineering-content/1 encoding.

Builds only the standalone JSON/hash helper, outside the repository. Python's
json/hashlib/base64 supply independent expected encodings, not C snapshots.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
HARNESS = r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#ifdef _WIN32
#include <io.h>
#include <fcntl.h>
#endif
#include "engineering_json.inc"
int main(int argc,char **argv) {
    FILE *f; long rawlen; size_t n,written=0; char *data,*out;
    int ok=0; EngJson j;
#ifdef _WIN32
    _setmode(_fileno(stdout),_O_BINARY);
#endif
    if(argc!=3)return 70;
    f=fopen(argv[2],"rb");if(!f)return 71;
    fseek(f,0,SEEK_END);rawlen=ftell(f);rewind(f);
    if(rawlen<0){fclose(f);return 72;}
    n=(size_t)rawlen;
    data=(char*)malloc(n+1);out=(char*)malloc(n*6+4096);
    if(!data||!out){fclose(f);return 73;}
    if(fread(data,1,n,f)!=n){fclose(f);return 74;}
    fclose(f);data[n]=0;
    if(!strcmp(argv[1],"hash")){eng_sha256(data,n,out);puts(out);ok=1;}
    else if(!strcmp(argv[1],"encode")){
        ok=eng_base64_encode(data,n,out,n*6+4096,&written);
        if(ok)fwrite(out,1,written,stdout);
    }else if(!strcmp(argv[1],"decode")){
        ok=eng_base64_decode(data,n,out,n*6+4096,&written);
        if(ok)fwrite(out,1,written,stdout);
    }else if(!strcmp(argv[1],"quote")){
        ok=!memchr(data,0,n)&&eng_json_quote(data,out,n*6+4096);
        if(ok)fputs(out,stdout);
    }else{
        ok=eng_json_parse_n(&j,data,n);
        if(ok && !strcmp(argv[1],"canonical")){
            ok=eng_json_canonical(&j,0,out,n*6+4096);
            if(ok)fputs(out,stdout);
        }else if(ok && !strcmp(argv[1],"keys")){
            ok=eng_json_keys(&j,0,"id,version","name");
        }else if(ok && !strcmp(argv[1],"accessors")){
            int array=eng_json_member(&j,0,"values"),boolean=-1;
            int64_t integer=0;char text[8];char tiny[2]={'x',0};size_t z;
            ok=eng_json_is_object(&j,0)&&eng_json_size(&j,0)==2
                &&eng_json_is_array(&j,array)&&eng_json_size(&j,array)==4
                &&eng_json_integer(&j,eng_json_at(&j,array,0),&integer)&&integer==INT64_MIN
                &&eng_json_boolean(&j,eng_json_at(&j,array,1),&boolean)&&boolean==1
                &&!eng_json_integer(&j,eng_json_at(&j,array,1),&integer)
                &&eng_json_is_null(&j,eng_json_at(&j,array,2))
                &&eng_json_string(&j,eng_json_at(&j,array,3),text,sizeof(text))&&!strcmp(text,"abc")
                &&eng_json_at(&j,array,-1)==-1&&eng_json_at(&j,array,4)==-1
                &&eng_json_member(&j,0,"missing")==-1
                &&!eng_json_canonical(&j,0,tiny,sizeof(tiny))&&!tiny[0]
                &&!eng_json_quote("abc",tiny,sizeof(tiny))&&!tiny[0]
                &&!eng_json_string(&j,eng_json_at(&j,array,3),tiny,sizeof(tiny))
                &&!eng_base64_encode("a",1,tiny,sizeof(tiny),&z)
                &&!eng_base64_decode("YWJj",4,tiny,sizeof(tiny),&z);
        }else if(ok)ok=0;
        if(!ok)fputs(j.error,stderr);
        eng_json_free(&j);
    }
    free(data);free(out);return ok?0:1;
}
'''


class EngineeringJson(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        parent = Path(tempfile.gettempdir()) / 'geometry-tests'
        parent.mkdir(exist_ok=True)
        cls.temp = tempfile.TemporaryDirectory(prefix='engineering-json-', dir=parent)
        cls.addClassCleanup(cls.temp.cleanup)
        cls.work = Path(cls.temp.name)
        # tests/binaries.py builds this helper once (source-fingerprint cached, so SAC only
        # sees it once) and hands it over here; recompiling per class run is what collided with SAC.
        prebuilt = os.environ.get('GEOMETRY_TEST_ENGINEERING_JSON')
        if prebuilt:
            cls.exe = Path(prebuilt)
            if not cls.exe.is_file():
                raise AssertionError('GEOMETRY_TEST_ENGINEERING_JSON does not exist: ' + prebuilt)
            cls.compiler_output = 'prebuilt: ' + prebuilt
            return
        src = cls.work / 'engineering-json-test.c'
        src.write_text(HARNESS, encoding='utf-8')
        cls.exe = cls.work / ('engineering-json-test.exe' if os.name == 'nt' else 'engineering-json-test')
        include = ROOT / 'geometry-core'
        cc = shutil.which(os.environ.get('CC', 'cc'))
        if os.name == 'nt':
            vswhere = Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')) / 'Microsoft Visual Studio/Installer/vswhere.exe'
            if not vswhere.exists():
                raise unittest.SkipTest('MSVC discovery unavailable')
            install = subprocess.check_output([str(vswhere), '-latest', '-products', '*', '-requires', 'Microsoft.VisualStudio.Component.VC.Tools.x86.x64', '-property', 'installationPath'], text=True).strip()
            vcvars = Path(install) / 'VC/Auxiliary/Build/vcvars64.bat'
            if not vcvars.exists():
                raise unittest.SkipTest('MSVC C compiler unavailable')
            build = cls.work / 'build.cmd'
            build.write_text('@echo off\ncall "' + str(vcvars) + '" >nul\ncl /nologo /utf-8 /O2 /W4 /wd4505 /I"' + str(include) + '" /Fe:"' + str(cls.exe) + '" /Fo:"' + str(cls.work / 'engineering-json-test.obj') + '" "' + str(src) + '"\n', encoding='utf-8')
            command = ['cmd', '/d', '/c', str(build)]
        elif cc:
            command = [cc, '-std=c11', '-O2', '-Wall', '-Wextra', '-Wno-unused-function', '-I', str(include), str(src), '-o', str(cls.exe)]
        else:
            raise unittest.SkipTest('No supported C compiler')
        result = subprocess.run(command, cwd=cls.work, capture_output=True, text=True, errors='replace')
        if result.returncode or not cls.exe.exists():
            raise AssertionError(result.stdout + result.stderr)
        cls.compiler_output = result.stdout + result.stderr
        # A fresh unsigned executable can need SAC evaluation; this is an
        # environment failure, never evidence that malformed JSON was rejected.
        ready = cls.work / 'ready.txt'
        ready.write_bytes(b'')
        for attempt in range(4):
            try:
                subprocess.run([str(cls.exe), 'hash', str(ready)], capture_output=True, check=True)
                break
            except OSError as exc:
                if getattr(exc, 'winerror', None) != 4551:
                    raise
                if attempt == 3:
                    raise unittest.SkipTest('Smart App Control blocked native helper after retries') from exc
                time.sleep(12)

    def run_native(self, mode, data, accept=True):
        data = data.encode('utf-8') if isinstance(data, str) else data
        path = self.work / 'input.bin'
        path.write_bytes(data)
        run = subprocess.run([str(self.exe), mode, str(path)], capture_output=True, timeout=10)
        self.assertEqual(run.returncode, 0 if accept else 1, run.stderr.decode('utf-8', errors='replace'))
        return run.stdout

    def test_sha256_standard_vectors_and_padding_boundaries(self):
        vectors = [b'', b'abc', b'abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq', b'a' * 1000000]
        vectors += [bytes(range(n)) for n in (1, 55, 56, 63, 64, 65, 119, 120, 127, 128, 129, 255)]
        for source in vectors:
            with self.subTest(length=len(source)):
                self.assertEqual(self.run_native('hash', source).strip().decode(), hashlib.sha256(source).hexdigest())

    def test_canonical_key_order_nested_unicode_and_controls(self):
        values = [
            {'z': [None, True, False, -2**63, 2**63-1], 'a': {'品牌': '角材🪵', 'thickness': '6.00'}},
            {'z': '\b\f\n\r\t\x01"\\/', 'b': {}, 'a': []},
            {'é': 1, 'e\u0301': 2, '中': 3, '😀': 4},
        ]
        random.seed(734)
        for _ in range(12):
            values.append({f'key-{k}': [random.randint(-10**12, 10**12), {'raw': '面材', 'flag': bool(k % 2)}] for k in random.sample(range(16), 16)})
        for value in values:
            expected = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
            for ascii_input in (True, False):
                with self.subTest(value=value, escaped=ascii_input):
                    source = json.dumps(value, ensure_ascii=ascii_input, indent=2)
                    self.assertEqual(self.run_native('canonical', source), expected)
        self.assertEqual(self.run_native('canonical', '-0'), b'0')

    def test_strict_json_rejects_malformed_types_unicode_and_duplicates(self):
        invalid = [b'', b' ', b'01', b'-01', b'+1', b'1.0', b'1e0', b'1E+2', b'NaN', b'Infinity',
                   b'9223372036854775808', b'-9223372036854775809', b'{}{}', b'[1,]', b'{"a":1,}',
                   b'{a:1}', b'{"a" 1}', b'[truefalse]', b'/*x*/{}', b'\xef\xbb\xbf{}',
                   b'{"a":1,"a":2}', b'{"a":1,"\\u0061":2}', b'{"x":{"a":1,"a":2}}',
                   b'"\\ud800"', b'"\\udfff"', b'"\\ud800\\u0041"', b'"\\ud800\\ud800"',
                   b'"\\u0000"', b'"\\u12z4"', b'"\\u12"', b'"\\x20"', b'"a\x00b"', b'{}\x00{}',
                   b'"a\nb"', b'"\x80"', b'"\xc0\xaf"', b'"\xe0\x80\xaf"', b'"\xed\xa0\x80"',
                   b'"\xf0\x80\x80\xaf"', b'"\xf4\x90\x80\x80"', b'"\xf5\x80\x80\x80"', b'"\xe2\x82"']
        for source in invalid:
            with self.subTest(source=source):
                self.run_native('canonical', source, False)

    def test_capacity_boundaries_and_large_object(self):
        self.run_native('canonical', '[' * 130 + '0' + ']' * 130, False)
        self.run_native('canonical', ' ' * (1024 * 1024) + '0', False)
        self.assertEqual(self.run_native('canonical', ' ' * (1024 * 1024 - 1) + '0'), b'0')
        value = {f'k{i:05d}': i for i in reversed(range(20000))}
        expected = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
        self.assertEqual(self.run_native('canonical', json.dumps(value)), expected)

    def test_schema_keys_required_unknown_and_accessor_types(self):
        self.run_native('keys', '{"version":1,"id":"panel"}')
        self.run_native('keys', '{"version":1,"id":"panel","name":null}')
        for source in ('[]', '{"id":"p"}', '{"version":1,"id":"p","unknown":1}'):
            self.run_native('keys', source, False)
        self.run_native('accessors', '{"values":[-9223372036854775808,true,null,"abc"],"unused":{}}')

    def test_quote_matches_canonical_strings(self):
        for source in ('', '角材🪵', '\x01\b\t\r\n\f"\\/', 'line\u2028separator'):
            self.assertEqual(self.run_native('quote', source), json.dumps(source, ensure_ascii=False).encode())
        self.run_native('quote', b'\xc0\x80', False)

    def test_base64_rfc_vectors_binary_and_strict_padding(self):
        for source in (b'', b'f', b'fo', b'foo', b'foob', b'fooba', b'foobar', bytes(range(256))):
            encoded = base64.b64encode(source)
            self.assertEqual(self.run_native('encode', source), encoded)
            self.assertEqual(self.run_native('decode', encoded), source)
        for source in (b'Zg', b'Zg=', b'=g==', b'Z===', b'Zg==AAAA', b'Zm=8', b'Zm9v\n', b'Zh==', b'Zm9=', b'====', b'AA-_'):
            with self.subTest(source=source):
                self.run_native('decode', source, False)


if __name__ == '__main__':
    unittest.main(verbosity=2)
