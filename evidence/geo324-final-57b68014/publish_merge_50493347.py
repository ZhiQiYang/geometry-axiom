#!/usr/bin/env python3
"""Archive the completed owner ordinary merge without changing acceptance facts."""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil

B=Path('/tmp/geo324-owner-20261024');O=B/'merge-50493347-publication'
R=Path('/tmp/geo324-faces-work-20261024');D=Path('/tmp/geo324-faces-prbody-work-20261024')
BR='codex/geo324-faces-20261024';TRAIN='504933473d7b9bdfc5964f73402a710f1222fc96'
OLD_SOURCE='f1217b0fa5e933e14906833bf4981dad97061b04';OLD_TRAIN='f64d638f15c48d2b9723b7ae9d230fb5dacb82d9'
OLD_E='c8806b5f1aa6363d573b30a9df1748e61e1b9ccf';OLD_D='ebdeaca3b4e396c64d084e9acf7017888d809f73'
CAPTURE=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
CAPTURE_SHA='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
if hashlib.sha256(CAPTURE.read_bytes()).hexdigest()!=CAPTURE_SHA:raise SystemExit('capture byte pin mismatch')
if O.exists():raise SystemExit('refuse overwrite')
prior=json.loads((B/'merge-train-50493347/receipt.json').read_text())
if prior.get('exitCode')!=0 or prior.get('remoteHead')!=prior.get('sourceHead') or prior.get('incomingTrainSHA')!=TRAIN:raise SystemExit('merge not actually completed and remotely confirmed')
F=prior['sourceHead'];PREFIX='evidence/geo324-final-'+F[:8]
O.mkdir()
spec=importlib.util.spec_from_file_location('capture',str(CAPTURE));cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env.pop('PYTHONOPTIMIZE',None)
r=cap.Recorder(O,env,F)
report={'schema':'geo324.merge-publication.v1','productSourceSHA':F,'incomingTrainSHA':TRAIN,'prefix':PREFIX,'productTestsExecuted':False,'exitCode':None,'errors':[], 'driverSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'captureSHA256':CAPTURE_SHA}
def run(a,cwd=R):return r.run(a,cwd=cwd,timeout=180,source_variant='source-merge-metadata-publication')
def matrix(text):return text.split('| Gate | 目前結果 | 原 exit | execution SHA |',1)[1].split('\n\n',1)[0]
try:
 for repo,expected in ((R,F),(D,OLD_D)):
  _,head,_=run(['git','rev-parse','HEAD'],repo);_,clean,_=run(['git','status','--porcelain=v1','--untracked-files=all'],repo)
  if head.decode().strip()!=expected or clean:raise RuntimeError('owner publication checkout moved or dirty')
 target=R/PREFIX
 if target.exists():raise RuntimeError('evidence prefix already exists')
 target.mkdir(parents=True)
 shutil.copytree(B/'merge-train-50493347',target/'merge-originals')
 shutil.copytree(B/'merge-train-50493347-preparation',target/'merge-preparation')
 shutil.copytree(B/'network-recovery-publication',target/'prior-evidence-publication')
 for name in ('merge_train_50493347.py','publish_merge_50493347.py'):shutil.copyfile(B/name,target/name)
 state=json.loads((B/'current-preparation-binding/CURRENT_STATE_PREPARED.json').read_text())
 if len(state['rows'])!=16 or any(row['status']!='UNRUN' or row['originalExitCode'] is not None or row['executionSHA'] is not None for row in state['rows']):raise RuntimeError('prior prepared matrix is not entirely unknown')
 state['productSourceSHA']=F;state['trainMerge']['incomingTrain']=TRAIN;state['evidenceHead']=None
 state['publicationRole']='evidenceHead is the containing Git commit; all execution facts remain unknown'
 (target/'CURRENT_STATE.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
 (target/'PROGRESS.md').write_text('# #324 替代線進度（最新列車合流）\n\n產品 source S：`'+F+'`；incoming train：`'+TRAIN+'`；前一 evidence E：`'+OLD_E+'`。此 S 已一般 push／ls-remote 核同。\n\n普通 merge 保留原兩 leaf Grok blobs；對 train 非 evidence 差恰原三檔；expected 只 host_sources39→45，其餘 registry metadata 精確等 train；SSOT／決策佇列 blobs 精確等 incoming train。所有原 merge 命令、exit、stdout/stderr、環境、SHA 在 merge-originals。沒有 rebase／force push／合併 PR。\n\n本次只同步 root 已推的 Claude／main／P17 架構產物，沒有執行任何產品、裁判、Chrome、build 或 ledger。架構原四檔屬 incoming train 的原 sourceBaseHead；#324 owned W leaf／excluded test 的適用性仍須原三裁判與四檔刷新，不能冒本 S 已 fresh。tests/mutation_bridge.py 的 oracle hash 也讀 tests/*.py，原 mutate --check 仍必跑，整份帳本由 root 統排。\n\n唯一 CURRENT_STATE.json 保留16列 UNRUN，原 exit／executionSHA 全 null。三 predicate v2 原 driver／60秒／具名正常紅與逐案0/1/0計畫不改。新 merge 靜審與正式同 SHA 驗收待 root 排槽；不把舊 f121 的靜審外推本 S。\n')
 inventory={}
 for item in sorted(target.rglob('*')):
  if item.is_file():inventory[item.relative_to(target).as_posix()]={'bytes':item.stat().st_size,'sha256':hashlib.sha256(item.read_bytes()).hexdigest()}
 (target/'PACKAGE_MANIFEST.json').write_text(json.dumps({'sourceSHA':F,'incomingTrainSHA':TRAIN,'files':inventory,'productTestsExecuted':False},ensure_ascii=False,indent=2)+'\n')
 run(['git','add','--force','--sparse','--',PREFIX])
 _,staged,_=run(['git','diff','--cached','--name-only','-z'])
 if any(not name.decode().startswith(PREFIX+'/') for name in staged.split(b'\0') if name):raise RuntimeError('staged outside own evidence prefix')
 run(['git','diff','--cached','--check'])
 run(['git','commit','-m','docs(geo324): archive current train merge preparation'])
 _,head,_=run(['git','rev-parse','HEAD']);report['evidenceHead']=head.decode().strip()
 run(['git','push','origin','refs/heads/'+BR+':refs/heads/'+BR])
 _,remote,_=run(['git','ls-remote','--exit-code','origin','refs/heads/'+BR]);report['remoteEvidenceHead']=remote.decode().split()[0]
 if report['remoteEvidenceHead']!=report['evidenceHead']:raise RuntimeError('evidence remote mismatch')
 old=(D/'PR_BODY.md').read_text();new=old
 for a,b in [(OLD_TRAIN,TRAIN),(OLD_SOURCE,F),(OLD_E,report['evidenceHead']),('evidence/geo324-final-f1217b0f/','evidence/geo324-final-'+F[:8]+'/')]:
  if new.count(a)!=1:raise RuntimeError('body identity binding is not unique: '+a)
  new=new.replace(a,b,1)
 old_peer='p88_priority已對新S／普通merge原件／v2完成純靜審118 checks、0 findings，完整原checker錯判1與窄更正報告同存；這不是動態驗收。'
 new_peer='p88_priority只對先前S f1217b0f／當時普通merge原件／v2完成純靜審118 checks、0 findings，完整原checker錯判1與窄更正報告保留；不把它外推本次S。新merge的獨立靜審待補，正式動態仍未執行。'
 if new.count(old_peer)!=1:raise RuntimeError('body prior-peer text moved')
 new=new.replace(old_peer,new_peer,1)
 old_raw='26條merge命令、完整stdout/stderr/env/SHA、fresh review、v1/v2／manifest／peer與前批publication原流。'
 new_raw='本次merge原命令、完整stdout/stderr/env/SHA與前批publication原流；先前fresh review／v1/v2／manifest／peer保於原evidence/geo324-final-f1217b0f/。'
 if new.count(old_raw)!=1:raise RuntimeError('body archive text moved')
 new=new.replace(old_raw,new_raw,1)
 old_network='10條恢復原命令與完整streams封於revision-2-network；正式16gate仍未跑。'
 if new.count(old_network)!=1:raise RuntimeError('body original recovery archive text moved')
 new=new.replace(old_network,'10條恢復原命令與完整streams封於原evidence/geo324-final-f1217b0f/revision-2-network；正式16gate仍未跑。',1)
 old_next='原兩重槽給323/314，本owner不搶槽。'
 if new.count(old_next)!=1:raise RuntimeError('body slot text moved')
 new=new.replace(old_next,'後續動態依root時槽執行，本owner不搶槽。',1)
 new+='\n本次另普通merge root已公開50493347完整列車，原架構四檔保 incoming train 的 sourceBaseHead；#324 owned W leaf／excluded test 的原裁判與四檔刷新仍未跑。mutation bridge oracle hash 包含 tests/*.py，因此不能把列車既有帳本或架構收據直接當作本S有效。\n'
 if matrix(old)!=matrix(new) or len([line for line in matrix(new).splitlines() if '未執行' in line])!=16:raise RuntimeError('formal matrix changed')
 (D/'PR_BODY.md').write_text(new)
 run(['git','add','--force','--sparse','--','PR_BODY.md'],D)
 _,staged,_=run(['git','diff','--cached','--name-only','-z'],D)
 if staged!=b'PR_BODY.md\0':raise RuntimeError('body staged outside PR_BODY.md')
 run(['git','diff','--cached','--check'],D)
 run(['git','commit','-m','docs(geo324): describe current train source and pending gates'],D)
 _,head,_=run(['git','rev-parse','HEAD'],D);report['bodyHead']=head.decode().strip()
 run(['git','push','origin','refs/heads/'+BR+'-prbody:refs/heads/'+BR+'-prbody'],D)
 _,remote,_=run(['git','ls-remote','--exit-code','origin','refs/heads/'+BR+'-prbody'],D);report['remoteBodyHead']=remote.decode().split()[0]
 if report['remoteBodyHead']!=report['bodyHead']:raise RuntimeError('body remote mismatch')
 report['bodySHA256']=hashlib.sha256((D/'PR_BODY.md').read_bytes()).hexdigest();report['formalRowsRemainUnrun']=16;report['exitCode']=0
except BaseException as error:report['errors'].append(repr(error));report['exitCode']=1
finally:
 report['endedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['commandCount']=len(r.rows)
 cap.dump(O/'receipt.json',report);print(json.dumps(report,ensure_ascii=False))
raise SystemExit(report['exitCode'])
