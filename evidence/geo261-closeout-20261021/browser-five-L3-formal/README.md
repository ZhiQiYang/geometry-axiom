# L3 五項 browser 正式證據

來源分支 `codex/geo261-closeout-20261021`，完整 SHA `6589248c9a94bdf0460d8f84dd1610e51048188b`。五項按原 scope 依序各跑一次，150／47／350／242／79 通過，失敗皆 0；各 Node 真退出碼 0。沒有在封裝時重測。

| job | 原測試 CLI／scope | 通過 | 整 job 上限秒 | 原始輸出與真碼 |
|---|---|---:|---:|---|
| assembly | `GEOMETRY_ASSEMBLY_ONLY=1 node geometry-web/cdp_test.js` | 150 | 900 | [完整 raw](run/assembly/run.log) · [命令/env](run/assembly/command.json) · [Node/期限收據](run/assembly/receipt.json) · [接受器](run/assembly/acceptance.json) |
| documents | `node geometry-web/documents_browser_test.js` | 47 | 600 | [完整 raw](run/documents/run.log) · [命令/env](run/documents/command.json) · [Node/期限收據](run/documents/receipt.json) · [具名完整性](run/documents/acceptance.json) |
| grid | `GEOMETRY_GRID_SYSTEM_ONLY=1 node geometry-web/cdp_test.js` | 350 | 900 | [完整 raw](run/grid/run.log) · [命令/env](run/grid/command.json) · [Node/期限收據](run/grid/receipt.json) · [接受器](run/grid/acceptance.json) |
| space | `node geometry-web/space_model_test.js` | 242 | 900 | [完整 raw](run/space/run.log) · [命令/env](run/space/command.json) · [Node/期限收據](run/space/receipt.json) · [固定 census](run/space/acceptance.json) |
| timber | `GEOMETRY_TIMBER_ONLY=1 node geometry-web/space_model_test.js` | 79 | 1200 | [完整 raw](run/timber/run.log) · [命令/env](run/timber/command.json) · [Node/期限收據](run/timber/receipt.json) · [固定 census](run/timber/acceptance.json) |

每 job 期限由 npm build 前起算，包含啟動、測試與原 owned cleanup，沒有增加 15／10／15／15／20 分鐘之外的建置預算。各環境依原 wrapper 分離 TMPDIR、feedback、profile、HTTP/CDP 埠；父命令 `env -u CC -u PYTHONOPTIMIZE python3 -B`，本機 Chromium/Noto CJK。服務私有 runtime 的三 binary 本輪 reused，沒有將 native 全域 binary 搬給 browser。五項來源前後 L3 clean，154 個 Git 來源逐 bytes核對，runtime前後 fresh相同，清理沒有 live/zombie survivor且各兩埠拒絕。

assembly/grid 原 partial harness 沒有自行比對完整 golden；外層按原指定 P77/P82、P70/P71/P78/P87/P88 段核對凍結 golden。documents 無 golden/completed 欄位，外層比對凍結來源全部 47 個具名 PASS 依序及最後健康守門。space/timber 使用原固定逐群 census，未添加 scope 或修改省略群組。assembly 的 `Injected lost success response` 原控制保留，不宣稱零 transport failure。服務清理 SIGINT／readiness 首次未就緒等原子退出照存，不把每條子命令都說成 0。

wrapper 真 wait 0 見 [launcher收據](launch/launcher-receipt.json) 及 [.exit-code](launch/.exit-code)；launcher 程序真碼 0 見 [永久父碼](launch/browser-five-L3-formal-6589248c-launcher-process.exit-code)。工具 session 85316 最終 chunk b9d980 真 exit0，見 [觀察轉錄](launch/browser-five-L3-formal-6589248c-exec-observation.json)；它是對話工具回傳轉錄，非 transport 自動 log。[實際父命令](launch/browser-five-L3-formal-6589248c-parent-command-code.txt)、[監督stdout/stderr](launch/orchestrator.log)、[launcher快照](launch/launcher-code.txt)、[wrapper快照](launch/wrapper-code.txt) 均逐 bytes保留。

run 保存完整五項 raw、原 210 筆 suite manifests 與 81 張 PNG。事後另捕捉 15 件107195 bytes：7 grid gcanvas、5 同下載目錄 JSON 測試收據、documents 3 原輸入；另核原 wrapper 已存9件非PNG，不重複複製。[產物索引](run/declared-artifact-capture.json) 明列原路徑、bytes、hash、mtime、既存/新增分類，missing0。PDF/Markdown為合成測試輸入，notes JSON為匯出後roundtrip輸入；不稱使用者下載。只保存原bytes，沒有重生成，也沒有把 Chrome profile、cache 或 binary 入包；原 suite manifest 完全不改。事後捕捉不冒充在原job期限內。

[主報告](run/報告.md)、[主驗證](run/final-verification.json)、[事後真碼](run/post-run-tool-observations.json) 與 [獨立審查](peer/peer.json)、[產物獨審](peer/artifact-peer.json)、[peer方法與界線](peer/README.md) 全保留。舊五項接受器沒有獨立保存原碼，本輪唯讀接受器按原條件重新寫出並保存，未宣稱精確移植。探索誤猜 source-before.json 及首接受器把原 lost-response 控制定位錯檔造成的 exit1，均是外層工具問題，完整原碼／streams／真碼／最小修正保留在 peer；不改產品或重跑正式測試，不把這些 exit1 當產品紅。

未驗與不確定：未逐張人工目視 PNG；本機 Chromium 與 CI Google Chrome差異未排除。與另一 heavy槽 Q38/gates 的 CPU/IO競用未排除，這些耗時不用於 P189 性能。斷言混合trusted input、DOM/程式整合與 native API，868個斷言不是868個真人端到端情境。本輪沒有新跑撤回突變，歷史突變證據另包；這份包只宣告五項 browser，不代替 canvas/native/gates/P189 的各自驗收。

`source-index.json` 是原件到包內路徑的精確映射；`SHA256SUMS` 涵蓋除自身外全部檔。可用 `sha256sum -c SHA256SUMS` 檢查包。工具方法均以 `.txt` 保存原bytes、0644；沒有 `.py/.js/.cjs` 可執行副本。
