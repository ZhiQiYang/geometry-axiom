#!/usr/bin/env python3
"""root排定認證重試窗口後，原錄製一般push本owner兩ref；不改任何commit。"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path

CAPTURE=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
PIN='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
SOURCE='f1217b0fa5e933e14906833bf4981dad97061b04'
REFS=(('codex/geo324-faces-20261024','de5142a0f4eaf45125309a93b939fefcd9891c25',Path('/tmp/geo324-faces-work-20261024')),
      ('codex/geo324-faces-20261024-prbody','2fc63aef4ce3c54a96d57e38dd123f7f9ce1320b',Path('/tmp/geo324-faces-prbody-work-20261024')))
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();out=args.out.resolve()
    if out.exists() or not out.is_relative_to(Path('/tmp')):parser.error('out must be new beneath /tmp')
    out.mkdir(parents=True)
    actual=hashlib.sha256(CAPTURE.read_bytes()).hexdigest()
    if actual!=PIN:raise SystemExit('capture helper mismatch; refused before load')
    spec=importlib.util.spec_from_file_location('capture',CAPTURE)
    capture=importlib.util.module_from_spec(spec);spec.loader.exec_module(capture)
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env.pop('PYTHONOPTIMIZE',None)
    rec=capture.Recorder(out,env,SOURCE)
    report={'schema':'geo324.ordinary-push-retry.v1','sourceSHA':SOURCE,'rows':[],
            'helperSHA256':actual,'driverSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'remotePublicationComplete':False,'productTestExecuted':False,'exitCode':None,'errors':[]}
    def run(command,repo,check=True):return rec.run(command,cwd=repo,timeout=120,check=check,source_variant='metadata-normal-push-only')
    try:
        for branch,head,repo in REFS:
            row={'branch':branch,'expectedHead':head,'confirmedRemoteHead':None,'pushExitCode':None}
            report['rows'].append(row)
            _,local,_=run(['git','rev-parse','refs/heads/'+branch],repo)
            _,status,_=run(['git','status','--porcelain=v1','--untracked-files=all'],repo)
            if local.decode().strip()!=head or status:raise RuntimeError('local ref moved or own checkout dirty; refuse stale retry')
            before,raw,_=run(['git','ls-remote','--exit-code','origin','refs/heads/'+branch],repo,check=False)
            row['remoteBeforeExit']=before['actual_process_returncode']
            if row['remoteBeforeExit']!=0:raise RuntimeError('remote-before lookup failed; preserve pending refs without further push attempts')
            row['remoteBeforeHead']=raw.decode().split()[0]
            pushed,_,_=run(['git','push','origin','refs/heads/'+branch+':refs/heads/'+branch],repo,check=False)
            row['pushExitCode']=pushed['actual_process_returncode']
            if row['pushExitCode']!=0:raise RuntimeError('ordinary push failed; local commits retained')
            _,raw,_=run(['git','ls-remote','--exit-code','origin','refs/heads/'+branch],repo)
            row['confirmedRemoteHead']=raw.decode().split()[0]
            if row['confirmedRemoteHead']!=head:raise RuntimeError('remote-after differs from exact local head')
        report['remotePublicationComplete']=len(report['rows'])==2 and all(row['confirmedRemoteHead']==row['expectedHead'] for row in report['rows'])
        report['exitCode']=0 if report['remotePublicationComplete'] else 1
    except BaseException as error:
        report['errors'].append(repr(error));report['exitCode']=1
    finally:
        report['endedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['commandCount']=len(rec.rows)
        capture.dump(out/'receipt.json',report);print(json.dumps(report,ensure_ascii=False))
    return report['exitCode']
if __name__=='__main__':raise SystemExit(main())
