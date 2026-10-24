#!/usr/bin/env python3
"""只 fetch owner 私有 ref；保存最新324原評論，不碰共用 FETCH_HEAD。"""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path

BASE=Path('/tmp/geo324-owner-20261024');OUT=BASE/'latest-review-refresh'
REPO=Path('/tmp/geo324-faces-work-20261024')
SOURCE='f1217b0fa5e933e14906833bf4981dad97061b04'
PRIVATE='refs/remotes/geo324-review/handoff-20261024'
if OUT.exists():raise SystemExit('refuse overwrite')
OUT.mkdir()
spec=importlib.util.spec_from_file_location('capture','/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
capture=importlib.util.module_from_spec(spec);spec.loader.exec_module(capture)
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env.pop('PYTHONOPTIMIZE',None)
rec=capture.Recorder(OUT,env,SOURCE)
report={'schema':'geo324.latest-review-refresh.v1','sourceSHA':SOURCE,'exitCode':None,'errors':[],'productTestExecuted':False}
try:
    rec.run(['git','fetch','--no-write-fetch-head','--no-tags','origin','handoff/codex-takeover-20261021:'+PRIVATE],cwd=REPO,timeout=180)
    _,raw,_=rec.run(['git','rev-parse',PRIVATE],cwd=REPO,timeout=30);report['handoffSHA']=raw.decode().strip()
    _,raw,_=rec.run(['git','show',report['handoffSHA']+':handoff/pr-reviews/324.md'],cwd=REPO,timeout=30)
    report['reviewSHA256']=hashlib.sha256(raw).hexdigest()
    previous=BASE/'initial-metadata/subcommands/000003/stdout.bin'
    report['sameReviewBytesAsInitialD193']=raw==previous.read_bytes()
    (OUT/'LATEST_324.md').write_bytes(raw)
    report['exitCode']=0
except BaseException as error:
    report['errors'].append(repr(error));report['exitCode']=1
finally:
    report['endedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['commands']=len(rec.rows)
    capture.dump(OUT/'receipt.json',report);print(json.dumps(report,ensure_ascii=False))
raise SystemExit(report['exitCode'])
