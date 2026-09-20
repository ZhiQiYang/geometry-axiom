# 給進到這個 repo 的 agent

> 立於 2026-09-18。觸發事故:同一個專案一度同時存在 5 份「公理層閱讀器」
> (正典、React 原型的離線版、手機批註版、桌面手機共用版、設計審查快照),
> 使用者無法分辨哪一份是真的。刪除本檔前請先確認有替代機制。

## 🔴 公理層閱讀器只准有一份

**正典是 `geometry-guide/公理層-閱讀器.html`。**

它是**批註版**:單一自足檔、**零外部引用**(無 `<link>`、無 `<script src>`、
無 `http(s)://`、無 `@import`、無外部字型),直接雙擊即可離線使用,
桌機/手機依寬度自動切換版面。**不需要、也不准再做「離線版」。**

使用者的工作流是「在它上面讀條文 → 批註 → 依批註改 `公理層.md` → 重出下一版閱讀器」,
每一版取代前一版。它內建五道完整性 assert(見下),任何一道失敗會**連桌面版面一起失效**。

> **正典同步入口：`geometry-guide/sync_axiom_reader.py`**（GEO-128）。
> 它從 `公理層.md` + `geometry-guide/公理層-白話.md` 同步版本化正典 HTML，
> 保留互動模板、批註、例圖及未改段落身份；詳見 `geometry-guide/READER-BUILD.md`。
> `make_axiom_reader.py` 仍產出另一套追溯診斷頁，**不是正典**。
> 每條的「見證圖」區塊來自 `geometry-guide/witness/`(GEO-131,一條文一圖、由夾具經引擎推導、圖變即警報),
> 同步器只讀檔嵌入;要改圖請走 `witness.py`,不要手改 HTML 或 SVG。
> 寫檔前必須通過五道 assert，並逐字對照獨立讀取的 SSOT，不能僅讓內部 JSON 自洽：
> 1. `docHash(state) === state.documentHash`,其中
>    `docHash = sha256(JSON.stringify(blocks.map(b=>[b.id,b.source,b.separator])))`
> 2. `<script id="clause-data">` 與 `axiom-review-data.clauses` 的 JSON **必須全等**
> 3. 每條每節:`blocks` 的 `source+separator` 串接 **必須等於** `clauses[section]`
>    (每節最後一段 `separator` 是 `''`；其餘精確保留 SSOT 原文分隔，可能是 `'\n'` 或 `'\n\n'`)
> 4. 每個 block:`sha256(source) === sourceHash`
> 5. 可編輯 block:DOM `.review-target` 的 **textContent** 必須等於
>    `window.axiomMobile.inline(source)` 算繪後的 textContent
>
> 因此**不能只改可見 HTML、也不能只改一份 JSON**。可靠做法是:由 blocks 反推 clauses、
> 全部重算雜湊、`subs` 從 `公理層.md` 重新解析(改 `body` 卻忘了同步 `subs`
> 已經出過一次事,見 BACKLOG GEO-124),並用閱讀器自己的 `inline()` 產生 HTML。

### 禁止

- 不准新增第二個閱讀器產物。包含但不限於:離線版、手機版、桌機手機共用版、
  精簡版、任何 `npm run build` 出來的 `dist/`。
- 不准把正典 HTML「另存一份再改」成第二個長期存在的閱讀器。
  改內容時可以先產出新檔再覆蓋正典路徑,但**最終只能有一份**,舊版不保留。
- 不准把任何 build 產物當閱讀器使用、交付或提交。

### `geometry-guide/axiom-reader-design/` 的定位

那是**設計參考**,不是閱讀器來源。可以留著看,但它 build 出來的東西
(`dist/`、`公理層閱讀器-離線版.html`)一律不是閱讀器,不得交付或提交。
該資料夾內另有一份 `AGENTS.md` 給外部 agent,規則相同。

### 設計規格

版面、色票、字級、元件、互動一律照 `geometry-guide/閱讀器-設計規格.md`。
改版工單見 `BACKLOG.md` 第 9 流(GEO-114～121)。

### 例外

只有使用者當場明示同意才能破例,且必須在 `BACKLOG.md` 開工單記錄原因。
agent 不得自行判定「這次情況特殊」。

## 🔴 公理層是 SSOT,不得擅改

`公理層.md` 是驗收基準。判斷任何行為對錯前先讀它,**不可從 C 碼或工法反推**。
發現矛盾只回報,不動手;要改必須使用者明示授權,並逐條 diff 給使用者看過。

`公理層.md:319` 的紀律:**條文未定案前不得實作**——推不出的行為就是 bug。

## 已知地雷

- `current_geometry.c` 含 NUL byte 且是 CRLF,`grep` 會**靜默截斷**。
  要掃它一律用 Python 以二進位模式讀。
- root `.gitignore` 是**允許清單制**(`/*` 全忽略,逐項 `!` 放行),
  且全域忽略 `*.svg`、`*.exe`、`*.bak-*`。新增檔案發現 git 看不到,先看這裡。
- `make_axiom_reader.py` 有建置期強制檢查:條文數 < 60、懸空引用、
  白話出現公理層沒有的條號 → 一律非 0 退出。過期的閱讀器比沒有更糟。

## 正典重建與驗證

```sh
python3 geometry-guide/sync_axiom_reader.py
python3 geometry-guide/sync_axiom_reader.py --check
python3 tests/test_axiom_reader.py
```

既有正典 HTML 是版本化模板的一部分；缺失時從 Git 還原，不另造閱讀器。
可用 `--review-json` 合併同源批註備份；相同 ID 內容衝突必須拒絕，不自動覆寫。
修改版面／互動時仍須遵循設計規格及五道 assert。CLI 結構檢查不能冒充手機或真實瀏覽器操作驗證。
