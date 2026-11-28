# X2 歷史專案語料與寫入版本守門

基底：`4c4028f8f80f09963f14a46062cbfcf8db76637b`。工作包：issue #487 X2；設計與交付：issue #386。

`project-save-history.json` 封存 21 份正向 `.gcanvas` 原件，以及一份歷史上已提交、刻意使用 `/999` 的拒絕夾具。每份都帶完整歷史 commit、原路徑、Git blob、原始 bytes 與 SHA-256。`gzipBase64` 只壓縮整份原件；解壓後未改任何位元組。正向檔涵蓋 `/1`、`/3`–`/20`，另含 `flat-ceiling/1` 與 `/2` 的實際保存配方。`/2`、在途 R13 的 `/21`、`/22` 真實歷史原件仍未確認，沒有用修改 header 或當前 writer 產物冒充。

## 裁判範圍

`node --test --test-reporter=spec tests/test_project_save_compat.js` 共 30 項。

- 正向語料走正式 `unpack → 不修改 → pack`。獨立 expected 來自凍結原件，不呼叫產品 writer 建造 expected。每個 ZIP 成員的路徑與完整 bytes 都相同，包括 `manifest.json` 的鍵序、所有欄位與字串、`world.scene`、原始 PDF／圖片。這 21 件不需要 manifest 欄位差異白名單。
- 唯一不要求相同的是 ZIP 容器編碼：壓縮方法、時間戳、成員順序及不影響成員內容的 ZIP metadata。成員增加、刪除、改名或改內容一律紅。
- 真歷史 `/999` 原件從 reader 及 writer 兩端均須拒絕。writer 測例直接以 `fflate.unzipSync` 取原件資料，避開 `P.unpack` 的拒絕，確實測到寫入入口；這與產品共用 ZIP vendor，獨立的是 expected 的歷史原件來源。其他未知或不合法顯式版本也拒絕，輸入與來源不變且未呼叫 ZIP writer。
- 缺少 `format` 的新建 API 仍可用；顯式 `undefined` 不等於缺少欄位。getter 不得被呼叫。新建 API 的 JSON key 插入位置可以不同，該測例明確比結構；這不是歷史檔逐位元裁判的例外。
- 依 I32／I41／I65，未知能力與封閉附件 schema／欄位拒絕；依 FT1，已知 schema 內未知 generator 原樣保留且不能生成。兩種情形分開驗證。
- metadata `set → undo → redo` 使用既有 `reference_workspace_vm.cjs` 的公開宿主入口，比較 before／direct／undo／redo 的 ZIP 成員。DOM、PDF、picker 是假物件，不能當 Chromium、原生 World 歷史或 L4 證據。

本片沒有修改格式配號、已知版本的選版邏輯或 I68 合法 single-draft 正規化。它只在正規化之前檢查明示輸入版本；不新增 future schema 唯讀開檔行為。

## 驗原件與取出檔案

本地已具備記錄的歷史 Git commit 時，可逐份重驗：

```bash
python3 -B tests/diagnostics/project_save_history.py --verify-history
```

工具用 `git show <完整歷史 SHA>:<原路徑>` 與解出的原件逐位元比較，並關閉隱式 lazy fetch。缺少 commit 時明確失敗，不把目前 writer 生成的檔案當替代。普通測試只使用封存原件，離線及 sparse checkout 都能執行，不依賴歷史物件或網路。

要用正式 App 冷開，可解出全部原件；目錄必須尚未存在：

```bash
python3 -B tests/diagnostics/project_save_history.py --extract /tmp/x2-history-originals
```

套用端的 Chromium 後續驗收應由「檔案 → 開啟專案…」逐件載入，保持未操作，經「另存新檔…」再用 Python `zipfile` 等讀取器比較全部成員 bytes；另以全新服務程序與瀏覽器 profile 冷開，核原生場景、來源頁面與模型重建。未知格式須在替換當前專案前明確拒絕，已知 schema 的未知 generator 則只允許檢視。這些正式 UI／OS 選檔檢查尚未在本片完成，不宣稱 L4。

## 先紅後綠及具名撤回

只套 T：`X2_FUTURE_ORIGINAL_WRITE_REFUSED` 紅在 `X2_FUTURE_WRITE_REFUSED`；`X2_UNKNOWN_FORMAT_WRITE_REFUSED` 紅在 `X2_UNKNOWN_FORMAT:geometry-canvas/999`，均為 Missing expected rejection。其餘 28 項綠。套 P 後 30 項綠。

套 P 後執行以下診斷；輸出目錄必須尚未存在：

```bash
python3 -B tests/diagnostics/project_save_compat_withdrawals.py --out /tmp/x2-withdrawals
```

六個撤回：移除版本守門、先呼叫 format getter、刪除明示 undefined、改寫 manifest 值、擅自換未知 generator 版號、丟來源成員。每個都在獨立 Node module loader 中跑原始／突變／恢復，要求 `0/1/0`、指定的唯一測例、指定 assertion 與 `ERR_ASSERTION`；不是任意非零 exit 就通過。每次 child 上限 45 秒，保留每段完整 log、命令與退出碼，核產品／測試／語料 SHA-256 及執行後不變。診斷不改工作樹，不是正式 CI 成本收據。

## 原有守門與採入

新 suite 由原工具建立：

```bash
python3 -B tests/native_registry.py --init-suite node:project_save_compat --kind node-test --file tests/test_project_save_compat.js
```

交付中的 `tests/suites.d/node__project_save_compat.json` 保持工具產生的 `pending-ci-census`。不能手填 count 或成本；正式 registry／六片會在未量測時拒絕。套用端依 `tests/FRAGMENTED-REGISTRIES.md` 派發 **Native suite measurement**，使用 `node:project_save_compat`，再由可下載官方 artifact 的既定執行者用 `--import-suite` 匯入真正 census／cost、原樣採入 stage，跑 registry contract、正式六片與 complete。本機 30 項綠不替代這些 gate。

沒有改動 `.github/`、公理層、既有測試、golden、時限、byte pin、架構收據或正典閱讀器；本片不需要受限路徑的第二片補丁。
