#!/usr/bin/env python3
"""Publish the unchanged original three-predicate actual with the independent peer."""
import datetime
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tarfile

B=Path('/tmp/geo324-owner-20261024');O=B/'predicate-actual-publication-57b68014'
R=Path('/tmp/geo324-faces-work-20261024');D=Path('/tmp/geo324-faces-prbody-work-20261024')
BR='codex/geo324-faces-20261024';P='evidence/geo324-final-57b68014';S='57b680140da2c6b77ab0d362a72029d8d7c9334b'
E='47affde689e48d1ee89e4247740f694c5a069c6b';DH='6b1a111b7635f1b0d9730b72217956a507f6dd5c'
PROOF=Path('/tmp/geo324-predicate-proof-57b68014');SOURCE=Path('/tmp/geo324-predicate-source-57b68014')
LAUNCH=B/'predicate-actual-launch-57b68014'
PEER=Path('/tmp/train337-adversarial/GEO324_PREDICATE_ACTUAL_PEER.json');PEER_SHA='075f987fdc99fbedb52f9e9719946839886fe80ab6a5c9c8facb332c580e8e01'
CLARIFY=Path('/tmp/train337-adversarial/REVIEW_REPORT_EXIT_CLARIFICATION.json');CLARIFY_SHA='cd0c31d3b9768d0d84052a9d90aa4fd57d4f3b6f0451b41cb09b6d9c51c7f518'
HELPER=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py');HELPER_SHA='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
def sha(raw):return hashlib.sha256(raw).hexdigest()
if O.exists():raise SystemExit('refuse overwrite')
for path,expected in [(HELPER,HELPER_SHA),(PEER,PEER_SHA),(CLARIFY,CLARIFY_SHA)]:
    if sha(path.read_bytes())!=expected:raise SystemExit('frozen input changed: '+str(path))
inner=json.loads((PROOF/'receipt.json').read_text());peer=json.loads(PEER.read_text())
if inner['sourceSHA']!=S or inner['exitCode']!=0 or inner['proofAccepted'] is not True or peer['source_sha']!=S or peer['exit_code']!=0 or peer['findings'] or peer['receipt_sha256']!=sha((PROOF/'receipt.json').read_bytes()):raise SystemExit('actual or independent peer not accepted')
if [r['predicate'] for r in inner['rows']]!=['list','dict','feature'] or any(r['originalExitCodes']!=[0,1,0] or not r['byteRestored'] for r in inner['rows']):raise SystemExit('original proof phases not exact')
O.mkdir();spec=importlib.util.spec_from_file_location('capture',str(HELPER));cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env.pop('PYTHONOPTIMIZE',None);rec=cap.Recorder(O,env,S)
report={'schema':'geo324.original-three-predicate-actual-publication.v1','sourceSHA':S,'actualOriginalDriverExit':0,'actualOriginalPhaseExits':[[0,1,0]]*3,'independentActualPeerReportExit':0,'independentActualPeerSHA256':PEER_SHA,'oldPackagePeerReportExit':1,'oldPackagePeerActualHelperExit':0,'remainingFormalRowsUNRUN':13,'driverSHA256':sha(Path(__file__).read_bytes()),'exitCode':None,'errors':[]}
def run(a,cwd=R):return rec.run(a,cwd=cwd,timeout=180,source_sha=S,source_variant='original-three-predicate-actual-publication')
try:
    for repo,expected in ((R,E),(D,DH)):
        _,head,_=run(['git','rev-parse','HEAD'],repo);_,status,_=run(['git','status','--porcelain=v1','--untracked-files=all'],repo)
        if head.decode().strip()!=expected or status:raise RuntimeError('owner worktree moved or dirty')
    t=R/P;revision=t/'revision-5-predicate-actual';revision.mkdir()
    shutil.copyfile(t/'PACKAGE_MANIFEST.json',revision/'PREVIOUS_ROOT_MANIFEST.json')
    shutil.copyfile(PEER,revision/PEER.name);shutil.copyfile(CLARIFY,revision/CLARIFY.name)
    shutil.copytree(B/'manifest-timing-addendum-publication',revision/'prior-completed-publication')
    shutil.copyfile(Path(__file__),revision/Path(__file__).name)
    (revision/'PR_BODY_BEFORE_ACTUAL.md').write_bytes((D/'PR_BODY.md').read_bytes())
    originals={}
    for label,root in [('proof',PROOF),('launch',LAUNCH)]:
        for path in sorted(root.rglob('*')):
            if path.is_symlink():raise RuntimeError('unexpected symlink in original proof')
            if path.is_file():originals[label+'/'+path.relative_to(root).as_posix()]=path
    for row in json.loads((PROOF/'tracked-inputs.json').read_text()):
        path=SOURCE/row['path'];raw=path.read_bytes()
        if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise RuntimeError('fixed input changed before packaging')
        originals['fixed-source/'+row['path']]=path
    for name,path in [('run_face_predicate_proofs_v2.py',B/'preparation/run_face_predicate_proofs_v2.py'),('launch_predicate_actual.py',B/'launch_predicate_actual.py'),('capture.py',HELPER)]:originals['tools/'+name]=path
    raw_dir=t/'raw';raw_dir.mkdir(exist_ok=True);archive=raw_dir/'three-predicate-originals-57b68014.tar.gz';inventory=[]
    with archive.open('wb') as destination:
        with gzip.GzipFile(filename='',mode='wb',fileobj=destination,mtime=0) as compressed:
            with tarfile.open(fileobj=compressed,mode='w|') as tar:
                for name,path in sorted(originals.items()):
                    raw=path.read_bytes();inventory.append({'archivePath':name,'originalPath':str(path),'bytes':len(raw),'sha256':sha(raw)})
                    tar.add(path,arcname=name,recursive=False)
    expected={r['archivePath']:r for r in inventory};seen=set()
    with tarfile.open(archive,'r:gz') as tar:
        for member in tar:
            if member.name in seen or member.name not in expected or not member.isfile():raise RuntimeError('archive member set invalid')
            seen.add(member.name);raw=tar.extractfile(member).read();row=expected[member.name]
            if len(raw)!=row['bytes'] or sha(raw)!=row['sha256'] or raw!=originals[member.name].read_bytes():raise RuntimeError('archive original bytes mismatch')
    if seen!=set(expected):raise RuntimeError('missing archive original files')
    (raw_dir/'three-predicate-originals-57b68014.inventory.json').write_text(json.dumps({'sourceSHA':S,'files':inventory,'excludedFiles':[],'producerRoundtripVerified':True},ensure_ascii=False,indent=2)+'\n')
    receipts=t/'receipts';receipts.mkdir(exist_ok=True);receipt_path=receipts/'predicate-three-original.json';receipt_path.write_bytes((PROOF/'receipt.json').read_bytes())
    state=json.loads((t/'CURRENT_STATE.json').read_text())
    for index,key in enumerate(('list','dict','feature')):
        row=next(r for r in state['rows'] if r['gate']=='predicate-'+key)
        if row['status']!='UNRUN' or row['originalExitCode'] is not None:raise RuntimeError('predicate state was already changed')
        row.update({'executionSHA':S,'originalExitCode':[0,1,0],'status':'PASS','allowedSkip':None,'receipt':{'path':P+'/receipts/predicate-three-original.json','sha256':sha(receipt_path.read_bytes()),'jsonPointer':'/rows/'+str(index)},'proofScope':'one unchanged public Python behavioral method; original native transport is mocked; supplementary, not full45/native/browser'})
    if sum(r['status']=='UNRUN' for r in state['rows'])!=13 or len(state['rows'])!=16:raise RuntimeError('other formal rows changed')
    (t/'CURRENT_STATE.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    with (t/'PROGRESS.md').open('a') as stream:
        stream.write('\n## 三predicate實際補證\n\n固定公開產品 S57b680140da2c6b77ab0d362a72029d8d7c9334b 的獨立薄checkout，原v2工具未改，list／dict／feature三原method各真0／1／0、正常具名unclassified診斷、還原bytes與來源前後clean。setup＋actual約2.714秒；無R3、編譯、Chrome或效能量測。完整52內命令＋10外命令streams／37inputs／三還原樹／凍結工具已逐byte封包，producer roundtrip全同。獨立actual peer551 checks／0 findings；這三列PASS，另13列仍UNRUN，沒有把mock native運輸方法當完整45／native／browser。\n\n原package peer1019報告exit_code1與其helper實際process0分欄澄清，原JSON／舊E不覆寫，澄清原件同封；該metadatafinding沒有改動原test或source。\n')
    manifest=json.loads((t/'PACKAGE_MANIFEST.json').read_text());files={}
    for path in sorted(t.rglob('*')):
        if path.is_file() and path!=t/'PACKAGE_MANIFEST.json':
            raw=path.read_bytes();files[path.relative_to(t).as_posix()]={'bytes':len(raw),'sha256':sha(raw)}
    manifest['files']=files;manifest['formalRowsRemainUNRUN']=13;manifest['completedOriginalPredicateRows']=3;manifest['productTestsExecuted']=True
    (t/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    for name,row in files.items():
        raw=(t/name).read_bytes()
        if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise RuntimeError('current package manifest mismatch')
    run(['git','add','--force','--sparse','--',P]);_,staged,_=run(['git','diff','--cached','--name-only','-z'])
    if any(not x.decode().startswith(P+'/') for x in staged.split(b'\0') if x):raise RuntimeError('stage outside own evidence')
    run(['git','diff','--cached','--check','--',P+'/PROGRESS.md',P+'/CURRENT_STATE.json',P+'/PACKAGE_MANIFEST.json',P+'/revision-5-predicate-actual/publish_predicate_actual.py'])
    run(['git','commit','-m','test(geo324): archive original predicate withdrawal proofs'])
    _,head,_=run(['git','rev-parse','HEAD']);report['evidenceHead']=head.decode().strip()
    run(['git','push','origin','refs/heads/'+BR+':refs/heads/'+BR]);_,remote,_=run(['git','ls-remote','--exit-code','origin','refs/heads/'+BR]);report['remoteEvidenceHead']=remote.decode().split()[0]
    if report['remoteEvidenceHead']!=report['evidenceHead']:raise RuntimeError('evidence remote mismatch')
    rows=[]
    for row in state['rows']:
        if row['status']=='PASS':rows.append('| '+row['gate']+' | 通過（原0/1/0） | `0/1/0` | `'+S+'` |')
        else:rows.append('| '+row['gate']+' | 未執行 | `null` | `null` |')
    body='''柱／樑 native snapshot 缺少或損壞 `faces` 時，公開 evaluate 路徑回原 `UNSUPPORTED / BASE_SOURCE_BINDING / I32 / Native box source faces disagree with legacy provenance.`，避免未分類例外。這是 #324 的 Codex 替代線；已普通合入完整列車，三predicate補證已實跑，完整整合仍待驗收。

| 來源角色 | 完整SHA／分支 |
|---|---|
| 原PR-local base | `7dae5f21c7ca401e660450d437e60ba566218da8` |
| Grok原head | `4e176e830b691269cc72d021ce7e1bc0b167d621` |
| 已普通merge train | `504933473d7b9bdfc5964f73402a710f1222fc96` |
| 公開產品S／本次execution SHA | `'''+S+'''` |
| 目前evidence E | `'''+report['evidenceHead']+'''` |
| 替代head／正文分支 | `codex/geo324-faces-20261024`／`codex/geo324-faces-20261024-prbody` |
| PR預定base | `codex/train-337-continue-20261024`（列車draft #338） |

對指定train，非evidence差恰原三檔121+/2-；兩leaf等Grok原blobs，expected只host_sources39→45，其餘metadata精確等train；SSOT／決策blob原字等train。合流純靜審254 checks／0 findings，不代正式執行。沒有rebase、force push或合併PR。

唯一current-state矩陣：三predicate原命令序列是baseline／withdraw／restored；`null`是未跑，不是skip。45只是expected契約，本輪未跑完整45。

| Gate | 目前結果 | 原 exit | execution SHA |
|---|---|---|---|
'''+ '\n'.join(rows)+'''

原v2 driver SHA `4b5c05f1a2d7a5cf24c1e2b4d21641c560a7fe7a25db1109a6127d315ddd406d` 未改。獨立薄checkout先逐Git原blob／工作bytes核37inputs，只複製精確tracked四packages／三fixtures；原三公開Python method各真0/1/0，撤回每組有column／beam兩個正常AssertionError及精確null／nested-list／feature-list TypeError／AttributeError診斷，無ERROR、import、crash、skip或timeout。每phase原60秒保留，來源前後clean、三份產品bytes還原。原helper mock native transport，這批不是native或browser驗收。

52內命令＋10外setup命令的argv／exit／環境／SHA／完整stdout/stderr、37inputs、三份還原樹與凍結工具全封於 `'''+P+'''/raw/three-predicate-originals-57b68014.tar.gz`，逐member inventory無排除且producer roundtrip逐bytes同。原receipt SHA `58bf107cbe1207cf695c81b11001881e233075c4782dd6673ed08e4d878b85fb`；獨立actual peer551 checks／報告0且原helper process0，SHA `'''+PEER_SHA+'''`，同封revision-5。

先前metadata修正／原件完整保留：原出版collector1是對原patch whitespace跑check所得2，raw未改；manifest自索引排除自身；E495 generated PROGRESS合法追加6行，舊true只指寫新metadata前對E792 snapshot的驗證時點。原package peer1019有1finding（report exit_code1，helper實際process0），精確澄清另封，不把原報告回寫成綠。這些不是產品裁判結果。

架構原四檔屬incoming train的sourceBaseHead，#324 owned W leaf／excluded test需原三裁判與四檔刷新，尚未跑；mutation bridge oracle hash讀tests/*.py，不能把列車帳本直接當本S有效，完整帳本由root統排。其餘13列依root時槽繼續，下一步先完整45／affected importer，再同SHA full native＋expected、六browser、mutation check及架構。沒有新增skip或放寬斷言，不宣稱可合併。
'''
    (D/'PR_BODY.md').write_text(body);run(['git','add','--force','--sparse','--','PR_BODY.md'],D);_,staged,_=run(['git','diff','--cached','--name-only','-z'],D)
    if staged!=b'PR_BODY.md\0':raise RuntimeError('body stage outside exact file')
    run(['git','diff','--cached','--check'],D);run(['git','commit','-m','docs(geo324): report actual predicate proofs and remaining gates'],D)
    _,head,_=run(['git','rev-parse','HEAD'],D);report['bodyHead']=head.decode().strip()
    run(['git','push','origin','refs/heads/'+BR+'-prbody:refs/heads/'+BR+'-prbody'],D);_,remote,_=run(['git','ls-remote','--exit-code','origin','refs/heads/'+BR+'-prbody'],D);report['remoteBodyHead']=remote.decode().split()[0]
    if report['remoteBodyHead']!=report['bodyHead']:raise RuntimeError('body remote mismatch')
    report['bodySHA256']=sha((D/'PR_BODY.md').read_bytes());report['archiveSHA256']=sha(archive.read_bytes());report['archiveBytes']=archive.stat().st_size;report['archiveMembers']=len(inventory);report['exitCode']=0
except BaseException as error:report['errors'].append(repr(error));report['exitCode']=1
finally:
    report['endedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['commandCount']=len(rec.rows);cap.dump(O/'receipt.json',report);print(json.dumps(report,ensure_ascii=False))
raise SystemExit(report['exitCode'])
