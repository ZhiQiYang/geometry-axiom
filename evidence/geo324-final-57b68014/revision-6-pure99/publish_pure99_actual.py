#!/usr/bin/env python3
"""Publish seven original pure-Python modules, preserving earlier environment failures."""
import datetime
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tarfile

B=Path('/tmp/geo324-owner-20261024');O=B/'pure99-publication-57b68014'
R=Path('/tmp/geo324-faces-work-20261024');D=Path('/tmp/geo324-faces-prbody-work-20261024')
BR='codex/geo324-faces-20261024';P='evidence/geo324-final-57b68014';S='57b680140da2c6b77ab0d362a72029d8d7c9334b'
E='602b393298b7217347532c7f8b0faba118e02e45';DH='a15cfe3778f30feff3548d7465aa97e16c9148d7'
SOURCE=Path('/tmp/geo324-predicate-source-57b68014')
RUNS={'pure65-r1':Path('/tmp/geo324-pure-suite-57b68014-r1'),'pure65-r2':Path('/tmp/geo324-pure-suite-57b68014-r2'),'pure18':Path('/tmp/geo324-more-pure-57b68014-r1'),'domain-pins-r1':Path('/tmp/geo324-domain-pins-57b68014-r1'),'domain-pins-r2':Path('/tmp/geo324-domain-pins-57b68014-r2')}
PEERS={
 '/tmp/train337-adversarial/GEO324_PURE65_ACTUAL_PEER.json':'ecb3b9ed8538a8bf98a39d1419e71c695eaf896239afd7757858ca53741aac81',
 '/tmp/train337-adversarial/GEO324_PURE18_ACTUAL_PEER.json':'2c8d256b1da68480693ae5c7f5371cc1d4807f629661d9b4d0a6aff40eab6fde',
 '/tmp/train337-adversarial/GEO324_DOMAIN_PINS_ACTUAL_PEER.json':'2afbbe135ad1c5f10fd104bf6074f2ed5ef12762ef0f762ce5350cb934c9f6b7',
 '/tmp/train337-adversarial/GEO324_PREDICATE_PUBLICATION_PEER.json':'cb84763e199578422cb684a05b2e73b98c416e6eae89c1ccc2e6cdc0d682457e'}
HELPER=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py');HPIN='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
def sha(raw):return hashlib.sha256(raw).hexdigest()
if O.exists():raise SystemExit('refuse overwrite')
if sha(HELPER.read_bytes())!=HPIN:raise SystemExit('capture pin changed')
for path,pin in PEERS.items():
 if sha(Path(path).read_bytes())!=pin:raise SystemExit('peer changed')
good=[(k,json.loads((RUNS[k]/'receipt.json').read_text())) for k in ('pure65-r2','pure18','domain-pins-r2')]
for name,r in good:
 if r['exitCode']!=0 or r['sourceAfter']!={'head':S,'porcelain':''} or any(x['executionSHA']!=S or x['originalProcessExit']!=0 or x['originalResult']['failed'] or x['originalResult']['skipped'] for x in r['rows']):raise SystemExit('original actual not accepted')
if sum(x['originalResult']['passed'] for _,r in good for x in r['rows'])!=99:raise SystemExit('expected seven-module actual scope differs')
O.mkdir();spec=importlib.util.spec_from_file_location('capture',str(HELPER));cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env.pop('PYTHONOPTIMIZE',None);rec=cap.Recorder(O,env,S)
report={'schema':'geo324.seven-pure-module-publication.v1','sourceSHA':S,'originalSuiteExits':[0]*7,'originalSuiteTests':[45,10,10,9,8,1,16],'originalSuitePassCount':99,'nativeOrBrowserOrFullImporterCompletion':False,'exitCode':None,'errors':[],'driverSHA256':sha(Path(__file__).read_bytes())}
def run(a,cwd=R):return rec.run(a,cwd=cwd,timeout=180,source_sha=S,source_variant='seven-original-pure-module-evidence-publication')
try:
 for repo,expected in ((R,E),(D,DH)):
  _,h,_=run(['git','rev-parse','HEAD'],repo);_,clean,_=run(['git','status','--porcelain=v1','--untracked-files=all'],repo)
  if h.decode().strip()!=expected or clean:raise RuntimeError('owner checkout drifted')
 t=R/P;revision=t/'revision-6-pure99';revision.mkdir()
 shutil.copyfile(t/'PACKAGE_MANIFEST.json',revision/'PREVIOUS_ROOT_MANIFEST.json')
 shutil.copytree(B/'predicate-actual-publication-57b68014',revision/'prior-completed-publication')
 shutil.copyfile(Path(__file__),revision/Path(__file__).name)
 for path in PEERS:shutil.copyfile(path,revision/Path(path).name)
 (revision/'PR_BODY_BEFORE_PURE99.md').write_bytes((D/'PR_BODY.md').read_bytes())
 originals={};fixed={}
 for label,root in RUNS.items():
  for path in sorted(root.rglob('*')):
   if path.is_symlink():raise RuntimeError('unexpected original symlink')
   if path.is_file():originals[label+'/'+path.relative_to(root).as_posix()]=path
  if (root/'INPUTS.json').exists():
   for row in json.loads((root/'INPUTS.json').read_text()):
    if row['path'] in fixed and fixed[row['path']]!=row:raise RuntimeError('original source input identity differs between runs')
    fixed[row['path']]=row
 for name,row in fixed.items():
  path=SOURCE/name;raw=path.read_bytes()
  if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise RuntimeError('retained original input changed')
  originals['fixed-source/'+name]=path
 for name in ('run_pure_importer_suites.py','run_pure_importer_suites_r2.py','run_more_pure_importers.py','run_domain_pins_pure.py','run_domain_pins_pure_r2.py'):originals['tools/'+name]=B/name
 originals['tools/capture.py']=HELPER
 archive=t/'raw/seven-pure-modules-57b68014.tar.gz';inventory=[]
 with archive.open('wb') as destination:
  with gzip.GzipFile(filename='',mode='wb',fileobj=destination,mtime=0) as compressed:
   with tarfile.open(fileobj=compressed,mode='w|') as tar:
    for name,path in sorted(originals.items()):
     raw=path.read_bytes();inventory.append({'archivePath':name,'originalPath':str(path),'bytes':len(raw),'sha256':sha(raw)});tar.add(path,arcname=name,recursive=False)
 expected={x['archivePath']:x for x in inventory};seen=set()
 with tarfile.open(archive,'r:gz') as tar:
  for member in tar:
   if not member.isfile() or member.name not in expected or member.name in seen:raise RuntimeError('unexpected archive member')
   seen.add(member.name);raw=tar.extractfile(member).read();r=expected[member.name]
   if len(raw)!=r['bytes'] or sha(raw)!=r['sha256'] or raw!=originals[member.name].read_bytes():raise RuntimeError('archive not exact original bytes')
 if seen!=set(expected):raise RuntimeError('archive is incomplete')
 (t/'raw/seven-pure-modules-57b68014.inventory.json').write_text(json.dumps({'sourceSHA':S,'files':inventory,'excludedFiles':[],'producerRoundtripVerified':True},ensure_ascii=False,indent=2)+'\n')
 result_rows=[]
 for label,r in good:
  for row in r['rows']:result_rows.append({'archiveReceipt':label+'/receipt.json','originalReceiptSHA256':sha((RUNS[label]/'receipt.json').read_bytes()),**row})
 index={'schema':'geo324.original-seven-module-result-index.v1','sourceSHA':S,'rows':result_rows,'scope':'seven complete original unittest modules only;99passed,0failed,0skipped;partial project and incomplete importer set','environmentAttemptsPreserved':{'thinGitUnknownOption':{'archiveReceipt':'pure65-r1/receipt.json','collectorExit':2,'gitExit':129,'testsExecuted':0},'missingMaterializedFixture':{'archiveReceipt':'domain-pins-r1/receipt.json','originalExit':1,'originalPassed':15,'originalFailed':1,'class':'environment FileNotFoundError only;exact tracked5431B fixture added before rerunning only this suite'}},'wrapperEvidenceLimits':['Original suite launch request did not pre-pin wrapper hash; independent peer calculated preserved wrapper hashes after execution.','Original1200s is supported by saved request and wrapper; capture rows lack a timeout_seconds field. No such capture field is claimed.']}
 receipt=t/'receipts/pure-python99.json';receipt.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
 state=json.loads((t/'CURRENT_STATE.json').read_text());row=next(x for x in state['rows'] if x['gate']=='affected-importers')
 row.update({'status':'PARTIAL','executionSHA':S,'originalExitCode':None,'partialOriginalExits':[0]*7,'receipt':{'path':P+'/receipts/pure-python99.json','sha256':sha(receipt.read_bytes()),'jsonPointer':'/rows'},'completedModules':[r['suite'] for r in result_rows],'missingModules':['test_geometry_host_native','test_geo261_default_native'],'proofScope':'7of9 importer modules;99original Python tests;not full importer gate/native/browser'})
 state['bindingRole']='Current original execution facts are scoped per row:three predicatePASS;affected-importersPARTIAL;remaining12UNRUN.'
 state['publicationRole']='Containing Git commit is evidence head. Original executionSHA and exits remain explicit;null means unknown,never a skip.'
 (t/'CURRENT_STATE.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
 with (t/'PROGRESS.md').open('a') as stream:stream.write('\n## 七個原pure Python module：99/99\n\n固定同S57，原_unittest_runner完整host_sources45、source_runtime10、kernel_runtime10、rectangular_python9、host_world8、kernel_compatibility1、domain_source_pins16，全部原exit0、0fail／0skip、來源初末clean。無C、browser、R3或全域binary cache。原65／18／16獨立actual peers322／356／604 checks均0。affected-importers列只部分7/9，host_native30與default_native13真C依賴待槽；fullnative／expected aggregate與六browser未跑。\n\n原setup sparse add不支援flag129／collector2（0tests），與domain_pins少原tracked5431B fixture所致15pass1error／原exit1全部原件封存；只修物化配置後重跑受影響項，未改test／assert。原wrapper未在事前request pin hash、c387沒有timeout_seconds欄的證據限制照保。CURRENT_STATE兩句舊allunknown角色文字只在此actual批同步為逐列真狀態，不回寫原E。\n')
 manifest=json.loads((t/'PACKAGE_MANIFEST.json').read_text());files={}
 for path in sorted(t.rglob('*')):
  if path.is_file() and path!=t/'PACKAGE_MANIFEST.json':
   raw=path.read_bytes();files[path.relative_to(t).as_posix()]={'bytes':len(raw),'sha256':sha(raw)}
 manifest['files']=files;manifest['formalRowsRemainUNRUN']=12;manifest['partialFormalRows']=1;manifest['remainingIncompleteGates']=13
 (t/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 run(['git','add','--force','--sparse','--',P]);_,staged,_=run(['git','diff','--cached','--name-only','-z'])
 if any(not x.decode().startswith(P+'/') for x in staged.split(b'\0') if x):raise RuntimeError('stage outside own evidence')
 run(['git','diff','--cached','--check','--',P+'/CURRENT_STATE.json',P+'/PACKAGE_MANIFEST.json',P+'/PROGRESS.md',P+'/receipts/pure-python99.json',P+'/revision-6-pure99/publish_pure99_actual.py'])
 run(['git','commit','-m','test(geo324): archive seven pure Python importer suites'])
 _,h,_=run(['git','rev-parse','HEAD']);report['evidenceHead']=h.decode().strip()
 run(['git','push','origin','refs/heads/'+BR+':refs/heads/'+BR]);_,remote,_=run(['git','ls-remote','--exit-code','origin','refs/heads/'+BR]);report['remoteEvidenceHead']=remote.decode().split()[0]
 if report['remoteEvidenceHead']!=report['evidenceHead']:raise RuntimeError('evidence remote mismatch')
 old=(D/'PR_BODY.md').read_text();body=old
 edits=[(E,report['evidenceHead']),('三predicate補證已實跑，完整整合仍待驗收。','三predicate補證與七個pure Python module99tests已實跑，完整整合仍待驗收。'),('45只是expected契約，本輪未跑完整45。','原host_sources完整45已實跑45/45；fullnative／expected aggregate仍未跑。'),('| affected-importers | 未執行 | `null` | `null` |','| affected-importers | 部分：7/9 module，99/99 | 七個`0`；兩suite未跑 | `'+S+'` |'),('其餘13列依root時槽繼續，下一步先完整45／affected importer，再同SHA full native＋expected、六browser、mutation check及架構。','尚有13個gate未完成（12UNRUN、affected-importers部分7/9）；host_native30真fresh C build與default_native13 freshbridge/model-base先等C槽，再續fullnative＋expected、六browser、mutation check及架構。')]
 for a,b in edits:
  if body.count(a)!=1:raise RuntimeError('body narrow replacement not unique: '+a)
  body=body.replace(a,b,1)
 body+='\n七個完整原Python module：host_sources45、source_runtime10、kernel_runtime10、rectangular_python9、host_world8、kernel_compatibility1、domain_source_pins16，共99/99、0fail／0skip，原runner各exit0、execution同S57，source每批前後clean；不是單一fullsuite、native或全部importer。65／18／16原件獨審322／356／604 checks各0；原request與保留wrapper支持1200秒，c387沒有timeout_seconds欄，wrapper hash是事後獨審所計而非事前pin，這些限制不抹除。完整raw、原環境失敗與7個module原JSON/log、固定Git inputs、凍結tools封於raw/seven-pure-modules-57b68014.tar.gz；沒有改測試或斷言。\n'
 (D/'PR_BODY.md').write_text(body);run(['git','add','--force','--sparse','--','PR_BODY.md'],D);_,staged,_=run(['git','diff','--cached','--name-only','-z'],D)
 if staged!=b'PR_BODY.md\0':raise RuntimeError('body stage outside exact file')
 run(['git','diff','--cached','--check'],D);run(['git','commit','-m','docs(geo324): report99pure tests and incomplete native gates'],D)
 _,h,_=run(['git','rev-parse','HEAD'],D);report['bodyHead']=h.decode().strip()
 run(['git','push','origin','refs/heads/'+BR+'-prbody:refs/heads/'+BR+'-prbody'],D);_,remote,_=run(['git','ls-remote','--exit-code','origin','refs/heads/'+BR+'-prbody'],D);report['remoteBodyHead']=remote.decode().split()[0]
 if report['remoteBodyHead']!=report['bodyHead']:raise RuntimeError('body remote mismatch')
 report['bodySHA256']=sha((D/'PR_BODY.md').read_bytes());report['archiveBytes']=archive.stat().st_size;report['archiveSHA256']=sha(archive.read_bytes());report['archiveMembers']=len(inventory);report['exitCode']=0
except BaseException as error:report['errors'].append(repr(error));report['exitCode']=1
finally:
 report['endedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['commandCount']=len(rec.rows);cap.dump(O/'receipt.json',report);print(json.dumps(report,ensure_ascii=False))
raise SystemExit(report['exitCode'])
