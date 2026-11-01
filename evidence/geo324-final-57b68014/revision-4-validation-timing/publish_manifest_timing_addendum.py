#!/usr/bin/env python3
"""Append the exact validation-time qualification requested by package peer1."""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil

B=Path('/tmp/geo324-owner-20261024');O=B/'manifest-timing-addendum-publication'
R=Path('/tmp/geo324-faces-work-20261024');D=Path('/tmp/geo324-faces-prbody-work-20261024')
BR='codex/geo324-faces-20261024';P='evidence/geo324-final-57b68014';S='57b680140da2c6b77ab0d362a72029d8d7c9334b'
E='495e625a86e54c47a0445a22056ded55b4ebab3e';PRIOR='792d086eb046263384888b3b0a064ae96f0cdc27';BODY='7eab7b7396d66879ffc35318b6780317aba631af'
PEER=Path('/tmp/train337-adversarial/GEO324_PACKAGE_V2_ACTUAL_PEER.json');PEER_SHA='f8dcbdcd89da4da3fa8b79546794f4e3c7c7e8b404bbaefbd2ed188ea9bab3f4'
HELPER=Path('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py');HELPER_SHA='c387835c03fce36be0861b7fa5228ae494ad2be94bfa9cd62d4f36b9782dc762'
def sha(raw):return hashlib.sha256(raw).hexdigest()
if O.exists():raise SystemExit('refuse overwrite')
if sha(HELPER.read_bytes())!=HELPER_SHA or sha(PEER.read_bytes())!=PEER_SHA:raise SystemExit('frozen input changed')
O.mkdir();spec=importlib.util.spec_from_file_location('capture',str(HELPER));cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env.pop('PYTHONOPTIMIZE',None);rec=cap.Recorder(O,env,S)
report={'schema':'geo324.manifest-validation-timing-addendum-publication.v1','sourceSHA':S,'productTestsExecuted':False,'originalPackagePeerExit':1,'originalPackagePeerSHA256':PEER_SHA,'exitCode':None,'errors':[],'driverSHA256':sha(Path(__file__).read_bytes())}
def run(a,cwd=R):return rec.run(a,cwd=cwd,timeout=180,source_variant='metadata-validation-timing-qualification')
def matrix(t):return t.split('| Gate | 目前結果 | 原 exit | execution SHA |',1)[1].split('\n\n',1)[0]
try:
    for repo,head in ((R,E),(D,BODY)):
        _,raw,_=run(['git','rev-parse','HEAD'],repo);_,clean,_=run(['git','status','--porcelain=v1','--untracked-files=all'],repo)
        if raw.decode().strip()!=head or clean:raise RuntimeError('owner worktree changed or dirty')
    t=R/P;mp=t/'PACKAGE_MANIFEST.json';original_manifest=mp.read_bytes();manifest=json.loads(original_manifest)
    if 'PACKAGE_MANIFEST.json' in manifest['files'] or manifest['excludedSelf']!='PACKAGE_MANIFEST.json':raise RuntimeError('v2 inventory self exclusion missing')
    if set(manifest['files'])!={p.relative_to(t).as_posix() for p in t.rglob('*') if p.is_file() and p!=mp}:raise RuntimeError('v2 current inventory file set changed')
    for name,row in manifest['files'].items():
        raw=(t/name).read_bytes()
        if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise RuntimeError('v2 listed bytes changed: '+name)
    _,prior_progress,_=run(['git','show',PRIOR+':'+P+'/PROGRESS.md'])
    _,e495_progress,_=run(['git','show',E+':'+P+'/PROGRESS.md'])
    if (t/'PROGRESS.md').read_bytes()!=e495_progress or not e495_progress.startswith(prior_progress):raise RuntimeError('PROGRESS history is not exact append-only')
    append=e495_progress[len(prior_progress):]
    if len(e495_progress.splitlines())-len(prior_progress.splitlines())!=6:raise RuntimeError('unexpected original PROGRESS append scope')
    revision=t/'revision-4-validation-timing';revision.mkdir()
    shutil.copyfile(PEER,revision/PEER.name)
    shutil.copytree(B/'merge-peer-and-manifest-correction-publication',revision/'prior-completed-publication')
    shutil.copyfile(Path(__file__),revision/Path(__file__).name)
    (revision/'E495_PACKAGE_MANIFEST.json').write_bytes(original_manifest)
    (revision/'E495_PROGRESS_APPEND.bin').write_bytes(append)
    addendum={'schema':'geo324.manifest-validation-timing-qualification.v1','sourceSHA':S,'originalStatementFile':P+'/revision-3-peer-and-manifest/MANIFEST_CORRECTION.json','originalStatementEvidenceHead':E,'originalPackagePeerExit':1,'originalPackagePeerSHA256':PEER_SHA,'statementField':'allOtherOriginalListedFilesBytesHashVerifiedUnchanged','preciseVerificationTime':'In publish_merge_peer_and_manifest_correction.py, the strict E792 existing-files verification loop completed BEFORE revision-3 creation and BEFORE PROGRESS.md was appended. The field records that pre-edit validation snapshot only. It is not an assertion that generated metadata stayed unchanged in E495 or later commits.','verifiedSnapshotEvidenceHead':PRIOR,'intentionalGeneratedMetadataChangeInE495':{'path':P+'/PROGRESS.md','operation':'append only','appendedLines':6,'priorSHA256':sha(prior_progress),'E495SHA256':sha(e495_progress),'appendBytes':len(append),'appendSHA256':sha(append),'exactAppendSnapshot':'E495_PROGRESS_APPEND.bin'},'otherIntentionalMetadataChangesInE495':['PACKAGE_MANIFEST.json regenerated excluding itself','new revision-3 metadata members added','PR_BODY.md in separate prbody branch updated'],'originalSourceAndRawOutputsUnchanged':True,'originalE495ManifestPreserved':'E495_PACKAGE_MANIFEST.json','oldPeerAndE495NotRewritten':True,'formalGateRowsUnchangedUNRUN':16}
    (revision/'VALIDATION_TIMING_ADDENDUM.json').write_text(json.dumps(addendum,ensure_ascii=False,indent=2)+'\n')
    with (t/'PROGRESS.md').open('a') as stream:
        stream.write('\n## 套件peer1的驗證時點澄清\n\n原package peer1019項有1 metadata finding，報告完整保留於revision-4-validation-timing。上節「其它列冊檔未變」與原JSON true，精確指publisher開始寫新metadata之前、對E792 snapshot逐檔驗證的時點；不指E495或此後生成的PROGRESS也維持原hash。E495合法追加6行，前後與append的精確hash/bytes及原E495 manifest另封。原source／命令raw未改，原peer1不回寫，342檔新manifest的原hash核對結果保留；本次只追加時點限定並重新列冊current所有檔。16正式仍UNRUN，新的限定等待獨立窄複核。\n')
    inventory={}
    for p in sorted(t.rglob('*')):
        if p.is_file() and p!=mp:
            raw=p.read_bytes();inventory[p.relative_to(t).as_posix()]={'bytes':len(raw),'sha256':sha(raw)}
    manifest['files']=inventory;manifest['validationTimingAddendum']='revision-4-validation-timing/VALIDATION_TIMING_ADDENDUM.json'
    mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    for name,row in inventory.items():
        raw=(t/name).read_bytes()
        if len(raw)!=row['bytes'] or sha(raw)!=row['sha256']:raise RuntimeError('current manifest mismatch: '+name)
    run(['git','add','--force','--sparse','--',P])
    _,staged,_=run(['git','diff','--cached','--name-only','-z'])
    if any(not x.decode().startswith(P+'/') for x in staged.split(b'\0') if x):raise RuntimeError('stage outside own evidence')
    run(['git','diff','--cached','--check','--',P+'/PROGRESS.md',P+'/PACKAGE_MANIFEST.json',P+'/revision-4-validation-timing/VALIDATION_TIMING_ADDENDUM.json',P+'/revision-4-validation-timing/publish_manifest_timing_addendum.py'])
    run(['git','commit','-m','docs(geo324): qualify evidence validation snapshot timing'])
    _,head,_=run(['git','rev-parse','HEAD']);report['evidenceHead']=head.decode().strip()
    run(['git','push','origin','refs/heads/'+BR+':refs/heads/'+BR])
    _,remote,_=run(['git','ls-remote','--exit-code','origin','refs/heads/'+BR]);report['remoteEvidenceHead']=remote.decode().split()[0]
    if report['remoteEvidenceHead']!=report['evidenceHead']:raise RuntimeError('evidence remote mismatch')
    old=(D/'PR_BODY.md').read_text()
    if old.count(E)!=1:raise RuntimeError('body old E identity not unique')
    new=old.replace(E,report['evidenceHead'],1)+'\n原package獨審1019項的1個metadata finding完整保留：E495 的 generated PROGRESS 合法追加6行；舊JSON的「其它列冊檔未變」只指寫新metadata前對E792 snapshot驗證時點。revision-4另封精確前後／append hash與bytes、原peer1及原E495 manifest；不把該true讀成E495或此後PROGRESS不變。原raw、來源、16正式UNRUN都不改，時點限定待獨立窄複核。\n'
    if matrix(old)!=matrix(new):raise RuntimeError('formal matrix changed')
    (D/'PR_BODY.md').write_text(new)
    run(['git','add','--force','--sparse','--','PR_BODY.md'],D);_,staged,_=run(['git','diff','--cached','--name-only','-z'],D)
    if staged!=b'PR_BODY.md\0':raise RuntimeError('body stage outside exact file')
    run(['git','diff','--cached','--check'],D);run(['git','commit','-m','docs(geo324): distinguish raw preservation from metadata append'],D)
    _,head,_=run(['git','rev-parse','HEAD'],D);report['bodyHead']=head.decode().strip()
    run(['git','push','origin','refs/heads/'+BR+'-prbody:refs/heads/'+BR+'-prbody'],D)
    _,remote,_=run(['git','ls-remote','--exit-code','origin','refs/heads/'+BR+'-prbody'],D);report['remoteBodyHead']=remote.decode().split()[0]
    if report['remoteBodyHead']!=report['bodyHead']:raise RuntimeError('body remote mismatch')
    report['bodySHA256']=sha((D/'PR_BODY.md').read_bytes());report['manifestFiles']=len(inventory);report['formalRowsRemainUNRUN']=16;report['exitCode']=0
except BaseException as error:report['errors'].append(repr(error));report['exitCode']=1
finally:
    report['endedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['commandCount']=len(rec.rows);cap.dump(O/'receipt.json',report);print(json.dumps(report,ensure_ascii=False))
raise SystemExit(report['exitCode'])
