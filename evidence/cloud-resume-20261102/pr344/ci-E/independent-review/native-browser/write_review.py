import hashlib
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
SOURCE=Path('/tmp/geometry-pr344-20261102')
path=OUT/'native-browser-review.json'
report=json.loads(path.read_text())
assert report['review_passed'] and report['browser_accepted'] and not report['native_accepted'] and not report['overall_ci_accepted']
versions={row['runtime']['version']for row in report['browser']}
roots={row['runtime']['root']for row in report['browser']}
assert len(versions)==1 and roots=={'/home/runner/work/geometry-axiom/geometry-axiom'}
assert all(row['runtime']['schema']=='geometry-runtime/1' and row['runtime']['fresh'] is True for row in report['browser'])
runtime_source=(SOURCE/'geometry-web/runtime_version.py').read_bytes()
assert b"status.get('version') != source_version(root)"in runtime_source
assert b"Path(status.get('root', '')).resolve() != root.resolve()"in runtime_source
runtime=dict(passed=True,groups=6,shared_runtime_version=next(iter(versions)),runtime_roots=sorted(roots),
             original_runtime_probe_source_sha256=hashlib.sha256(runtime_source).hexdigest(),
             provenance='Each original current-head job ran the source-version/root/freshness probe before its actual browser command. Six raw runtime markers are fresh and agree on the exact runtime version and original runner root.',
             limitation='No local service or runtime probe executed; only original CI raw markers and current probe source bytes read.')
(OUT/'runtime-marker-review.json').write_text(json.dumps(runtime,ensure_ascii=False,indent=2)+'\n')
browser=', '.join(row['name']+': '+str(row['passed'])+'/0'for row in report['browser'])
canvas=next(row for row in report['browser']if row['name']=='browser (canvas)')
server_lines=canvas['server_log_diagnostics']['lines']
text=f'''#344 terminal native/browser 獨立核收

固定 source `{report['pr_head']}`，真 GitHub execution merge `{report['execution_commit']}`，tree `{report['execution_tree']}` 與 source 相同，parents 為 main `5775a9e9e46bca801a9a70aaeafcdab9f597bc4d` 與本 source。核對時 source clean。終態 Integration `41388718270` 為 failure，僅 native (2/3) 與 native complete coverage 失敗；Mutation `41388718083` 官方 API 為 success，其 artifact 由父核收。

本 HEAD 的 source AST registry、expected 與 timing 重新推導為 **231 suites、77/77/77**，不是沿用舊分支數量。原始 194 Python unittest 與 33 Node log 已逐項對收據；計數型套件 **5349 total / 5348 pass / 0 failed / 1 指定 GDI skip**。分片 union 恰好一次、沒有重疊或遺漏，expected/timing SHA 相符。

唯一 native bad row 是 exit-code-only mutation:check，actual exit 1 / failed 1；完整 raw inventory 的 **53 STALE IDs 恰為當前全部 53 bridge IDs**，每筆均顯示 source/oracle restoration，原因是 oracle 變更（含 equivalence oracle），不是產品 assertion fail。先前 status-only log 只見八個範例，本次由官方完整 raw 確認總數。原 complete coverage log 以 `ValueError: 分片身分／規劃／真實退出不符：.../shard-2.json` 拒絕，actual exit 1；官方 artifact 沒有 native-complete.json。

官方 coverage proof 原件為 **0/1/0**：中段拿掉 c:integrity，指定 unittest 產生真 AssertionError，tests=1、errors/skips=0；只讀原件，沒有重跑負控制。這不會把失敗的 native aggregate 改為綠。

六組 browser 原 raw 通過：{browser}。Canvas 是真 full、filters/modifiers 皆空、85 段 2267/0/0，raw 每段精確符合當前 golden，沒有採用 FLOW partial；唯一 browser 例外是明確注入的 fb-auto-probe。六個 fresh runtime marker 的 version/root 一致，對應當前原 source probe 的 freshness/version/root 檢查。Canvas appended server log 診斷另保留 {len(server_lines)} 行，沒有當成額外 browser assertion 或猜定 socket 關閉原因。

12 個 integration ZIP 的官方 API digest、所有 ZIP member 與 extracted 原件逐 byte 相同；10 個整 job log 對原 run ZIP 逐 byte 相同。3038 項核對成立，無新增阻擋，但 **native_accepted=false、overall_ci_accepted=false**。本輪只有 stdlib/Git/source 與已保存原件讀取，沒有 API、產品、Chrome、build、source/PR 修改或本地 test/負控制執行。

主 JSON SHA-256：`{hashlib.sha256(path.read_bytes()).hexdigest()}`。
'''
(OUT/'native-browser-review.md').write_text(text)
print(json.dumps({'report_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'runtime_groups':6,'runtime_version':next(iter(versions))}))
