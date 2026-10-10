"""Read archived records/source only. Never invokes tests, browsers or services."""
import ast, hashlib, json, re, subprocess, tarfile
from datetime import datetime, timezone
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=Path('/workspace/geometry-axiom')
PUB=Path('/workspace/closure-evidence/public-candidate')
ARCHIVE=PUB/'native/new-owner-native-suite-raw-logs.tar.gz'
NATIVE='458779f003e1f57fdc0f4420564a0b295227843e'
BROWSER='5174a8dafd8c48329d7166abbd3d104e3c28c0c4'
HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
sha=lambda b:hashlib.sha256(b).hexdigest()
def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def at(path,needle):
    lines=(ROOT/path).read_text().splitlines()
    return {'path':path,'line':next(n for n,s in enumerate(lines,1) if needle in s),'symbol_or_text':needle}

origin=Path('/workspace/closure-evidence/inventory/remote-refresh-environment-return/open-issues.json')
issue=next(x for x in json.loads(origin.read_text()) if x['number']==24)
(OUT/'issue-24-body.md').write_text(issue['body']+'\n')
dump(OUT/'issue-24-source.json',{'source':str(origin),'source_sha256':sha(origin.read_bytes()),'url':issue['html_url'],'updated_at':issue['updated_at'],'state':issue['state'],'note':'Previously archived API response; no new network request or issue mutation.'})
requirements={}
for n,line in enumerate(issue['body'].splitlines(),1):
    m=re.match(r'\| (A\d\d) \| (.*?) \| (.*?) \|',line)
    if m:requirements[m[1]]={'scenario':m[2],'expected':m[3],'source_body_line':n}
assert len(requirements)==24

# Extract existing raw logs into the assigned output directory, byte-for-byte.
with tarfile.open(ARCHIVE) as t:
    selected=[m for m in t.getmembers() if m.isfile() and (m.name.endswith('/node_tests-js.log') or re.search(r'/py_test_assembly_(rules|capacity|generation|parameter_refs)\.(json|log|unittest.log)$',m.name))]
    for m in selected:
        p=OUT/'raw-native'/Path(m.name).name;p.parent.mkdir(exist_ok=True);p.write_bytes(t.extractfile(m).read())
dump(OUT/'raw-native/extraction.json',{'archive':str(ARCHIVE),'archive_sha256':sha(ARCHIVE.read_bytes()),'members':[{'archive_member':m.name,'file':Path(m.name).name,'sha256':sha((OUT/'raw-native'/Path(m.name).name).read_bytes())} for m in selected]})
browser_log=PUB/'gates/full-cdp-r3/command.log'
browser_lines=browser_log.read_text().splitlines()
node_lines=(OUT/'raw-native/node_tests-js.log').read_text().splitlines()
native_receipt=json.loads((PUB/'native/full-run-all-new-owners.json').read_text())
browser_receipt=json.loads((PUB/'gates/full-cdp-r3/receipt.json').read_text())
assert native_receipt['head']['stdout'].strip()==NATIVE and native_receipt['exit_code']==0 and native_receipt['status']['stdout']==''
assert browser_receipt['before']['git']['head']==BROWSER and browser_receipt['after']['git']['head']==BROWSER
assert browser_receipt['execution']['exitCode']==0 and browser_receipt['evidence']['canonicalResult']['completed']
assert browser_receipt['log']['sha256']==sha(browser_log.read_bytes())
registry={}
for name in ['rules','capacity','generation','parameter_refs']:
    path=f'tests/test_assembly_{name}.py'
    tree=ast.parse((ROOT/path).read_text())
    methods={n.name:{'path':path,'line':n.lineno,'end_line':n.end_lineno,'source_sha256':sha(ast.get_source_segment((ROOT/path).read_text(),n).encode())} for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith('test_')}
    receipt=json.loads((OUT/f'raw-native/py_test_assembly_{name}.json').read_text())
    assert len(methods)==receipt['total']==receipt['run']==receipt['passed'] and receipt['failed']==receipt['skipped']==0
    registry.update({key:dict(value,suite=name,suite_raw_receipt=f'raw-native/py_test_assembly_{name}.json',tested_sha=NATIVE,result='pass via complete unfiltered file execution and AST census; dot log does not name individual methods') for key,value in methods.items()})
dump(OUT/'native-method-census.json',registry)

def N(*names):return [dict(registry[name],oracle=name) for name in names]
def U(*names):
    result=[]
    for name in names:
        matches=[(n,l) for n,l in enumerate(browser_lines,1) if l.startswith('P77 '+name+' ✓')]
        assert len(matches)==1,(name,matches)
        n,line=matches[0]
        found=[]
        for p in (ROOT/'geometry-web').glob('assembly*_test.js'):
            for ln,s in enumerate(p.read_text().splitlines(),1):
                if "check('"+name+"'" in s:found.append({'path':str(p.relative_to(ROOT)),'line':ln})
                if re.fullmatch(r'同值換來源 [12] 確認保留精確引用',name) and 'check(`同值換來源 ${index+1} 確認保留精確引用`' in s:
                    found.append({'path':str(p.relative_to(ROOT)),'line':ln,'note':'Generated index+1 name; concrete raw log value preserved.'})
        assert found,name
        result.append({'oracle':name,'raw_log':str(browser_log),'line':n,'raw':line,'result':'pass','tested_sha':BROWSER,'source_locations':found})
    return result
def J(*names):
    result=[]
    for name in names:
        matches=[(n,l) for n,l in enumerate(node_lines,1) if l.startswith('✔ '+name+' (')]
        assert len(matches)==1,(name,matches)
        n,line=matches[0]
        found=[]
        for p in (ROOT/'tests').glob('test_*.js'):
            for ln,s in enumerate(p.read_text().splitlines(),1):
                if "test('"+name+"'" in s:found.append({'path':str(p.relative_to(ROOT)),'line':ln})
        assert found,name
        result.append({'oracle':name,'raw_log':'raw-native/node_tests-js.log','line':n,'raw':line,'result':'pass','tested_sha':NATIVE,'source_locations':found,'scope':'Node test; fake HTTP/DOM unless test explicitly constructs real service'})
    return result

core=lambda symbol:at('geometry-core/assembly.inc',symbol)
web=lambda symbol:at('geometry-web/assembly-workspace.js',symbol)
store=lambda symbol:at('geometry-web/project-store.js',symbol)
ref=lambda symbol:at('geometry-web/reference-workspace.js',symbol)
bridge=lambda symbol:at('geometry-web/assembly_bridge.inc',symbol)
rows=[]
def row(i,impl,native=(),browser=(),node=(),observed='',limits='',remaining='No additional mandatory internal work established by these records; preserve the stated observation boundary.',status='bounded automated evidence'):
    rows.append(dict(id=i,**requirements[i],implementation=impl,native=N(*native),browser=U(*browser),node=J(*node),observed=observed,limitations=limits,remaining=remaining,status=status))

row('A01',[web('async function prepareDraft'),ref('function setAssemblyDraft'),core('static bool asm_publish')],['test_publish_without_geometry_and_native_identity'],['空世界草稿從零開始','開啟中的草稿保存最新值','發布後原生卡片可找到且不生成角材'],['draft-only projects require assembly capability and format 7, preserving incomplete values'],observed='空白正式 UI 建草稿，ZIP 保存未發布值；native 規則可獨立於面、角材存在。',limits='P77 草稿 ZIP 使用 exportBytes/importBytes；不是 OS chooser。')
row('A02',[web('function ruleForm'),core('static bool asm_validate_rule')],['test_publish_without_geometry_and_native_identity'],['A23 390px 空白建立完整規則的精確來源','A23 手機發布資料由原生核心讀回完全一致'],observed='真新增槽位、member、joint；完整規則定義由 native 讀回相等。',limits='390px 為 Chromium emulation，非手機。')
row('A03',[web('function ruleForm'),web('function diagram'),core('static bool asm_validate_rule')],['test_orthogonal_split_and_geometric_loop'],['正交分段按局部交換連續構件','A04 不同局部配置真正寫進原生發布版本'],['endpoint and direction choices change drawn SVG attributes, not only text'],observed='連續方交換改 typed definition；SVG 端點/方向有具體幾何屬性 oracle。')
row('A04',[web('function ruleForm'),core('static bool asm_validate_rule')],[],['A04 單次局部交換精確改第一接合並保留第二接合','A04 不同局部配置真正寫進原生發布版本','A04 真正保存重開後兩處不同接合與完整定義不變'],observed='局部 first joint 精確交換，第二 joint 和其餘欄位全等，发布及 ZIP 重開仍全等。',limits='P77 ZIP 走正式 API；不是 chooser。A04 原已補齊，不重開舊待辦。')
row('A05',[core('static bool asm_validate_rule'),web('function diagram')],['test_missing_duplicate_and_unknown_fields_rejected','test_binding_slot_and_face_contract'],['起終端控制改变接觸處實際圖形位置','局部 u/v 控制改变實際方向箭頭端點','圖上點選與鍵盤選面同步表單','新增方向及端點圖形旋轉縮放不改固定身分','示意控制結果與真核心讀回一致且不生成角材'],observed='end/side/dir 固定身份，游標式 side 與未知 kind 拒絕；UI 图/表單與 native 相符。')
row('A06',[core('static bool asm_validate_rule'),bridge('static void json_assembly_preview')],['test_duplicate_scope_and_endpoint_rejected'],['衝突預覽拒絕且正式世界為空'],observed='重複 scope/endpoint 診斷含 joints 1 and 2；共用 reject oracle 核確認拒絕、dump/revision不變。')
row('A07',[core('static bool asm_validate_rule'),web('function ruleForm')],['test_immutable_version_rename_reorder_and_fixed_binding'],['改名排序不改接合身分'],observed='改名重排不變 joint/member 對應；native 新版可倒序而舊 binding 保持 v1。')
row('A08',[core('static bool asm_validate_rule'),core('static bool assembly_rebuild'),web('function ruleForm')],['test_missing_duplicate_and_unknown_fields_rejected','test_binding_slot_and_face_contract','test_referenced_rule_delete_and_atomic_rebind'],['刪除使用中槽位指出構件'],observed='被引用 slot 的 UI 刪除拒絕；native dangling refs拒絕，合法改綁+刪除同交易可Undo/Redo。')
row('A09',[core('static bool asm_validate_rule')],['test_orthogonal_split_and_geometric_loop'],observed='具四個 member 的四邊幾何鄰接環發布成功，規則數精確為2。',limits='不是求值依賴循環求值器測試。')
row('A10',[core('nested rules are unsupported')],['test_missing_duplicate_and_unknown_fields_rejected'],observed='kind=nested-rule、未知欄位、錯引用由 I40 schema 原子拒絕。',limits='首版無巢狀規則引用/求值器；#24 A10 明文容許此能力邊界。',remaining='None within adopted authoring schema. Do not add a recursive evaluator to satisfy an inexpressible case.',status='explicit accepted capability boundary')
row('A11',[core('static bool asm_binding_parse'),web('function sources'),web('function bindingForm')],['test_material_source_and_parameter_recomputation'],['同值換來源 1 確認保留精確引用','同值換來源 2 確認保留精確引用','換來源重做保存重開保留固定版本與參數引用'],observed='同材同版、同材不同版、不同材3配置；逆序slots，以固定identity比完整value/effective/path；新材料版不暗升；fresh native reload全state/dump。')
row('A12',[core('static bool asm_binding_parse'),web('function bindingForm'),store('function validateAssemblyDraft')],['test_unselected_binding_is_saved_as_incomplete'],['未選材料保存為未完成'],['draft-only projects require assembly capability and format 7, preserving incomplete values'],observed='全空与4種僅一slot缺face/orientation合法incomplete；已選來源/value/path保留；fresh reload完整相等；面/角材/instance皆空。')
row('A13',[core('static bool asm_binding_parse'),core('static bool asm_validate_rule')],['test_bad_dimension_sources_rejected_not_incomplete','test_wrong_typed_fractional_sources_and_legacy_delete_reject','test_material_kind_field_and_fixed_version_are_not_incomplete_values'],observed='不存在材料/版、錯kind/axis/type、非正尺寸與非法ParameterRef原子拒絕；容量上界/下一筆拒絕另有capacity具名方法census。')
row('A14',[web('function diagram'),core('static bool assembly_dimensions_changed')],['test_canvas_move_preserves_preview_and_history'],['旋轉縮放只改檢視','拖曳原生卡片只改位置','新增方向及端點圖形旋轉縮放不改固定身分'],observed='旋轉縮放完整draft不變；真drag位置變且native rule fingerprint不變；native canvas-pos在pending binding後保留confirm及Undo/Redo。',limits='真drag的直接oracle沒有同時全量比對每一份binding/material mapping；原20261004索引已明示此限制。',remaining='Optional strengthening: capture full assembly-read before/after the same trusted drag and compare every binding; not evidence of a discovered product bug or a reopened accepted A04/A18/A23 gap.',status='composed evidence with declared direct-oracle limit')
row('A15',[web('function freeId'),web('async function prepareDraft'),core('static bool assembly_operation')],['test_copy_and_idempotent_publication','test_newid_wraps_past_max_in_independent_assembly_namespaces'],['複製有新原生身分','A15 真複製跳過原生及草稿取得規則3','A15 複製發布保留原有2與MAX且未吞草稿1'],['new and copied rules/bindings skip interleaved native and draft IDs after uint32 wrap'],observed='native同名copy新ID，UI複製/新增/MAX回繞，不覆寫既有native或草稿。')
row('A16',[core('static bool asm_publish'),core('static bool assembly_versions_immutable'),web('async function prepareDraft')],['test_immutable_version_rename_reorder_and_fixed_binding','test_same_transaction_delete_republish_cannot_change_fixed_version','test_intermediate_identity_replacement_is_rejected_before_later_restore'],['新版本不升級既有配置','A04 不同局部配置真正寫進原生發布版本'],observed='immutable舊版不可覆寫，包括delete/republish/copy繞過；發布v2不暗升binding。')
row('A17',[web('function bindingForm'),web('function invalidate'),bridge('static void cmd_assembly_cancel')],['test_atomic_new_version_rebind_delete_cancels_and_commits','test_cancel_and_protocol_tokens_do_not_commit'],['預覽寫出換了哪一版','取消換版不改正式配置','預覽與取消不改真核心且特殊名稱只作文字'],['explicit new-version mapping keeps typed sources and its fixed provenance through undo and redo'],observed='UI明選新版/preview/cancel後binding仍v1；native cancel完整state+revision+dump相等且token不能確認；草稿選版可保留。',limits='沒有單一UI case同時全量比較World+history+dirty；正式preview取消不是撤銷先前已明選草稿，後者已有local history。',remaining='Optional single-UI World/history/dirty snapshot strengthening; existing acceptance index explicitly treats this as composed coverage, not a newly necessary product change.',status='composed evidence with declared direct-oracle limit')
row('A18',[core('static void assembly_dump'),core('static bool apply_assembly_line'),store('function validateAssemblyDrafts'),ref('c.assemblyDrafts=JSON.parse')],['test_scene_roundtrip_in_fresh_process','test_material_source_and_parameter_recomputation','test_unselected_binding_is_saved_as_incomplete'],['保存重開保留所有版本配置與卡片位置','A18 範例配置一固定第1版且逐槽來源與有效值正確','A18 範例配置二固定第2版且保留精確未完成槽位','A18 範例版本槽位排序與未發布草稿不混為另一版','回覆完成後共用保存重開仍保留 B 精確資料'],['binding create/update intent and exact original source survive formal archive reopen'],observed='兩版本+各自binding精確來源/null，草稿獨立；fresh native scene全等。額外compound-project清空確認+fresh browser正式Save/New/Open覆蓋非空model+draft+assembly instance。',limits='P77位置是hasPos，不是所有座標全等；compound另有完整payload equality，但fixture不等於P77所有兩版組合。',remaining='No reopened A18 gap. Optional one-archive two-bindings+draft+all-position coordinates joint equality is additional strengthening, not a discovered missing implementation.')
row('A19',[ref('function setAssemblyDraft'),ref('function beginAssemblyConfirmation'),store('class ContextHistory'),web('async function confirm')],['test_atomic_new_version_rebind_delete_cancels_and_commits','test_referenced_rule_delete_and_atomic_rebind','test_identical_delete_republish_has_no_revision_or_history_change'],['成功僅清理提交草稿且只新增一筆共用歷史','單步復原原生發布同時恢復兩份草稿','單步重做只清理原提交草稿','換來源單步復原還原先前 B 引用','換來源重做保存重開保留固定版本與參數引用','G08 刪除整個實例與三支原生角材','G08 單步復原映射與實例','G08 單步重做刪除'],['assembly drafts and native confirmation share undo and redo without losing incomplete edits','ordinary, rejected and no-op assembly results release the guard and preserve native history counts'],observed='native建立/刪除/改綁交易完整Undo/Redo，Node共用history與no-op，UI發布dirty=true只一筆history、草稿協調；另真instance刪除Undo/Redo。',limits='未聲稱每一種規則/綁定UI刪除/改綁均在同一案例逐步比較dirty。',remaining='Optional UI delete-rule/delete-binding/rebind per-action dirty snapshot strengthening; native operations and shared-history mechanism have named evidence. No product defect discovered by this read-only mapping.',status='composed evidence with declared direct-oracle limit')
row('A20',[core('static bool apply_assembly_line'),store('function validateAssemblyDrafts'),ref('assertAssemblyIdle')],['test_truncated_corrupt_and_duplicate_records_are_atomic'],['G06 能力不足拒絕匯入且世界草稿歷史不變'],['draft capability stripping, old format, unknown schema and duplicate IDs reject','a late successful assembly reply cannot dirty, append history or notify an externally replaced context','matrix: unknown project versions and stripped or unknown capability markers are rejected'],observed='殘缺/重複/未知schema/必要能力不足明確拒絕；原native dump 或project context/history保留。')
row('A21',[store('const ASSEMBLY_FORMAT'),store('class ContextHistory')],[],[],['old projects stay v1/v2 without defining existing faces; an empty definition list is not a forced upgrade','a face with no PDF or model saves and reopens its definition as v3, independently for each placement','timber records round trip as v4 with exact id zero, source snapshots and independent geometry packages','engineering scene remains the sole source and selects v5 with a required capability','parameter projects use /6, retain scene bytes and require native support','legacy v1/v2/v3 archives and height-edit inputs do not gain empty timber fields or forced v4 upgrades'],observed='v1/v2/v3/v4/v5/v6實際ZIP accepted/roundtrip保留format與來源；沒有只用拒絕降版負例替代合法舊格式。',limits='Node存儲/服務測試，不宣称所有旧版都在真OS chooser跑一遍。')
row('A22',[core('Authoring validates sources and local topology'),web('async function newInstance'),at('geometry-core/assembly_generation.inc','static bool')],['test_authoring_capability_does_not_enable_model_generation','test_missing_wrong_sources_and_inward_joint_geometry_are_atomic','test_unsupported_section_orientation_and_joint_topology','test_unselected_sources_report_i42_and_preserve_world_on_create_and_edit','test_source_change_collision_rejects_entire_world'],['發布後原生卡片可找到且不生成角材','示意控制結果與真核心讀回一致且不生成角材','G06 未選定位線不能套用'],observed='authoring不生成；model load因CAPABILITY拒絕。不完整有限生成輸入禁止套用；有限生成具名負例驗錯承載/guide/support、inward接合、超出支持拓樸/方向與碰撞拒絕、World不變。',limits='不把有限3member生成宣稱任意拓樸。')
row('A23',[web('function ruleForm'),web('function bindingForm'),web('function close'),web('function lockConfirm'),at('geometry-web/assembly-workspace.css','44px')],[],['390px 完成 A/B 材料配置','390px 無橫向溢出與小於44px操作','390px 端點方向圖可操作且沒有橫向溢出','390px 最大縮放旋轉後選面至少44px且不覆蓋接觸圖','A23 390px 空白建立完整規則的精確來源','A23 390px 從空白新增全流程無橫向溢出','A23 未發布手機草稿真正保存重開仍可編輯','A23 手機發布資料由原生核心讀回完全一致','A23 手機已發布規則再重開仍保留身分接合與來源','確認期間明確鎖住改稿切稿關閉與連點','未知结果只用鍵盤返回重連再開不盲送也不刪草稿'],['declining the existing leave gate preserves the old draft owner and pending token'],observed='桌面+390px真建/編輯/控制/返回與鍵盤恢復；草稿/發布兩次重開，完整定義native equality；尺寸44px和無overflow。',limits='合成輸入不是手機IME；P77保存重開是正式API；compound補產品Save/New/Open，仍不是OS dialog。')
row('A24',[at('geometry-web/docs/ASSEMBLY-RULES-VALIDATION.md','## A24 實機驗收交接')],observed='沒有實體iOS/Android驗收收據。既有M1–M5操作與裝置表仍未填。',limits='Linux Chromium/390px、Node、native、完整CDP均不能代替實體鍵盤/IME/OS chooser/下載目的地/取消。',remaining='Physical-device QA owner (not assigned in accessible records) runs existing M1–M5 on actual iOS/Android, records tested full SHA/runtime, OS/browser/device/orientation/input method, real saved file/destination/reopen and cancel outcomes. Project owner signs off; #19/#24 remain open.',status='external manual acceptance not executed')

compound=[]
compound_audit=json.loads((PUB/'gates/compound-project/audit.json').read_text())
for width in [1400,390]:
    path=PUB/f'gates/compound-project/artifacts/{width}/result.json'
    record=json.loads(path.read_text())
    assert record['passed'] and all(x['passed'] for x in record['checks'])
    for item in record['checks']:
        compound.append(dict(item,viewport=width,raw_result=str(path),raw_result_sha256=sha(path.read_bytes()),tested_sha=compound_audit['head']))
for r in rows:
    r['supplemental']=compound if r['id'] in ('A18','A23') else []

bindings={'native':{'receipt_path':str(PUB/'native/full-run-all-new-owners.json'),'receipt_sha256':sha((PUB/'native/full-run-all-new-owners.json').read_bytes()),'receipt':native_receipt,'environment':json.loads((PUB/'native/full-run-all-new-owners-environment.json').read_text()),'native_binary_source_binding':'public-candidate/native/full-run-all-new-owners.stdout records all required binaries fresh; browser receipt below binds configured binary SHA plus separate live process observation. Native full suite inherits binaries runner environment; no newly executed probe.'},'browser':{'receipt_path':str(PUB/'gates/full-cdp-r3/receipt.json'),'receipt_sha256':sha((PUB/'gates/full-cdp-r3/receipt.json').read_bytes()),'command':browser_receipt['command'],'before':browser_receipt['before'],'after':browser_receipt['after'],'execution':browser_receipt['execution'],'log':browser_receipt['log'],'source_binding':json.loads((PUB/'gates/full-cdp-r3/executed-source-binding.json').read_text()),'live_process_observation':json.loads((PUB/'gates/full-cdp-r3/pre-run-live-process.json').read_text()),'limitations':browser_receipt['limitations']},'compound':{k:compound_audit[k] for k in ['head','command','commandExitCode','gateExitCode','dirtyBefore','dirtyAfter','runtimeBefore','runtimeAfter','canonicalLimitations','sources']}}
dump(OUT/'execution-bindings.json',bindings)

files=set()
for r in rows:
    for item in r['implementation']+r['native']:files.add(item['path'])
    for evidence in r['browser']+r['node']:
        for loc in evidence['source_locations']:files.add(loc['path'])
# Transitive native source closure is separately attested by the saved source-impact audit.
files.update(['公理層.md','geometry-core/assembly_types.h','geometry-web/project-store.js','geometry-web/reference-workspace.js','tests/run_all.py'])
identities=[]
for path in sorted(files):
    versions={}
    for revision in [NATIVE,BROWSER,HEAD]:
        proc=subprocess.run(['git','show',revision+':'+path],cwd=ROOT,capture_output=True)
        versions[revision]={'git_exit':proc.returncode,'sha256':sha(proc.stdout) if proc.returncode==0 else None}
    identities.append({'path':path,'revisions':versions,'same_across_recorded_heads':len({x['sha256'] for x in versions.values()})==1,'worktree_sha256':sha((ROOT/path).read_bytes())})
dump(OUT/'source-identities.json',identities)
assert all(x['same_across_recorded_heads'] for x in identities),[x['path'] for x in identities if not x['same_across_recorded_heads']]
dump(OUT/'mapping.json',{'schema':'assembly-A01-A24-readonly-evidence-map/1','recorded_at':datetime.now(timezone.utc).isoformat(),'review_head':HEAD,'native_tested_sha':NATIVE,'browser_tested_sha':BROWSER,'no_tests_executed':True,'execution_bindings':'execution-bindings.json','rows':rows})
(OUT/'P77-excerpt.txt').write_text('\n'.join(f'{n}: {l}' for n,l in enumerate(browser_lines,1) if l.startswith('P77 ') or l.startswith('=== P77'))+'\n')
out=['# #24 A01–A24 逐條來源／封存證據映射','',
'只讀審查；沒有啟動 native、瀏覽器、測試或服務，沒有修改 repo、public-candidate、queue 或外部資料。原矩陣來自封存 GitHub #24 body；完整原文與來源雜湊保存在 `issue-24-body.md` / `issue-24-source.json`。不是依公理編號猜測 A 編號。','',
f'目前審查 HEAD `{HEAD}`；原始 native 命令實際受測 clean `{NATIVE}`，full-CDP-r3 實際受測 clean `{BROWSER}`。後續 docs-only 提交不重新標成產品實跑版本。所有本表使用的產品／測試檔在三個 SHA bytes 相同，見 `source-identities.json`；完整 native 閉包與 app VM slices另見既有 `public-candidate/report-support/native-source-impact-458-to-5174.json`。','',
'native 檔案方法由 AST 定位，逐檔 census 精確等於完整執行收據 run=passed、failed=skipped=0，並已閱讀相關 oracle。原始 unittest log 只有點號；本表不冒稱原始 log 逐方法列名。Node/raw P77 則有具名通過行。沒有以 suite 或斷言總數替代條目內容。','',
'可用原件：`public-candidate/native/full-run-all-new-owners.json`（命令、clean SHA、exit 0）、`raw-native/`（封存 tar member 原bytes）、`public-candidate/gates/full-cdp-r3/{receipt.json,command.log}`（命令、clean SHA、runtime/bridge、exit 0、completed=true、具名 P77）、`public-candidate/gates/compound-project/`（產品保存/清空/fresh browser重開）。完整命令/環境/時間/來源腳本雜湊/退出碼/載入bridge獨立觀察整理於 `execution-bindings.json`；native全套為 `ulimit -s 16384` 後 `python3 tests/run_all.py`，browser為 `node geometry-web/cdp_test.js`，不可把裸命令當有相同環境。full-CDP raw exception 1 為既有 P38 預期注入；P77 自身具名例外檢查通過，不稱全局 zero exception。','',
'判定：A01–A23 都能找到對應已執行 oracle 或 A10 的原文允許能力邊界。A14/A17/A19 保留既有組合證據的直接觀察限制；這份唯讀映射沒有發現新的必須改產品的 assembly 缺陷，亦不能把這些限制改寫成一個未曾執行的全量 UI oracle。A24 是確定尚未執行的實體裝置條件。整張 #19/#24 保持 open；其他 #173/#174/Resume 的已知產品失敗仍由各自 gate 管理，本表不代替整體候選批准。','']
for r in rows:
    out.extend([f"## {r['id']} — {r['scenario']}",'',f"原矩陣原文：**{r['expected']}**（`issue-24-body.md:{r['source_body_line']}`；https://github.com/ZhiQiYang/geometry-axiom/issues/24）。",'',
      '實作：'+'；'.join(f"`{x['path']}:{x['line']}` `{x['symbol_or_text']}`" for x in r['implementation'])+'。','',f"判定：**{r['status']}**。{r['observed']}",''])
    for kind in ['native','browser','node']:
        for e in r[kind]:
            loc=(f"{e['path']}:{e['line']} / {e['suite_raw_receipt']}" if kind=='native' else f"{e['raw_log']}:{e['line']}")
            out.append(f"- {kind} `{e['oracle']}` — {e['result']}；受測 `{e['tested_sha']}`；`{loc}`。")
    if r['supplemental']:
        out.append('- compound-project：1400/390 各自具名 `trusted New clears native World, model, drafts, instances and changes project identity`、`second browser process with fresh profile starts empty before Open`、`fresh-profile formal chooser restores complete World, references, instances, model and draft bytes` 均通過；完整11項/width來源與時刻見 mapping.json supplemental，原件 `public-candidate/gates/compound-project/artifacts/{1400,390}/result.json`；受測 clean `'+BROWSER+'`，命令/gate退出0。API seed明示，正式Save/New/Open是真產品控件及chooser事件，但不是OS picker。')
    out.extend(['',f"限制：{r['limitations'] or '仅覆盖具名 oracle 及其 fixture，不扩推任意参数/全部装置。'}",'',f"剩餘：{r['remaining']}",''])
out.extend(['## A24 原有 M1–M5 解除步驟','',
'依 `geometry-web/docs/ASSEMBLY-RULES-VALIDATION.md:49` 原交接，不另設新驗收：M1 中文IME/鍵盤/直橫向/焦點與可達性；M2 真保存且在OS目的地找到非空gcanvas；M3 另一空白專案經OS選檔重開；M4 兩發布版/完整與未完整binding/草稿重開核對；M5 離開提示、OS選檔和可取消保存提示的取消。填日期、驗收者、裝置、OS、瀏覽器、runtime/完整SHA及原始結果。可取得紀錄沒有指名當前實體裝置驗收owner，保持 unknown，不虛構已派工。','',
'## 可加強但不得偽稱已執行的組合觀察','',
'A14：同一次真drag前後全量 assembly-read 對所有binding/material mapping。A17：明選v2並preview/cancel的同一UI案例一次核對World/history/dirty；取消的起點應是已選草稿，不能錯把撤銷草稿選版當契約。A19：規則/綁定各自UI刪除與改綁逐次dirty快照。A18：同一兩binding+draft archive的所有座標精確 equality。既有 20261004 acceptance index 已明示前三者/位置限制，且把 A17/A18 整合 oracle列為可加強、非新增必要要求；本次保留此區別，不把未做的單一大case說成已做，也不擴張工作範圍。',''])
(OUT/'README.md').write_text('\n'.join(out))
dump(OUT/'artifact-hashes.json',{'created':datetime.now(timezone.utc).isoformat(),'files':[{'path':str(p.relative_to(OUT)),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='artifact-hashes.json']})
print(json.dumps({'rows':len(rows),'review_head':HEAD,'source_files_checked':len(identities),'output':str(OUT),'no_tests_executed':True},ensure_ascii=False))
