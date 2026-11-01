#!/usr/bin/env python3
"""Publish completed source peer and a transparent evidence-only manifest correction."""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil

B=Path('/tmp/geo324-owner-20261024');OUT=B/'merge-peer-and-manifest-correction-publication'
R=Path('/tmp/geo324-faces-work-20261024');D=Path('/tmp/geo324-faces-prbody-work-20261024')
BR='codex/geo324-faces-20261024';PREFIX='evidence/geo324-final-57b68014'
S='57b680140da2c6b77ab0d362a72029d8d7c9334b'
OLD_E='792d086eb046263384888b3b0a064ae96f0cdc27';OLD_D='df3c0dbdfc6092c264204f575000590f970f933b'
PEER=Path('/tmp/train337-adversarial/GEO324_MERGE_57B_STATIC_PEER.json')
PEER_SHA='8c1b1af8b8775b3b1fef645046d0535f956782fdd9127c013dfc6a43aca03761'
CAPTURE=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
CAPTURE_SHA='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
def sha(raw):return hashlib.sha256(raw).hexdigest()
if OUT.exists():raise SystemExit('refuse overwrite')
if sha(CAPTURE.read_bytes())!=CAPTURE_SHA or sha(PEER.read_bytes())!=PEER_SHA:raise SystemExit('frozen helper or peer hash mismatch')
OUT.mkdir()
spec=importlib.util.spec_from_file_location('capture',str(CAPTURE));cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env.pop('PYTHONOPTIMIZE',None)
rec=cap.Recorder(OUT,env,S)
report={'schema':'geo324.peer-manifest-correction-publication.v1','sourceSHA':S,'productTestsExecuted':False,'priorEvidenceHead':OLD_E,'priorBodyHead':OLD_D,'priorIndependentSourcePeerSHA256':PEER_SHA,'driverSHA256':sha(Path(__file__).read_bytes()),'captureSHA256':CAPTURE_SHA,'exitCode':None,'errors':[]}
def run(argv,cwd=R):return rec.run(argv,cwd=cwd,timeout=180,source_variant='metadata-peer-publication-manifest-correction')
def matrix(text):return text.split('| Gate | 目前結果 | 原 exit | execution SHA |',1)[1].split('\n\n',1)[0]
try:
    for repo,expected in ((R,OLD_E),(D,OLD_D)):
        _,head,_=run(['git','rev-parse','HEAD'],repo);_,status,_=run(['git','status','--porcelain=v1','--untracked-files=all'],repo)
        if head.decode().strip()!=expected or status:raise RuntimeError('owner checkout drifted or dirty')
    target=R/PREFIX;manifest_path=target/'PACKAGE_MANIFEST.json';previous=manifest_path.read_bytes();old=json.loads(previous)
    if sha(previous)!='c707b52c898350673d6ebbe4dfd8be8026fe1c0b614b10c431ea8920bc1e0223':raise RuntimeError('previous manifest bytes drifted')
    if old['files']['PACKAGE_MANIFEST.json']['sha256']!='734d2ab95c6e9a4f7da8e92a7016fed3e58a35bd459baa3782b1b64e40c8b4f4':raise RuntimeError('unexpected stale self-entry')
    actual_names={p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file() and p!=manifest_path}
    if actual_names!=set(old['files'])-{'PACKAGE_MANIFEST.json'}:raise RuntimeError('old package file set differs beyond known self-entry')
    for name,row in old['files'].items():
        if name=='PACKAGE_MANIFEST.json':continue
        raw=(target/name).read_bytes()
        if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise RuntimeError('old raw changed: '+name)
    revision=target/'revision-3-peer-and-manifest';revision.mkdir()
    (revision/'PREVIOUS_PACKAGE_MANIFEST.json').write_bytes(previous)
    shutil.copyfile(PEER,revision/PEER.name)
    shutil.copytree(B/'merge-50493347-publication-resume1',revision/'prior-completed-publication')
    shutil.copyfile(Path(__file__),revision/Path(__file__).name)
    (revision/'PR_BODY_BEFORE_PEER.md').write_bytes((D/'PR_BODY.md').read_bytes())
    correction={'schema':'geo324.evidence-manifest-self-index-correction.v1','sourceSHA':S,'originalEvidenceHead':OLD_E,'originalManifestGitPath':PREFIX+'/PACKAGE_MANIFEST.json','originalManifestSHA256':sha(previous),'originalManifestPreservedAt':'PREVIOUS_PACKAGE_MANIFEST.json','defect':'The previous resume loop inventoried the prior same-name PACKAGE_MANIFEST.json as a self entry. That single entry is stale; it is not a raw-output change or product/test failure.','oldStaleSelfEntry':old['files']['PACKAGE_MANIFEST.json'],'allOtherOriginalListedFilesBytesHashVerifiedUnchanged':True,'correction':'Current root inventory explicitly excludes itself; the immutable prior manifest is a separately hashed revision member.','originalMergePeerScope':'254 checks: source merge/44 raw commands/body, not an assertion that the old complete package manifest passed.','newDynamicGateFacts':False,'formalRowsRemainUNRUN':16}
    (revision/'MANIFEST_CORRECTION.json').write_text(json.dumps(correction,ensure_ascii=False,indent=2)+'\n')
    with (target/'PROGRESS.md').open('a') as stream:
        stream.write('\n## 合流獨立靜審與 manifest 自索引修正\n\n新來源 S 的合流窄審已完成254 metadata checks／0 findings；原 peer 保於 revision-3-peer-and-manifest，不把此結果外推正式16 gate或整包驗證。完整前一18條出版命令與原 streams 同封。\n\n自查發現原E792的root manifest把前一版同名manifest也列為self-entry，只有此metadata自索引過期；原manifest完整bytes另存，所有其它列冊檔已逐bytes/hash驗證未變。新root manifest明確排除自身，原snapshot以獨立revision member守門；原出版1／raw whitespace2與完整raw全保，沒有改原輸出、產品碼或測試。正式16列仍UNRUN。\n')
    inventory={}
    for p in sorted(target.rglob('*')):
        if p.is_file() and p!=manifest_path:
            raw=p.read_bytes();inventory[p.relative_to(target).as_posix()]={'bytes':len(raw),'sha256':sha(raw)}
    manifest={'schema':'geo324.evidence-inventory.v2','sourceSHA':S,'incomingTrainSHA':'504933473d7b9bdfc5964f73402a710f1222fc96','excludedSelf':'PACKAGE_MANIFEST.json','priorImmutableManifest':'revision-3-peer-and-manifest/PREVIOUS_PACKAGE_MANIFEST.json','files':inventory,'productTestsExecuted':False,'formalRowsRemainUNRUN':16}
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    if set(inventory)!={p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file() and p!=manifest_path}:raise RuntimeError('new inventory not complete')
    for name,row in inventory.items():
        raw=(target/name).read_bytes()
        if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise RuntimeError('new package byte/hash mismatch: '+name)
    report['newManifestFiles']=len(inventory);report['oldRawFilesUnchanged']=True
    run(['git','add','--force','--sparse','--',PREFIX])
    _,staged,_=run(['git','diff','--cached','--name-only','-z'])
    if any(not p.decode().startswith(PREFIX+'/') for p in staged.split(b'\0') if p):raise RuntimeError('stage outside own evidence')
    run(['git','diff','--cached','--check','--',PREFIX+'/PROGRESS.md',PREFIX+'/PACKAGE_MANIFEST.json',PREFIX+'/revision-3-peer-and-manifest/MANIFEST_CORRECTION.json',PREFIX+'/revision-3-peer-and-manifest/publish_merge_peer_and_manifest_correction.py'])
    run(['git','commit','-m','docs(geo324): archive merge peer and correct manifest self-index'])
    _,head,_=run(['git','rev-parse','HEAD']);report['evidenceHead']=head.decode().strip()
    run(['git','push','origin','refs/heads/'+BR+':refs/heads/'+BR])
    _,remote,_=run(['git','ls-remote','--exit-code','origin','refs/heads/'+BR]);report['remoteEvidenceHead']=remote.decode().split()[0]
    if report['evidenceHead']!=report['remoteEvidenceHead']:raise RuntimeError('evidence remote mismatch')
    old_body=(D/'PR_BODY.md').read_text();body=old_body
    if body.count(OLD_E)!=1:raise RuntimeError('old body evidence identity not unique')
    body=body.replace(OLD_E,report['evidenceHead'],1)
    needle='新merge的獨立靜審待補，正式動態仍未執行。'
    if body.count(needle)!=1:raise RuntimeError('body peer clause moved')
    body=body.replace(needle,'本次merge另由train_adversarial_review完成254 metadata checks／0 findings，原source／44命令／body窄範圍原件已封；不把此窄審冒整包或正式動態通過。正式動態仍未執行。',1)
    body+='\nE792原root manifest的self-entry過期已另附保真修正：原manifest bytes與原254peer範圍保留，新root inventory排除自身並逐檔驗bytes/hash。沒有修改raw或任何gate結果；完整前一18條出版原件封於revision-3-peer-and-manifest。\n'
    if matrix(old_body)!=matrix(body) or len([line for line in matrix(body).splitlines() if '未執行' in line])!=16:raise RuntimeError('formal matrix changed')
    (D/'PR_BODY.md').write_text(body)
    run(['git','add','--force','--sparse','--','PR_BODY.md'],D)
    _,staged,_=run(['git','diff','--cached','--name-only','-z'],D)
    if staged!=b'PR_BODY.md\0':raise RuntimeError('body stage outside exact file')
    run(['git','diff','--cached','--check'],D)
    run(['git','commit','-m','docs(geo324): report source peer and evidence manifest correction'],D)
    _,head,_=run(['git','rev-parse','HEAD'],D);report['bodyHead']=head.decode().strip()
    run(['git','push','origin','refs/heads/'+BR+'-prbody:refs/heads/'+BR+'-prbody'],D)
    _,remote,_=run(['git','ls-remote','--exit-code','origin','refs/heads/'+BR+'-prbody'],D);report['remoteBodyHead']=remote.decode().split()[0]
    if report['remoteBodyHead']!=report['bodyHead']:raise RuntimeError('body remote mismatch')
    report['bodySHA256']=sha((D/'PR_BODY.md').read_bytes());report['formalRowsRemainUNRUN']=16;report['exitCode']=0
except BaseException as error:
    report['errors'].append(repr(error));report['exitCode']=1
finally:
    report['endedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['commandCount']=len(rec.rows)
    cap.dump(OUT/'receipt.json',report);print(json.dumps(report,ensure_ascii=False))
raise SystemExit(report['exitCode'])
