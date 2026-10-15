import json,pathlib,re,subprocess
repo=pathlib.Path('/tmp/geometry-p095-201');root=pathlib.Path('/tmp/geometry-wake25-201');out=repo/'tests/evidence/201-p104-wsl-budgets-20261014'
r=json.loads((root/'native/native-receipt.json').read_text());s=(root/'native/native.stdout').read_text();match=re.search(r'^合計\(已執行、有計數者\)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)',s,re.M);assert match
total,passed,failed,skipped=map(int,match.groups()[:4]);suites=re.findall(r'^\[(\d+)/(\d+)\]',s,re.M);assert suites[-1]==('87','87')
assert r['exit']==0 and failed==0 and skipped==1 and r['sources_unchanged'] and not r['git_status']
assert re.search(r'^node:tests-js\s+703\s+703\s+0\s+0\s+',s,re.M)
assert re.search(r'^py:test_axiom_reader\s+41\s+41\s+0\s+0\s+',s,re.M)
summary={'tested_head':r['head'],'base_main':r['base_main'],'suites':87,'total':total,'pass':passed,'fail':failed,'skip':skipped,'actual_exit':r['exit'],'seconds':r['seconds'],'sources_unchanged':r['sources_unchanged'],'git_status':r['git_status'],'formal_wsl':False}
(root/'native-summary.json').write_text(json.dumps(summary,indent=2)+'\n');(out/'native-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
tap=root/'native/run_all-logs/node_tests-js.log';raw=tap.read_text();assert tap.stat().st_mtime>=__import__('datetime').datetime.fromisoformat(r['started_at']).timestamp()
names=list(dict.fromkeys(x['name'] for x in json.loads((root/'train9-case-durations.json').read_text())))
six=[]
for name in names:
 m=re.search(r'^✔ '+re.escape(name)+r' \(([\d.]+)ms\)',raw,re.M);assert m,name
 six.append({'name':name,'duration_ms':float(m.group(1)),'result':'pass','scope':'this cloud full native; not formal WSL'})
assert len(six)==6
(out/'native-six-cases.json').write_text(json.dumps(six,indent=2)+'\n')
current=(out/'README.md').read_text()
assert '## 整合與撤修對照' not in current
current+=(root/'README-addendum.md').read_text()
current+=f"\n## 完整雲端 native\n\n受測乾淨 head `{r['head']}`、base `{r['base_main']}`，命令 `ulimit -s 16384; python3 -u tests/run_all.py --build`。87/87 suites，{passed} pass／{failed} fail／{skipped} 具名 Windows GDI skip，實際 OS exit {r['exit']}，{r['seconds']:.3f} 秒。Node703/703、reader41/41（詳原表）；所有 tracked 檔案執行前後 hash 相同，結束 git status 為空。實際 child status 先寫 `native-actual-exit.json`，再做任何後處理，沒有把 helper 狀態當 child 狀態。\n\n這是雲端完整非瀏覽器登錄測試，不是 WSL 收據、正式七項或完整 CDP。保留第9班首紅／Rule2；P-104 四案新期限與 main 整合已交付，新固定來源仍須本機正式列車驗收。preflight／legacy兩案舊期限未改，不能因本輪雲端綠燈就宣稱其 WSL 已驗收。20份新WSL TAP仍由本機原件持有人核對，雲端未聲稱獨立取得。\n"
current+='\n本輪完整 Node 日誌含原 Rule2 六個具名案例，全部通過（數值見 `native-six-cases.json`）；四案子集沒有被移算成完整703。sum-of-suite 表列792.3秒，實際 child wall822.379秒含建置與runner前後處理，不混用兩者。\n'
(out/'README.md').write_text(current)
print(json.dumps(summary))
