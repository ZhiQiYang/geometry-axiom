# #44 F1a cloud 本機驗收

產品程式 head：`e30d4a2`；整合基線 main `693a1c8`（已含 PR56、PR63 format9、PR64）。未改 `app.js`、`reference-workspace.js`、`project-store.js`、原生共用模組或公理。實作／接線契約見 [SOURCE-INSPECTOR-CONTRACT.md](SOURCE-INSPECTOR-CONTRACT.md)。

同版 runtime：`8d8701720d1282e6a1723132ed922787f6e378fe8ccc8086dd1591c81c2f6b23`，`runtime_version.py --probe 18892` 回 `fresh:true`。原生使用 `tests/binaries.py` 登記且指紋相符的 Linux GCC C11/O2 bridge/model-base；16 MiB stack 與既有 Windows build 的 stack 設定一致。Chromium 151／Playwright，隔離 TEMP feedback／browser profile／三個獨立測試 World。

| 驗證 | 命令／結果 |
| --- | --- |
| 完整非瀏覽器 | `ulimit -s 16384; python tests/run_all.py`：44 suites，1412 pass、0 fail、1 具名 Windows GDI 平台跳過，exit 0；expected 不降低原有數量 |
| 真原生 F1a | 上列含 `tests.test_source_inspector` 10/10：card/field/placement/grid/binding/timber 0、AST typed ref、signed index、固定材料／規則版、同值換來源、override、更新／刪除、isolated snapshot replay、pending token／World／revision／undo 保全、transport UTF-8／1 MiB／暫存清理、網格 definition/value 分離 |
| JS 邊界 | 上列含 `tests/test_source_inspector.js` 9/9：48 nodes／6 depth、有環及缺來源、實際 closure 與 I9 候選／RC 歸屬分開、同值不同 fixed-version edge、未知身分／舊資料、late async／context／frame／revision／取消、無效指紋拒絕 |
| 原生缺陷反證 | TEMP 副本只移除 `si_ast` 的 ref edge；C 編譯 exit 0，仍運行真核心；同一 10 項有 1 fail、9 pass，exit 1，精確抓到 `parameter-field:10:f0 → parameter-field:0:f0` 遺漏；無編譯失敗或 skip，正式原生／registry 未替換 |
| 正式 app F1a | `GEOMETRY_TEST_URL=http://127.0.0.1:18892/ GEOMETRY_FEEDBACK_DIR=/tmp/geometry-f1a/feedback-final GEOMETRY_CHROME=/usr/bin/chromium node geometry-web/source_inspector_browser_check.js`：18 pass／0 fail，exit 0 |
| 完整既有 space suite | 同版隔離 18894 執行 `geometry-web/space_model_test.js`：183 pass／0 fail，exit 0；scope 為 full-space-suite，另外的 timber-material／timber-source-guards 專項未計入此數 |
| 完整既有 app CDP | 同版隔離 18893、19443 執行 `geometry-web/cdp_test.js`，無 filter：completed:true、1809 pass／0 fail／0 略過群組、76 段 golden matched，exit 0；raw exception 1 為既有 P38 `fb-auto-probe` 刻意探針，未預期例外 0；P76 390px 全部觸控控制 ≥44px 通過 |

F1a 瀏覽器用實際 C World 建立 face/timber 0，再走正式 source → preview → create 的空間模型流程；用正式 `.gcanvas` export/import 保存重開。點來源確實選到 timber 0 及 parameter field 0，不以原本已選取的物件充當定位成功。比對 core dump、dirty、history、revision、完整模型資料；來源異動僅顯示狀態，模型未重新生成。

late-response oracle 先取得真實原生 snapshot HTTP 回覆再延後交付；分別取消、換專案及在等待中改動 native revision，核對舊回覆不能重畫／修改新專案。390×844 真畫面與 1280×900 畫面已留存於 `/tmp/geometry-f1a/browser-final`；未宣稱實體手機或 OS 檔案選擇器已驗。

畫面證據：[正式桌面來源路徑](evidence/source-inspector-desktop.png)、[390px 真模型來源變更狀態](evidence/source-inspector-390.png)。

開發過程的失敗均不計通過證據：8 MiB stack 下全量出現原生崩潰；比對未修改 main 在 16 MiB 下完整 1370 pass／0 fail，F1a 同樣設定也恢復通過。第一次 app CDP 在 P76 抓到新增摘要只有 32px，1566 pass／1 fail、completed:false；已修為窄屏 44px，保留原 log `/tmp/geometry-f1a/cdp.log`，最終完整回歸如上。瀏覽器測試的 hidden `innerText` 及不合法 placement fixture 已修正，模型比較使用 canonical JSON 保留跨保存的完整資料；沒有移除斷言或以 mocked 回覆替換真原生資料。

完整原始日誌：`/tmp/geometry-f1a/final-nonbrowser.log`、`final-source-browser.log`、`final-space.log`、`final-cdp.log`。所有最終驗證均為上述 product head 與 runtime；此記錄及 PNG 證據的提交不改任何執行程式，native／runtime 指紋維持相同。

剩餘介面範圍：沒有 durable incarnation receipt，內容相同仍為 identity unknown；#47 的確切支撐 record 未整合前保持 support unknown。材料／做法／spec／datum／舊規則版尚無可靠欄位定位入口，按原生身分顯示並說明限制。F1b 受控重建及新公理另案。Actions 額度阻塞，不重跑 CI／改付費或設定；只建立一次 draft PR，交整合 owner 決定。
