# GEO-261：最終雲端驗收紀錄（仍阻擋合併）

本輪在雲端固定 `0da1f08c75a411442a2e4a431e72459563b8b9a2` 驗收：完整 native 通過；canvas 在 P73 斷言失敗後停止。依「產品或測試紅燈即停下回報」規則，後續五個瀏覽器 job 與專項未執行，**仍不可合併**。產品、裁判、公理、容量與 P-177 守門流量均未改。

## SHA 與證據

| 角色 | 完整 SHA |
|---|---|
| 產品與裁判凍結來源；完整帳本實際執行來源 | `52b951940f570011b257cd207741ba0a7f6d7ce9` |
| 帳本產物提交；架構重產實際執行來源 | `0548c05cccbb7b35def6bbc3d6b285004be676e5` |
| 架構產物提交 | `60425b629aee9f74f4e62ea88af9882bc8968881` |
| 本輪唯一受驗來源 | `0da1f08c75a411442a2e4a431e72459563b8b9a2` |
| 本輪雲端收據提交 | `4ff5f11934c045fed946f99cb3990481ff320079` |

既有四個 SHA 都可解析且位於整合分支祖先鏈。75 筆 active 帳本保留真實 `execution.head=52b95194…`；`52→0da` 只有帳本、架構與交接資料變更。獨立靜態身分稽核 26 項成立，涵蓋來源、184 檔 include closure、core／bridge oracle、工具與架構 inputs；本輪 native 的 `mutation:check` 也實際退出 0。完整 hash、可重現腳本及原輸出在證據內，靜態核對不取代動態驗收。

收據提交只封存資料，不當成已驗產品。正文位於 `codex/geo261-final-prbody-20261022` 的 `PR_BODY.md`；自身 commit 請讀該分支 HEAD。

## 環境與方法

全部在雲端 Linux 執行。`google-chrome --version`＝`Google Chrome 156.0.8078.47`；`node --version`＝`v24.19.0`。官方 stable 套件經簽章、索引與套件 SHA256 驗證，安裝至 workspace 前綴，未登記 system dpkg。`fonts-noto-cjk` 已安裝；Python 3.12.14、GCC 14.2、PyYAML 6.0.3，版本原輸出與安裝收據已封存。

按固定 SHA 的 workflow 原指令串行執行，僅替換埠、暫存／feedback／截圖路徑與 Chrome 位置，保留 probe、case、golden、清理與退出碼。原 WSL runner 需要 mount 權限且先排 canvas，故用 repo 外監督器依指定順序執行；差異與工具 hash 入收據，沒有 flaky 豁免。

## 本輪結果

| 關卡 | 實際結果／退出碼 | 正式 CI 時限 | 實際耗時 |
|---|---|---:|---:|
| native：`ulimit -s 16384; python3 tests/run_all.py --build` | **退出 0**；224 suites，5,177＝5,176 通過＋1 個允許的 Windows GDI skip，0 失敗 | 35 分鐘 | 1,726.2514 秒，時限內 |
| canvas：完整 `node geometry-web/cdp_test.js` | **退出 1**；1,695 通過／1 失敗，`completed:false`；P73 紅，golden 未比較 | 35 分鐘 | 1,264.1338 秒，時限內 |
| assembly | 未執行：依 P73 紅燈停止 | 15 分鐘 | — |
| documents | 未執行：依 P73 紅燈停止 | 10 分鐘 | — |
| grid | 未執行：依 P73 紅燈停止 | 15 分鐘 | — |
| space | 未執行：依 P73 紅燈停止 | 15 分鐘 | — |
| timber | 未執行：依 P73 紅燈停止 | 20 分鐘 | — |
| 帳本 `mutation:check` | native 內實際退出 0；70 killed／1 crashed／4 equivalent／3 retired | 納入 native | 見 suite 收據 |
| 舊包 replay | native 的 `py:test_geo261_model_base_replay`，6／6 通過 | 納入 native | 見 suite 收據 |
| P52 正式交錯量測與等待負控制 | 未執行：依 P73 紅燈停止 | 專項 | — |
| Q38：`tests/section_profile_mutation_check.py` 完整 gate | 未執行：依 P73 紅燈停止 | 專項 | — |
| §7：`geometry-core/card-reference/run_mutations.py` | 未執行：依 P73 紅燈停止 | 專項 | — |
| §7：`geometry-core/card-reference/run_axiom_mutations.py` | 未執行：依 P73 紅燈停止 | 專項 | — |
| P-189 三方交錯量測與 dump 等價 | 未執行：依 P73 紅燈停止 | 專項 | — |
| 架構 manifest 獨立命令 | 未執行：依 P73 紅燈停止 | 專項 | — |
| 架構裁判自測獨立命令 | 未執行：依 P73 紅燈停止 | 專項 | — |
| 產品架構獨立命令 | 未執行：依 P73 紅燈停止 | 專項 | — |

native 另確認 `contact_sources` 13／13、`wood_contact_world` 10／10、`mutation_anchors` 3／3。GDI 保留 skip、M20 保留 crashed。架構三條待執行命令是 `tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json`、`tests/test_architecture_contract.py`、`tests/test_product_architecture.py`，皆帶 `python -B`；native 套件結果不冒充這三次獨立執行。

Chrome 已可執行；後續未跑原因是遵守紅燈停止規則，不能標為「Chrome 無法安裝／本環境無法執行」。P-189 尚無本輪數字：main `adbaebf9…`／base `3e600772…`／final `0da1f08c…` 的 N＝16／32／48／64 各點 final／main≤2 及 base／final 的 `loadfile`＋`dump` 逐 byte 相同，都尚未驗證。

## P73 阻擋與診斷界線

原失敗為：`P73 assertion failed: 空空間不畫假邊界，提供加入成員入口 false`。canvas 在此停止，沒有完成後續區段，也沒有執行完整 golden 比較。P52 區段已完成 43 個斷言，`SYNC_WAIT P52-5=345ms` 只是本次單一觀察，不是正式 P52 專項。P88＝143、P72B＝50 也已跑完，但這些區段結果不補整個 canvas 的失敗。

隔離診斷保存原 `syncSpacePlanAnnotations` 函式及相同四個 predicate：隱藏 SVG 的 `hidden` attribute 為 true、`svg.hidden` 為 undefined、computed display 為 none，但 `getScreenCTM()` 非 null。直接執行原函式後，SVG 插入 0×0 網格 rect／path；四個 predicate 只有 `hasNoShape` 由 true 變 false，其他維持 true。這支持隱藏 SVG 的屬性判斷與網格註記互動是待查方向。

**證據限制：**原失敗的 `FATAL_UI` 沒有逐一保存四個 predicate 值，也沒有落盤 fatal screenshot；不假造原現場值或截圖，不把隔離診斷寫成原場景逐欄重現。靜態比較證明固定 main `adbaebf9…` 的函式 hash 與 predicate 相同，但未跑 main 完整對照，**尚不能證明此紅燈不是本 PR 的新退化**。本輪停在此產品／測試問題，沒有修正或放寬斷言。

## 環境修正與保留的失敗

初輪 native 的清理測試留下兩個 PPID 1、狀態 Z 的 `sleep`：容器 PID 1 是不回收孤兒的 `tail`。保留紅燈後中止，退出 130，未冒稱原輪通過。repo 外標準 `PR_SET_CHILD_SUBREAPER` 監督器補足回收能力，未更改測試；單項診斷 1／1，完整 native 重跑時原套件 12／12 通過。另一次啟動因 TMP 碰撞於 preflight 退出 78，未開始 native，不計作產品失敗或通過。各輪收據、`/proc`、監督器原碼與回收事件均保留。

## 原始證據與最後審查回覆

證據位於 [evidence/geo261-final-0da1f08c/](https://github.com/ZhiQiYang/geometry-axiom/tree/4ff5f11934c045fed946f99cb3990481ff320079/evidence/geo261-final-0da1f08c)：先讀 `README.md`、`SUMMARY.json`，再依 `*.raw.tar.gz` 清單讀完整命令、退出碼、stdout／stderr、環境、SHA、suite 記錄與 SHA256。原始失敗及環境修正後的執行分開封存，靜態稽核附重現方法。歷史附件不補本輪未跑項目。

最後審查原文：交接分支 `888a999f` 的 `handoff/pr288-latest-review-20261022.md`。

1. **帳本來源不可解析：**已由可解析祖先 `52b95194…` 的完整重產帳本取代，保留原 execution head；本輪來源／closure／oracle／tool 靜態核對與 native 的 `mutation:check=0` 均有 repo 內收據。
2. **最終整合驗收未完成，仍阻擋。**native 已完成，canvas P73 失敗，其餘依規則未跑。未以歷史綠燈或 Actions 零步驟 failure 外推完成。
3. **正文過時：**本正文分列來源、帳本、架構與收據 SHA，矩陣只列固定 `0da…` 的本輪結果；由使用者貼回 #288。

最不確定的是 P73 原現場觸發條件、相對 main 的退化歸屬及未跑清單。實體手機／iOS、Windows 正式服務與 P72B optional 真雙服務往返未另驗。釐清 P73 並完成必要重驗後再請複審；本次不 force push、不合併，未展開其他列車。
