#!/usr/bin/env python3
"""只出版本 owner 小型準備原件與 pending 正文；不啟測或寫其它分支。"""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil

BASE=Path('/tmp/geo324-owner-20261024')
OUT=BASE/'preparation-publication'
REPO=Path('/tmp/geo324-faces-work-20261024')
BODY_REPO=Path('/tmp/geo324-faces-prbody-work-20261024')
SOURCE='06e492d6d59c1ab2c5505e5300f7542f7063468d'
BRANCH='codex/geo324-faces-20261024'
BODY_BRANCH=BRANCH+'-prbody'
PREFIX='evidence/geo324-final-06e492d6'
if OUT.exists() or BODY_REPO.exists(): raise SystemExit('refuse overwrite')
OUT.mkdir()
spec=importlib.util.spec_from_file_location('capture','/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py')
capture=importlib.util.module_from_spec(spec);spec.loader.exec_module(capture)
env=os.environ.copy();env['PATH']='/workspace/geo261-environment/bin:'+env['PATH'];env['PYTHONDONTWRITEBYTECODE']='1';env.pop('PYTHONOPTIMIZE',None)
rec=capture.Recorder(OUT,env,SOURCE)
report={'schema':'geo324.preparation-publication.v1','productSourceSHA':SOURCE,'branch':BRANCH,
        'bodyBranch':BODY_BRANCH,'evidencePrefix':PREFIX,'exitCode':None,'errors':[],
        'productTestsExecuted':False,'allFormalGates':'UNRUN'}
def run(command,cwd=REPO,check=True,data=None):
    return rec.run(command,cwd=cwd,check=check,data=data,timeout=180,
                   source_sha=SOURCE,source_variant='metadata-publication-not-product-test')
try:
    _,head,_=run(['git','rev-parse','HEAD'])
    _,status,_=run(['git','status','--porcelain=v1','--untracked-files=all'])
    if head.decode().strip()!=SOURCE or status: raise RuntimeError('owner source state changed')
    target=REPO/PREFIX
    target.mkdir(parents=True)
    for name in ('initial-metadata','base-branch-publication','merge-main-preparation',
                 'authority-and-plan','authority-and-plan-resume1','preparation'):
        shutil.copytree(BASE/name,target/name,ignore=shutil.ignore_patterns('__pycache__'))
    (target/'tools').mkdir()
    for path in sorted(BASE.glob('*.py')):
        shutil.copyfile(path,target/'tools'/path.name)
    shutil.copyfile('/workspace/geo261-environment/final-f-contact-checker-proof-tools/capture.py',target/'tools/capture.py')
    for path in BASE.glob('METADATA_PREPARATION_CORRECTION.*'):
        shutil.copyfile(path,target/path.name)
    progress='''# #324 替代線進度

產品來源 S：`06e492d6d59c1ab2c5505e5300f7542f7063468d`。分支 `codex/geo324-faces-20261024`；此批只封存準備與原件，全部正式 gate 尚未執行。

已完成：從 Grok `4e176e830b691269cc72d021ce7e1bc0b167d621` 開自有分支，普通 merge main `eda91c8593f0795278f7f16ff8b93d147a4fdaa7` 無衝突；merge 原 exit0、一般 push0、ls-remote0且同 S。相對 main 只原三檔／121+/2-，兩個 leaf blobs 保 Grok 原 bytes；expected 只 host_sources39→45，其餘 JSON metadata 逐項同 main。SSOT／決策 blob 精確同 main，沒有改字。薄 checkout 原47files／1,037,381B，沒有複製 Git objects。

已讀最新 handoff d193946b8e0fbda024d3b134c4851e9393a43d38 的324審查及17:01作者雲端交接。原 Windows45 tests與零步驟 Actions失敗保其原角色，不是本輪 S 的結果。原 startup feedback list 首次因薄 checkout 漏 feedback_store 而 exit1；只補物化該既有依賴後 list0（沒有未處理回報），完整兩次原件同存。沒有改產品或測試。

環境：繼承 PATH 下 google-chrome 真 FileNotFound，原準備 collector1保留；依既有安裝路徑補 PATH 後 `google-chrome --version`0=156.0.8078.47、`node --version`0=v24.19.0。不重新安裝、不把環境命令當產品 gate。

三 predicate 各自 baseline／withdraw／restored 的外部補充收據工具已備，僅AST0、尚未執行；原 tests/assertions 不變。原內建 helper 最後只 restored 第一個 case 的範圍如實記錄。GATE_PLAN與CURRENT_STATE_PREPARED列16個UNRUN項，沒有以準備0冒綠。

下一步：root排新train的一般合流順序，固定真正 final SHA，再按磁碟／slot跑原 registry、full native＋expected、六browser、affected importers、三predicate原method各0/1/0、mutation --check、原架構三條。原帳本過期與四檔架構刷新如實列，完整ledger由root統一排。最多2重活；canvas／perf獨占。尚未merge train，沒有編譯、Chrome、bench或測試執行。全部產物交p88_priority獨立對抗審；審查目前pending。
'''
    (target/'PROGRESS.md').write_text(progress)
    (target/'SOURCE.json').write_text(json.dumps({'sourceSHA':SOURCE,'grokSHA':'4e176e830b691269cc72d021ce7e1bc0b167d621',
       'mainSHA':'eda91c8593f0795278f7f16ff8b93d147a4fdaa7','handoffSHA':'d193946b8e0fbda024d3b134c4851e9393a43d38',
       'sourceScope':['geometry-templates/woodworking/geometry_woodworking/model_sources.py','tests/test_geometry_host_sources.py','tests/run_all.expected.json'],
       'formalFinalSHA':None,'allFormalGates':'UNRUN','trainMergePerformed':False},ensure_ascii=False,indent=2)+'\n')
    inventory={}
    for path in sorted(target.rglob('*')):
        if path.is_file(): inventory[path.relative_to(target).as_posix()]={'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    (target/'PACKAGE_MANIFEST.json').write_text(json.dumps({'sourceSHA':SOURCE,'files':inventory,'noFormalGateClaimed':True},ensure_ascii=False,indent=2)+'\n')
    run(['git','add','--force','--sparse','--',PREFIX])
    _,staged,_=run(['git','diff','--cached','--name-only','-z'])
    paths=[p.decode() for p in staged.split(b'\0') if p]
    if not paths or any(not path.startswith(PREFIX+'/') for path in paths): raise RuntimeError('staged scope outside own evidence')
    report['evidenceFiles']=len(paths)
    run(['git','commit','-m','docs(geo324): record main merge and pending cloud acceptance'])
    _,evidence,_=run(['git','rev-parse','HEAD']);report['evidenceHead']=evidence.decode().strip()
    run(['git','push','origin','refs/heads/'+BRANCH+':refs/heads/'+BRANCH])
    _,remote,_=run(['git','ls-remote','--exit-code','origin','refs/heads/'+BRANCH])
    if remote.decode().split()[0]!=report['evidenceHead']: raise RuntimeError('remote evidence mismatch')
    report['remoteEvidenceHead']=remote.decode().split()[0]
    run(['git','branch',BODY_BRANCH,SOURCE])
    run(['git','worktree','add','--no-checkout',str(BODY_REPO),BODY_BRANCH])
    run(['git','sparse-checkout','set','--no-cone','--stdin'],cwd=BODY_REPO,data=b'/.gitignore\n/PR_BODY.md\n')
    run(['git','read-tree','-mu','HEAD'],cwd=BODY_REPO)
    state=json.loads((BASE/'preparation/CURRENT_STATE_PREPARED.json').read_text())
    table='\n'.join('| '+row['gate']+' | 未執行 | `null` | `null` |' for row in state['rows'])
    body=f'''修正柱／樑 native snapshot 缺少或損壞 `faces` 時洩出未分類例外：沿公開 evaluate 路徑，保原 `UNSUPPORTED / BASE_SOURCE_BINDING / I32 / Native box source faces disagree with legacy provenance.` 四元組。這是 #324 的 Codex 替代工作線，仍為草稿，完整雲端驗收尚未執行。

| 來源角色 | 完整 SHA／分支 |
|---|---|
| 原 PR-local base | `7dae5f21c7ca401e660450d437e60ba566218da8` |
| Grok 原 head | `4e176e830b691269cc72d021ce7e1bc0b167d621` |
| 普通 merge 的 main | `eda91c8593f0795278f7f16ff8b93d147a4fdaa7` |
| 目前產品 source S | `{SOURCE}` |
| 準備 evidence head E | `{report['evidenceHead']}` |
| 最新審查 handoff | `d193946b8e0fbda024d3b134c4851e9393a43d38` |
| 替代 head／正文 | `{BRANCH}`／`{BODY_BRANCH}` |

main→S 恰三檔、121+/2-；兩個 leaf 保原 Grok bytes，`run_all.expected.json` 只聯集 `py:test_geometry_host_sources`39→45，其餘 metadata 與 main 全等。SSOT／決策佇列 blob 精確同 main。沒有 rebase／force push／PR merge。新 train 尚未合流，正式 final SHA 未固定，不能用本輪準備冒稱列車已驗收。

原模組45是目前 expected 契約：五支公開行為方法覆蓋柱／樑 missing、null/object、非dict、int/list feature，另三 predicate controls 保原斷言。原作者 Windows/Python3.14 的45 tests exit0是歷史結果，本輪沒有重跑，不是 S 的綠燈。原 Actions39721803849七 job零步驟 failure仍只記環境。

唯一 current-state 驗收矩陣如下。`null` 表示本輪沒有原 exit／受驗 execution SHA，並非允許 skip；目前沒有新增 skip 豁免。

| Gate | 目前結果 | 原 exit | execution SHA |
|---|---|---|---|
{table}

三 predicate 的外部補充工具只完成AST檢查，待同一正式source逐案跑原method的0/1/0並封完整streams。原內建control最後只重跑第一個restored，不能靠其綠燈補造另外兩案restored輸出。feature=int被後段集合檢查擋住；同方法的list feature才殺得掉feature型別predicate。

準備／merge原件在 `{PREFIX}/`：原命令、exit、完整stdout/stderr、環境、SHA、工具與manifest一併保留。source merge／一般push／ls-remote均0；只物化約1MiB必要source，沒有build或Chrome。環境 PATH修正後 Chrome156.0.8078.47／Node24.19.0真版本命令均0；最初PATH缺Chrome的失敗與薄checkout漏feedback_store的read-only失敗均保，修正只補PATH／既有依賴物化，沒有改產品。

下一步由root排新train一般合流及重測槽，固定可解析final SHA，跑原full native＋expected／六browser／importers／mutation check及架構三條；過期帳本與四檔架構產物依原規則處理，不放寬判準、不全帳本重產於本準備回合。所有動態與p88_priority對抗審仍pending，不宣稱可合併。root依handoff/pr-requests/README送建立替代draft PR請求。
'''
    (BODY_REPO/'PR_BODY.md').write_text(body)
    run(['git','add','--force','--sparse','--','PR_BODY.md'],cwd=BODY_REPO)
    _,staged,_=run(['git','diff','--cached','--name-only'],cwd=BODY_REPO)
    if staged.decode().splitlines()!=['PR_BODY.md']: raise RuntimeError('body stage scope mismatch')
    run(['git','diff','--cached','--check'],cwd=BODY_REPO)
    run(['git','commit','-m','docs(geo324): publish replacement PR acceptance matrix'],cwd=BODY_REPO)
    _,head,_=run(['git','rev-parse','HEAD'],cwd=BODY_REPO);report['bodyHead']=head.decode().strip()
    report['bodySHA256']=hashlib.sha256((BODY_REPO/'PR_BODY.md').read_bytes()).hexdigest()
    run(['git','push','origin','refs/heads/'+BODY_BRANCH+':refs/heads/'+BODY_BRANCH],cwd=BODY_REPO)
    _,remote,_=run(['git','ls-remote','--exit-code','origin','refs/heads/'+BODY_BRANCH],cwd=BODY_REPO)
    if remote.decode().split()[0]!=report['bodyHead']: raise RuntimeError('remote body mismatch')
    report['remoteBodyHead']=remote.decode().split()[0]
    _,status,_=run(['git','status','--porcelain=v1','--untracked-files=all'])
    if status: raise RuntimeError('evidence checkout not clean after publication')
    _,status,_=run(['git','status','--porcelain=v1','--untracked-files=all'],cwd=BODY_REPO)
    if status: raise RuntimeError('body checkout not clean after publication')
    report['exitCode']=0
except BaseException as error:
    report['errors'].append(repr(error));report['exitCode']=1
finally:
    report['endedUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['commands']=len(rec.rows)
    capture.dump(OUT/'receipt.json',report);print(json.dumps(report,ensure_ascii=False))
raise SystemExit(report['exitCode'])
