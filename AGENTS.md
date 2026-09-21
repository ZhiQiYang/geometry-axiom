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

### `geometry-guide/axiom-reader-design/` 已於 2026-09-20 移除

那是第 3 版設計原型(React + Vite,38 個檔、21MB,占當時 repo 36%),
它服務的 `閱讀器-設計規格.md` 同日整份作廢,於是它也失去依據。
**完整內容仍在 git 歷史裡**(移除前最後一版見該次 commit 的父節點),要考古用 `git show` 取回,
不要重新 checkout 回工作區。

### `make_axiom_reader.py`:診斷工具,不是產品(🔒 2026-09-20 拍板)

它產的是**追溯診斷頁,不是正典**。2026-09-20 起加了機制而不只是文字規則:
預設寫到系統暫存目錄;`--in-repo` 才寫進 repo,而且正典存在時一律拒絕並要求改用
`sync_axiom_reader.py`。理由見本檔開頭那場「一度同時存在 5 份閱讀器」的事故。

使用者拍板**留著但標為診斷工具**:它維護著公理層的第二套渲染,追溯功能與 `axiom_matrix.py`
高度重疊。閘門已擋住風險,現在不礙事;**下次它壞掉或再造成困擾時就刪,不必搶救**。

### 設計規格

`geometry-guide/閱讀器-設計規格.md` **已於 2026-09-20 整份作廢**(使用者拍板),
不得引用為施工依據;第 9 流的 GEO-116～119、GEO-121 一併作廢。

版面、色票、字級、元件、互動的判準改為:
- **`BACKLOG.md` GEO-120(🔒 已拍板)**——單頁長捲(Ctrl+F 保住)、hover 預覽與固定參照欄並存、
  雙主題且**深色為預設**、系統字體疊,以及「追溯燈號/三向連結/樞紐徽章不得丟失」的連帶約束。
- **`BACKLOG.md` 第 11 流(GEO-139～149)**——2026-09-20 UI/UX 審查 16 條的處理工單。

### 例外

只有使用者當場明示同意才能破例,且必須在 `BACKLOG.md` 開工單記錄原因。
agent 不得自行判定「這次情況特殊」。

## 🔴 公理層是 SSOT,不得擅改

`公理層.md` 是驗收基準。判斷任何行為對錯前先讀它,**不可從 C 碼或工法反推**。
發現矛盾只回報,不動手;要改必須使用者明示授權,並逐條 diff 給使用者看過。

`公理層.md:319` 的紀律:**條文未定案前不得實作**——推不出的行為就是 bug。

## 改 `sync_axiom_reader.py` 的補丁時

同步器對一份**會演化的產物**做將近百次文字替換。這個管線最常見的失效不是「補丁做錯」,
而是**「補丁被靜默跳過」**——「有沒有套用過」是用改前/改後的樣子判定的,被改的內容一變,判定就失效。
2026-09-20/21 一天內踩了四次。

所以:**每個補丁都必須登記一個「套用後一定看得到」的標記**。
`force()` 與 `inject_css()` 會自動登記;移除式改寫(先刪再插)要自己呼叫
`PATCHES.expect_present(...)`。`rebuild()` 結束時一次驗完,失效時會指名是哪一個補丁。
新增補丁後跑一次同步,看報告裡的 `"patches"` 數字有沒有跟著加。

還有一條:**凡是內容會隨資料變的標記(算出來的數字、清單),一律「先移除再插入」**,
不得用 `force()` 的改前/改後判定——那個判定只看「形狀在不在」,看不出「內容過期了」。
2026-09-21 篩選 chip 就是這樣凍結在第一次建置的數字(GEO-152)。登記簿也擋不住這種,
要靠針對資料一致性的測試。

另外:**補丁腳本一律用檔案寫入工具產生,不要用 shell heredoc**——
heredoc 會把 `
` 這類跳脫序列吃掉,而 `current_geometry.c` 是統一 CRLF(見下方地雷)。

## 已知地雷

- **`surface N` 是「boundary N + placement N」合體一行**,所以它要的 id 必須在
  **兩個** id 空間裡都空。`newid` 的 `boundary` / `placement` 只各自保證自己那一邊,
  **不得在 JS 裡用 `Math.max()` 或連續加號湊**——撞到既有 id 時 `surface` 是交易式
  重宣告,會**靜默覆寫**並回 `ok:true`。要幾個就跟橋接器要幾個:`newid <n>` 的
  `surfaces` 欄位(GEO-157)。

- `current_geometry.c` 含 NUL byte 且是 CRLF,`grep` 會**靜默截斷**。
  要掃它一律用 Python 以二進位模式讀。
- root `.gitignore` 是**允許清單制**(`/*` 全忽略,逐項 `!` 放行),
  且全域忽略 `*.svg`、`*.exe`、`*.bak-*`。新增檔案發現 git 看不到,先看這裡。
- `make_axiom_reader.py` 有建置期強制檢查:條文數 < 60、懸空引用、
  白話出現公理層沒有的條號 → 一律非 0 退出。過期的閱讀器比沒有更糟。
- **`公理層.md` 在 Windows 上是 CRLF**。`.gitattributes` 只把 `current_geometry.c`
  與見證 SVG/manifest 標成 `-text`,**沒有**標它;git 裡存 LF,簽出成 CRLF。
  凡是拿它的 bytes 算雜湊、比對或做同一性判斷,**一律先 `replace(b"\r\n", b"\n")`**
  ——行尾是簽出方式,不是條文內容。踩過一次:GEO-153,Windows 上整個建模功能被擋掉。
  同樣的判斷見 `geometry-guide/witness.py::_sha`。

## 正典重建與驗證

```sh
python3 geometry-guide/sync_axiom_reader.py
python3 geometry-guide/sync_axiom_reader.py --check
python3 tests/test_axiom_reader.py
```

既有正典 HTML 是版本化模板的一部分；缺失時從 Git 還原，不另造閱讀器。
可用 `--review-json` 合併同源批註備份；相同 ID 內容衝突必須拒絕，不自動覆寫。
修改版面／互動時仍須遵循 GEO-120 與第 11 流工單及五道 assert(設計規格已作廢)。CLI 結構檢查不能冒充手機或真實瀏覽器操作驗證。

## 在 Windows 上跑測試

沒有 gcc 系編譯器的機器(本機就是),有兩個地方會**假性**失敗,別誤判成程式有問題:

- `tests/test_modeling_runtime.py` 走 `geometry-core/modeling/base.py`,預設用 `CC`(預設 `cc`)
  以 `-std=c11 … -o` 編 `geometry-core/model_base.c`。MSVC 的 `cl.exe` 不吃這套旗標,
  於是每個案例都先撞 `UNSUPPORTED / BASE_COMPILER`,**比任何其他閘門都早**——
  真正的缺陷會被整個遮住(GEO-153 就是這樣差點被我誤判)。
  **解法**:用 MSVC 自己編一支 adapter,再用 `GEOMETRY_MODEL_BASE` 指過去
  (`base.py` 明文支援這個覆寫)。編到 `%TEMP%\geometry-tests\`,不要編進 repo:

  ```bat
  call "...\VC\Auxiliary\Build\vcvars64.bat"
  cl /nologo /utf-8 /O2 /W3 /U_WIN32 /Fe:%TEMP%\geometry-tests\model-base.exe ^
     /Fo:%TEMP%\geometry-tests\ geometry-core\model_base.c /link /STACK:16777216
  ```

  ```sh
  GEOMETRY_MODEL_BASE="$TEMP/geometry-tests/model-base.exe" python -m unittest tests.test_modeling_runtime
  ```

- `tests/test_modeling_transport.py` 在 `setUpClass` 就**寫死** `cc … -o` 去編 `web_bridge.c`,
  沒有環境變數可覆寫,所以本機整組跑不動。它沒有碰 `/upload` 或 `newid`。

`tests/test_bridge_integrity.py` 與 `tests/test_reference_contract.py` 吃
`GEOMETRY_TEST_BRIDGE`;`test_bridge_integrity` 要用 `python tests/test_bridge_integrity.py`
跑(`python -m unittest` 會讓它 `import run_tests` 失敗)。

**編出來的 exe 一律放 `%TEMP%\geometry-tests\`**:Smart App Control 會擋 repo 目錄下
新編的未簽章 exe(WinError 4551)。

### 重編 bridge 的三個坑(GEO-157 各踩一次)

1. **exe 被鎖住時 `cl` 會失敗,但看起來像成功**。`cl` 會先印來源檔名再連結,
   所以「有看到 `web_bridge.c`」**不等於**編成功;真正的失敗長這樣:
   `LINK : fatal error LNK1104: 無法開啟檔案 …bridge.exe`。
   重編前先把 server 與 bridge 殺乾淨:

   ```sh
   powershell -NoProfile -Command "Get-Process bridge -ErrorAction SilentlyContinue | Stop-Process -Force"
   ```

   **重編後一定要驗二進位真的換了**(找該版本獨有的字串),不要只看編譯器的輸出。

2. **剛編好的 bridge,第一次被 python 生成子行程時會被 Smart App Control 擋**,
   症狀是 serve.py 回 `橋接器連線中斷,請重新啟動服務`,而同一支 exe 從 shell 直接跑**沒事**。
   這是 SAC 在評估新二進位,**等一下再啟動一次就好**。
   看到這個字串不要當成程式壞了——GEO-157 時我差點據此誤判 cdp_test 的結果。

3. **`cdp_test.js` 會覆寫 `geometry-web/docs/screens/*.png`**(已提交的截圖)。
   跑完用 `git checkout -- geometry-web/docs/screens/` 還原,別混進 commit。

### 跑 cdp_test

```sh
GEOMETRY_BRIDGE="$TEMP\geometry-tests\bridge.exe" python geometry-web/serve.py 8799 &
GEOMETRY_TEST_URL="http://localhost:8799/" node geometry-web/cdp_test.js
```

它是**唯一真的執行 `app.js` 的 harness**(headless Chrome 實際點按鈕);
`canvas_test.js` 與 `tests/*.py` 都只到橋接器為止。動到 `app.js` 的行為就得跑它。
