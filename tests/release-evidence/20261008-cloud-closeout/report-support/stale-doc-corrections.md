# 既有描述的修訂與交接狀態

以下行號釘在 clean `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`。root已隨本次提交修訂RELEASE-CANDIDATE，並發布且GET核對#137／#153／#155正文。#175-owned INTEGRATION-GATES的兩處仍未修改，等待該owner接回；不把交接清單稱已修正。歷史收據的 SHA、數字及原結果保留；更正的是「目前／本輪」指涉與過廣的範圍。

| 路徑／行 | 現有文字及問題 | 建議的有界更正／責任 |
|---|---|---|
| `geometry-web/docs/RELEASE-CANDIDATE.md:8–10` | 「目前整合分支為 codex/final-release-closeout-20261008」仍指 #169。 | root 在頂端加現況 banner，連本次 cloud-closeout README，明列舊章節是 #169 歷史；最終完整 SHA／PR 另填。不要把舊表所有數字改綁 5174。 |
| 同檔 `:21` | 「#141 的九個元件檔已逐 blob 包含在 #146」。 | 已區分7份實作／測試與2份文件；全部9檔在#146均同blob，後續候選只改2份文件。避免把文件當可執行元件，不誤稱未接回。 |
| 同檔 `:68–105` | 「本輪實測」及 2177、82 suites 等章節容易被當作新雲端候選結果。 | 保留原頭／原收據，章節明標 #169 歷史。新 458 native/CDP 與 5174 gates 只引用本次權威 matrix，不將數字相加。 |
| 同檔 `:131–136` | 「最後遠端核對的24個來源PR」是舊輪。 | 明標歷史快照；新32 PR／27 issues及時間另連本次清單，不否定原24筆觀測。 |
| 同檔 `:142` | Resume 安全限制仍實際存在。 | 保留限制，加本次獨審連結及協調 writer／durable barrier 下一步。不能刪 guard 或將 Resume 改成只剩 CI／裝置條件。 |
| `tests/INTEGRATION-GATES.md:402–407` | 「本次中斷 ticket 修補的 browser 未執行；AF_UNIX EPERM限制未解除」是當時環境。 | **#175 owner** 更新為歷史未執行；另連 clean5174 scenario-lifecycle/workflow 真browser receipts，保留各自範圍及未驗 BFCache／跨profile／手機等。不宣稱完整 Resume。root不競寫該檔。 |
| 同檔 `:474` | 「PR141 的九份 owner 檔案逐 blob 重用」。 | **#175 owner** 區分7份實作／測試與2份文件；與RELEASE-CANDIDATE一致。 |
| PR #137 正文 | actual head `38975775cf42e9dc454aab2e25fc186d9fbd759d`，舊freeze `9a687976`描述未清楚標歷史。 | 已於19:01:31Z以REST結構化body更新並GET核對；現況、依賴與#176 link前置，原freeze及raw作歷史保留。見pr137-summary-correction.json。不是送review comment；#168/#169留言仍暫停。 |

報告已用 `gates/matrix.md`／`matrix.json` 作當前 gate 狀態權威。`report-support/receipt-index.json` 是本次整理時的12筆固定快照（歷史full CDP＋11筆當前gate），不是隨測試更新的另一份最終matrix。

## 單一重現命令文件已補的實際路徑

以下缺口已在[commands.md](../commands.md)補齊；原執行腳本和raw不改寫。這是靜態recipe核對，不冒稱全新checkout已重跑：

- 公開 `async-new-head/browser_probe.py`、`bhit_probe.py`、`async-edge-ce74/browser_probe.py`、`async-transition-ce74/edge_transition_probe.py` 硬編 `REPO=/workspace/geometry-axiom`。`--url`可改不代表repo根可改。說明目前要求的checkout位置，或由owner做明確root參數化、另留新腳本hash；不能把原檔hash誤綁改後腳本。
- `gates/edge-transition-ce74/artifacts/executed-*` 是證據封存名，runner實際依賴同目錄 `edge_transition_probe.py`、probe依賴 `edge_transition_instrumentation.js`。可直接引用已保留原名的 `async-transition-ce74/` 子包；不要叫使用者從executed前綴檔直接跑而缺依賴。
- `contracts/browser/browser-run-02/script.py` 可傳 `--root`／`--url`／`--bridge`／`--out`，但預設 `grid-final/grid-rule-timber.scene`、`assembly-final/reopened-owned.scene` 相對該script目錄不存在。recipe必須明傳包內實際fixture路徑，並先核hash；不依賴雲端私有原位置。
- repo正規gates使用checkout內原測試檔；`gates/*/sources/launch-adapters/` 已有sandbox啟動adapter，不需復原私有 `/workspace/closure-evidence/python-launch` 路徑才可啟動。recipe須示明環境變數、獨立服務、16 MiB process stack、fresh native來源收據、實際gate命令與新空白輸出目錄。
- 新的compound／Q38 restart／CSS corrected probes在實跑後再封存精確腳本與依賴原名，將receipt中的歷史暫存路徑與可重現命令分開；歷史命令不改寫。

以上為靜態封裝檢查，不宣稱已在全新checkout執行portable recipe。

#153／#155曾待browser的正文也已更正：[REST／GET收據](pr153-pr155-summary-corrections.json)。原PR head與原正文保留為歷史，新增只綁5174的整合觀察；#54完整成本目標仍未證成，詳見[成本對照](final-contract-mapping/room54/README.md)。
