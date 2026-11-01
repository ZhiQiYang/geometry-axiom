#!/usr/bin/env python3
"""root 授權的 ordinary merge；只解 expected count 聯集，不啟測。"""
import datetime
import importlib.util
import json
import os
from pathlib import Path
import re

BASE=Path('/tmp/geo324-owner-20261024');OUT=BASE/'merge-train-f64d638f'
REPO=Path('/tmp/geo324-faces-work-20261024')
BRANCH='codex/geo324-faces-20261024'
BEFORE='07615668c110684826390990cd2d6134eb6025fd'
TRAIN='f64d638f15c48d2b9723b7ae9d230fb5dacb82d9'
GROK='4e176e830b691269cc72d021ce7e1bc0b167d621'
PRBASE='7dae5f21c7ca401e660450d437e60ba566218da8'
OWNED=('geometry-templates/woodworking/geometry_woodworking/model_sources.py','tests/test_geometry_host_sources.py','tests/run_all.expected.json')
if OUT.exists():raise SystemExit('refuse overwrite')
OUT.mkdir()
spec=importlib.util.spec_from_file_location('capture','/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
capture=importlib.util.module_from_spec(spec);spec.loader.exec_module(capture)
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env.pop('PYTHONOPTIMIZE',None)
rec=capture.Recorder(OUT,env,BEFORE)
report={'schema':'geo324.train-merge.v1','branch':BRANCH,'beforeEvidenceHead':BEFORE,'incomingTrainSHA':TRAIN,
        'productTestsExecuted':False,'exitCode':None,'errors':[]}
def run(command,check=True):
 return rec.run(command,cwd=REPO,timeout=180,check=check,
                source_sha=report.get('sourceHead',BEFORE),source_variant='source-merge-not-product-test')
def object_bytes(revision,path):return run(['git','show',revision+':'+path])[1]
try:
    _,head,_=run(['git','rev-parse','HEAD'])
    _,clean,_=run(['git','status','--porcelain=v1','--untracked-files=all'])
    if head.decode().strip()!=BEFORE or clean:raise RuntimeError('owner checkout moved or dirty')
    for path in OWNED[:2]:
        _,a,_=run(['git','rev-parse',TRAIN+':'+path]);_,b,_=run(['git','rev-parse',PRBASE+':'+path])
        if a!=b:raise RuntimeError('train independently changed original product/test leaf; deeper review required: '+path)
    merge,_,_=run(['git','merge','--no-ff','-m','Merge current train into GEO-324 faces validation',TRAIN],check=False)
    if merge['actual_process_returncode']!=0:
        _,unresolved,_=run(['git','diff','--name-only','--diff-filter=U'],check=False)
        report['conflictedPaths']=unresolved.decode().splitlines()
        if report['conflictedPaths']!=['tests/run_all.expected.json']:
            raise RuntimeError('non-expected conflict requires product peer; no automatic choice')
        for stage in (1,2,3):run(['git','show',':'+str(stage)+':tests/run_all.expected.json'])
        incoming=object_bytes(TRAIN,'tests/run_all.expected.json')
        incoming_json=json.loads(incoming)
        if incoming_json['suites']['py:test_geometry_host_sources']['count']!=39:
            raise RuntimeError('unexpected incoming host count')
        chosen,count=re.subn(rb'("py:test_geometry_host_sources"\s*:\s*\{[^}]*?"count"\s*:\s*)39(?=\s*[,}])',rb'\g<1>45',incoming,count=1)
        if count!=1:raise RuntimeError('expected count replacement not unique')
        target=REPO/'tests/run_all.expected.json';target.write_bytes(chosen)
        a,b=json.loads(incoming),json.loads(chosen);a['suites']['py:test_geometry_host_sources']['count']=45
        if a!=b:raise RuntimeError('manual union alters other expected metadata')
        run(['git','add','--sparse','--','tests/run_all.expected.json'])
        run(['git','commit','--no-edit'])
    _,head,_=run(['git','rev-parse','HEAD']);report['sourceHead']=head.decode().strip()
    _,parents,_=run(['git','rev-list','--parents','-n','1','HEAD']);report['parents']=parents.decode().split()[1:]
    if report['parents']!=[BEFORE,TRAIN]:raise RuntimeError('ordinary merge parent mismatch')
    for path in OWNED[:2]:
        _,a,_=run(['git','rev-parse',GROK+':'+path]);_,b,_=run(['git','rev-parse','HEAD:'+path])
        if a!=b:raise RuntimeError('original Grok leaf bytes not preserved: '+path)
    for path in ('公理層.md','決策佇列.md'):
        _,a,_=run(['git','rev-parse',TRAIN+':'+path]);_,b,_=run(['git','rev-parse','HEAD:'+path])
        if a!=b:raise RuntimeError('incoming train authority blob not preserved: '+path)
    original_expected=object_bytes(TRAIN,'tests/run_all.expected.json')
    current_expected=object_bytes('HEAD','tests/run_all.expected.json')
    a,b=json.loads(original_expected),json.loads(current_expected)
    report['incomingHostSourceCount']=a['suites']['py:test_geometry_host_sources']['count']
    if a['suites']['py:test_geometry_host_sources']['count'] not in (39,45) or b['suites']['py:test_geometry_host_sources']['count']!=45:raise RuntimeError('host source count mismatch')
    a['suites']['py:test_geometry_host_sources']['count']=45
    if a!=b:raise RuntimeError('expected metadata beyond host count differs from train')
    report['allOtherExpectedMetadataExactlySameAsTrain']=True
    _,changed,_=run(['git','diff','--name-only',TRAIN,'HEAD'])
    names=changed.decode().splitlines();report['sourcePathsVersusTrain']=[name for name in names if not name.startswith('evidence/')]
    if sorted(report['sourcePathsVersusTrain'])!=sorted(OWNED):raise RuntimeError('source scope beyond original 3 files')
    run(['git','diff','--stat',TRAIN,'HEAD','--',*OWNED])
    run(['git','diff',TRAIN,'HEAD','--',*OWNED])
    run(['git','diff','--check',TRAIN,'HEAD','--',*OWNED])
    _,clean,_=run(['git','status','--porcelain=v1','--untracked-files=all'])
    if clean:raise RuntimeError('source checkout dirty after merge')
    run(['git','push','origin','refs/heads/'+BRANCH+':refs/heads/'+BRANCH])
    _,remote,_=run(['git','ls-remote','--exit-code','origin','refs/heads/'+BRANCH]);report['remoteHead']=remote.decode().split()[0]
    if report['remoteHead']!=report['sourceHead']:raise RuntimeError('remote source mismatch')
    report['exitCode']=0
except BaseException as error:
    report['errors'].append(repr(error));report['exitCode']=1
finally:
    report['endedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['commandCount']=len(rec.rows)
    capture.dump(OUT/'receipt.json',report);print(json.dumps(report,ensure_ascii=False))
raise SystemExit(report['exitCode'])
