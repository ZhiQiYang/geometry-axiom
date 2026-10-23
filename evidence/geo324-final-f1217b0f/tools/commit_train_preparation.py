#!/usr/bin/env python3
"""Gitauth修復前只commit本owner準備原件/正文；不偽稱已push。"""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil

BASE=Path('/tmp/geo324-owner-20261024');OUT=BASE/'train-preparation-local-publication'
REPO=Path('/tmp/geo324-faces-work-20261024');BODY_REPO=Path('/tmp/geo324-faces-prbody-work-20261024')
SOURCE='f1217b0fa5e933e14906833bf4981dad97061b04'
TRAIN='f64d638f15c48d2b9723b7ae9d230fb5dacb82d9'
BRANCH='codex/geo324-faces-20261024';BODY_BRANCH=BRANCH+'-prbody'
PREFIX='evidence/geo324-final-f1217b0f'
PEER=Path('/tmp/train337-adversarial/324-v2')
if OUT.exists():raise SystemExit('refuse overwrite')
OUT.mkdir()
spec=importlib.util.spec_from_file_location('capture','/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
capture=importlib.util.module_from_spec(spec);spec.loader.exec_module(capture)
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env.pop('PYTHONOPTIMIZE',None)
rec=capture.Recorder(OUT,env,SOURCE)
report={'schema':'geo324.local-preparation-publication.v1','sourceSHA':SOURCE,'trainSHA':TRAIN,
        'branch':BRANCH,'bodyBranch':BODY_BRANCH,'evidencePrefix':PREFIX,'exitCode':None,'errors':[],
        'productTestsExecuted':False,'pushAttempted':False,'remotePublicationComplete':False,
        'networkStatus':'root reported credential lookup failure at 18:25Z; ordinary retry is root-coordinated around 18:55Z; this collector commits locally only'}
def run(command,cwd=REPO):
 return rec.run(command,cwd=cwd,timeout=120,source_sha=SOURCE,source_variant='local-metadata-commit-not-product-test')
try:
    _,head,_=run(['git','rev-parse','HEAD']);_,status,_=run(['git','status','--porcelain=v1','--untracked-files=all'])
    if head.decode().strip()!=SOURCE or status:raise RuntimeError('owner source moved or dirty')
    run(['python3','-B','-c','import ast,hashlib,json;from pathlib import Path;p=Path("/tmp/geo324-owner-20261024/preparation/run_face_predicate_proofs_v2.py");ast.parse(p.read_bytes());print(json.dumps({"kind":"AST-only","sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"productTestExecuted":False}))'])
    peer=json.loads((PEER/'CHECKS_CORRECTED.json').read_text())
    if peer['source_sha']!=SOURCE or peer['driver_sha256']!='4b5c05f1a2d7a5cf24c1e2b4d21641c560a7fe7a25db1109a6127d315ddd406d' or peer['findings']:
        raise RuntimeError('independent static peer source/driver/findings mismatch')
    target=REPO/PREFIX;target.mkdir(parents=True)
    for name in ('merge-train-f64d638f','latest-review-refresh','preparation-v2','current-preparation-binding','preparation-publication'):
        shutil.copytree(BASE/name,target/name,ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(PEER,target/'independent-static-peer')
    (target/'tools').mkdir()
    for path in (BASE/'preparation/run_face_predicate_proofs_v2.py',BASE/'merge_current_train.py',
                 BASE/'bind_current_preparation.py',BASE/'refresh_latest_review.py',Path(__file__)):
        shutil.copyfile(path,target/'tools'/path.name)
    shutil.copyfile(BASE/'geo324-pr-request.json',target/'geo324-pr-request.json')
    progress=f'''# #324 替代線進度（新列車合流）

產品 source S：`{SOURCE}`；incoming train：`{TRAIN}`。來源分支 `{BRANCH}`。S已在18:21:51Z正常push／ls-remote0核同。此批準備E與正文D只本地commit，Git認證於18:25Z出現lookup故障，root安排約18:55Z一般重試；本批不聲稱已push。

已完成：普通merge train（父E07615668＋Ff64d638f），無衝突、原26命令/streams/hash完整保存；對train的非evidence source恰3檔121+/2-，兩leaf仍Grok原blob，expected僅host_sources39→45，其餘registry metadata全等train；SSOT/queue blob全等train。diffcheck0、來源checkout乾淨，沒有覆蓋列車產品。前一輪main merge／環境／準備原件在公開E07615668c110684826390990cd2d6134eb6025fd，完整原publication streams也封於本批。

Fresh handoff已讀4aeabc8ec05b358e22fe2375f97dce64324fbc22；324.md原bytes精確同d193，最新仍要求同source的正式整合。原review hash59261d7b9c2a9f04ea74b222a7e4c76fab048c00756949d9246ba38e1ad9e1ad。

v2三predicate補充driver SHA4b5c05f1a2d7a5cf24c1e2b4d21641c560a7fe7a25db1109a6127d315ddd406d，僅AST0、沒有執行。依peer新增helper c387載入前pin、逐Git tracked blobs唯一複製來源／工作bytes核對、正常FAIL對應原具名診斷；原tests/assertion/60秒不改。p88_priority純靜審118 checks／0 findings，原checker把os.environ.copy誤當FS copy的exit1及窄更正版全保；不是產品紅，也不是動態通過。current-state三predicate計畫只改成精確v2檔名，frozen前件不覆寫。

正式registry／full native＋expected／六browser／affected importer／三predicate0/1/0／mutation --check／原架構三條共16列仍全部UNRUN，原exit與executionSHA都null。沒有編譯、Chrome、bench、ledger重產或裁判執行。root兩重槽目前給323/314，本owner不搶槽、不建新大checkout。

下一步：root統一handoff request（draft #338列車之上）及Git普通push重試；確認正式source／架構刷新安排後，依原gate清單補全部同SHA原件。遇紅收齊分類，不放寬斷言；完整ledger由root統排。不得用AST／出版0冒綠。
'''
    (target/'PROGRESS.md').write_text(progress)
    inventory={}
    for path in sorted(target.rglob('*')):
        if path.is_file():inventory[path.relative_to(target).as_posix()]={'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    (target/'PACKAGE_MANIFEST.json').write_text(json.dumps({'sourceSHA':SOURCE,'files':inventory,
      'productTestsExecuted':False,'remotePublicationComplete':False},ensure_ascii=False,indent=2)+'\n')
    run(['git','add','--force','--sparse','--',PREFIX])
    _,staged,_=run(['git','diff','--cached','--name-only','-z'])
    names=[p.decode() for p in staged.split(b'\0') if p]
    if not names or any(not name.startswith(PREFIX+'/') for name in names):raise RuntimeError('staged evidence scope mismatch')
    run(['git','commit','-m','docs(geo324): record train merge and reviewed proof preparation'])
    _,head,_=run(['git','rev-parse','HEAD']);report['localEvidenceHead']=head.decode().strip();report['evidenceFiles']=len(names)
    state=json.loads((BASE/'current-preparation-binding/CURRENT_STATE_PREPARED.json').read_text())
    matrix='\n'.join('| '+row['gate']+' | 未執行 | `null` | `null` |' for row in state['rows'])
    body=f'''柱／樑 native snapshot 缺少或損壞 `faces` 時，公開 evaluate 路徑應回原 `UNSUPPORTED / BASE_SOURCE_BINDING / I32 / Native box source faces disagree with legacy provenance.`，避免洩出未分類例外。這是 #324 的 Codex 替代線；產品已疊新列車，正式雲端驗收仍未執行。

| 來源角色 | 完整 SHA／分支 |
|---|---|
| 原 PR-local base | `7dae5f21c7ca401e660450d437e60ba566218da8` |
| Grok 原 head | `4e176e830b691269cc72d021ce7e1bc0b167d621` |
| 已普通merge main | `eda91c8593f0795278f7f16ff8b93d147a4fdaa7` |
| 已普通merge train | `{TRAIN}` |
| 目前公開產品 S | `{SOURCE}` |
| 本批本地 evidence E（尚未push） | `{report['localEvidenceHead']}` |
| 前批公開 evidence | `07615668c110684826390990cd2d6134eb6025fd` |
| Fresh審查handoff | `4aeabc8ec05b358e22fe2375f97dce64324fbc22` |
| 替代head／正文分支 | `{BRANCH}`／`{BODY_BRANCH}` |
| PR預定base | `codex/train-337-continue-20261024`（列車draft #338） |

對指定train，非evidence產品差異恰原三檔121+/2-。兩leaf保原Grok blobs；expected只聯集 `py:test_geometry_host_sources`39→45，其它registry metadata精確等train。SSOT／決策佇列blob精確等train，不改字。普通merge／push來源S／ls-remote及diffcheck均0，沒有rebase或force push，沒有合併PR。

目前45只是expected契約，非本輪實跑數。五支公開行為方法涵蓋柱／樑missing、null/object、非dict、int/list feature，並保三predicate controls。原作者Windows/Python3.14的45 tests exit0是歷史結果；Actions39721803849七job零步驟failure仍屬環境，兩者都不能代本輪S。

唯一 current-state 驗收矩陣如下。`null`表示沒有本輪原exit／execution SHA，不是允許skip；沒有新增skip豁免。正式final SHA尚待root排合流／架構刷新順序。

| Gate | 目前結果 | 原 exit | execution SHA |
|---|---|---|---|
{matrix}

三predicate補充driver v2 SHA `4b5c05f1a2d7a5cf24c1e2b4d21641c560a7fe7a25db1109a6127d315ddd406d` 只AST0。它先pin原c387 helper，從精確Git tracked blobs構建獨立四packages／三fixtures，逐案原method baseline／withdraw／restored各封完整streams及正常0/1/0。mutant另核原helper具名unclassified診斷，不能用setup/import/syntax/error或timeout冒正常紅。原test/assertions/60秒不改。原內建helper最後只跑第一個restored，不捏造其餘兩案輸出；feature=int會被後段集合擋住，同method的list feature才有牙齒。

p88_priority已對新S／普通merge原件／v2完成純靜審118 checks、0 findings，完整原checker錯判1與窄更正報告同存；這不是動態驗收。原frozen準備不覆寫，只追加current計畫的v2精確檔名。產品／正式裁判／Chrome都尚未執行。

原件位於 `{PREFIX}/`（此批本地commit，尚未push）：26條merge命令、完整stdout/stderr/env/SHA、fresh review、v1/v2／manifest／peer與前批publication原流。Git認證18:25Z突然lookup失敗，root安排約18:55Z一般重試；來源S已在故障前公開，本批E及這份正文的最新commit仍待推。沒有把pending標成已公開。

下一步：root統一推handoff替代draft PR request；排正式同SHA native＋expected／六browser／importers／三predicate0/1/0／mutation check與架構三原裁判／四檔刷新。帳本過期如實交root統排，不在準備階段重產全ledger。原兩重槽給323/314，本owner不搶槽。不宣稱可合併。
'''
    (BODY_REPO/'PR_BODY.md').write_text(body)
    run(['git','add','--force','--sparse','--','PR_BODY.md'],cwd=BODY_REPO)
    _,staged,_=run(['git','diff','--cached','--name-only'],cwd=BODY_REPO)
    if staged.decode().splitlines()!=['PR_BODY.md']:raise RuntimeError('body staged scope mismatch')
    run(['git','diff','--cached','--check'],cwd=BODY_REPO)
    run(['git','commit','-m','docs(geo324): update train source and pending acceptance matrix'],cwd=BODY_REPO)
    _,head,_=run(['git','rev-parse','HEAD'],cwd=BODY_REPO);report['localBodyHead']=head.decode().strip()
    report['bodySHA256']=hashlib.sha256((BODY_REPO/'PR_BODY.md').read_bytes()).hexdigest()
    for repository in (REPO,BODY_REPO):
        _,status,_=run(['git','status','--porcelain=v1','--untracked-files=all'],cwd=repository)
        if status:raise RuntimeError('own worktree dirty after local commits')
    report['exitCode']=0
except BaseException as error:
    report['errors'].append(repr(error));report['exitCode']=1
finally:
    report['endedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['commands']=len(rec.rows)
    capture.dump(OUT/'receipt.json',report);print(json.dumps(report,ensure_ascii=False))
raise SystemExit(report['exitCode'])
