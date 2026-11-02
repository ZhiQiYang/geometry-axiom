import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
report_path = OUT / 'pr345-independent-native-browser-check.json'
report = json.loads(report_path.read_text())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert report['audit_passed'] is True and report['native_accepted'] is False
browser = ', '.join(f"{row['name']}: {row['passed']}/0" for row in report['browser'])
text = f'''#345 獨立原件審查

固定 source `{report['pr_head']}`；真 GitHub execution merge `{report['execution_commit']}`，tree `{report['execution_tree']}` 與 source HEAD 相同。17 原工具／workflow／expected／timing／golden 檔的 SHA 與 HEAD Git bytes 相符，source 工作目錄乾淨。保存的 snapshot 是 `20261102T034113Z`。

三片 native 77/76/77、共 230 suites 的 source registry、timing plan、expected 與原始 log 一致；194 份 Python unittest、32 份 Node log 均已獨立比對。計數型 suite 共 5340、5339 pass、1 指定 GDI skip、0 assertion failed。唯一失敗是 exit-code-only `mutation:check`：actual process exit 1、failed=1，53 bridge stale；native (2/3) 官方 conclusion=failure，其餘 229 suites 沒有失敗。這輪 native 不能核收為綠燈。

父 `native-rejection-receipt.json` 確實綁定真 merge metadata 與原 `tests/native_shard_receipts.py`，actual exit 1；原 stdout/stderr SHA 相符，stderr 以「分片身分／規劃／真實退出不符」拒絕 shard-2。官方 native-complete-coverage ZIP 逐 byte 核過，只有七份負控制檔、沒有 native-complete.json；本地也沒有成功 aggregate。該官方 complete-coverage job 在此 snapshot 仍 in_progress，未虛稱其終態。

原 coverage 負控制仍為真 0/1/0：移除 c:integrity 產生指定 unittest 的 AssertionError，errors/skips=0；這只證明 coverage guard，有別於本輪失敗的 native aggregate。

已完成四組 browser 原始 assertion／結構收據／fresh runtime／真 merge 一致：{browser}。timber、canvas 在此 snapshot 仍 in_progress，沒有採為通過。共 {len(report['official_zips'])} 個已保存官方 ZIP 的 digest、head/run 與 extracted members 逐 byte 相符。

3056 個核對條件成立，未發現分類或 source/tool 綁定的新阻擋。保留 #345 正式紅燈與兩個 pending browser；沒有 API 請求、產品 suite、binary execution 或 source／PR 修改。

報告 SHA-256：`{sha(report_path)}`
核對腳本 SHA-256：`{sha(OUT / 'pr345-check-native-browser.py')}`
'''
(OUT / 'pr345-independent-review.md').write_text(text)
print(json.dumps({'report_sha256':sha(report_path),'script_sha256':sha(OUT / 'pr345-check-native-browser.py'),
                  'native_accepted':False,'completed_browser_groups':len(report['browser']),'official_zip_count':len(report['official_zips'])}))
