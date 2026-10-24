#!/usr/bin/env python3
"""Publish original registry-list only; preserve earlier execution SHAs and pending gates."""
import gzip,hashlib,importlib.util,json,os,shutil,tarfile
from pathlib import Path
B=Path('/tmp/geo324-owner-20261024');O=B/'registry-list-publication-1f0ebd3e';R=Path('/tmp/geo324-faces-work-20261024');D=Path('/tmp/geo324-faces-prbody-work-20261024');A=B/'registry-list-1f0ebd3e'
P='evidence/geo324-final-57b68014';BR='codex/geo324-faces-20261024';M='1f0ebd3e2108d6a4af6b436b5dd3f604df4b8599';OLD_E='8db79c254365b43104e596b0680df47b67f52232';OLD_D='bbd963046a9ed0c4f805a784195c23a93875fd60'
H=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
PEERS={'/tmp/geo260-peer-followups/registry-list-1f0ebd3e/REVIEW.json':'ab05c5fc73f8634e22bb9d53cbf31791a56881d23a5b40277dfc7dccb01d3287','/tmp/train337-adversarial/GEO324_NATIVE43_PUBLICATION_PEER.json':'90b06f062d55cd42a30e0d38d3bb9dee5ea4ab48fcb898d8e8a6e8015b958674','/tmp/train337-adversarial/GEO339_FORWARD_340_PACKAGE_PEER.json':'44fbfe18dbe07c13387511b9004141ef47c68730c06c45fd9e20c68c3e4261ae'}
PROVENANCE=['/tmp/geo260-peer-followups/review.py','/tmp/geo260-peer-followups/FIRST_ATTEMPT_METADATA_FAILURE.json','/tmp/train337-adversarial/GEO324_NATIVE43_INITIAL_PUBLISHER_COLLECTION_SCHEMA_ERROR.json','/tmp/train337-adversarial/review_324_native43_initial_publisher_collection_error.py.txt','/tmp/train337-adversarial/GEO339_FORWARD_INITIAL_ARCHITECTURE_NAME_ERROR.json','/tmp/train337-adversarial/review_339_forward_initial_architecture_name_error.py.txt']
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
if O.exists() or sha(H.read_bytes())!='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762':raise SystemExit('out/capture mismatch')
for n,h in PEERS.items():
 if sha(Path(n).read_bytes())!=h:raise SystemExit('peer changed')
actual=json.loads((A/'receipt.json').read_bytes())
if sha((A/'receipt.json').read_bytes())!='3747b5b456db8d6704aa13128cae9c8a954c1fc2f4965e4b392187fda110bb6f' or actual['originalExit']!=0 or actual['exitCode']!=0 or actual['sourceSHA']!=M:raise SystemExit('actual not original accepted list')
O.mkdir();sp=importlib.util.spec_from_file_location('capture',H);cap=importlib.util.module_from_spec(sp);sp.loader.exec_module(cap);env=dict(os.environ);env.pop('PYTHONOPTIMIZE',None);env['PYTHONDONTWRITEBYTECODE']='1';rec=cap.Recorder(O,env,M)
report={'schema':'geo339.original-registry-list-publication.v1','sourceSHA':M,'originalExit':0,'scope':'list/discovery only;not expected aggregate, methods, build or browser','errors':[],'exitCode':None}
def run(argv,cwd=R):return rec.run(argv,cwd=cwd,timeout=180,source_sha=M,source_variant='original-registry-list-result-publication')
try:
 for repo,want in ((R,OLD_E),(D,OLD_D)):
  _,head,_=run(['git','rev-parse','HEAD'],repo);_,status,_=run(['git','status','--porcelain=v1','--untracked-files=all'],repo)
  if head.decode().strip()!=want or status:raise RuntimeError('own checkout drift')
 t=R/P;rev=t/'revision-9-registry-list';rev.mkdir()
 for n in ('CURRENT_STATE.json','PACKAGE_MANIFEST.json'):shutil.copyfile(t/n,rev/('PREVIOUS_'+n))
 (rev/'PR_BODY_BEFORE_REGISTRY_LIST.md').write_bytes((D/'PR_BODY.md').read_bytes());shutil.copyfile(Path(__file__),rev/Path(__file__).name)
 shutil.copytree(B/'forward-merge-340-publication',rev/'prior-completed-publication')
 for n in PEERS:shutil.copyfile(n,rev/Path(n).name)
 provenance=rev/'reviewer-metadata-attempts';provenance.mkdir()
 for n in PROVENANCE:shutil.copyfile(n,provenance/Path(n).name)
 originals={}
 for p in sorted(A.rglob('*')):
  if p.is_symlink():raise RuntimeError('unexpected symlink')
  if p.is_file():originals['registry-list/'+p.relative_to(A).as_posix()]=p
 originals['tools/run_registry_list_1f0ebd3e.py']=B/'run_registry_list_1f0ebd3e.py';originals['tools/capture.py']=H
 archive=t/'raw/original-registry-list-1f0ebd3e.tar.gz';inventory=[]
 with archive.open('wb') as destination:
  with gzip.GzipFile(filename='',fileobj=destination,mode='wb',mtime=0) as compressed:
   with tarfile.open(fileobj=compressed,mode='w|') as tar:
    for n,p in sorted(originals.items()):
     b=p.read_bytes();inventory.append({'archivePath':n,'originalPath':str(p),'bytes':len(b),'sha256':sha(b)});tar.add(p,arcname=n,recursive=False)
 expected={x['archivePath']:x for x in inventory};seen=set()
 with tarfile.open(archive,'r:gz') as tar:
  for m in tar:
   if not m.isfile() or m.name not in expected or m.name in seen:raise RuntimeError('unexpected archive member')
   seen.add(m.name);b=tar.extractfile(m).read();row=expected[m.name]
   if len(b)!=row['bytes'] or sha(b)!=row['sha256'] or b!=originals[m.name].read_bytes():raise RuntimeError('original roundtrip mismatch')
 if seen!=set(expected):raise RuntimeError('archive incomplete')
 save(t/'raw/original-registry-list-1f0ebd3e.inventory.json',{'sourceSHA':M,'files':inventory,'excludedFiles':[],'producerRoundtripVerified':True})
 receipt=t/'receipts/registry-list-original.json';shutil.copyfile(A/'receipt.json',receipt)
 state=json.loads((t/'CURRENT_STATE.json').read_bytes());row=next(x for x in state['rows'] if x['gate']=='registry-list');row.update({'status':'PASS','executionSHA':M,'originalExitCode':0,'receipt':{'path':P+'/receipts/registry-list-original.json','sha256':sha(receipt.read_bytes()),'jsonPointer':'/originalExit'},'proofScope':'Original --list registry/discovery and required-entry existence only; no test-method, build, browser or full expected acceptance'})
 state['bindingRole']='Original registry-list0 at current M;four completed importer/predicate rows retain executionS57;other11rowsUNRUN. No expected/native/browser acceptance is inferred from list.';save(t/'CURRENT_STATE.json',state)
 with (t/'PROGRESS.md').open('a') as f:f.write('\n## 原registry-list清點0（不執行方法）\n\nM1f0獨立薄checkout先補原M全部tests根py/js/cjs/mjs與run_all literal已登錄owner/browser入口，347inputs逐Gitblob同。真原python3 -B tests/run_all.py --list exit0，12capture commands原fullstreams，前後M clean/stage列印/inputhash同；沒有build、測試方法、expected比較或browser執行。原stdout各正式入口都明說本命令未驗。清點actual子peer802／0；包裹它的多任務peer腳本在後續noWood schema檢查錯退出1，只有thread原stderr而無獨立stderr檔，原provenance保留，不冒整helper0。\n\n另外合封C43公開Git包peer359／0、forwardmerge/package peer358／0；各自初版metadata工具錯誤與無獨立capture限制照保。forwardmerge transitive執行閉包另由323審查，該358報告不冒此項完成。142／predicate仍原S57；現在11其他列UNRUN，未以清點冒全專案綠。\n')
 manifest=json.loads((t/'PACKAGE_MANIFEST.json').read_bytes());files={}
 for p in sorted(t.rglob('*')):
  if p.is_file() and p!=t/'PACKAGE_MANIFEST.json':b=p.read_bytes();files[p.relative_to(t).as_posix()]={'bytes':len(b),'sha256':sha(b)}
 manifest.update(files=files,formalRowsRemainUNRUN=11,remainingIncompleteGates=11);save(t/'PACKAGE_MANIFEST.json',manifest)
 run(['git','add','--force','--sparse','--',P]);_,staged,_=run(['git','diff','--cached','--name-only','-z'])
 if any(not x.decode().startswith(P+'/') for x in staged.split(b'\0') if x):raise RuntimeError('stage outside own prefix')
 run(['git','diff','--cached','--check','--',P+'/CURRENT_STATE.json',P+'/PACKAGE_MANIFEST.json',P+'/PROGRESS.md',P+'/revision-9-registry-list/publish_registry_list_actual.py']);run(['git','commit','-m','test(geo339): archive original registry discovery result'])
 _,head,_=run(['git','rev-parse','HEAD']);report['evidenceHead']=head.decode().strip()
 run(['git','push','origin','refs/heads/'+BR+':refs/heads/'+BR]);_,remote,_=run(['git','ls-remote','--exit-code','origin','refs/heads/'+BR]);report['remoteEvidenceHead']=remote.decode().split()[0]
 if report['remoteEvidenceHead']!=report['evidenceHead']:raise RuntimeError('remote evidence mismatch')
 body=(D/'PR_BODY.md').read_text();edits=[(OLD_E,report['evidenceHead']),('| registry-list | 未執行 | `null` | `null` |','| registry-list | 原清點通過（非expected） | `0` | `'+M+'` |'),('尚有12列UNRUN：registry-list、fullnative＋expected、六browser、mutation check及架構三條。','尚有11列UNRUN：fullnative＋expected、六browser、mutation check及架構三條。'),('公開Git/archive對抗審仍待本批推送後進行。','固定Ecfdfa公開Git/archive獨審359 checks／0，原report及首版metadata錯誤另封revision-9。'),('12UNRUN狀態不變。','該合流快照曾有12UNRUN；本次只補registry-list0，其餘11UNRUN。')]
 for a,b in edits:
  if body.count(a)!=1:raise RuntimeError('nonunique narrow body edit: '+a)
  body=body.replace(a,b,1)
 body+='\nM1f0原python3 -B tests/run_all.py --list已真exit0，只驗registry/discovery與已登錄入口存在性，不執行方法、expected比較、Cbuild或browser；347原Git inputs／12capture原命令與初末clean完整封raw/original-registry-list-1f0ebd3e.tar.gz。獨立actual子報告802 checks／0；包裹該報告的peer整體在後續另一項schema檢查退出1、無獨立stderrcapture，精確限制與原provenance同封。C43公開peer359／0、forwardmerge/package358／0也已封；後者不包含九module transitive讀取路徑審查，該項仍另待323。11UNRUN維持，沒有可合併宣稱。\n'
 (D/'PR_BODY.md').write_text(body);run(['git','add','--force','--sparse','--','PR_BODY.md'],D);_,staged,_=run(['git','diff','--cached','--name-only','-z'],D)
 if staged!=b'PR_BODY.md\0':raise RuntimeError('body outside exact file')
 run(['git','diff','--cached','--check'],D);run(['git','commit','-m','docs(geo339): distinguish registry listing from integration acceptance'],D);_,head,_=run(['git','rev-parse','HEAD'],D);report['bodyHead']=head.decode().strip()
 run(['git','push','origin','refs/heads/'+BR+'-prbody:refs/heads/'+BR+'-prbody'],D);_,remote,_=run(['git','ls-remote','--exit-code','origin','refs/heads/'+BR+'-prbody'],D);report['remoteBodyHead']=remote.decode().split()[0]
 if report['remoteBodyHead']!=report['bodyHead']:raise RuntimeError('remote body mismatch')
 report.update(bodySHA256=sha((D/'PR_BODY.md').read_bytes()),archiveBytes=archive.stat().st_size,archiveSHA256=sha(archive.read_bytes()),archiveMembers=len(inventory),exitCode=0)
except BaseException as e:report['errors'].append(repr(e));report['exitCode']=1
finally:cap.dump(O/'receipt.json',report);print(json.dumps(report,ensure_ascii=False),flush=True)
raise SystemExit(report['exitCode'])
