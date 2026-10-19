import hashlib,json,pathlib,re,subprocess
root=pathlib.Path('/workspace/geometry-axiom');scratch=pathlib.Path('/tmp/geometry-198-review2')
text=(scratch/'aggregate/run.log').read_text()
stages=re.findall(r'^\[(\d+)/83\] (\S+)',text,re.M);assert len(stages)==83 and [int(x[0]) for x in stages]==list(range(1,84))
tot=re.search(r'^合計\(已執行、有計數者\)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)',text,re.M);assert tot
total,passed,failed,skipped=map(int,tot.groups());assert (total,passed,failed,skipped)==(2731,2721,9,1)
assert json.loads((scratch/'aggregate/run.json').read_text())['returncode']==1
previous=json.loads(subprocess.check_output(['git','show','HEAD:tests/run_all.expected.json'],cwd=root))['suites']
current=json.loads((root/'tests/run_all.expected.json').read_text())['suites']
changes={k:{'before':previous[k],'after':v} for k,v in current.items() if previous[k]!=v}
assert set(changes)=={'c:integrity','core:run_tests','py:test_reference_contract'}
unchanged={}
for name in ('tests/test_reference_workspace_races.js','geometry-web/reference-workspace.js','geometry-web/project-store.js','geometry-core/rule_cases/catalog.py'):
    disk=(root/name).read_bytes();base=subprocess.check_output(['git','show','635dd86:'+name],cwd=root)
    assert disk.replace(b'\r\n',b'\n')==base.replace(b'\r\n',b'\n')
    unchanged[name]=hashlib.sha256(disk).hexdigest()
analysis={'suites_completed':len(stages),'total':total,'passed':passed,'failed':failed,'allowed_gdi_skip':skipped,'returncode':1,'reader_failures':5,'node_test_timeouts':4,'expected_count_changes':changes,'node_control_sources_unchanged_from_base':unchanged,'supplemental_node_suite':{'scope':'partial single suite with original defaults and test timeouts','passed':651,'failed':0,'skipped':0,'returncode':0},'scope':'Original full-run nine failures preserved. Supplemental node green is not a full-run waiver or final-head seven-job acceptance.'}
(scratch/'aggregate/analysis.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n')
paragraph='完整非瀏覽器 `python3 tests/run_all.py --build --update-expected`：83 suite 全部執行，2731 個有計數項為 2721 pass、9 fail、1 個具名允許 Windows GDI skip，實際 returncode 1、784.51 秒。9 fail＝reader 5 紅＋原 Node workspace races 4 個 5 秒 test timeout（不是 suite 逾時）。數量表只增加 native 164→176、scene 147→153、reference 40→48；沒有刪除斷言或豁免失敗。其後以未修改原設定重跑整個 `node:tests-js`，651/651、0 skip、exit 0；另原 races 檔 fresh native 控制為 61/61、0 skip。補跑均為限定範圍，不能拼成 83 suite 全綠；原 4 個逾時未重現、成因未定，沒有 main 同案例失敗證據或正式豁免。'
assert 'ℹ tests 61' in (scratch/'node-isolated-fresh/run.log').read_text() and 'ℹ pass 61' in (scratch/'node-isolated-fresh/run.log').read_text()
assert 'node:tests-js' in (scratch/'node-repeat/run.log').read_text() and json.loads((scratch/'node-repeat/run.json').read_text())['returncode']==0
out=root/'tests/evidence/geo198/review-b1-m1';out.mkdir(parents=True,exist_ok=True)
readme=(scratch/'evidence-readme.md').read_text().replace('%AGGREGATE%',paragraph+'\n\n`node-isolated/` 首輪是 60 pass／1 skip，因沒有提供 fresh bridge 而未跑 native ABA，不計完整通過；`node-isolated-fresh/` 使用 runner 相同 fresh 環境後 61/61。`node-repeat/` 只保留該次所選 Node 的 suite log，未把 cache 中未重跑的其他 suite log 冒充新結果。')
readme=readme.replace('内容','內容');(out/'README.md').write_text(readme)
body=(scratch/'pr-body.md').read_text().replace('%AGGREGATE%',paragraph).replace('後续','後續').replace('遗漏','遺漏');(scratch/'pr-body.md').write_text(body)
path=root/'tests/geo198/README.md';body=path.read_text().replace('後续','後續')
body+='\n最新產品修正 `f32f574`；M61 定義 `865f543`；完整 native 執行 `82af4ab`（before 乾淨）。\n最新 native 176/176、reference 48/48、scene 153/153，原 143 規格及接受／拒絕變動 0。\n最新帳本 55 筆：47 killed、1 crashed、4 equivalent、3 retired；52 個重編重跑＋3 筆驗退休依據，stale=0。\n真 Chromium 33/33，原完整 space 228/228、七群 completed、無 filter、直接 returncode 0。\n'+paragraph+'\n新增記憶體追溯診斷為 R7／R12／R14／R15、相對親代 +753 字元；正典未寫入，owner #192 及正式七 job 仍待。\n本輪 service log 有 1 次 BrokenPipeError，未定位／未豁免；不以 console 空宣稱整體健康。\n'
path.write_text(body);print(json.dumps(analysis,ensure_ascii=False))
