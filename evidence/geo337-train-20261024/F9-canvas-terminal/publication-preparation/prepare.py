from pathlib import Path
import json,hashlib,subprocess,datetime
O=Path(__file__).parent
F='4f8a794f4167c3562eb182045102e86e9e37cca9';E='c32e70aa2c848f89a0e2e9fd92ed232a4dd27bcc';D='1c601b40a6f5e0e1d50461186736d469666db4b9';H='d0091b9284cce6dfeabee20aab63dcc7d9560ca7'
def h(b):return hashlib.sha256(b).hexdigest()
def J(p):return json.loads(Path(p).read_bytes())
bindings=[]
def get(ref,path):
 argv=['git','-C','/workspace/geometry-axiom','show',ref+':'+path];r=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if r.returncode:raise RuntimeError(r.stderr.decode())
 bindings.append({'argv':argv,'exit_code':r.returncode,'stdout_bytes':len(r.stdout),'stdout_sha256':h(r.stdout),'stderr':r.stderr.decode(),'storage':'完整原件仍在固定Gitblob，不另外複製payload。'});return r.stdout
old=get(E,'evidence/geo337-train-20261024/PROGRESS.md');body=get(D,'PR_BODY.md').decode();nextold=get(H,'handoff/NEXT.md')
formal=J('/workspace/geo337-F9-canvas-actual-peer-20261025/REVIEW.json');packagepeer=J('/workspace/geo337-F9-canvas-terminal-package-actual-peer-20261025/REVIEW.json');package=J('/tmp/geo337-F9-canvas-terminal-package-20261025/RESULT.json');comparefinal=J('/workspace/geo323-F9-owner-compare-once-EXEC_FINAL-20261025.json')
assert formal['exit_code']==0 and formal['original_exit']==0 and formal['ci_35_minute_gate_exit']==0 and packagepeer['exit_code']==0 and packagepeer['checks']==5396 and package['collection_exit']==0 and comparefinal['exit_code']==0
changes=[('| 證據 E | `'+E+'` |','| 證據 E | `{{EVIDENCE_HEAD}}` |'),('| canvas | RUNNING at F9：2026-10-25 11:22:04 UTC啟動；完整瀏覽器步驟尚無終態，原35分鐘裁判不變 |','| canvas | F9 原workflow／wrapper exit0，35分鐘裁判0；1723.223173秒。完整2267 assertions、零fail／skip；85段golden相符，P73=69、P88=143；原件peer170/0 |'),('先核基底／來源再修，未免除斷言。','已定位固定歷史基底的測試範圍問題；嚴格修正草案待主代理批次採入與撤回／恢復反證，尚未修改F9或免除斷言。'),('| required CI／替代驗收 | 審查記cd19的run40183211769七job failure、steps0；新E的Actions未讀。已核實OWNER帳戶明確批准同一final SHA七項＋專項全綠替代；目前native1、canvas執行中、五browser未跑，替代條件尚未達成 |','| required CI／替代驗收 | 母證據E c32的原API查詢exit0、total_count0／runs[]，僅代表當時沒有run；本次新E的Actions未讀。OWNER批准同一final SHA七項＋專項全綠替代；目前native1、五browser未跑，替代條件尚未達成 |'),('精確白名單候選與後段audit正在外部準備，**尚未正式採用／重驗**；原R8 outer1與全36樣本保留，不換base、不重抽，不擴及P-189。','依核可白名單執行的新F9 comparison單項已於12:14:21 UTC取得outer／stage exit0；逐列與175／350完整性獨審尚在進行，完整原件本批尚未公開。原R8 outer1與全36樣本保留，不換base、不重抽，不擴及P-189，也不把此單項0當作required-eight或整份驗收通過。'),('B2／B3的當次OWNER批准已經原API核實，但比較器正式重驗及完整替代驗收條件尚未完成；不標READY-TO-MERGE。','B2／B3的當次OWNER批准已經原API核實；新comparison單項0的完整原流／獨審待下一批公開，完整替代驗收條件仍未達成；不標READY-TO-MERGE。')]
for a,b in changes:
 assert body.count(a)==1,(a,body.count(a));body=body.replace(a,b)
needle='| #323 required-eight／PF3／native後段 |'
assert body.count(needle)==1
body=body.replace(needle,'| #323 新comparison單項 | F9 outer／stage exit0（12:12:46–12:14:21 UTC）；原件逐列與175／350完整性peer待完成，本批未公開完整原流；不移標F8 R8結果 |\n'+needle)
body+='\n\n[F9完整canvas原件與雙獨審](https://github.com/ZhiQiYang/geometry-axiom/tree/{{EVIDENCE_HEAD}}/evidence/geo337-train-20261024/F9-canvas-terminal/)：原workflow在11:22:04.734796–11:50:47.957901 UTC執行，原35分鐘界線2100秒未放寬。P38故意注入fb-auto-probe，原uncaughtBrowserExceptions=1且標EXPECTED、unexpected=0；P53 API故障與被取消的網路請求亦完整保留，不能改寫成診斷總數0。原件裁判170/0與封包5396/0分列，封包peer不代產品gate。四包保留656個regular檔45,780,854B＋4個symlink，全部ELF／cache／profile／診斷均收；只將5個SOURCEPLAN Git metadata／mutable latest葉作精確hash-only及1個Unix socket作metadata-only，原payload保留，私有index完整封存另案。這是一輪F9完整canvas通過，不外推其他browser或重複穩定性已驗。\n'
# Keep all already-published links immutable; only new evidence identity and canvas prefix await E.
(O/'PR_BODY.template.md').write_text(body)
current=body.replace('`{{EVIDENCE_HEAD}}`','本檔所在證據提交；完整SHA由獨立prbody提交記錄').replace('https://github.com/ZhiQiYang/geometry-axiom/tree/{{EVIDENCE_HEAD}}/evidence/geo337-train-20261024/F9-canvas-terminal/','F9-canvas-terminal/')
progress=('# F9 目前驗收狀態：canvas已通過、native仍紅\n\n以下唯一矩陣是目前狀態；最末完整舊文只留歷史。\n\n'+current+'\n\n<details>\n<summary>歷史快照：E c32；當時canvas RUNNING及新comparison未執行文字已由上表取代</summary>\n\n以下 '+str(len(old))+' bytes 原樣保留，SHA256 `'+h(old)+'`。\n\n').encode()+old+b'\n</details>\n'
(O/'PROGRESS.md').write_bytes(progress)
nextdelta=f'''# NEXT增量草稿：F9 canvas已通過（尚未寫入handoff）

保留handoff `{H}` 的全部其他工作線與原件路徑；本段只取代其頂部當前狀態，不將舊RUNNING／未核實文案當成現況。這是持續工作交接，不是階段停止。

- 產品固定F9 `{F}`；整合分支 `codex/train-337-continue-20261024`。本草稿準備時已公開 E=`{E}`／prbody D=`{D}`；新canvas證據與正文由root普通push後填入 `{{{{EVIDENCE_HEAD}}}}`／`{{{{PRBODY_HEAD}}}}`，不能預稱已公開。
- canvas真終態：原工具session15990已exit0；11:22:04.734796–11:50:47.957901 UTC，1723.223172891012秒，35分鐘gate0。CDP2267/0、零skip、golden85段一致、P73=69/P88=143；P38原預期fb-auto-probe exception1保留，不改成總exception0。原件peer170/0 `/workspace/geo337-F9-canvas-actual-peer-20261025/REVIEW.json`。四part完整包 `/tmp/geo337-F9-canvas-terminal-package-20261025/` 收件0、包peer5396/0；private index完整封存另案，不拖canvas公開。不要重跑本輪canvas以取樣。
- reader三條0/0/0、unit51已完整公開於E c32；native原exit1／35分鐘gate0仍未修，唯一 `Geo314CommitPaths.test_kernel_has_no_changes_against_the_fixed_integration_base`，多出 `geometry-core/kernel/source.c`。原嚴格修正草案待root批次採入與反證，未改F9；不將其當通過。
- 新#323 comparison單項原outer／stage exit0，12:12:46.196815–12:14:21.618298 UTC；真API `/workspace/geo323-F9-owner-compare-once-EXEC_FINAL-20261025.json`。OUT `/workspace/geo323-F9-owner-compare-once-20261025-r1`；完整逐列／175-350驗證與收包由另線完成，這批canvas不等它，也不冒已公開compare原流。原F8 R8 outer1/compare1及36效能樣本原件保留；不能重抽、移標或擴及P-189。
- 下一步先跑其餘assembly/documents/grid/space/timber與P52/Q38/§7/P189/required-eight/PF3/memo/RC/#314/閱讀A未完成獨立專項，保原時限、斷言、golden與執行者獨占規則；收齊紅再按影響批次修。其他線各自branch/S/E/D沿原NEXT，不擅改或合併。
- #344新exact架構adapter只有靜審76/0：`/workspace/geo344-architecture-adapter-static-peer-20261025/REVIEW.json`；工具 `/workspace/geo344-architecture-adapter-preparation-20261025/refresh_architecture_cdp_exclusion.py` pin71cb2e314a3d3e7c3419bbe436f2c308a702d6b3be5f9668594fe729248de2de。需先owner固定a5後裔單manifest hash修正的新S344及完整604來源，再原三judge／單hash0-1-0／九Wguard真跑。全部UNRUN，既有strict9不重做。
- 當次OWNER批准已以原API帳戶等同性核實且公開於E c32；仍不能證真人手動輸入，不是本對話直接B′回答。准許三具名場景精確新增字串與既定CI替代，未擴P189/性能門檻；替代驗收仍須同final SHA七項＋專項全部綠。本次c32 CI原查詢exit0、0runs不等於failure或通過；新E須另讀。
- 不刪原收據、fixtures、git objects或既有原始payload；root近期精確退役的來源以其獨立保全收據為準，任何來源復用須先通過原source guard。不得直接因舊NEXT寫clean就假定目前完整材料化。仍不force push、不merge PR。
'''
(O/'NEXT.delta.md').write_text(nextdelta)
(O/'ORIGIN_BINDINGS.json').write_text(json.dumps(bindings,ensure_ascii=False,indent=2)+'\n')
prep={'schema':'geo337-F9-canvas-current-docs-preparation/1','source_sha':F,'source_evidence_head':E,'source_prbody_head':D,'handoff_source':H,'new_evidence_placeholder':'{{EVIDENCE_HEAD}}','source_history_bytes':len(old),'source_history_sha256':h(old),'source_history_exact_offset':progress.find(old),'source_history_exact_preserved':progress.count(old)==1,'canvas_original_exit':0,'canvas_35minute_gate_exit':0,'canvas_actual_peer_checks':170,'canvas_package_peer_checks':5396,'native_exit':1,'reader_exits':[0,0,0],'new_compare_outer_exit':0,'new_compare_full_peer_pending':True,'new_compare_full_originals_published_in_this_batch':False,'original_R8_outer_exit':1,'product_or_branch_changed':False,'publication_performed':False,'body_sha256':h(body.encode()),'progress_sha256':h(progress),'next_delta_sha256':h(nextdelta.encode())}
(O/'PREPARATION.json').write_text(json.dumps(prep,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(prep,ensure_ascii=False))
