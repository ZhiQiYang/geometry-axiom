#!/usr/bin/env python3
"""已授權 owner ref 上的薄 checkout／一般 merge；不啟動驗收。"""
import datetime
import importlib.util
import json
import os
from pathlib import Path

BASE = Path('/tmp/geo324-owner-20261024')
OUT = BASE/'merge-main-preparation'
COMMON = Path('/workspace/geometry-axiom')
WORK = Path('/tmp/geo324-faces-work-20261024')
BRANCH = 'codex/geo324-faces-20261024'
GROK = '4e176e830b691269cc72d021ce7e1bc0b167d621'
MAIN = 'eda91c8593f0795278f7f16ff8b93d147a4fdaa7'
OWNED = ('geometry-templates/woodworking/geometry_woodworking/model_sources.py',
         'tests/test_geometry_host_sources.py', 'tests/run_all.expected.json')
SPARSE = (
    '/AGENTS.md', '/.gitattributes', '/.gitignore', '/公理層.md', '/決策佇列.md',
    '/.github/workflows/integration-tests.yml', '/geometry-guide/PRODUCT-VISION.md',
    '/geometry-templates/woodworking/FIELD-RULES.md',
    '/geometry-core/geometry_kernel/', '/geometry-core/modeling/',
    '/geometry-app/geometry_app/', '/geometry-templates/woodworking/geometry_woodworking/',
    '/tests/__init__.py', '/tests/test_geometry_host_sources.py',
    '/tests/test_geometry_kernel_runtime.py', '/tests/test_geometry_source_runtime.py',
    '/tests/run_all.py', '/tests/run_all.expected.json',
)
if OUT.exists() or WORK.exists():
    raise SystemExit('refuse existing out/worktree')
OUT.mkdir()
(OUT/'SPARSE_PATTERNS.txt').write_text('\n'.join(SPARSE)+'\n')
spec = importlib.util.spec_from_file_location('capture','/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
capture=importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)
env=os.environ.copy()
env['PATH']='/workspace/geo261-environment/bin:'+env['PATH']
env['PYTHONDONTWRITEBYTECODE']='1'
env.pop('PYTHONOPTIMIZE',None)
rec=capture.Recorder(OUT,env,GROK)
report={'schema':'geo324.sparse-main-merge.v1','branch':BRANCH,'grokHead':GROK,'mainHead':MAIN,
        'worktree':str(WORK),'productOrTestExecuted':False,'exitCode':None,'errors':[]}
def run(argv,cwd=WORK,check=True,data=None):
    return rec.run(argv,cwd=cwd,timeout=180,check=check,data=data,
                   source_sha=report.get('sourceHead',GROK),source_variant='source-preparation-not-test')
try:
    _, local, _=run(['git','rev-parse','refs/heads/'+BRANCH],COMMON)
    if local.decode().strip()!=GROK:
        raise RuntimeError('owner branch moved from known published Grok head')
    _, remote, _=run(['git','ls-remote','--exit-code','origin','refs/heads/'+BRANCH],COMMON)
    if remote.decode().split()[0]!=GROK:
        raise RuntimeError('remote owner branch moved')
    run(['git','worktree','add','--no-checkout',str(WORK),BRANCH],COMMON)
    run(['git','sparse-checkout','set','--no-cone','--stdin'],data=('\n'.join(SPARSE)+'\n').encode())
    run(['git','read-tree','-mu','HEAD'])
    _, status, _=run(['git','status','--porcelain=v1','--untracked-files=all'])
    if status:
        raise RuntimeError('initial thin checkout not clean')
    merge, _, _=run(['git','merge','--no-ff','-m','Merge main into GEO-324 faces validation',MAIN],check=False)
    if merge['actual_process_returncode']!=0:
        _, unresolved, _=run(['git','diff','--name-only','--diff-filter=U'],check=False)
        report['unresolvedPaths']=unresolved.decode().splitlines()
        raise RuntimeError('merge needs explicit conflict resolution; original state and streams retained')
    _, head, _=run(['git','rev-parse','HEAD'])
    report['sourceHead']=head.decode().strip()
    _, parents, _=run(['git','rev-list','--parents','-n','1','HEAD'])
    report['parents']=parents.decode().split()[1:]
    if report['parents']!=[GROK,MAIN]:
        raise RuntimeError('merge parents mismatch')
    _, changed, _=run(['git','diff','--name-only',MAIN,'HEAD'])
    report['changedVersusMain']=changed.decode().splitlines()
    if sorted(report['changedVersusMain'])!=sorted(OWNED):
        raise RuntimeError('unexpected scope beyond original three paths')
    for path in OWNED[:2]:
        _, before, _=run(['git','rev-parse',GROK+':'+path])
        _, after, _=run(['git','rev-parse','HEAD:'+path])
        if before!=after:
            raise RuntimeError('original Grok leaf blob changed: '+path)
    for path in ('公理層.md','決策佇列.md'):
        _, before, _=run(['git','rev-parse',MAIN+':'+path])
        _, after, _=run(['git','rev-parse','HEAD:'+path])
        if before!=after:
            raise RuntimeError('main authority blob changed: '+path)
    _, main_expected, _=run(['git','show',MAIN+':tests/run_all.expected.json'])
    _, ours_expected, _=run(['git','show','HEAD:tests/run_all.expected.json'])
    a,b=json.loads(main_expected),json.loads(ours_expected)
    if a['suites']['py:test_geometry_host_sources']['count']!=39 or b['suites']['py:test_geometry_host_sources']['count']!=45:
        raise RuntimeError('host_sources expected count mismatch')
    a['suites']['py:test_geometry_host_sources']['count']=45
    if a!=b:
        raise RuntimeError('expected union changes anything beyond the one original count')
    report['expectedUnion']={'key':'py:test_geometry_host_sources','beforeMain':39,'after':45,'allOtherMetadataExactlyEqual':True}
    run(['git','diff','--stat',MAIN,'HEAD'])
    run(['git','diff',MAIN,'HEAD','--',*OWNED])
    run(['git','diff','--check',MAIN,'HEAD','--',*OWNED])
    _, clean, _=run(['git','status','--porcelain=v1','--untracked-files=all'])
    if clean:
        raise RuntimeError('merged source checkout not clean')
    materialized=[p for p in WORK.rglob('*') if p.is_file() and p.name!='.git']
    report['materializedFileCount']=len(materialized)
    report['materializedFileBytes']=sum(p.stat().st_size for p in materialized)
    if report['materializedFileBytes']>200*1024*1024:
        raise RuntimeError('materialized source exceeds authorized budget')
    run(['git','push','origin','refs/heads/'+BRANCH+':refs/heads/'+BRANCH])
    _, pushed, _=run(['git','ls-remote','--exit-code','origin','refs/heads/'+BRANCH])
    report['remoteHead']=pushed.decode().split()[0]
    if report['remoteHead']!=report['sourceHead']:
        raise RuntimeError('remote source mismatch')
    report['exitCode']=0
except BaseException as error:
    report['errors'].append(repr(error))
    report['exitCode']=1
finally:
    report['endedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    report['commandCount']=len(rec.rows)
    capture.dump(OUT/'receipt.json',report)
    print(json.dumps(report,ensure_ascii=False))
raise SystemExit(report['exitCode'])
