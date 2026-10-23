# GEO-261 最終雲端驗收：P73 阻擋，未完成完整清單

唯一受驗來源為 `0da1f08c75a411442a2e4a431e72459563b8b9a2`。本目錄只封存資料，沒有修產品、測試、公理、容量或 P-177 守門。**目前仍阻擋合併**，不能把已跑部分與歷史綠燈拼成完成。

| 項目 | 真實結果 | 實際耗時／正式時限 |
|---|---|---|
| native 原完整命令 | 退出 0；224 suites；5176通過、0失敗、1允許GDI skip | 1726.251 秒／35分鐘內 |
| mutation:check | native原row退出0；來源／oracle／tool帳本有效 | 納入native |
| 舊包 replay | native `py:test_geo261_model_base_replay` 6／6 | 納入native |
| canvas 完整命令 | 退出1；1695斷言通過、1失敗；completed=false | 1264.134 秒／35分鐘內 |
| assembly、documents、grid、space、timber | **未執行：依P73紅燈停止** | 無退出碼，不能填0 |
| P52正式專項、Q38、§7兩套、P-189 | **未執行：依P73紅燈停止** | 不是Chrome無法執行 |
| 架構三條指定獨立命令 | **未執行：依P73紅燈停止** | native內相關suite不冒充這三條獨立命令 |

native原命令為 `ulimit -s 16384; python3 tests/run_all.py --build`。六個browser job直接取受驗SHA的workflow，僅機械調整job專用port/tmp/Chrome路徑，字型已安裝另留dpkg證明；本輪只實際啟動canvas。每個已啟動job均保存原run、實際run、真實退出碼、完整stdout/stderr、環境版本、SHA、起訖時間、正式時限及來源前後狀態。

native原stdout的進度為224／224，表格也有224個suite。交接工具的原parser把沒有test級計數且pass欄為「-」的`mutation:check`排除，故封存的`native-parsed.json`保留`suites_ran=223`；這是計數口徑，不是漏跑。該row原輸出明列exit 0。此處224以完整原進度與表格為準，未修改parser原結果。

## P73 紅燈與診斷界線

失敗於 `geometry-web/uiux_review_test.js:219`：「空空間不畫假邊界，提供加入成員入口」。上一項可見空態與World不變通過，FATAL_UI顯示focus為space990、connection ready；原始失敗沒有逐項記錄四個predicate值，也沒有落盤fatal screenshot，不冒稱已有失敗瞬間影像。

隔離診斷逐字抽取受驗 `app.js` 的 `syncSpacePlanAnnotations()`，在同一已安裝Chrome執行。hidden attribute為true、computed display為none，但SVG的`.hidden`為undefined、getScreenCTM非null；原函式會插入0×0 grid rect/path，使P73四predicate中的hasNoShape從true轉false。這重現產品／測試整合問題的機制，不是重跑完整canvas，也不是豁免原斷言。固定main `adbaebf9…` 的該函式及predicate逐字相同；未跑main完整對照，所以仍不能斷言本輪失敗是否由GEO-261新增退化所觸發。

canvas在P73中止，完整golden沒有比較。已實跑P88=143、P72B=50、P52 section=43；P52-5單次SYNC_WAIT=345ms與原足跡斷言通過，**不等於P52正式16＋16交錯量測與五控制已完成**。

## 環境修正與原紅燈

Google Chrome stable 156.0.8078.47（官方簽章、索引及deb SHA256驗證，安裝於可寫prefix）、Node v24.19.0、fonts-noto-cjk均可用；不是六browser因缺Chrome而略過。

首輪native發現PID1為tail，不回收被殺的孤兒sleep，原清理斷言11／12。保留原紅燈並中止，原native退出130，沒有把它改寫成通過。repo外subreaper讀回PR_GET_CHILD_SUBREAPER=1並持續waitpid回收自己的孤兒；原單項診斷1／1，之後完整native重跑中的原suite12／12及整份native退出0。另一次啟動前置因TMP名稱碰撞退出78，未執行native；只修repo外driver輸出隔離。所有原碼、原輸出、proc狀態、原退出與reap事件均保留，無flaky豁免、無斷言放寬。

## SHA 分工

- 產品／裁判凍結及帳本實際執行來源：`52b951940f570011b257cd207741ba0a7f6d7ce9`。
- 帳本產物提交、架構實際執行來源：`0548c05cccbb7b35def6bbc3d6b285004be676e5`。
- 架構產物提交：`60425b629aee9f74f4e62ea88af9882bc8968881`。
- 本輪全部已啟動驗收唯一來源：`0da1f08c75a411442a2e4a431e72459563b8b9a2`。
- 本目錄的收據提交是後續資料提交，請用 `git log -1 --format=%H -- evidence/geo261-final-0da1f08c` 解析；不冒稱該新SHA重跑過產品驗收。

帳本仍保存真實execution.head=52；沒有把它偽改成0da。`identity-audit.raw.tar.gz` 有完整純檔案稽核：26／26核對、實際退出0、可重現命令及原輸出，明確不是動態驗收替代。

## 完整原始資料與讀回

- `receipts/native.json`、`native-parsed.json`：真實job收據及從原stdout導出的表格；raw native包含全部套件輸出。
- `receipts/canvas.json`、`canvas-cdp.json`：真實退出1、未完成與原P73失敗，不只摘取綠燈。
- `native.raw.tar.gz`、`canvas.raw.tar.gz`：原step命令、stdout/stderr、server log、原suite JSON/unittest logs、已有截圖及測試專案／feedback。省略Chrome profile/cache及可重建runtime二進位，沒有省略測試輸出。
- `initial-attempts.raw.tar.gz`：首輪環境紅、中止130、前置78及subreaper診斷。
- `p73-diagnosis.raw.tar.gz`：原函式、隔離HTML、Chrome原命令／stdout/stderr／退出、前後predicate與main靜態比較；不含新驗收綠燈。
- `tools-and-provenance.raw.tar.gz`：原交接工具還原、路徑替換、原／新hash、審查原文、雲端driver文字副本。尚未執行的專項工具不代表該專項已跑。
- `environment-and-launch.raw.tar.gz`：簽章／套件驗證、版本／啟動原輸出及回收事件。
- `ARCHIVE_INVENTORY.json`：每個archive內每個檔案的原bytes數與SHA256；`SHA256SUMS`校驗本目錄檔案。

在本目錄執行 `sha256sum -c SHA256SUMS`；以 `tar -xzf native.raw.tar.gz` 或對應archive解開。archive內保留原scratch相對層級；JSON中的原絕對`/tmp/...`位置只表示執行當時位置，對照archive內相對路徑讀取即可。stdout與stderr各原檔是權威；combined只供閱讀。原退出碼、測試數、skip、未跑、故意負控制與中斷保持區別。

依使用者規則，本輪在產品／測試紅燈後停止，沒有修碼、沒有force push、沒有合併。先處理P73，再依來源變更規則更新帳本／架構及重新驗收；本目錄不宣告PR可合。
