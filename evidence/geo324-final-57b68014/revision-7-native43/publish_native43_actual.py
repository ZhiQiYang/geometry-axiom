#!/usr/bin/env python3
"""Publish two original native importer modules and exact nine-module result index."""
import argparse
import datetime
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tarfile

B=Path('/tmp/geo324-owner-20261024');O=B/'native43-publication-57b68014'
R=Path('/tmp/geo324-faces-work-20261024');D=Path('/tmp/geo324-faces-prbody-work-20261024')
BR='codex/geo324-faces-20261024';P='evidence/geo324-final-57b68014';S='57b680140da2c6b77ab0d362a72029d8d7c9334b'
E='6a7cfab60b78441e4d0bbcccf4c82ae103ef34ab';DH='3daef7fe1c566efa7e675c3cedfebae59c11f74b'
N=Path('/tmp/geo324-native43-57b68014-r1');L=Path('/tmp/geo324-native43-launch-57b68014-r1');PREP=B/'native43-preparation'
HELPER=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py');HPIN='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
PEERS={
'/tmp/geo324-native43-static-peer-readingA/REVIEW.json':'18011efb00d46faaca1bc1d1655c0c6099da22da84f25b4c12c863349c91ca52',
'/tmp/train337-adversarial/GEO324_PURE99_PUBLICATION_PEER.json':'2eeffaacde19ab87da6a925b2e9fe08a911bcb81ad8bc6a88adf990d0dbc216f'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
parser=argparse.ArgumentParser();parser.add_argument('--peer',type=Path,required=True);parser.add_argument('--peer-sha',required=True);args=parser.parse_args()
if O.exists():raise SystemExit('refuse overwrite')
if sha(HELPER.read_bytes())!=HPIN:raise SystemExit('capture pin changed')
PEERS[str(args.peer)]=args.peer_sha
for path,pin in PEERS.items():
 if sha(Path(path).read_bytes())!=pin:raise SystemExit('peer changed: '+path)
peer=json.loads(args.peer.read_bytes())
if peer.get('accepted') is not True or peer.get('actual_peer_exit')!=0 or peer.get('findings')!=[]:raise SystemExit('actual peer not accepted')
n=json.loads((N/'receipt.json').read_bytes());launch=json.loads((L/'RESULT.json').read_bytes())
if sha((N/'receipt.json').read_bytes())!='60df6ba0ea9398b81413a05907f9b36e708f2453a2af532a03f767544e406ad6':raise SystemExit('original receipt changed')
if n['exitCode']!=0 or n['errors'] or n['buildOriginalProcessExit']!=0 or n['buildTimeout'] or launch['actual_process_returncode']!=0 or launch['timeout_expired']:raise SystemExit('original execution not accepted')
if n['sourceAfter']!={'head':S,'porcelain':'','inputsEqualBefore':True,'indexEqualBefore':True}:raise SystemExit('original source/stage mismatch')
if [(x['suite'],x['executionSHA'],x['originalProcessExit'],x['originalResult']['passed'],x['originalResult']['failed'],x['originalResult']['skipped']) for x in n['rows']]!=[('test_geometry_host_native',S,0,30,0,0),('test_geo261_default_native',S,0,13,0,0)]:raise SystemExit('original43scope differs')
O.mkdir();spec=importlib.util.spec_from_file_location('capture',HELPER);cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
env=dict(os.environ);env.pop('PYTHONOPTIMIZE',None);env['PYTHONDONTWRITEBYTECODE']='1';rec=cap.Recorder(O,env,S)
report={'schema':'geo324.native43-publication.v1','sourceSHA':S,'originalSuiteExits':[0,0],'originalSuiteTests':[30,13],'buildOriginalExit':0,'nativeFullOrBrowser':False,'errors':[],'exitCode':None,'publisherSHA256':sha(Path(__file__).read_bytes())}
def run(a,cwd=R):return rec.run(a,cwd=cwd,timeout=180,source_sha=S,source_variant='two-original-native-module-evidence-publication')
try:
 for repo,expected in ((R,E),(D,DH)):
  _,head,_=run(['git','rev-parse','HEAD'],repo);_,status,_=run(['git','status','--porcelain=v1','--untracked-files=all'],repo)
  if head.decode().strip()!=expected or status:raise RuntimeError('owner checkout drifted')
 t=R/P;rev=t/'revision-7-native43';rev.mkdir()
 for name in ('PACKAGE_MANIFEST.json','CURRENT_STATE.json'):shutil.copyfile(t/name,rev/('PREVIOUS_'+name))
 shutil.copyfile(Path(__file__),rev/Path(__file__).name)
 shutil.copytree(B/'pure99-publication-57b68014',rev/'prior-completed-publication')
 for path in PEERS:shutil.copyfile(path,rev/Path(path).name)
 (rev/'PR_BODY_BEFORE_NATIVE43.md').write_bytes((D/'PR_BODY.md').read_bytes())
 originals={}
 for label,root in {'native43':N,'launcher':L,'prepared-tools':PREP}.items():
  for path in sorted(root.rglob('*')):
   if path.is_symlink():raise RuntimeError('unexpected original symlink')
   if path.is_file():originals[label+'/'+path.relative_to(root).as_posix()]=path
 originals['tools/capture.py']=HELPER
 archive=t/'raw/two-native-importer-modules-57b68014.tar.gz';inventory=[]
 with archive.open('wb') as output:
  with gzip.GzipFile(filename='',fileobj=output,mode='wb',mtime=0) as compressed:
   with tarfile.open(fileobj=compressed,mode='w|') as tar:
    for name,path in sorted(originals.items()):
     raw=path.read_bytes();inventory.append({'archivePath':name,'originalPath':str(path),'bytes':len(raw),'sha256':sha(raw)});tar.add(path,arcname=name,recursive=False)
 expected={x['archivePath']:x for x in inventory};seen=set()
 with tarfile.open(archive,'r:gz') as tar:
  for member in tar:
   if not member.isfile() or member.name not in expected or member.name in seen:raise RuntimeError('unexpected archive member')
   seen.add(member.name);raw=tar.extractfile(member).read();row=expected[member.name]
   if len(raw)!=row['bytes'] or sha(raw)!=row['sha256'] or raw!=originals[member.name].read_bytes():raise RuntimeError('archive differs from original bytes')
 if seen!=set(expected):raise RuntimeError('incomplete archive')
 save(t/'raw/two-native-importer-modules-57b68014.inventory.json',{'sourceSHA':S,'files':inventory,'excludedFiles':[],'producerRoundtripVerified':True})
 shutil.copyfile(N/'receipt.json',t/'receipts/native43-original.json')
 old_index=json.loads((t/'receipts/pure-python99.json').read_bytes());rows=list(old_index['rows'])
 for row in n['rows']:rows.append({'archiveReceipt':'native43/receipt.json','originalReceiptSHA256':sha((N/'receipt.json').read_bytes()),**row})
 if len(rows)!=9 or sum(x['originalResult']['passed'] for x in rows)!=142:raise RuntimeError('nine-module scope mismatch')
 index={'schema':'geo324.original-nine-importer-module-index.v1','sourceSHA':S,'rows':rows,'originalModuleExits':[0]*9,'originalPassCount':142,'scope':'specified nine complete original unittest modules; project PARTIAL, not full native/expected aggregate or browser','actualCommandKind':'original tests/_unittest_runner.py per module; prepared run_all --build --only diagnostic was not executed','nativeBuild':{'originalExit':0,'receipt':P+'/receipts/native43-original.json'},'evidenceLimits':[n['internalPipeLimit'],'indexEqualBefore refers to git ls-files --stage printed bytes, not the .git/index file bytes.','Earlier pure99 wrapper pre-pin and timeout-field limits remain in pure-python99 index.']}
 receipt=t/'receipts/importers-nine-modules.json';save(receipt,index)
 state=json.loads((t/'CURRENT_STATE.json').read_bytes());row=next(x for x in state['rows'] if x['gate']=='affected-importers')
 row['preparedCommandNotExecuted']=row.pop('originalCommand');row['originalCommand']=None
 row.update({'status':'PASS','executionSHA':S,'originalExitCode':None,'originalModuleExits':[0]*9,'actualCommands':[x['originalCommand'] for x in rows],'receipt':{'path':P+'/receipts/importers-nine-modules.json','sha256':sha(receipt.read_bytes()),'jsonPointer':'/rows'},'completedModules':[x['suite'] for x in rows],'missingModules':[],'proofScope':'Specified9of9 importer modules;142original methods; not full project native/expected aggregate or browser'})
 row.pop('partialOriginalExits',None)
 state['bindingRole']='Current original execution facts scoped per row:three predicatePASS;specified nine importer modulesPASS;remaining12UNRUN. No synthetic aggregate exit is assigned.'
 save(t/'CURRENT_STATE.json',state)
 with (t/'PROGRESS.md').open('a') as f:f.write('\n## 兩原native importer module：43/43；指定九module總142/142\n\n固定S57薄source，原host_native30完整30/30（含真fresh fallback編譯），原private binaries.main build bridge/model-base exit0，原default_native13完整13/13、0fail／0skip；原outer／collector0，493Git inputs原始/LF初末同、HEAD/status clean與ls-files --stage輸出同，不冒.index檔bytes。全程secondary.lock序列，20:23:54終態正常釋鎖。\n\n前七99加此43＝指定九module142/142；actualCommands是各原_unittest_runner.py，準備版run_all --build --only診斷未執行，沒有冒aggregate結果。原compile900s／host fallback60s／default捕捉30s與各module1200s保留。完整公開stdout/stderr、raw Gitbatch493inputs、兩ELF與sidecars全部封包；原程式內部未公開pipes不另冒逐條流。fullnative＋expected、registry-list、六browser、mutation check及架構等12列仍UNRUN。\n')
 manifest=json.loads((t/'PACKAGE_MANIFEST.json').read_bytes());files={}
 for path in sorted(t.rglob('*')):
  if path.is_file() and path!=t/'PACKAGE_MANIFEST.json':
   raw=path.read_bytes();files[path.relative_to(t).as_posix()]={'bytes':len(raw),'sha256':sha(raw)}
 manifest.update(files=files,formalRowsRemainUNRUN=12,partialFormalRows=0,remainingIncompleteGates=12);save(t/'PACKAGE_MANIFEST.json',manifest)
 run(['git','add','--force','--sparse','--',P]);_,staged,_=run(['git','diff','--cached','--name-only','-z'])
 if any(not x.decode().startswith(P+'/') for x in staged.split(b'\0') if x):raise RuntimeError('stage outside own evidence')
 run(['git','diff','--cached','--check','--',P+'/CURRENT_STATE.json',P+'/PACKAGE_MANIFEST.json',P+'/PROGRESS.md',P+'/receipts/importers-nine-modules.json',P+'/revision-7-native43/publish_native43_actual.py'])
 run(['git','commit','-m','test(geo324): archive43native importer tests and nine module index'])
 _,head,_=run(['git','rev-parse','HEAD']);report['evidenceHead']=head.decode().strip()
 run(['git','push','origin','refs/heads/'+BR+':refs/heads/'+BR]);_,remote,_=run(['git','ls-remote','--exit-code','origin','refs/heads/'+BR]);report['remoteEvidenceHead']=remote.decode().split()[0]
 if report['remoteEvidenceHead']!=report['evidenceHead']:raise RuntimeError('remote evidence mismatch')
 body=(D/'PR_BODY.md').read_text();edits=[(E,report['evidenceHead']),('三predicate補證與七個pure Python module99tests已實跑，完整整合仍待驗收。','三predicate補證與指定九個importer module142tests已實跑，完整整合仍待驗收。'),('| affected-importers | 部分：7/9 module，99/99 | 七個`0`；兩suite未跑 |','| affected-importers | 指定9/9 module，142/142 | 九個原runner各`0` |'),('尚有13個gate未完成（12UNRUN、affected-importers部分7/9）；host_native30真fresh C build與default_native13 freshbridge/model-base先等C槽，再續fullnative＋expected、六browser、mutation check及架構。','尚有12列UNRUN：registry-list、fullnative＋expected、六browser、mutation check及架構三條。指定九module已完整，但沒有執行準備版run_all --build --only診斷，也不以各module成功冒aggregate全專案收斂。'),('不是單一fullsuite、native或全部importer。','這七個module批本身不是單一fullsuite或native；指定九module的目前完整狀態以唯一矩陣與native43原件為準。')]
 for old,new in edits:
  if body.count(old)!=1:raise RuntimeError('body narrow replacement not unique: '+old)
  body=body.replace(old,new,1)
 body+='\n兩個原C importer module另已實跑host_native30／default_native13，共43/43、0fail／0skip；先原fresh fallback編譯，再原binaries.main建bridge與model-base，皆原exit0，原私有ELF／sidecar／Git493inputs前後同。原各module1200s、compile900s、fallback60s、native捕捉30s未改。加前七99，指定九個module142/142；真命令是逐module原_unittest_runner.py，無合成aggregate exit。全數原公開stdout/stderr／環境／SHA與兩ELFbytes封raw/two-native-importer-modules-57b68014.tar.gz；內部既有capture_output未公開的pipes不另冒逐筆原流，stage守門是ls-files --stage輸出相同，非.index檔bytes。此批原件獨審見revision-7-native43；公開Git/archive對抗審仍待本批推送後進行。\n'
 (D/'PR_BODY.md').write_text(body);run(['git','add','--force','--sparse','--','PR_BODY.md'],D);_,staged,_=run(['git','diff','--cached','--name-only','-z'],D)
 if staged!=b'PR_BODY.md\0':raise RuntimeError('body stage outside exact file')
 run(['git','diff','--cached','--check'],D);run(['git','commit','-m','docs(geo324): report142importer methods and remaining gates'],D)
 _,head,_=run(['git','rev-parse','HEAD'],D);report['bodyHead']=head.decode().strip()
 run(['git','push','origin','refs/heads/'+BR+'-prbody:refs/heads/'+BR+'-prbody'],D);_,remote,_=run(['git','ls-remote','--exit-code','origin','refs/heads/'+BR+'-prbody'],D);report['remoteBodyHead']=remote.decode().split()[0]
 if report['remoteBodyHead']!=report['bodyHead']:raise RuntimeError('remote body mismatch')
 report.update(bodySHA256=sha((D/'PR_BODY.md').read_bytes()),archiveBytes=archive.stat().st_size,archiveSHA256=sha(archive.read_bytes()),archiveMembers=len(inventory),exitCode=0)
except BaseException as error:report['errors'].append(repr(error));report['exitCode']=1
finally:
 report['endedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['commandCount']=len(rec.rows);cap.dump(O/'receipt.json',report);print(json.dumps(report,ensure_ascii=False),flush=True)
raise SystemExit(report['exitCode'])
