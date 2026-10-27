#!/usr/bin/env python3
"""RC 量法精準反證 worker：執行原單一 unittest，不改原測試或來源。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest

ORACLE = 'geometry-core/framing-template/oracle/framing_oracle.py'
TEST = 'tests/test_geo318_reading_a_oracle.py'
INPUTS = (ORACLE, TEST,
          'geometry-core/framing-template/oracle/rooms.json',
          'geometry-core/framing-template/oracle/reading_a_cases.py',
          'geometry-core/framing-template/oracle/reading-a-expected-buildable.json')
METHOD = 'test_rc_face_is_measured_along_its_unlined_run'
CHANGES = {
    'builder-whole-face': (
        '            unlined = iv_subtract([(lo, hi)], lined)\n',
        '            unlined = [(lo, hi)]\n'),
    'checker-whole-face': (
        '                    run_lo = max([lo] + [b for a, b in lined if b <= bare_lo])\n'
        '                    run_hi = min([hi] + [a for a, b in lined if a >= bare_hi])\n',
        '                    run_lo, run_hi = lo, hi\n'),
}

def digest(raw): return hashlib.sha256(raw).hexdigest()
def require(ok, message):
    if not ok: raise RuntimeError(message)
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--sha',required=True)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--control',choices=('baseline',*CHANGES),required=True)
    args=parser.parse_args(); root=args.root.resolve(); source=args.source.resolve()
    require(re.fullmatch('[0-9a-f]{40}',args.sha) is not None,'source SHA must be a complete 40-hex commit')
    require(not sys.flags.optimize and os.environ.get('PYTHONOPTIMIZE') in (None,'','0'), 'assertions must remain enabled')
    require(not os.environ.get('PYTHONPATH') and not os.environ.get('PYTHONHOME'),'caller must clear Python import overrides')
    require(os.environ.get('GITHUB_SHA')==args.sha and os.environ.get('GITHUB_WORKSPACE')==str(root),'caller must explicitly bind original child SHA/workspace')
    def git(*parts):
        result=subprocess.run(['git',*parts],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        print('RC_METHOD_GIT '+json.dumps({'argv':['git',*parts],'exit':result.returncode,'stdout':result.stdout.decode('utf-8','replace'),'stderr':result.stderr.decode('utf-8','replace')},ensure_ascii=False),flush=True)
        require(result.returncode==0,'Git identity command failed'); return result.stdout
    require(git('rev-parse','HEAD').decode().strip()==args.sha,'wrong source HEAD')
    require(git('status','--porcelain=v1','--untracked-files=all')==b'','source must be clean')
    before={name:(root/name).read_bytes() for name in INPUTS}
    for name,raw in before.items(): require(raw==git('show',args.sha+':'+name),'original file differs from fixed Git blob')
    original=before[ORACLE]; variant=source.read_bytes()
    if args.control=='baseline':
        require(source==(root/ORACLE).resolve() and variant==original,'baseline/restored must use actual original source')
    else:
        old,new=CHANGES[args.control]; old,new=old.encode(),new.encode()
        require(not source.is_relative_to(root),'mutant must live outside source checkout')
        require(original.count(old)==1 and variant==original.replace(old,new,1),'variant must be the one exact approved RC withdrawal')
    print('RC_METHOD_BINDING '+json.dumps({'sourceSha':args.sha,'originalTest':str(root/TEST),'originalTestSha256':digest(before[TEST]),'method':METHOD,'originalOracleSha256':digest(original),'inputSha256':{p:digest(raw) for p,raw in before.items()},'variantSource':str(source),'variantSha256':digest(variant),'control':args.control,'allOtherSourceBytesEqual':True},ensure_ascii=False),flush=True)
    # 原 test 的 import framing_oracle 取得這個精確 source variant；原 method/fixtures/asserts 原樣。
    spec=importlib.util.spec_from_file_location('framing_oracle',source)
    oracle=importlib.util.module_from_spec(spec); sys.modules[spec.name]=oracle; spec.loader.exec_module(oracle)
    spec=importlib.util.spec_from_file_location('geo337_original_readingA_rc_test',root/TEST)
    module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module; spec.loader.exec_module(module)
    require(module.fo is oracle,'original method did not consume selected oracle module')
    suite=unittest.defaultTestLoader.loadTestsFromName('ReadingAOracle.'+METHOD,module)
    require(suite.countTestCases()==1,'must run the exact one original method')
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    require(result.testsRun==1 and not result.skipped and not result.errors,'skip/error/crash is infrastructure, not an assertion kill')
    require(all('AssertionError' in text for _,text in result.failures),'failure must be an actual original assertion')
    require(all((root/name).read_bytes()==raw for name,raw in before.items()),'original test/source changed during proof')
    require(source.read_bytes()==variant,'variant changed during proof')
    require(git('rev-parse','HEAD').decode().strip()==args.sha and git('status','--porcelain=v1','--untracked-files=all')==b'','source identity drifted during proof')
    print('RC_METHOD_OUTCOME '+json.dumps({'sourceSha':args.sha,'method':METHOD,'testsRun':result.testsRun,'assertionFailures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'originalFilesUnchanged':True},ensure_ascii=False),flush=True)
    return 0 if result.wasSuccessful() else 1

if __name__=='__main__':
    try: raise SystemExit(main())
    except RuntimeError as error:
        print('RC_METHOD_INFRASTRUCTURE: '+str(error),file=sys.stderr,flush=True)
        raise SystemExit(2)
