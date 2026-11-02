#!/usr/bin/env python3
"""正常出版已完成的兩ref重試原件，更新pending文字；不改任何gate。"""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil

B=Path('/tmp/geo324-owner-20261024');O=B/'network-recovery-publication'
R=Path('/tmp/geo324-faces-work-20261024');D=Path('/tmp/geo324-faces-prbody-work-20261024')
BR='codex/geo324-faces-20261024';P='evidence/geo324-final-f1217b0f';F='f1217b0fa5e933e14906833bf4981dad97061b04'
if O.exists():raise SystemExit('refuse overwrite')
O.mkdir()
spec=importlib.util.spec_from_file_location('capture','/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env.pop('PYTHONOPTIMIZE',None)
r=cap.Recorder(O,env,F);report={'sourceSHA':F,'productTestsExecuted':False,'exitCode':None,'errors':[]}
def run(a,cwd=R):return r.run(a,cwd=cwd,timeout=180,source_variant='metadata-network-recovery-publication')
try:
 prior=json.loads((B/'network-retry-1855/receipt.json').read_text())
 if prior['exitCode']!=0 or not prior['remotePublicationComplete']:raise RuntimeError('retry did not actually confirm both refs')
 _,head,_=run(['git','rev-parse','HEAD'])
 if head.decode().strip()!='de5142a0f4eaf45125309a93b939fefcd9891c25':raise RuntimeError('source metadata head moved')
 t=R/P;revision=t/'revision-2-network';revision.mkdir()
 shutil.copytree(B/'network-retry-1855',revision/'retry-originals')
 shutil.copytree(B/'train-preparation-local-publication',revision/'prior-local-publication')
 shutil.copyfile(B/'push_pending_refs.py',revision/'push_pending_refs.py')
 shutil.copyfile(Path(__file__),revision/'publish_network_recovery.py')
 shutil.copyfile(t/'PACKAGE_MANIFEST.json',revision/'PREVIOUS_PACKAGE_MANIFEST.json')
 (revision/'MANIFEST_ROLE.json').write_text(json.dumps({'originalSnapshotCommit':'de5142a0f4eaf45125309a93b939fefcd9891c25','originalManifest':'PREVIOUS_PACKAGE_MANIFEST.json','originalBytesPreserved':True,'currentRootManifest':'../PACKAGE_MANIFEST.json'},indent=2)+'\n')
 with (t/'PROGRESS.md').open('a') as stream:stream.write('\n## 18:55Z 網路恢復實際收據\n\nroot探針恢復後，原Ede5142a0／D2fc63aef兩ref均一般push0、ls-remote前後0且完整SHA核同。10條原命令／完整streams／環境／SHA封於revision-2-network/retry-originals。上文「只本地／待推」是原18:42時狀態，原件保留；本節追加真恢復結果。正式16gate仍UNRUN，沒有新增test snapshot或測試執行。\n')
 inventory={}
 for p in sorted(t.rglob('*')):
  if p.is_file() and p!=t/'PACKAGE_MANIFEST.json':inventory[p.relative_to(t).as_posix()]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 (t/'PACKAGE_MANIFEST.json').write_text(json.dumps({'sourceSHA':F,'files':inventory,'productTestsExecuted':False,'priorTwoRefsActuallyPublished':True,'priorRetryReceiptSHA256':'bcc5c090adbe1d6eff6f660eff5964ba5828e691ca789983d5a7bb01ee652d5e'},ensure_ascii=False,indent=2)+'\n')
 run(['git','add','--force','--sparse','--',P])
 _,staged,_=run(['git','diff','--cached','--name-only','-z'])
 if any(not p.decode().startswith(P+'/') for p in staged.split(b'\0') if p):raise RuntimeError('staged outside own evidence')
 run(['git','commit','-m','docs(geo324): record successful publication recovery'])
 _,head,_=run(['git','rev-parse','HEAD']);report['evidenceHead']=head.decode().strip()
 run(['git','push','origin','refs/heads/'+BR+':refs/heads/'+BR])
 _,remote,_=run(['git','ls-remote','--exit-code','origin','refs/heads/'+BR])
 if remote.decode().split()[0]!=report['evidenceHead']:raise RuntimeError('new evidence remote mismatch')
 report['remoteEvidenceHead']=remote.decode().split()[0]
 old=(D/'PR_BODY.md').read_text();new=old
 edits=[('本批本地 evidence E（尚未push）','目前 evidence E'),
        ('de5142a0f4eaf45125309a93b939fefcd9891c25',report['evidenceHead']),
        ('（此批本地commit，尚未push）','（本輪一般push及ls-remote已核同）'),
        ('Git認證18:25Z突然lookup失敗，root安排約18:55Z一般重試；來源S已在故障前公開，本批E及這份正文的最新commit仍待推。沒有把pending標成已公開。',
         'Git認證18:25Z曾lookup失敗，原本地commit／故障狀態皆保留。18:55Z root探針恢復後，原Ede5142a0／D2fc63aef兩ref均一般push0、ls-remote核同；本輪新E也已一般push0核同。10條恢復原命令與完整streams封於revision-2-network；正式16gate仍未跑。正文由同名-prbody分支一般推送，實際D與原exit另記於出版收據。')]
 for a,b in edits:
  if new.count(a)!=1:raise RuntimeError('body narrow binding not unique: '+a)
  new=new.replace(a,b,1)
 def matrix(text):return text.split('| Gate | 目前結果 | 原 exit | execution SHA |',1)[1].split('\n\n',1)[0]
 if matrix(old)!=matrix(new) or len([x for x in matrix(new).splitlines() if '未執行' in x])!=16:raise RuntimeError('current-state gate matrix changed')
 (D/'PR_BODY.md').write_text(new)
 run(['git','add','--force','--sparse','--','PR_BODY.md'],D)
 run(['git','diff','--cached','--check'],D)
 run(['git','commit','-m','docs(geo324): reflect successful preparation publication'],D)
 _,head,_=run(['git','rev-parse','HEAD'],D);report['bodyHead']=head.decode().strip()
 run(['git','push','origin','refs/heads/'+BR+'-prbody:refs/heads/'+BR+'-prbody'],D)
 _,remote,_=run(['git','ls-remote','--exit-code','origin','refs/heads/'+BR+'-prbody'],D)
 if remote.decode().split()[0]!=report['bodyHead']:raise RuntimeError('body remote mismatch')
 report['remoteBodyHead']=remote.decode().split()[0];report['bodySHA256']=hashlib.sha256((D/'PR_BODY.md').read_bytes()).hexdigest()
 report['formalRowsRemainUnrun']=16;report['exitCode']=0
except BaseException as error:report['errors'].append(repr(error));report['exitCode']=1
finally:
 report['endedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['commands']=len(r.rows)
 cap.dump(O/'receipt.json',report);print(json.dumps(report,ensure_ascii=False))
raise SystemExit(report['exitCode'])
