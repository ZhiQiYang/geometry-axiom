#!/usr/bin/env python3
"""Publish ordinary #340 forward-merge provenance; no subject tests or changed verdicts."""
import gzip,hashlib,importlib.util,json,os,shutil,tarfile
from pathlib import Path
B=Path('/tmp/geo324-owner-20261024');O=B/'forward-merge-340-publication';R=Path('/tmp/geo324-faces-work-20261024');D=Path('/tmp/geo324-faces-prbody-work-20261024')
P='evidence/geo324-final-57b68014';BR='codex/geo324-faces-20261024';M='1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599';S='57b680140da2c6b77ab0d362a72029d8d7c9334b';I='4d3a17c306cad42057589c5cfd964f1c32b755c4';OLD_E='cfdfa078abb38a46bda72e10056ddcc0ef74fb42';OLD_D='782721b20243665e693729b6116d45d8ea4d30ba'
H=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
if O.exists() or sha(H.read_bytes())!='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762':raise SystemExit('output/pin mismatch')
merger=json.loads((B/'merge-340-4d3a17c3-r3/receipt.json').read_bytes())
if merger['exitCode']!=0 or merger['sourceHead']!=M or merger['remoteSourceHead']!=M:raise SystemExit('merge not accepted')
O.mkdir();sp=importlib.util.spec_from_file_location('capture',H);cap=importlib.util.module_from_spec(sp);sp.loader.exec_module(cap);env=dict(os.environ);env.pop('PYTHONOPTIMIZE',None);env['PYTHONDONTWRITEBYTECODE']='1';rec=cap.Recorder(O,env,M)
report={'schema':'geo324.forward-340-publication.v1','sourceHead':M,'executionSourceHeadPreserved':S,'testExecution':False,'errors':[],'exitCode':None}
def run(argv,cwd=R):return rec.run(argv,cwd=cwd,timeout=180,source_sha=M,source_variant='ordinary-forward-merge-metadata-publication')
try:
 for repo,want in ((R,M),(D,OLD_D)):
  _,head,_=run(['git','rev-parse','HEAD'],repo);_,status,_=run(['git','status','--porcelain=v1','--untracked-files=all'],repo)
  if head.decode().strip()!=want or status:raise RuntimeError('own checkout drifted')
 run(['git','sparse-checkout','add','/'+P+'/'])
 t=R/P;rev=t/'revision-8-forward-340';rev.mkdir()
 for n in ('CURRENT_STATE.json','PACKAGE_MANIFEST.json'):shutil.copyfile(t/n,rev/('PREVIOUS_'+n))
 shutil.copyfile(Path(__file__),rev/Path(__file__).name);(rev/'PR_BODY_BEFORE_FORWARD_MERGE.md').write_bytes((D/'PR_BODY.md').read_bytes())
 shutil.copytree(B/'native43-publication-57b68014',rev/'prior-completed-native43-publication')
 originals={}
 for label,root in {'merge-r1-missing-object':B/'merge-340-4d3a17c3','merge-r2-committed-sparse-read-failure':B/'merge-340-4d3a17c3-r2','merge-r3-blob-read-finish':B/'merge-340-4d3a17c3-r3'}.items():
  for p in sorted(root.rglob('*')):
   if p.is_symlink():raise RuntimeError('unexpected symlink')
   if p.is_file():originals[label+'/'+p.relative_to(root).as_posix()]=p
 for n in ('merge_340_baton.py','merge_340_baton_r2.py','finish_merge_340_baton_r3.py'):originals['tools/'+n]=B/n
 originals['tools/capture.py']=H
 archive=t/'raw/forward-merge-340-1f0ebd3e.tar.gz';inventory=[]
 with archive.open('wb') as output:
  with gzip.GzipFile(filename='',fileobj=output,mode='wb',mtime=0) as compressed:
   with tarfile.open(fileobj=compressed,mode='w|') as tar:
    for n,p in sorted(originals.items()):
     b=p.read_bytes();inventory.append({'archivePath':n,'originalPath':str(p),'bytes':len(b),'sha256':sha(b)});tar.add(p,arcname=n,recursive=False)
 expected={x['archivePath']:x for x in inventory};seen=set()
 with tarfile.open(archive,'r:gz') as tar:
  for m in tar:
   if not m.isfile() or m.name not in expected or m.name in seen:raise RuntimeError('unexpected tar member')
   seen.add(m.name);b=tar.extractfile(m).read();r=expected[m.name]
   if len(b)!=r['bytes'] or sha(b)!=r['sha256'] or b!=originals[m.name].read_bytes():raise RuntimeError('original roundtrip failed')
 if seen!=set(expected):raise RuntimeError('incomplete archive')
 save(t/'raw/forward-merge-340-1f0ebd3e.inventory.json',{'sourceSHA':M,'originalExecutionSHA':S,'files':inventory,'excludedFiles':[],'producerRoundtripVerified':True})
 shutil.copyfile(B/'merge-340-4d3a17c3-r3/receipt.json',t/'receipts/forward-340-closure.json')
 state=json.loads((t/'CURRENT_STATE.json').read_bytes());state['productSourceSHA']=M;state['originalExecutionSourceSHA']=S;state['forwardMerge']={'incomingSource':I,'sourceMerge':M,'ordinaryMerge':True,'expectedUnion':'noWood13 + faces45;all other incoming metadata preserved'}
 state['bindingRole']='Current product source is forward merge M. Four completed scoped rows retain original executionS57; no new142/predicate execution claimed. Other12rows remainUNRUN; null is unknown, never skip.'
 for row in state['rows']:
  if row['status']=='PASS':row['sourceApplicability']={'currentProductSourceSHA':M,'originalExecutionSHA':S,'basis':'unchanged product/importer/selected contract closure;full493 materialization superset has four explicit nonexecuted-test/other-contract differences','closureReceipt':P+'/receipts/forward-340-closure.json','independentForwardMergePeer':'pending'}
 save(t/'CURRENT_STATE.json',state)
 with (t/'PROGRESS.md').open('a') as f:f.write('\n## 普通合入 #340：來源1f0ebd3e\n\n精確incoming4d3a17c3普通雙親merge至本線1f0ebd3e，對incoming非evidence仍只有faces兩leaf＋expected host_sources39→45，noWood13與其餘metadata、SSOT／queue原字保留。產品四根與currentC相對原142實測S57不變，原493廣物化集合只有expected與三個非target test葉不同，九target contracts相同。142與predicate0/1/0均保原executionS57，不冒新merge執行。架構四衍生檔與FIELD-RULES有限排除另明列；改變的三test驗收仍按各自原收據角色，不能由此closure冒新實跑。\n\nr1 incomingGitobject尚未fetch，show128／collector1未啟merge；r2 fetch0／merge0後誤從未物化evidence路徑讀JSON而FileNotFoundError／collector1，r3只改讀原Gitblob後完成核與普通push0。原raw全保，不改測試也不把metadata失敗當產品紅。現在base建議為codex/kernel-without-woodworking-20261023，root統一送請求；尚12列UNRUN，未合併PR。\n')
 manifest=json.loads((t/'PACKAGE_MANIFEST.json').read_bytes());files={}
 for p in sorted(t.rglob('*')):
  if p.is_file() and p!=t/'PACKAGE_MANIFEST.json':b=p.read_bytes();files[p.relative_to(t).as_posix()]={'bytes':len(b),'sha256':sha(b)}
 manifest.update(files=files,currentProductSourceSHA=M,originalAcceptanceSourceSHA=S);save(t/'PACKAGE_MANIFEST.json',manifest)
 run(['git','add','--force','--sparse','--',P]);_,staged,_=run(['git','diff','--cached','--name-only','-z'])
 if any(not n.decode().startswith(P+'/') for n in staged.split(b'\0') if n):raise RuntimeError('stage beyond own evidence')
 run(['git','diff','--cached','--check','--',P+'/CURRENT_STATE.json',P+'/PACKAGE_MANIFEST.json',P+'/PROGRESS.md',P+'/revision-8-forward-340/publish_forward_merge_340.py'])
 run(['git','commit','-m','docs(geo324): record ordinary no-woodworking merge provenance'])
 _,head,_=run(['git','rev-parse','HEAD']);report['evidenceHead']=head.decode().strip()
 run(['git','push','origin','refs/heads/'+BR+':refs/heads/'+BR]);_,remote,_=run(['git','ls-remote','--exit-code','origin','refs/heads/'+BR]);report['remoteEvidenceHead']=remote.decode().split()[0]
 if report['remoteEvidenceHead']!=report['evidenceHead']:raise RuntimeError('remote evidence mismatch')
 body=(D/'PR_BODY.md').read_text();old='| 公開產品S／本次execution SHA | `'+S+'` |';new='| 目前公開產品source M | `'+M+'` |\n| 原142／predicate實測execution S | `'+S+'` |\n| 已普通merge #340 source | `'+I+'` |'
 edits=[(old,new),(OLD_E,report['evidenceHead']),('| PR預定base | `codex/train-337-continue-20261024`（列車draft #338） |','| PR建議base | `codex/kernel-without-woodworking-20261023`（draft #340；root統一送變更請求） |'),('已普通合入完整列車，','已普通合入完整列車及#340，')]
 for a,b in edits:
  if body.count(a)!=1:raise RuntimeError('nonunique body edit: '+a)
  body=body.replace(a,b,1)
 body+='\n本線已普通merge #340精確source4d3a17c3至M1f0ebd3e，保faces45、noWood13與上游其餘registry。142／predicate實測仍只綁原S57；沒有在M重跑。完整產品四根／currentC與原S相同，九selected contracts同；原493廣集合變更僅expected與mutation_migration／wood_contact_world／rectangular_template三個非target測試葉，閉包原件見receipts/forward-340-closure.json，獨立forward-merge peer待核。原三個metadata回合失敗與原raw均保；12UNRUN狀態不變。\n'
 (D/'PR_BODY.md').write_text(body);run(['git','add','--force','--sparse','--','PR_BODY.md'],D);_,staged,_=run(['git','diff','--cached','--name-only','-z'],D)
 if staged!=b'PR_BODY.md\0':raise RuntimeError('body stage beyond exact file')
 run(['git','diff','--cached','--check'],D);run(['git','commit','-m','docs(geo324): distinguish merged source from original execution SHA'],D);_,head,_=run(['git','rev-parse','HEAD'],D);report['bodyHead']=head.decode().strip()
 run(['git','push','origin','refs/heads/'+BR+'-prbody:refs/heads/'+BR+'-prbody'],D);_,remote,_=run(['git','ls-remote','--exit-code','origin','refs/heads/'+BR+'-prbody'],D);report['remoteBodyHead']=remote.decode().split()[0]
 if report['remoteBodyHead']!=report['bodyHead']:raise RuntimeError('remote body mismatch')
 report.update(bodySHA256=sha((D/'PR_BODY.md').read_bytes()),archiveBytes=archive.stat().st_size,archiveSHA256=sha(archive.read_bytes()),archiveMembers=len(inventory),exitCode=0)
except BaseException as e:report['errors'].append(repr(e));report['exitCode']=1
finally:cap.dump(O/'receipt.json',report);print(json.dumps(report,ensure_ascii=False),flush=True)
raise SystemExit(report['exitCode'])
