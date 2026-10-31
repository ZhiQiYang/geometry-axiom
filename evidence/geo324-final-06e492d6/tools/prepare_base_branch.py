#!/usr/bin/env python3
"""建立及一般推送指定 owner ref；不物化 checkout、不執行產品。"""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path

BASE = Path('/tmp/geo324-owner-20261024')
OUT = BASE/'base-branch-publication'
REPO = Path('/workspace/geometry-axiom')
SOURCE = '4e176e830b691269cc72d021ce7e1bc0b167d621'
BRANCH = 'codex/geo324-faces-20261024'
if OUT.exists():
    raise SystemExit('refuse overwrite')
OUT.mkdir()
spec = importlib.util.spec_from_file_location('capture', '/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)
env = os.environ.copy()
env['PATH'] = '/workspace/geo261-environment/bin:' + env['PATH']
env['PYTHONDONTWRITEBYTECODE'] = '1'
env.pop('PYTHONOPTIMIZE', None)
rec = capture.Recorder(OUT, env, SOURCE)
result = {'schema':'geo324.base-branch-publication.v1','sourceHead':SOURCE,'branch':BRANCH,
          'checkoutCreated':False,'productOrTestExecuted':False,'exitCode':None,'errors':[]}
try:
    rec.run(['google-chrome','--version'],cwd=REPO,timeout=30)
    rec.run(['node','--version'],cwd=REPO,timeout=30)
    rec.run(['df','-B1','/workspace','/tmp'],cwd=REPO,timeout=30)
    _, status, _ = rec.run(['git','status','--short'],cwd=REPO,timeout=30)
    if status.strip():
        raise RuntimeError('shared working tree is dirty; refuse even ref-only mutation')
    row, existing, _ = rec.run(['git','show-ref','--verify','--hash','refs/heads/'+BRANCH],cwd=REPO,timeout=30,check=False)
    if row['actual_process_returncode'] not in (0,1,128):
        raise RuntimeError('unexpected show-ref exit')
    if existing.strip() and existing.decode().strip()!=SOURCE:
        raise RuntimeError('existing owner branch points elsewhere; refuse overwrite')
    row, remote, _ = rec.run(['git','ls-remote','--exit-code','origin','refs/heads/'+BRANCH],cwd=REPO,timeout=60,check=False)
    if row['actual_process_returncode'] not in (0,2):
        raise RuntimeError('cannot verify remote-before')
    if remote.strip() and remote.decode().split()[0]!=SOURCE:
        raise RuntimeError('remote exists with a different head; refuse update')
    if not existing.strip():
        rec.run(['git','branch',BRANCH,SOURCE],cwd=REPO,timeout=30)
    rec.run(['git','push','origin','refs/heads/'+BRANCH+':refs/heads/'+BRANCH],cwd=REPO,timeout=120)
    _, after, _=rec.run(['git','ls-remote','--exit-code','origin','refs/heads/'+BRANCH],cwd=REPO,timeout=60)
    if after.decode().split()[0]!=SOURCE:
        raise RuntimeError('remote-after SHA mismatch')
    result['remoteHead']=after.decode().split()[0]
    result['exitCode']=0
except BaseException as error:
    result['errors'].append(repr(error))
    result['exitCode']=1
finally:
    result['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    result['commandCount']=len(rec.rows)
    capture.dump(OUT/'receipt.json',result)
    initial=BASE/'initial-metadata'
    capture.dump(initial/'PREPARATION_COMPLETION.json',{
      'schema':'geo324.readonly-preparation-completion.v1',
      'originalCollectorExitCode':1,'productOrTestExecuted':False,
      'originalFailure':'google-chrome was not found in inherited PATH; original command/result and traceback retained',
      'correction':'prepend /workspace/geo261-environment/bin to PATH, per root; no installation and no product change',
      'correctedEnvironmentReceipt':str(OUT/'receipt.json'),
      'initialCommands':len(json.loads((initial/'subcommands.json').read_text())),
      'noGateResultClaimed':True})
    print(json.dumps(result,ensure_ascii=False))
raise SystemExit(result['exitCode'])
