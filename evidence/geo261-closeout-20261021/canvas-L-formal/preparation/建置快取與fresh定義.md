# 正式 L canvas 的建置快取與 fresh 定義

本說明只整理靜態查核與既有 A 收據；沒有建立工作樹、安裝套件、建置、啟動服務或瀏覽器，也沒有修改產品、CI 或既有調度器。正式 L 尚未放行。

## 已採用的執行方式

父代理決定正式 L 沿用 `/workspace/geometry-axiom`，執行原 `npm run build`、新服務與完整 `node geometry-web/cdp_test.js`；35 分鐘總期限仍從建置前開始，canvas 獨占重負載。沒有新增每輪必須冷建置的驗收條件。

正式收據須逐支記錄 `built` 或 `reused`，保留原 `built_at`、來源閉包雜湊、編譯命令、實際 binary 雜湊及 sidecar。若命中有效快取，應寫「本輪執行建置及來源／binary 新鮮度核對，沿用符合目前來源的 native 程式」，不能稱「本輪重新編譯」。另行執行的正式 native job 是否重編，應依它自己的原始紀錄判定，不由本 canvas 推定。

## 三種身分必須分開

1. **Git 來源**：調度器在開始及結束各核對完整指定 L SHA、乾淨工作樹及七個關鍵檔案 hash。L 的 ledger metadata 即使不改 runtime bytes，仍由 Git SHA 收據表達。
2. **native 新鮮度**：`tests/binaries.py:287` 將目前 C/include 來源閉包及編譯命令納入 fingerprint；`:335` 起另核對 binary SHA-256、大小與 mtime，並對照 sidecar。`:588` 起對 fresh 回傳 `reused`，只對缺失／過期程式編譯。這不是以 Git SHA 或本輪起始時間決定重編；fingerprint 也不等於完整編譯器安裝的 hash。
3. **服務新鮮度**：`geometry-web/runtime_version.py:118` 起擷取本輪來源及靜態資產；`fresh()` 比對目前 bytes，`probe()` 再核 version、fresh 與 root。調度器另核服務 PID 必須是本輪自建程序。`fresh:true` 表示來源仍相符，不表示 native 剛剛重新編譯。

`package.json` 的 build 只呼叫 `python3 geometry-web/start_local.py --build-only`。`start_local.py:27` 預設 native 目錄為 `/tmp/geometry-runtime/` 加上已解析 repository 根路徑的 SHA-256 前 20 位；`:74` 起載入該 root 的 `tests/binaries.py`、設定其 `OUT_DIR`、持鎖建置，再重新 `require_fresh`。同主 root 的 A 與 L 可以使用同目錄，但仍須通過目前來源與 binary 核對。服務啟動時會再次做同樣核對。

目前 main root 的目錄是 `/tmp/geometry-runtime/b9bc23103ebb114398f3`。既有 A 第二輪 `build.log` 明列三支全部 `reused`，不能回溯改稱 A 當輪新編：

| 程式 | 原 built_at（UTC） | 原 build_seconds | 編譯命令 |
|---|---|---:|---|
| core | 2026-10-20 19:31:15 | 15.3 | `cc -std=c11 -O2 current_geometry.c -lm -> core` |
| bridge | 2026-10-20 19:31:34 | 18.6 | `cc -std=c11 -O2 geometry-web/web_bridge.c -lm -> bridge` |
| model-base | 2026-10-20 19:31:50 | 16.2 | `cc -std=c11 -O2 geometry-core/model_base.c -lm -> model-base` |

原始憑據在 `../canvas-a-preflight-r2/build.log`、`native-identity.json` 及 `native-sidecars/`（以上路徑相對外部證據根；完整位置為 `/workspace/geo261-evidence/canvas-a-preflight-r2/`）。上述 50.1 秒是歷史建置耗時，不是正式 L 耗時預測。A 完整 job 2058.016 秒，距上限餘 41.984 秒；L 獨占可避免同輪 ledger 爭用，但尚無正式耗時結果。

## 全新 detached 工作樹的可行性與未採用原因

靜態上可行，無須改已審調度器：launcher 傳遞 `--root`；調度器的 cwd、Git snapshot、build、server、probe、Node 入口及 golden 讀取均跟隨解析後 root。`start_local`、`serve.py`、Python host bootstrap 及 native 來源都從自己的 `__file__` 或該 root 定位；服務將新目錄的 native 絕對路徑明確傳給橋接與建模程序。調度器清除繼承的 `PYTHONPATH`、`PYTHONHOME`、`NODE_PATH`、`NODE_OPTIONS` 及 `GEOMETRY_*`。

全新實際 root 路徑會產生不同 root-hash 快取目錄；只有在啟動前確認該目錄及程式確實不存在、未預先暖編，且本輪 build 明列 `built`，才可稱本輪新編。以符號連結指向 main 不會達到此效果，因 root 先經 `resolve()`。若未來採用，編譯必須留在原 35 分鐘內，不能移到計時前。

主 root 目前沒有根層或 `geometry-web/` 的 `node_modules`；根 package 無 dependency 清單，build 不需安裝。靜態公開 vendor 共 205 個追蹤檔案，沒有追蹤符號連結或一般未追蹤檔案。新的工作樹不應複製主樹的快取、依賴或未追蹤產物來冒充全新環境。這些屬可行性查核，未實際建立 detached L 或啟動它。

新的 root 可以隔離 native 快取及 build lock，並讓首次新編來源更清楚；代價是額外簽出與本輪三支編譯成本，且不能只憑目錄新就替代原始建置紀錄。最新審查要求同一最終來源實跑；父代理因此選擇既有主 root，保留精確來源與 built/reused 證據，不增加 cold-build 條件。

即使換 root，`assembly_workflow_test.js:57`、`:62` 的兩張截圖仍寫入 `/tmp/geometry-tests/assembly-desktop.png`、`assembly-mobile.png`。它們須像 A 一樣記錄本輪前後 mtime/hash，再唯讀封存；不可把新 root 說成所有暫存路徑皆隔離。其餘原測試宣告產物也應依本輪 raw 路徑封存。正式 canvas 獨占排程維持不變。

## 本次核對與限制

- 靜態讀取、Git 差異／狀態、vendor 清單與環境特定欄位查核完成；最後工具 hash 與 Git 狀態查核 exit 0。沒有產品驗收或突變控制，本次不產生產品通過結論。
- 查核時主分支為 `codex/geo261-closeout-20261021`，HEAD 為尚未接受為正式 L 的 `cd4ac98f44174729fb3a2f1c291c6c258c9a239a`，工作樹乾淨；相對 A 僅 `tests/mutants_results.json` 不同。不可將此 SHA 當已放行的正式 L。
- 既有 wrapper hash 未變：`327e926ae0e88fff4b04e68afdee9fb12e9dd2dff0a839fb340603a9fc20121a`。
- 既有 launcher hash 未變：`4f7935f1c516d118c06272a5ed96c4c5909cdbe124a4e746870b0001ce490181`。
- 查核時 `CC` 未設定，registry 預設使用 `cc`；正式啟動仍需保存實際命令，不可改成 `gcc` 再把兩者的 ledger 身分視為相同。
- 未實際驗證 detached 工作樹或正式 L 的可執行結果；最不確定的是正式完整 canvas 在原 35 分鐘內的實際餘裕。正式驗收仍等待正確完整 L SHA 與父代理放行。
