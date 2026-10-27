# 給進到這個 repo 的 agent

> 立於 2026-09-18。觸發事故:同一個專案一度同時存在 5 份「公理層閱讀器」
> (正典、React 原型的離線版、手機批註版、桌面手機共用版、設計審查快照),
> 使用者無法分辨哪一份是真的。刪除本檔前請先確認有替代機制。

## 開發前先讀：產品方向與現行規格

先讀 [產品願景整理草案](geometry-guide/PRODUCT-VISION.md)，理解跨場景、可組合物件的整體方向，
以及流程與完成面反向推演等尚在探索的想法。不要把天花板或櫃體例子當成產品範圍上限。
該文件待使用者審閱，**不是已採納公理、功能完成聲明或擴大實作授權**。
行為驗收仍以 `公理層.md` 為 SSOT；願景與條文有落差時先回報並提出待確認項，
不得據願景自行改條文或實作未定案行為。下列既有規則全部維持。

## 🔴 使用者需求帳（2026-10-27 使用者拍板 🔒）

使用者提過的功能要求，一律記在根目錄 [`需求帳.md`](需求帳.md)，那是需求的 SSOT。

觸發事故:
- 10-09 決策 K 的 8 項新功能，有 7 項只寫了條文，App 用不到，回報卻像已完成。
- 10-21 的交接清單漏列了全部待做功能。
- 使用者重複提出仍沒有進度。

使用者原話與完整由來見需求帳開頭。

1. **開工前先讀 `需求帳.md`。** 接手時，依協調分工承接未到 L4 的項目；需求帳本身不構成實作授權，實作以各項已採納的規格為準。交接時，整份帶給下一手，並確認對方真的排入。
2. **使用者一提新需求，當下就記進需求帳。** 寫原話、日期、出處。同一需求再次提出，「重複」欄加一，並移到該組最前。
3. **回報進度一律寫層級 L0–L5**（定義見需求帳）。「完成／做好了」只能用在 L4 以上：使用者在 App 裡用得到，並附操作路徑。條文採納是 L1、有實作 PR 是 L2、進 main 是 L3，都不算完成。
4. **狀態要當下查證才說。** 沒查就寫「未查證」，不寫「以為」「應該」「已安排」。
5. **不得默默暫停需求。** 因其他工作要暫停某項需求，先告訴使用者並取得同意。
6. **層級變動時，同步更新需求帳。** 附上該層級要求的證據。

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
> 舊診斷頁產生器 `make_axiom_reader.py` 已退役(GEO-165)，不要恢復第二套閱讀器。
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

### `make_axiom_reader.py` 已於 2026-09-21 退役(GEO-165)

它曾產出另一套追溯診斷頁。2026-09-21 發現 `--out` 仍能繞過專案內輸出限制,
依 2026-09-20 Q7 已拍板的「下次壞掉或再造成困擾時就刪,不必搶救」移除。
正典由 `sync_axiom_reader.py` 同步,追溯診斷使用 `axiom_matrix.py`;
舊工具只保留在 Git 歷史,不要恢復至工作區。

### 設計規格

`geometry-guide/閱讀器-設計規格.md` **已於 2026-09-20 整份作廢**(使用者拍板),
2026-09-21 自工作區移除(GEO-171;文件早已寫「移除」,檔案卻還在——把實況對齊文件)。
要考古用 `git show`,不要 checkout 回工作區。第 9 流的 GEO-116～119、GEO-121 一併作廢。

版面、色票、字級、元件、互動的判準改為:
- **`BACKLOG.md` GEO-120(🔒 已拍板)**——單頁長捲(Ctrl+F 保住)、hover 預覽與固定參照欄並存、
  雙主題且**深色為預設**、系統字體疊,以及「追溯燈號/三向連結/樞紐徽章不得丟失」的連帶約束。
- **`BACKLOG.md` 第 11 流(GEO-139～149)**——2026-09-20 UI/UX 審查 16 條的處理工單。

### 例外

只有使用者當場明示同意才能破例,且必須在 `BACKLOG.md` 開工單記錄原因。
agent 不得自行判定「這次情況特殊」。

## 使用者回報收件匣(GEO-183)

### 開啟與重啟應用的版本紀律（GEO-231）

使用者要求「開啟應用」時，以 `geometry-web/start.ps1` 為一般入口。
已有服務不可只看網址能連線就沿用；先跑
`python geometry-web/runtime_version.py --probe <port>`，成功才可宣稱為目前版本。
404、指紋不符、不同 repository 或 `fresh:false` 都不能當成功。
固定 `X-Geometry-Release` 是能力名稱，不是目前程式版本。

需要重啟時先保全目前專案與核心 `dump`；只停止目標 port 的服務及其子 bridge，
驗證或重編目前核心後啟動，載回場景並逐字核對 dump，再驗 `/runtime` 與實際畫面。
不得把使用者在用的服務當測試服務重置。完整 `.gcanvas` 的附圖及草稿不可用 `.scene`
備份冒充；保留瀏覽器分頁與既有專案恢復資料，不能擅清瀏覽器儲存。

使用者測 geometry-web 時用 F8 / 右下「回報」鈕 / Shift+F8 當場留回報,程式錯誤也會自動存一筆。
每筆在 repo 的 `feedback/<id>/`(不進 git):說明、指到的 DOM 元素、畫面狀態、回報前的操作黑盒子、
當下世界 `world.scene`、畫面快照 `page.html`、選填截圖。

- 使用者提到「回報」「剛剛測的」「F-2026…」、或開工時,**先跑**
  `python geometry-web/feedback_cli.py list`,再 `show <id>`;不要先請使用者重新描述。
- 元素字串(例如 `button#btnUndo`、`[data-fi-tab="guide"]`)對照 `geometry-web/docs/DOM-CONTRACT.md` 找功能,
  操作序列裡的 `api` 指令對照 `公理層.md` 判斷是不是條文要求的拒絕。
- 重現:`replay <id>` 用 core.exe 載回當下世界並列出改世界的指令;`page.html` 可直接用瀏覽器開來看畫面。
- 修完用 `close <id> "已修 <commit>"`;判定是條文要求的行為用 `--status wontfix` 並寫出條號。
  **不要刪回報資料夾**——那是使用者的原始紀錄。
- 回報只是線索,不是規格:使用者說「應該要能…」而條文不允許時,照 SSOT 紀律回報矛盾,不得直接改行為。

## 🔴 公理層是 SSOT,不得擅改

`公理層.md` 是驗收基準。判斷任何行為對錯前先讀它,**不可從 C 碼或工法反推**。
發現矛盾只回報,不動手;要改必須使用者明示授權,並逐條 diff 給使用者看過。

`公理層.md:614` 的紀律:**條文未定案前不得實作**——推不出的行為就是 bug。

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

- `current_geometry.c` 是**統一 CRLF**;要掃它一律用 Python 以二進位模式讀,
  不要靠 `grep` 掃全檔下定論。
  (**2026-09-21 更正**:這條原本寫「含 NUL byte,grep 會靜默截斷」。
  寫下時是真的——`7f94145` 版本有 4 個 NUL;檔案後來改動後 NUL 已經消失,
  現在是 0。CRLF 那半仍然成立,NUL 那半不再是事實。)
- root `.gitignore` 是**允許清單制**(`/*` 全忽略,逐項 `!` 放行),
  且全域忽略 `*.svg`、`*.exe`、`*.bak-*`。新增檔案發現 git 看不到,先看這裡。
- 正典同步後必須執行 `sync_axiom_reader.py --check` 與 `tests/test_axiom_reader.py`,
  不得用已退役的診斷頁產生器取代正典驗證。過期的閱讀器比沒有更糟。
- **`公理層.md` 在 Windows 上是 CRLF**。`.gitattributes` 只把 `current_geometry.c`
  與見證 SVG/manifest 標成 `-text`,**沒有**標它;git 裡存 LF,簽出成 CRLF。
  凡是拿它的 bytes 算雜湊、比對或做同一性判斷,**一律先 `replace(b"\r\n", b"\n")`**
  ——行尾是簽出方式,不是條文內容。踩過一次:GEO-153,Windows 上整個建模功能被擋掉。
  同樣的判斷見 `geometry-guide/witness.py::_sha`。

## 正典重建與驗證

```sh
python3 geometry-guide/sync_axiom_reader.py          # 就地重建正典
python3 geometry-guide/sync_axiom_reader.py --check  # 只驗現有產物
python3 tests/test_axiom_reader.py                   # 冪等 + 補丁 + 資料一致性
```

**這三條各驗各的,`--check` 綠燈不代表整條管線健康**:
`--check` 只對既有的 HTML 跑 `validate()`,**不呼叫 `rebuild()`**,
所以它的輸出永遠是 `"patches": 0`——`PatchLog`(專門攔「補丁被靜默跳過」)
在這條路徑上是空的。位元組冪等也不是 `--check` 驗的,是
`test_axiom_reader.py::test_rebuild_is_byte_idempotent_and_keeps_reviews`。
動過補丁或追溯資料之後,**三條都要跑**。

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

- `tests/test_modeling_transport.py`(GEO-171 起)吃 `GEOMETRY_TEST_BRIDGE` 直接用預編 bridge,
  不再需要 `cc`;但它會生出 serve.py 與 modeling_cli 子行程,**那些也要 `GEOMETRY_MODEL_BASE`**,
  兩個變數都給才會真的跑(`Ran 2 tests … OK`),只給一個會看到假的 `KeyError: 'derived'` /
  `BASE_COMPILER`。兩個都沒給 → 乾淨 skip。tearDown 在 Windows 改用 `terminate()`
  (`SIGINT` 不支援,原本會漏下 serve.py 行程並讓暫存目錄清不掉)。

  ```sh
  GEOMETRY_TEST_BRIDGE="$TEMP/geometry-tests/bridge.exe" GEOMETRY_MODEL_BASE="$TEMP/geometry-tests/model-base.exe" python -m unittest tests.test_modeling_transport
  ```

- `tests/mutate.py`(GEO-171 起)每個變異編到 `%TEMP%\geometry-tests\mutants\<id>\_mut.exe`
  (不再是 repo 內的 `tests/_mut.exe`——SAC 會擋、平行跑會互撞);暫存 `.c` 寫在 repo 根目錄
  `_mutant_<id>.c`(`#include "geometry-core/…"` 要相對於 `current_geometry.c` 的位置才解析得到),
  被 `.gitignore` 忽略且編完即刪。`MUTATE_RESULTS=<path>` 可把結果寫到別處,
  平行跑幾個 id 時各寫各的、事後合併,別讓多個行程同時寫 `mutants_results.json`。
  變異 exe **依指紋快取**(GEO-225 起:mutant + include 閉包 + 編譯指令相符就沿用,不重編),
  所以只有變異定義或核心來源變了才會產生新二進位;新二進位第一次可能被 SAC 擋,
  腳本會重試 3 次。啟動失敗、逾時、WinError 4551 記 `blocked`(受阻不算 killed,結束碼 2),
  這種受阻仍間隔 12 秒再試。基準線通過後,同一夾具連三次都以存取違規結束
  (Windows `0xC0000005` 或 Linux SIGSEGV `-11`)記 `crashed`:算被偵測到,與 `killed` 分開計,
  不把結束碼變成 2。其他異常結束碼仍是 `blocked`。
  每筆結果帶來源、閉包、變異、**裁判**(`run_tests.py` + 被 `TESTS` 引用的夾具)四組雜湊,
  任一不符就標 `stale`、不計入 killed——改了夾具要重跑 `mutate.py`,不然結果檔會自己說過期。
  `python tests/mutate.py --check` 只讀不跑;`--selftest` 驗它自己的誠實性機制。

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
   這是 SAC 在評估新二進位。**通常**等十幾秒重試一次就會放行,
   但**不保證**——有時會持續被擋;真的過不去就改走 WSL/GCC 那條路,
   不要去動安全設定。
   重點是:看到這個字串**先當成環境問題**,把「環境阻擋」與「程式失敗」分開記錄。
   GEO-157 時我差點據此誤判 cdp_test 的結果。

3. **截圖預設寫到 `%TEMP%\geometry-tests\`,不會碰 `geometry-web/docs/screens/*.png`**(已提交的截圖)。
   (**2026-10-01 更正**:這條原本寫「`cdp_test.js` 會覆寫 `docs/screens`」。寫下時是真的;
   現在 `cdp_test.js` 與各外掛模組的截圖都只寫 `%TEMP%` 或 `GEOMETRY_*_SCREENSHOT*` 指定的目錄。)
   只有把那些變數指進 repo 才會覆寫;跑完仍看一眼 `git status`,有變動就 `git checkout --` 還原。

### 跑 cdp_test

```sh
GEOMETRY_FEEDBACK_DIR="$TEMP/geometry-tests/fb-cdp" GEOMETRY_BRIDGE="$TEMP\geometry-tests\bridge.exe" python geometry-web/serve.py 8799 &
GEOMETRY_FEEDBACK_DIR="$TEMP/geometry-tests/fb-cdp" GEOMETRY_TEST_URL="http://localhost:8799/" node geometry-web/cdp_test.js
```

兩邊都要給同一個 `GEOMETRY_FEEDBACK_DIR`:P38 會實際送出回報並觸發一次自動擷取,
不設就寫進 repo 的 `feedback/`(混進使用者的真回報)——cdp_test 沒看到這個變數時會略過 P38 的送出段。

真的執行 `app.js` 的 harness 有兩支(headless Chrome 實際點按鈕):`cdp_test.js`,以及
空間/投影/牆高/角材流程專用的 `space_model_test.js`——後者**不包含在 `cdp_test.js` 的完整模式裡**,
要另外跑(同樣要給 `GEOMETRY_TEST_URL` 與 `GEOMETRY_FEEDBACK_DIR`,用法見它的檔頭)。
`canvas_test.js` 與 `tests/*.py` 都只到橋接器為止。動到 `app.js` 的行為就得跑 `cdp_test.js`;
動到空間工作區再加跑 `space_model_test.js`。
`*_test.js` 裡檔名不是這兩支、也不是 `canvas_test.js` / `polydraft_test.js` 的,都是 `cdp_test.js`
用 `require` 載入的外掛模組,不能單獨執行。

## 🟡 UI 減重紀律（2026-09-29 使用者拍板 🔒，GEO-219）

1. **新增可見 UI 入口、按鈕或常駐說明的工單，必須在 BACKLOG 條目寫明本次
   「拿掉或合併了什麼」。** 寫不出減項就先入 `決策佇列.md` 給使用者拍板，
   不得只加不減。
2. **每個工作畫面的常駐操作說明區塊不超過 3 塊。** 不計入：首次出現、可關閉
   且記住已讀的教學卡；錯誤／警告訊息；狀態列。既有超標畫面在下次改動該
   畫面時一併收斂，不為此另做大改。
