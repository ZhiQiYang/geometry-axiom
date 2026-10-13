import hashlib,json,pathlib,shutil,subprocess
root=pathlib.Path.cwd();out=root/'tests/evidence/k2a-contract-review-20261012';assert not out.exists()
base='49c391f2afbcee17bb2647fce74c3c5532a01527'
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==base
paths=['geometry-core/drafts-topology/PROPOSAL.md','geometry-core/drafts-topology/README.md']
changed=subprocess.check_output(['git','diff','--name-only'],text=True).splitlines();assert sorted(changed)==sorted(paths),changed
protected=['公理層.md','geometry-guide/公理層-白話.md','geometry-guide/公理層-閱讀器.html','current_geometry.c','BACKLOG.md','決策佇列.md','geometry-core/modeling/__init__.py','tests/mutants_results.json','tests/run_all.py','tests/run_all.expected.json']
assert subprocess.check_output(['git','diff',base,'--',*protected])==b''
def sha(b):return hashlib.sha256(b).hexdigest()
sources={p:sha((root/p).read_bytes()) for p in protected}
sources.update({p.relative_to(root).as_posix():sha(p.read_bytes()) for p in (root/'geometry-web').glob('*.js')})
old_proposal=subprocess.check_output(['git','show',base+':'+paths[0]]).decode();ssot=(root/'公理層.md').read_text()
record={'base_head':base,'status_at_checks':subprocess.check_output(['git','status','--porcelain'],text=True).splitlines(),
    'scope':'Documentation contract fixes only; observed exec-tool exits, not retroactive Popen receipts or product lifecycle acceptance',
    'source_sha256':sources,'ssot_lf_sha256':sha((root/'公理層.md').read_bytes().replace(b'\r\n',b'\n')),
    'documents':{p:{'before_sha256':sha(subprocess.check_output(['git','show',base+':'+p])),'after_sha256':sha((root/p).read_bytes())} for p in paths},
    'before_removal_exception':[s for s in old_proposal.splitlines() if '旗標只在該引用被移除' in s],
    'ssot_replacement_rule':[s for s in ssot.splitlines() if '只隨該引用被改指向另一個物件而離開' in s],
    'commands':[{'argv':['node','/tmp/geometry-191-budget.cjs'],'exec_tool_exit_observed':0},
                {'argv':['python3','geometry-guide/sync_axiom_reader.py','--check'],'exec_tool_exit_observed':0},
                {'argv':['python3','tests/test_axiom_reader.py'],'exec_tool_exit_observed':0,'tests':41}],
    'unexecuted':['M16 source-deletion/Undo/Redo runtime','M17/M18 collection World/save/cold-reopen runtime and specified mutants','final integrated reader/source checks','formal WSL seven jobs'],
    'dependencies':{'199_head':'e837a9308642a54ba55d7d399eb66805e1d5984e','201_head_observed':'19c7e76b301d3fa500dbcb2fbc856727ea002a12','P059_comment':6113440823,'P059_scope_correction':6113762903}}
c=(root/'current_geometry.c').read_bytes();record['c_bytes']={'crlf':c.count(b'\r\n'),'bare_lf':c.count(b'\n')-c.count(b'\r\n'),'nul':c.count(b'\0')}
assert record['c_bytes']=={'crlf':13047,'bare_lf':0,'nul':0}
out.mkdir(parents=True)
for src,name in [('/tmp/geometry-191-budget.cjs','budget.cjs'),('/tmp/geometry-191-budget.log','budget.json'),
                 ('/tmp/geometry-191-reader-check.log','reader-check.log'),('/tmp/geometry-191-reader-tests.log','reader-tests.log'),
                 (__file__,'package.py')]:shutil.copyfile(src,out/name)
(out/'receipt.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
(out/'contract.diff').write_bytes(subprocess.check_output(['git','diff','--',*paths]))
(out/'README.md').write_text('''# #191 採納後契約審查修正

前版 `49c391f2afbcee17bb2647fce74c3c5532a01527` 加 dirty 提案／導讀修文，沒有產品修改。receipt 綁定原／新 Markdown、SSOT 的 LF hash、正典／核心／原 JS validator 閉包；不是乾淨新 head 的產品驗收。

M1 原文「被移除」與 I68／R54 只許改指另一物件矛盾，改為同一草稿純刪 lost 引用／清空／去標拒絕，整份明示捨棄另依 R54。M2 補新接納最壞 lost／orphans／集合外殼／能力／manifest 的逐層預算，以及已裁決 P-059 的有界歷史例外；不改 SSOT 或另授一般容量。M3 補 M16 完整 World＋附件的刪來源→窗內 Undo→Redo，包含新預覽拒／可重新預覽／拒及舊令牌不復活。M17／M18 補上限、+1、保存／冷開與指定突變契約。

budget.cjs 直接用本 head 原 Features.validateGridDraft，確實接受 131072-byte 未標草稿；補一個 lost 變131084、原單份 validator 容量拒。九個各自通過原單份 validator 的不同編輯基底草稿，有限 JSON record 恰1048576，九個 lost 增108至1048684；再列九個 orphan 至1048737。raw／rule 字串各≤4096。這是實際單份 validator＋JSON 字節算術，不是此 head 尚無的集合 runtime／刪除／保存／冷開／UndoRedo 證明。

原 --check exit0（patches0、五 assert／獨立 SSOT 通過）與原 reader 41/41 exit0，完整 log 含原 ResourceWarning 保留；没有同步寫入正典、沒有第二份 HTML。相對基準，產品 C／INC／JS、SSOT／白話／正典／🔒、runner／expected／核心 ledger 不變。未新增 runtime 測試或造紅綠／核心突變帳；表中指定突變是實作期要求，不宣稱已跑。

#191→#199 是必带同批整合依賴：P-049 的新建免基底檢查及 R55 唯一相向側面；本 head 尚未帶入，不把 descendant 算作已修。P-059 已由 #201 原件交付，仍依最終整合核收；本次不冒稱重跑其結果。正式七 job、M16–M18 新 runtime 驗收仍待原 owner；維持 draft，不合併。

SHA256SUMS 核全部 payload（不自雜湊），contract.diff 給精確修文。無新 UI 入口。CLI／算術結果不能代替最終整合 SHA 的原生／瀏覽器裁判。
'''.replace('没有','沒有').replace('必带','必帶'))
manifest=''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in sorted(out.iterdir()) if p.is_file())
(out/'SHA256SUMS').write_text(manifest);print(json.dumps({'payloads':len(manifest.splitlines()),'protected_sources_unchanged':True}))
