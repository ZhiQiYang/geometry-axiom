# GEO-225 接手驗證紀錄

2026-10-01。接續 Claude 未完成的測試精煉；依使用者「根據發現的問題改善」及接手授權執行。
`prototypes/engineering-spec/` 維持原狀。公理條文未修改，正典閱讀器只同步測試追溯資料。

## 已完成的修正

- `binaries.py` 檢查來源指紋；`run_all.py` 彙總非瀏覽器測試，區分失敗、略過與環境阻擋，核對每套測試數量。
- CDP 每段斷言數與版本化 golden 比對；部分執行不能更新完整 golden。缺 golden 的單元測試現在會失敗。
- 共用 bridge／CDP 輔助函式；負例釘住實際拒絕原因，避免指令拼錯仍被算成合法拒絕。
- Q26：移除過期 `reference_smoke.js`；確認／取消／復原仍由完整 CDP 驗證。
- Q27：`bench_paint` 的無效次數先返回，保留 GDI harness 的零呼叫斷言。
- Q29：全高子格有真實邊界支撐時，錯向副支以 `V_PRIMARY_AXIS` 拒絕；同位置改為主支成功且長 2960。原缺支撐案例改釘 R6(b)。另釘 I10 一面一主格、I25 標準參照；無限父格的錯誤訊息指名父／子格與應用的 lattice-cell 形式。
- 變異判決附來源、include 閉包、變異、裁判雜湊；快取驗證 exe 本身。SAC 持續阻擋時，支援同一裁判在 WSL/GCC 執行，使用分開的暫存快取。
- 取消只憑結果紀錄採用無 sidecar 執行檔的路徑；舊版以這種方式補發的 adopted sidecar 也會重建。自測用被替換的檔案確認它不能冒充原變異。
- Linux 全套實跑發現 `polydraft_test.js` 忽略入口傳入的 `GEOMETRY_TEST_CORE`，仍寫死 `core.exe`。已改用明示的核心路徑，單獨執行時才依平台選預設檔名。
- P68 在來源更新後會先關閉編輯器，再非同步刷新列表；測試現在等待刷新穩定後才重新點擊來源，避免點中仍在處理中的舊列表。

## 新夾具與等價變異核對

- M16：`_edge_straddle_hi.scene` 的寬度帶 u=[2170,2210] 超出孔邊擋面 [1800,2200]，依 D11/R6(d) 拒絕全寬支撐不足。與既有低端越界案例互補；變異後改被較晚的 V_CUT_PRIORITY 拒絕，因此此例也是診斷順序的裁判。
- M24：`_edge_face_touch_only.scene` 的合法跨距與被引用邊只接於 u=1500，依 R6(c) 的重疊篩選先拒絕。此測試驗**拒絕階段／診斷**：變異仍會被後續端面支撐檢查拒絕，不能宣稱它讓非法幾何成功落地。
- M36：重新讀取唯一呼叫鏈 `world_revalidate → world_validate_derived`。前者先以 `reference_check_all` 執行相同的 `collect_stop_faces`／`count_legal_stops` 與相同 `has_between` 條件；兩次檢查之間只重建 spaces，不修改角材或擋面來源。因此只移除後者的重複檢查在現行呼叫鏈等價。Claude 留下的 7143 組差分探測為輔助證據，未當作形式證明或重新執行的結果。

## 執行紀錄

- 正典同步：99 個補丁、五道 assert、獨立 SSOT 對照通過；`--check` 通過；閱讀器 25 tests 通過。
- 最新 Windows bridge：子格 31 tests、無限格網 19 tests 通過；CDP 計數單元測試 13 tests 通過。
- 變異工具自測：81 checks 通過（含缺 sidecar 及舊 adopted 快取拒用）。
- Claude 留存的完整瀏覽器紀錄：1490 通過斷言、0 失敗、0 略過、72 段 golden matched；唯一例外是 P38 主動注入的回報探針。此筆在本次兩處核心修正之前，不替代新核心的回歸。
- Windows `run_all.py`：已執行 857 個計數項目，856 通過、0 失敗、1 個 `/dev/full` 平台略過。另有來源相符但尚被 SAC 阻擋的 integrity／GDI／model-base，所需 suites 明確未執行，退出碼 2；不稱完整通過。
- WSL 補跑建模相關 7 套共 132 tests 通過；C integrity 80/80 檢查點通過。另以同版本 Node v24.15.0 執行 Linux 全套（runtime 僅置於 `/tmp`，核對官方 SHA-256，未新增專案依賴）。
- Linux 初輪完整回歸：1173 通過、6 失敗、1 略過；6 個失敗均為多邊形測試未使用傳入核心路徑。修正後該套 75/75 通過，另以明示不存在的核心路徑確認它不會偷偷退回預設程式。完整重跑（同一入口、無篩選）結果為 1180 個計數項目：1179 通過、0 失敗、1 個 Windows GDI 略過，退出碼 3。
- 變異完整重跑：48 筆＝39 killed、5 equivalent、3 retired、1 blocked（M20）；0 survived、0 invalid、0 stale。Windows 再執行 `--check` 得到相同分類與雜湊結果。M20 在正常基準 138/138 通過後，Linux 仍連續 3 次因 SIGSEGV（-11）被原政策列為 blocked。
- 快取守門修正後，Windows 與 Linux 的 81 項自測皆通過；M16/M24 以同指紋快取重新執行，仍由兩個新增夾具抓到，未重編。
- 首輪新核心完整 CDP 在 P68 中止：899 通過、1 個 P61 失敗、P68 逾時。P61 為接手執行時漏設 WSL 檔案路徑轉換；P68 另以獨立模式重現為點擊早於介面刷新。修正後 P68 在 WSL 環境 36/36 通過，P61 在原生 Windows 服務重測通過；該次 reference-only 執行共 422 通過、0 失敗（部分模式，不比對完整 golden）。
- 第二輪 CDP 使用 Windows 服務與新 Windows bridge；模型 adapter 經暫存啟動器呼叫同源 WSL/GCC 執行檔（Windows 版本仍遭 SAC 阻擋）。872 通過、0 斷言失敗後，P65 等待預覽逾時：WSL 閒置關閉，重新啟動超過 adapter 的 20 秒預算，且 `/tmp` 執行檔隨重啟消失。測試環境已加上暫時保持 WSL 運作的行程、重建 adapter，實際範例端點 3.99 秒回傳 3 筆；沒有放寬產品或測試時限。
- 環境修復後，新核心完整 CDP：1490 通過斷言、0 失敗、0 略過，72 段與既有 golden 逐段相符，退出碼 0。唯一瀏覽器例外為 P38 主動注入的回報探針。P61 檔案載入、P65 建模預覽、P68 來源編輯均通過；未更新 golden。完整日誌位於 `%TEMP%/geometry-tests/geo225-cdp-final.log`。

## 尚待事項

- Q28：是否把「正常基準線＋變異版穩定崩潰」獨立列為 crashed，待使用者選擇。目前維持 blocked，不計 killed。
- Windows SAC（WinError 4551）擋住部分新編執行檔；收尾再次執行 GDI 測試仍在啟動前受阻。GDI 僅能在 Windows 驗證，仍列未驗證；其他所需非瀏覽器測試已於 Linux 通過。

斷言數、測試案例數、C 檢查點與變異數是不同單位，不相加宣稱端到端情境數。
