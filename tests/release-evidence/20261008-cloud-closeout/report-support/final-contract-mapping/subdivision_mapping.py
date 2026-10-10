#!/usr/bin/env python3
"""Read source and existing receipts; write a clause mapping, never execute tests."""
import ast, hashlib, json, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/workspace/geometry-axiom')
E = Path('/workspace/closure-evidence')
OUT = E / 'inventory/final-contract-mapping/subdivision'
OUT.mkdir(parents=True, exist_ok=True)
def read(p): return Path(p).read_text(encoding='utf-8')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p, x): Path(p).write_text(json.dumps(x, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
commands=[]
def git(*args):
    r=subprocess.run(['git',*args],cwd=ROOT,text=True,capture_output=True)
    commands.append({'command':['git',*args],'cwd':str(ROOT),'stdout':r.stdout,'stderr':r.stderr,'exitCode':r.returncode})
    if r.returncode: raise RuntimeError(r.stderr)
    return r.stdout.strip()
head=git('rev-parse','HEAD'); status=git('status','--short'); main=git('rev-parse','origin/main')
test_head='5174a8dafd8c48329d7166abbd3d104e3c28c0c4'
native_head='458779f003e1f57fdc0f4420564a0b295227843e'
issue_path=E/'inventory/publication-review/remote-post-pr176/open-issues.json'
issue=next(x for x in json.loads(read(issue_path)) if x['number']==62)
dump(OUT/'issue62-source.json',issue)
clauses={m.group(1):{'scenario':m.group(2).strip(),'expectation':m.group(3).strip()} for m in re.finditer(r'^\| (SR\d\d) \| (.*?) \| (.*?) \|$',issue['body'],re.M)}
assert len(clauses)==24
native_source=ROOT/'tests/test_grid_subdivision_oracle.py'
native_methods={n.name:{'name':n.name,'source':str(native_source),'line':n.lineno,'endLine':n.end_lineno} for n in ast.walk(ast.parse(read(native_source))) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith('test_')}
native_receipt=E/'native/full-run-all-new-owners-suite-logs/py_test_grid_subdivision_oracle.json'
native_log=E/'native/full-run-all-new-owners-suite-logs/py_test_grid_subdivision_oracle.unittest.log'
cdp=E/'gates/full-cdp-r3/command.log'; cdp_lines=read(cdp).splitlines()
node=E/'native/full-run-all-new-owners-suite-logs/node_tests-js.log'; node_lines=read(node).splitlines()
browser_oracles=[{'line':i,'oracle':line.strip(),'log':str(cdp)} for i,line in enumerate(cdp_lines,1) if re.search(r'^P8[78]\s.+✓',line)]
dump(OUT/'browser-named-oracles.json',browser_oracles)
dump(OUT/'native-method-census.json',{'sourceSha256':sha(native_source),'methods':list(native_methods.values()),'executionReceipt':str(native_receipt),'executionReceiptSha256':sha(native_receipt),'unittestLog':str(native_log),'unittestLogSha256':sha(native_log),'bindingLimit':'unittest log is dot-only. Names come from AST and the complete registered 41-test receipt with zero skip/failure; log does not print each method name.'})

def N(prefix):
    prefix={'test_single_cell_selector':'test_single_cell_and_all_cells_overlap',
            'test_repeat_pitch_917':'test_repeat_pitch917',
            'test_invisible_single_cell':'test_source_cell_outside_face',
            'test_query_capacity':'test_query_cell_capacity',
            'test_selector_filters':'test_rectangle_selector_filters',
            'test_unthinnable':'test_single_cell_4232',
            'test_exact_query':'test_exact_rectangle',
            'test_manual':'test_rule_and_manual',
            'test_source_rule_capacity':'test_rule_capacity',
            'test_uint32':'test_maximum_uint32',
            'test_second':'test_only_second_actual_component',
            'test_wrong_source':'test_same_rule_key_in_another_source'}.get(prefix,prefix)
    matches=[v for k,v in native_methods.items() if k.startswith(prefix)]
    assert len(matches)==1,(prefix,matches)
    return matches[0]
def B(*fragments):
    fragments=tuple({'衝突':'重疊 cell'}.get(f,f) for f in fragments)
    matches=[x for x in browser_oracles if any(f in x['oracle'] for f in fragments)]
    assert matches,fragments
    return matches
def J(*fragments):
    matches=[{'line':i,'oracle':l,'log':str(node)} for i,l in enumerate(node_lines,1) if l.startswith('✔') and any(f in l for f in fragments)]
    assert matches,fragments
    return matches
rows=[]
def row(id,state,native,browser,node_,observed,remaining):
    rows.append({'id':id,**clauses[id],'state':state,'nativeOracles':[N(x) for x in native],'browserOracles':B(*browser) if browser else [],'nodeOracles':J(*node_) if node_ else [],'observedScope':observed,'remainingExactScope':remaining})
row('SR01','observed', ['test_cancel_create_key_lifecycle'], ['空白','新建來源','新增規則'], [], 'P87 從空白 context 經來源／rule 真 UI 建立，核對無配置、面或舊規則；native create/cancel/key/history 另有完整 snapshot。','本列既定空世界範圍無新增待辦。')
row('SR02','observed', ['test_literal_source_and_binding_numerical_vectors','test_single_cell_selector'], ['真 signed cell','真 signed','完整 tuple','selected cell'], [], 'all-cells/single-cell 原生數值、selector 與 UI signed binding/query；大索引完整 tuple 保留實際 cell，不以抽樣位置代替。','本列具名範圍已核收；不重跑同版。')
row('SR03','observed', ['test_literal_source_and_binding_numerical_vectors','test_full_source_edit_retains_rules'], ['200','六','原子確認','原子'], [], '16 literal vectors 與兩種 anchored bindings 的 source 600→900 獨立期望值；P87 候選 200×200／六格，P88 真 UI source edit 原子確認。','本列算術／pitch 基準已核收；參數與 anchor 修改組合另列 SR15。')
row('SR04','superseded-expectation', ['test_source_rules_require_dual_repeat','test_repeat_pitch_917'], ['901','902','903'], [], '原 issue 的 REPEAT_PANEL 成功預期已被正式採納的 repeat-only 公理 D19a/I25a 取代。原生 panel 普通來源 917 保留；新增／保留子規則明確 SOURCE_KIND 拒絕。917÷7=131 的 repeat 算術向量不冒稱 panel 規則支援。','只更新舊 SR04 文字指向已採納公理；不得為舊期待擴張 panel rule 功能。')
row('SR05','observed', ['test_invalid_divisions'], ['U0','U66','1/1','U7'], [], '指定 DIVISION_NOT_EXACT／DIVISION_RANGE／RULE_SYNTAX native 原因及完整狀態不變；P87 實際無效欄位与 native 拒絕。','本列具名負例已核收。')
row('SR06','partial-evidence', ['test_invalid_divisions','test_source_rules_require_dual_repeat'], ['901','902','903'], ['native source closure preflight rejects unknown rule syntax'], '缺軸、finite、stagger、panel SOURCE_KIND／未改來源有原生及 UI 證據；unknown rule syntax 保存前預驗另有具名負例。','遞迴子規則在 v1 明確排除，但封存 oracle 未指名一個實際 recursive payload 的拒絕。補既有拒絕路徑的 payload→原因→World 不變證據；不新增巢狀能力。')
row('SR07','observed', ['test_literal_source_and_binding_numerical_vectors','test_literal_segments'], ['真 signed cell','完整 tuple'], [], '正負 literal vectors、父邊排除與不同 anchor 相對求值；UI full tuple/pick 使用真實 signed cell。','本列固定向量範圍已核收。')
row('SR08','observed', ['test_placed_reference_records_real_applied_grid','test_formal_rule_line_timber_undo_redo'], ['完整 tuple','signed binding','signed 字串','大 signed'], [], '相對 binding 索引 9007199254740993/-9007199254740995，placed reference／JSON／dump 保留字串；P88 真 ZIP→新空白 context 重開。','本列已核收；native roundtrip helper 的舊 no-op 限制不再代替新 reset/load oracle。')
row('SR09','observed-with-limits', ['test_hole_clipping','test_legal_comb'], ['parent/孔裁切','孔','凹'], [], 'native 固定 clip segments、五孔梳形 41 段；P88 L 形／孔洞實際線 hit/source jump、u/v anchor clipping 以及顯示 cache。','已觀察指定 L 形／孔樣本；沒有理由把它擴成任意多邊形全部 UI 標籤布局的证明。無另開一般化測試要求。')
row('SR10','observed', ['test_invisible_single_cell'], ['零可見','零線','零可見線'], [], 'cell(20,20) 保留身分、座標存在而 segments=[]；舊 manual 正面積 I25 拒絕；P88 exact 零線立即完成。','本列指定面外樣本已核收。')
row('SR11','observed', ['test_query_capacity','test_selector_filters','test_segment_capacity','test_unthinnable'], ['抽樣','sample'], [], 'native 10000 cells 與 40000-cell 搜尋範圍、回傳 cell/segment 上限、sample stride/完整 cell、不建立額外 World grids；8孔4232段單格拒絕有5秒有界 worker 等待。','已核收工程預算／固定工作量 oracle；不宣稱無上限效能。')
row('SR12','observed', ['test_query_capacity','test_segment_capacity','test_unthinnable','test_exact_query'], ['抽樣','真 Tab/Enter','完整定位','實際 cell','真實 cell'], [], 'exact 容量明拒、sample 明示 incomplete／stride／真 identity；P88 真 focus 與 Tab/Enter 使用精確 cell 回覆，延遲回覆不得奪焦。','本列有界 exact/sample 既定範圍已核收。')
row('SR13','observed', ['test_single_cell_selector','test_manual'], ['同 cell','衝突'], [], 'RULE_OVERLAP/SELECTOR_MISS 與 MANUAL_CONFLICT 兩建立順序，native 完整狀態保留；P87 UI 同 cell 衝突。','本列冲突原生守門已核收；沒有正式新增 manual 编辑 UI 要求。')
row('SR14','partial-evidence', ['test_cancel_create_key_lifecycle','test_explicit_edit','test_highwater','test_source_rule_capacity','test_uint32'], ['改名','高水位','刪除後','重建'], [], 'rename/delete/recreate、高水位、create 不覆蓋／edit 不復活、uint32 exhausted；取消不消耗 key；真 UI 與保存有對照。','未找到具名 reorder/permutation oracle。先對照現有可用重排入口或保存序列重排是否屬既定操作，再補 stable key 比對；不自行新增重排 UI。')
row('SR15','partial-evidence', ['test_full_source_edit_retains_rules'], ['兩面正常 UI','預覽','原子確認','原子'], [], '兩配置不同 anchor 共源，native 600→900 所有 binding 重算；P88 兩面正常 UI pitch edit/cancel/confirm/undo/redo。','現有 P88 pitch edit 在正式 guide/direct 引用建立之前。尚缺同一 rule、兩面與已存在有限下游的 source parameter／anchor 更新組合；先確認來源支持的參數/錨點入口，再沿既定流程補精確動作與 affected-object 比對。')
row('SR16','partial-evidence', ['test_second'], ['預覽','原子確認','原子'], [], 'native 兩面中只有第二構件23非法，preview bindings={0,1}、violations={23}、confirm 全拒且完整 snapshot 不變；P88 兩面合法修改有真 UI。','尚未找到相同第二面構件非法情境經真 UI 預覽／拒絕，逐字核對失敗來源/構件及兩面/World/history 不變的 oracle。這是 UI 組合證據缺口，不是已重現產品缺陷。')
row('SR17','observed', ['test_formal_guide','test_wrong_source','test_missing_rule'], ['引用鎖','錯 source'], [], 'divisions/selector/delete RULE_REFERENCED；錯 source 同 key、missing key/index 原因；P88 真 guide 錯 source 與被引用 rule 刪除 UI。','本列具名來源／引用保護已核收。')
row('SR18','partial-evidence', ['test_direct_line_needs_real_support','test_formal_rule_line_timber_undo_redo'], ['真 direct at-line','真 at-line native 拒絕','只修 selector'], [], 'guide 軸座標允許長1560，direct完整父cell／真支撐的合法secondary長540；P88 bad selector拒絕→修selector原地成功。native reset/load 保留正式引用。','角色負例仍缺具名鎖因：native primary 兩次 I13/R6 拒絕同時含無支撐/超父cell限制；P88 拒絕是不存在支撐 t9999。需先提供合法支撐且完整 footprint 合法，只切錯角色並鎖定角色原因與資料不變。不可把目前失敗原因改稱角色通過。')
row('SR19','observed', [], ['未失焦','raw','真 Save ZIP','草稿'], ['raw source rule draft survives real ZIP','rule raw values including future selector','strict raw rule shapes'], 'raw /2 未失焦、空白、不合法 signed字串與真 /13 ZIP 保存／新 context 重開；無 native 自動確認。','本列既定 raw 草稿路徑已核收。')
row('SR20','observed', ['test_formal_rule_line_timber_undo_redo'], ['真 Save ZIP 含兩配置','新空白 context 真重開','高水位'], ['formal reader opens a real archive in a fresh project context','rules coexist with existing raw drafts'], '真 UI ZIP含兩配置+guide/direct+key/signed；新空白 context 後 Open 全dump相等。native正式角材另 reset 確认清空後load。Node完整來源包含未用source/highwater及raw。','完整閉包按上述具名證據組合核收；不是同一單次 UI 錄像包含所有 unused/raw 條件，不能把組合證據描述成一輪。')
row('SR21','observed', ['test_unsupported_model_adapter','test_native_save','test_saved'], [], ['every older schema refuses rules','manifest capability removal','native source closure preflight rejects missing source','service without the required native capability'], 'Node正式reader 原生preflight缺來源／能力／格式負例；native scene marker/closure原子拒絕。另 rule-reader gate 有真 browser canonical/evidence/capability拒絕且零confirm與World/context/raw/history不變。','本列具名負例已核收；rule-reader 34 的細項另見封存 command.log，不以總數代替。')
row('SR22','observed-with-limits', ['test_cancel_create_key_lifecycle','test_query_success'], ['遲到','late','過期','context','undo','復原','重做'], ['rule confirmation removes raw draft','native rejection and preview cancellation','rule prepared leases reject','late rule reply cannot','retry uses the committed receipt'], 'native token/complete history；Node context/native revision/session/raw/history leases、lost reply reconciliation；P87/P88 真 UI cancel/history/切 context/延遲 query與focus owner有具名原始結果。','此為 source-rule交易範圍。全產品 #173 held A→B ownership 與 #174 source疑點不能被這些通過抵銷，沿既有專項保留。')
row('SR23','partial-evidence', [], ['1280','390','真 Tab/Enter','真 Save ZIP','兩面正常 UI'], [], 'P87/P88 1280及390真點擊／選項鍵盤、空白建source/rule、兩binding/applied面、guide/direct、pitch修改、保存新空白重開；44px/無水平溢出/焦點有原始檢查。','完整 issue必走順序要求先建立引用、再第二面、再改pitch看既有有限下游；P88先完成兩面+pitch更新才建引用，且SR16的非法下游UI與SR18角色鎖因未覆蓋。只補這條組合差異，不重跑所有已過基礎gates。390雙擊其他產品流程仍按原專項，不能宣稱全產品鍵盤等效。')
row('SR24','external-unverified', [], [], [], '桌面 Chromium 390px 與受控 chooser只證明自動化入口；未取得實體手機原始驗收。','由實機QA在交付精確版本分別記錄觸控、IME/軟鍵盤、OS選檔、下載位置；保存裝置/OS/瀏覽器版本與原始結果。不得關閉或稱全平台通過。')

assert len(rows)==24
inputs=[issue_path,native_source,native_receipt,native_log,cdp,E/'gates/full-cdp-r3/receipt.json',node,E/'native/full-run-all-new-owners.json',E/'public-candidate/report-support/native-source-impact-458-to-5174.json',ROOT/'公理層.md',ROOT/'geometry-core/GRID-SUBDIVISION-NATIVE-CONTRACT.md',ROOT/'geometry-core/NATIVE-SUBDIVISION-VALIDATION-20261004.md',ROOT/'tests/mutate.py',ROOT/'tests/mutants_results.json',ROOT/'geometry-web/grid_rule_editor_test.js',ROOT/'geometry-web/grid_rule_lines_test.js',ROOT/'tests/test_subdivision_project_store.js',ROOT/'tests/test_grid_rule_draft.js',E/'gates/rule-reader/receipt.json',E/'gates/rule-reader/command.log']
source_diff=git('diff','--name-status',test_head,head,'--','tests/test_grid_subdivision_oracle.py','geometry-web/grid_rule_editor_test.js','geometry-web/grid_rule_lines_test.js','tests/test_grid_rule_draft.js','tests/test_subdivision_project_store.js','公理層.md')
metadata={'schema':'geometry-final-clause-mapping/1','createdAt':datetime.now(timezone.utc).isoformat(),'scope':'Read-only source/evidence mapping. No test execution, product mutation, policy/axiom change, issue closure or release approval.','author':'/root/report_finalize','currentHead':head,'main':main,'currentStatus':status,'browserTestHead':test_head,'nativeTestHead':native_head,'sourceDifferenceFromBrowserTestForMappedFiles':source_diff,'browserReceipt':str(E/'gates/full-cdp-r3/receipt.json'),'nativeReceipt':str(E/'native/full-run-all-new-owners.json'),'nativeSourceEquivalence':str(E/'public-candidate/report-support/native-source-impact-458-to-5174.json'),'executionBinding':{'browserCommand':['node','geometry-web/cdp_test.js'],'browserExitCode':0,'browserRuntime':json.loads(read(E/'gates/full-cdp-r3/receipt.json'))['before']['runtime'],'nativeCommand':['python3','tests/run_all.py'],'nativeExitCode':json.loads(read(E/'native/full-run-all-new-owners.json'))['exit_code']},'inputs':[{'path':str(p),'sha256':sha(p)} for p in inputs],'rows':rows}
dump(OUT/'sr01-sr24.json',metadata)
dump(OUT/'mapping-commands.json',{'argv':sys.argv,'python':sys.version,'commands':commands,'readOnly':True})
lines=['# #62 SR01–SR24：來源與封存 oracle 映射','',f'只讀核對於 {metadata["createdAt"]}。目前 head `{head}`；main `{main}`。未跑測試、未改產品或公理。','',f'真瀏覽器收據：`node geometry-web/cdp_test.js`，exit 0，clean `{test_head}`。具名 P87/P88 原始通過行見 [browser-named-oracles.json](browser-named-oracles.json)，runtime／bridge 指紋見 [full-CDP receipt](../../../gates/full-cdp-r3/receipt.json)。2207/0 只作整體執行背景，不推導每列已驗。','',f'原生／Node：`python3 tests/run_all.py`，exit 0，clean `{native_head}`；[native source-equivalence](../../../public-candidate/report-support/native-source-impact-458-to-5174.json)保留版本界線。41個 native 方法由 [AST census＋完整原始收據](native-method-census.json)配對，原始 unittest log 只有點號，沒有逐方法印名。JSON逐列保留精確 test function、source line、原始 log line。','', '狀態 `observed` 只核收本列所列樣本；`partial-evidence` 是精確證據缺口，不是產品失敗；既有獨立審查不因本映射重開。','', '| ID | 狀態 | 已有具名 oracle／實際觀察 | 真正剩餘範圍 |','|---|---|---|---|']
for r in rows:
    names=', '.join('`'+x['name']+'`' for x in r['nativeOracles'])
    b='; P87/P88 log '+','.join(str(x['line']) for x in r['browserOracles'][:6])+('…' if len(r['browserOracles'])>6 else '') if r['browserOracles'] else ''
    j='; Node log '+','.join(str(x['line']) for x in r['nodeOracles']) if r['nodeOracles'] else ''
    lines.append('| '+r['id']+' | '+r['state']+' | '+(names+b+j+'。'+r['observedScope']).replace('|','／')+' | '+r['remainingExactScope'].replace('|','／')+' |')
lines += ['', '完整來源雜湊與逐條 machine index：[sr01-sr24.json](sr01-sr24.json)。issue原文快照：[issue62-source.json](issue62-source.json)。', '', '## 不屬於單列可推論的交付條件', '', '- SR04 原文與現行 SSOT 的差异是歷史期待被採納修正；不追加 panel rule 功能。', '- 原生 ASan/UBSan 歷史文件載 frozen `f0a185df8a8a5e15d792fad7f35fcd1a68d38478` 的152/152、64MiB stack及原始log hash `00766856e9148ff432cf7826e4b9958f29c48d30f1cd9b7aad3a38b54bf0c430`，但指定 `/tmp/subdivision-repeat-only-sanitizers-valid.log` 在本環境不存在。這份文件是歷史申報，不是本輪原始log已驗；需原owner交回log/build命令/來源閉包，才判是否已可沿用；不先要求重跑。', '- `tests/mutate.py`的48筆為一般scene/core守門，当前只核到freshness check。沒有指名 #62 五項必要故障注入的逐項變異/編譯/原版通過/語義失敗/恢復結果收據。不得拿40 killed或其它專項mutation數字頂替；原owner先定位既有原件，缺件再對應列明未驗。', '- 原生驗證文件提到reader三道同步及兩份歷史snapshot；此次完整aggregate中的reader測試不能倒推歷史同步命令原件已存在。沿既有reader交付鏈索引核對，不新增第二閱讀器。', '- #62整段關單仍受SR06/SR14/SR15/SR16/SR18/SR23精確範圍、故障注入/歷史原件及SR24限制；不能泛稱只剩外部條件。']
(OUT/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'output':str(OUT),'clauses':len(rows),'nativeMethods':len(native_methods),'browserNamedOracles':len(browser_oracles),'sourceDiff':source_diff,'head':head},ensure_ascii=False))
