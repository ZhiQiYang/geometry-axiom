# PR #202 收尾審查：dc4e929 既有 raw 交付

回應 [dot 6111110031](https://github.com/ZhiQiYang/geometry-axiom/pull/202#issuecomment-6111110031)。
本目錄只交付上一輪已完成的原始收據，沒有為補交重新執行測試。
來源是本工人啟動的隔離測試及 repository 的合成夾具；畫面是測試場景，
不含使用者私人圖紙、使用者 feedback 原始資料、憑證或瀏覽器個人設定檔。

## 受測身分與交付身分

- **受測 head**：`dc4e929580228dcfbfe1e46a03192d5e6e1d71d3`。
- **受測 tree**：`a52cda4a1d146454a01cfaa64107afeda6cbecd7`。
- 本交付提交在該 head 上只加入本目錄的證據與說明；不是新 head 的驗收。
- `raw/native/receipt/checkout-before.json` 與 `checkout-after.json` 的
  head/tree/source 相同，tracked diff/status 均空；記錄的 19 份來源 Git blob
  SHA-256 已對照受測提交核符。兩份 JSON 不逐 byte 相同：before 的 binaries
  是空映射，after 有執行後的 binary／sidecar 快照，不把它當前後 binary 全等證據。

## 原封包與可讀展開

原封包 [geometry-198-review-dc4e929.tar.gz](geometry-198-review-dc4e929.tar.gz)
是上一輪 `/workspace/geometry-198-review-dc4e929.tar.gz` 的逐 byte 複製：

```text
bytes: 5069241
SHA-256: 741aa19e0148ebdd6bb496d3905d0189d6218b8ef32c138a14e2c8c9451c71fa
```

[`raw/`](raw/) 是原封包全部 273 個檔案的逐 byte 展開，包含原始失敗及開發 harness
失敗，未改寫、刪去或清洗日誌。[sha256.json](raw/sha256.json) 列 272 個 payload
檔案（不自列 manifest），交付時全部核符。可在本目錄執行：

```sh
sha256sum geometry-198-review-dc4e929.tar.gz
python3 -c 'import hashlib,json,pathlib; r=pathlib.Path("raw"); m=json.loads((r/"sha256.json").read_text()); assert all(hashlib.sha256((r/p).read_bytes()).hexdigest()==h for p,h in m.items()); print(len(m), "payload hashes match")'
```

## 審查入口與原始結果

| 證據 | 入口 | 結果／界線 |
|---|---|---|
| 整體摘要 | [summary.json](raw/summary.json) | 各 runner 分開記錄，不拼接成全綠 |
| native 命令、時間、exit | [job.json](raw/native/receipt/job.json) | 原 `run_all.py --build`，83 suites，2699 pass／5 reader fail／1 allowed skip，exit 1；691.549 秒，未逾原 CI 900 秒 |
| native 原始斷言與數量 | [run-all.log](raw/native/receipt/run-all.log)、[逐套件日誌](raw/native/suite-logs/) | run-all log SHA-256 `c2365d1a577e566f0f87937c315d4008607749961b5e980e6bb568291ed95779`；沒有 update-expected |
| 前後 head/tree/source | [before](raw/native/receipt/checkout-before.json)、[after](raw/native/receipt/checkout-after.json) | 同一乾淨 head/tree；binary 身分另見 [binary-state.json](raw/native/receipt/binary-state.json) |
| A/B Chromium 局部驗收 | [result.json](raw/browser/targeted/result.json)、[driver log](raw/browser/targeted-driver.log)、[截圖](raw/browser/targeted/) | 29/29，1400×900／390×900；不是完整 space 或 WSL 裁判 |
| 完整 space 原始失敗 | [result.json](raw/browser/space/result.json)、[space.log](raw/browser/space.log)、[最終畫面](raw/browser/space/final-state.png) | 13 pass／2 fail，exit 1；projection definition closes 逾時、group completeness 未完成，其他群組未跑完 |
| reader 記憶體診斷 | [result.json](raw/reader-diagnostic/result.json)、[trace diff](raw/reader-diagnostic/parent-vs-head-trace.diff) | 親代到 head 增加 R7／R15 追溯 238 字元；未寫 canonical，不等三道全綠 |
| 正式 wrapper 實際阻擋 | [formal-wrapper-attempt.log](raw/formal-wrapper-attempt.log)、[documents job](raw/formal-documents/receipt/job.json) | unshare 拒絕；Chrome 路徑前置檢查失敗、commands=[]；均不算 job 通過 |
| freshness／執行器 | [mutation-check.log](raw/mutation-check.log)、[executors](raw/executors/) | 原命令與上一輪診斷／Playwright harness 保留 |

`raw/browser/targeted-*` 的早期失敗是 harness 開發過程，不能混算最終 29/29。
原 `ci_job.py` 的 environment_differences 是通用文字，不證明 Google Chrome 已就緒；
實際安裝的是 Chromium 與 Noto CJK，documents 前置檢查仍失敗。

既有限制保持：退化項讓 obstacles 整份報錯；合法 c2 只保證直接 apply-proj；
B 樑 cut-strip 後仍留既有 strip/bbox 鬼影。沒有所有障礙精確裁切或一般多區投影聲明。

正典接續來源是 [#192 原本機 owner 回覆](https://github.com/ZhiQiYang/geometry-axiom/pull/192#issuecomment-6110968023)
及 [Claude 同步裁決](https://github.com/ZhiQiYang/geometry-axiom/pull/192#issuecomment-6110320003)。
須由既有 owner 在最終整合 head 納入本項 R7／R15 追溯並驗三道；完整 space 與
正式／代理 WSL 七 job 仍待。此目錄可供獨立核查，不代表審查者已核准；PR 保持 draft。
