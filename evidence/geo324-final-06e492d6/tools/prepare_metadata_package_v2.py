#!/usr/bin/env python3
"""收原規範／工具靜態資訊，產生待執行 current-state；不執行測試。"""
import ast
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path

BASE=Path('/tmp/geo324-owner-20261024')
OUT=BASE/'authority-and-plan-resume1'
REPO=Path('/tmp/geo324-faces-work-20261024')
SOURCE='06e492d6d59c1ab2c5505e5300f7542f7063468d'
MAIN='eda91c8593f0795278f7f16ff8b93d147a4fdaa7'
HANDOFF='d193946b8e0fbda024d3b134c4851e9393a43d38'
if OUT.exists(): raise SystemExit('refuse overwrite')
OUT.mkdir()
spec=importlib.util.spec_from_file_location('capture','/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
capture=importlib.util.module_from_spec(spec);spec.loader.exec_module(capture)
env=os.environ.copy();env['PATH']='/workspace/geo261-environment/bin:'+env['PATH'];env['PYTHONDONTWRITEBYTECODE']='1';env.pop('PYTHONOPTIMIZE',None)
rec=capture.Recorder(OUT,env,SOURCE)
report={'schema':'geo324.authority-preparation.v1','sourceSHA':SOURCE,'mainSHA':MAIN,'handoffSHA':HANDOFF,
        'productTestExecuted':False,'exitCode':None,'errors':[],'authority':[]}
try:
    for path in ('AGENTS.md','geometry-guide/PRODUCT-VISION.md','公理層.md','決策佇列.md'):
        row,raw,_=rec.run(['git','show',SOURCE+':'+path],cwd=REPO,timeout=30)
        report['authority'].append({'path':path,'gitSHA':SOURCE,'rawSHA256':hashlib.sha256(raw).hexdigest(),
                                   'LF_SHA256':hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest(),'rawCommand':row['directory']})
    row,raw,_=rec.run(['git','rev-parse','--verify','refs/remotes/origin/pr-333'],cwd=REPO,timeout=30,check=False)
    if row['actual_process_returncode']==0:
        fieldref=raw.decode().strip()
        row,raw,_=rec.run(['git','show',fieldref+':geometry-templates/woodworking/FIELD-RULES.md'],cwd=REPO,timeout=30,check=False)
        report['fieldRules']={'sourceSHA':fieldref,'commandExit':row['actual_process_returncode'],
                             'rawSHA256':hashlib.sha256(raw).hexdigest(),'rawCommand':row['directory'],
                             'status':'reference only; does not replace SSOT or lock queue'}
    else:
        report['fieldRules']={'sourceSHA':None,'status':'origin/pr-333 ref unavailable; no invented authority'}
    # 原 AGENTS 的 read-only startup inbox；只物化這個既有 script，不擴 checkout。
    patterns=(BASE/'merge-main-preparation/SPARSE_PATTERNS.txt').read_text()+'/geometry-web/feedback_cli.py\n/geometry-web/feedback_store.py\n'
    rec.run(['git','sparse-checkout','set','--no-cone','--stdin'],cwd=REPO,data=patterns.encode(),timeout=60)
    rec.run(['python3','-B','geometry-web/feedback_cli.py','list'],cwd=REPO,timeout=60)
    rec.run(['git','status','--porcelain=v1','--untracked-files=all'],cwd=REPO,timeout=30)
    rec.run(['git','grep','-n','-e','geometry_app.model_runtime','-e','geometry_app.model_native',
             '-e','geometry_app.model_world','-e','modeling.engine','-e','WoodworkingModelProvider',SOURCE,
             '--','tests/test_*.py'],cwd=REPO,timeout=30)
    rec.run(['python3','-B','-c',
             'import ast,hashlib,json;from pathlib import Path;p=Path("/tmp/geo324-owner-20261024/preparation/run_face_predicate_proofs.py");ast.parse(p.read_bytes());print(json.dumps({"kind":"AST-only-not-product-test","exit":0,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}))'],cwd=BASE,timeout=30)
    gates=[('registry-list','python3 tests/run_all.py --list'),
           ('native-and-full-expected','ulimit -s 16384; python3 tests/run_all.py --build'),
           *[(job,'original integration-tests.yml browser job: '+job) for job in ('canvas','assembly','documents','grid','space','timber')],
           ('affected-importers','original run_all --build --only named suites; PARTIAL diagnostic'),
           *[('predicate-'+key,'run_face_predicate_proofs.py: original '+key+' method baseline/withdraw/restored') for key in ('list','dict','feature')],
           ('mutation-check','python3 tests/mutate.py --check'),
           ('architecture-contract','python3 -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json'),
           ('architecture-tests','python3 -B tests/test_architecture_contract.py'),
           ('product-architecture-tests','python3 -B tests/test_product_architecture.py')]
    current={'schema':'geo324.current-state.v1','productSourceSHA':SOURCE,'evidenceHead':None,'formalFinalSHA':None,
             'trainMerge':'not yet performed; root will schedule the source sequence',
             'rows':[{'gate':key,'originalCommand':command,'executionSHA':None,'originalExitCode':None,
                      'status':'UNRUN','allowedSkip':None,'receipt':None} for key,command in gates]}
    capture.dump(BASE/'preparation/CURRENT_STATE_PREPARED.json',current)
    frozen={}
    for path in sorted((BASE/'preparation').iterdir()):
        if path.is_file(): frozen[path.name]={'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    capture.dump(OUT/'PREPARATION_MANIFEST.json',{'sourceSHA':SOURCE,'files':frozen,'productGateExecuted':False})
    report['exitCode']=0
except BaseException as error:
    report['errors'].append(repr(error));report['exitCode']=1
finally:
    report['endedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['commands']=len(rec.rows)
    capture.dump(OUT/'receipt.json',report)
    print(json.dumps(report,ensure_ascii=False))
raise SystemExit(report['exitCode'])
