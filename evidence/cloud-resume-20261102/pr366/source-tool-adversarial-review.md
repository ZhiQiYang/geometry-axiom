# #366 source 工具對抗審查

來源：`/tmp/geometry-pr366-20261102`，`git rev-parse HEAD` = `502a64ff6214dd6060927b7f14643a533536f20d`；`git status --porcelain=v1` 空白。只讀審查與 Python AST／雜湊檢視，未跑產品測試、未執行下載二進位、未改 source、未啟動 CI、未 push 或留言。

結論：未發現足以單獨否定此新 head 官方 CI 證據的來源工具缺陷。舊 head 帳本不能只改 manifest head 通過：verify 額外逐筆要求 execution.head 等於 checkout HEAD，再由原 strict 驗來源、閉包、裁判、runner 與結果完整性。以下為核收必須保留的信任邊界，不能以單一離線 verify exit 0 取代。

## 需人工／API 補足的兩項邊界

1. **中等，離線 verifier 沒有綁定指定 Actions run、attempt 或負面 probe。** `.github/scripts/mutation_evidence.py:185–191` 保存 `run_id`、`run_attempt`、`platform`、`negative_cache_probe`，但 `verify:203–219` 不讀取它們；因此同一 head 不同 run／attempt 的七片可混用，或刪改 probe 欄仍不會因這些欄位本身遭拒。當前官方 workflow 的 `download-artifact` 未指定另一 run（`.github/workflows/mutation-evidence.yml:104–107`），而 `run_shard:170–174` 確實執行 probe 及還原後 strict，所以不能據此說當前 CI 漏跑。核收應以官方 artifact API 的 run 歸屬及 digest、七片 manifest.run_id/run_attempt、各 execute job 的 strict exit 1 與還原通過 log 一起建立結論。可選後續補強：verify 接受 expected run／attempt 並要求七片一致，驗 probe ID 屬於該片及 strict_exit=1；這仍須官方 log／來源可信度作根。

2. **低，bridge raw hash 與結構化結果分開核對，離線 verifier 不重新解析 raw。** `require_binaries:67–81` 檢查原 stdout／stderr bytes 的 hash；原 `tests/mutation_bridge.py:404–465` 驗 `receipt.result` 的完整方法與判決，沒有從已下載 stdout 再解析一次來比對 result。來源 `_run:334–347` 直接從同次 stdout 解析，故當前未改來源的實際 runner 不會自然產生不一致。這不是針對可自行重寫整份帳本及所有 hash 的偽造者的認證機制；原 runner 自己在 `tests/mutate.py:1181–1185` 也明確說 checksum 只抓意外修改。官方 ZIP 原件與 API digest 是必要外部根。當前核收可抽核或全量比對 raw marker 和 ledger.result；不應把重新計算本地 hash 宣稱成官方 provenance。

## 已確認的守門

- PR mutation 工作流程四處 checkout（workflow:28、50、68、98）皆使用 `github.event.pull_request.head.sha || github.sha`；此 run 的 mutation receipt 應綁 PR head `502a64f`。integration 若使用 PR 合成 merge，須另記實際 checkout SHA，不能套用 mutation 的 head 語義。
- `shards:45–55` 斷言全表 ID 不重複且完整；`verify:198–230` 要求恰好七份 manifest、已知且唯一 shard、指派 ID 精確順序、ledger 精確 ID、全片聯集精確等於現行表。
- JSON manifest／shard ledger 由 `read_json:25–33` 拒絕重複鍵。
- `verify:208–219` 要求 schema、head、原工具及 supervisor SHA；三個檔案 bytes 與 manifest hash 相符；每筆 active execution.head 等於 checkout HEAD。
- tar 使用 Python `extractall(..., filter="data")`（verify:222–223），拒絕絕對越界、目錄越界與特殊裝置檔；未發現會執行 artifact 二進位的 verify 路徑。
- `require_binaries` 要求每筆 active 的實際 baseline、mutant、restored（bridge）二進位與 sidecar；bridge 另核 raw bytes 與 sidecar 原件 hash。core 驗 sidecar 的身份與指紋欄位，並由 tar hash 保留原件。
- 每片 strict 和全表 strict 是兩道檢查（verify:225–239）；全表使用空 cache 不會取消先前各片二進位實檔檢查。
- 架構 supervisor 直接執行原三命令（architecture_evidence.py:29–40），逐條保留 command、exit、raw hash，非零 exit、零 unittest 計數或 skip 會拒絕（:44–56）。完成前再次檢查 tracked diff（:59）；scanner 必須 `ok=true` 且零 diagnostics（:60–62）。來源 input closure 及三支 scanner／test hashes 被記入 receipt（:64–78）。離線核收需自行逐項比對 receipt 與原 raw、head/run/attempt；此程式是產生器，沒有獨立 architecture verify mode。

## 執行證據與限制

所有工具呼叫只讀來源；`python -B` AST／SHA 檢查、`git rev-parse` 與 `git status --porcelain=v1` 皆 exit 0。AST 確認 verify 的直接 manifest subscript keys 為 head、ids、schema、shard、supervisor_sha256、tool_sha256；未讀取 run_id／run_attempt／negative_cache_probe。未以 synthetic artifact 執行完整 verify；尚未核讀官方 ZIP 內容或目前 job log，因此本報告不宣稱當前 120 active 已完成或七片 bad-cache 已實證。

來源 SHA-256（bytes 原件）：

| 路徑 | SHA-256 |
|---|---|
| `.github/scripts/mutation_evidence.py` | `28ec987f9b66f64bea33eff555f807e144d6f2363f202bce55ab85bd51e912fc` |
| `.github/scripts/architecture_evidence.py` | `9899d18b3fb80a750308e2342d8309ca7a2470ec5aab4f977bc3213690b07b5b` |
| `.github/workflows/mutation-evidence.yml` | `c5d39c10de1df05ff1a582f228b4ee5fb088d0637337dc96c552d993a35d1fdb` |
| `tests/MUTATION-EVIDENCE.md` | `995b07d62b232a8d094ec059da096bbe1eecf8506e27c358fbd64f4221304991` |
| `tests/mutate.py` | `bd2d0c768439a93e7f848ff0299a5b164aabe1d80a0f4e9a5bcb7ab83eb4b315` |
| `tests/mutation_bridge.py` | `7febe80ba29a3c0e7821277f47102a57a0c9ab0610a02e8981bb0eb2a79b3c58` |
