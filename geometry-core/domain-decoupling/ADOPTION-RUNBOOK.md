# GEO-261 採納執行手冊（未執行）

日期：2026-10-16。這份文件只記錄逐條提案獲得使用者明示採納後的執行順序；不構成採納，不是實作或驗證完成聲明。此盤點先在 repository 外完成，再收錄於 P0 提案；沒有修改 SSOT、白話、正典閱讀器、模型執行器、產品或測試，沒有啟停服務。

## 1. 本次採納對象必須固定

| 項目 | 值 |
|---|---|
| 工作樹 | `D:/geometry-axiom-work/geo261` |
| 提案提交 | `17a25e92c75e8c89063e36ca329729980d8ea6a9` |
| 原始 SSOT 提交 | `1c80751150d0767ba52509537caf8d5542769ccb` |
| 原始 SSOT LF SHA-256 | `ab31dc36d5416762ac44932940a94f6142b72e831ceb62c0bc67375512109004` |
| `clause-map.json` LF SHA-256 | `51841370641ea38d45d4d46a1767f8c4fd4b4fb4c47c0deb4ce82d0476fa5ca4` |
| `AXIOM-PROPOSAL.md` LF SHA-256 | `905e49111b5bb8c4fadecb46c89c0d9ff59deb7d3064b602ae23bfc72ca6b609` |
| 完整提案重建後 SSOT LF SHA-256 | `f5ef63e26c0816a2167a8afb515ee915680f10388e62089073482582efc0612b` |
| 完整提案重建後 UTF-8 LF bytes | `309382` |
| 條文清冊 | 204 條：D 69、I 76、R 59；103 條修改、101 條原文保留；另改完整前言及排除章 |
| 作用域 | K 29、M 95、W 30、H 50 |

上表最後兩個內容指紋由目前凍結提案在記憶體中呼叫 P0 的 `validate_proposal()` 重建後計算，沒有寫入 SSOT。採納當時要再以提交中的實際 bytes 獨立重算，不能因上表列過就跳過驗證。提案有任何新差異時，本手冊中提案 hash 與 after hash 都失效，須重新逐條呈現並取得對新版的採納。

批准範圍應能定位到這個提交及完整逐條差異，含前言與排除章。保持提案的歷史 `status: proposed-not-approved` 與全部 `before` 原文；另建立採納收據記錄使用者批准、批准內容指紋、寫入提交及結果 hash，不把歷史提案偽裝成當初已核准。

## 2. 開工前保全與前置檢查

1. 先執行 `python geometry-web/feedback_cli.py list`；若有此次相關回報，再讀 `show <id>`。記錄工作樹與分支、HEAD、diff、未追蹤檔及其他 agents 的所有權，不覆寫他人變更。
2. 在研究區／正式證據目錄保全 immutable baseline 的來源、執行器及裁判指紋，並保留原 `.gcanvas`／模型交換包 bytes、producer provenance、預期接受或拒絕。舊檔不能用新 writer 重新生成來代替；`.scene` 不能代替完整專案及附件。
3. 從 `1c807...:公理層.md` 取得獨立舊來源，正規化 CRLF→LF 後確認上表原始 hash；再檢查工作區 SSOT 尚與這份舊來源完全相等。不能只比較 JSON 的 `before` 與自己的 `sourceSha256`。
4. 從批准提交讀提案的兩個檔案，驗 hash、204 條完整順序、M 條文完整保留 W/H 原文、Markdown/JSON 的逐字相等，以及全部章節。現在的 `tests/test_domain_decoupling_proposal.py` 是 29 個 P0 測試；它證明提案完整性，不證明分層實作存在。
5. 確認既有唯一正典 `geometry-guide/公理層-閱讀器.html` 存在，備份批註資料到證據區。若正典缺失，從 Git 恢復該版本模板。不得另建閱讀器、離線版、手機版或 dist 產物。
6. 不啟動、不重置使用者目前服務。後續測試使用隔離 port、TEMP feedback/evidence 目錄及已驗來源指紋的 core/bridge/model-base。需要交付後重開應用時，再依 GEO-231 保存完整目前專案與 dump、限定停止目標服務及其 bridge、復原並逐字核對 dump、最後驗 `/runtime` 與實際畫面。

## 3. 先遷移 P0 裁判，再寫入 SSOT

現有 P0 刻意要求「目前 SSOT = before」。採納後直接重跑會出現 `SOURCE_HASH`／`CLAUSE_BEFORE`，這是階段不符，不可刪檢查或把 `before` 改成新文。

建議以獨立採納收據顯式進入 P1，保留原 P0 validator 作為「凍結舊來源＋批准提案」的完整性裁判：

1. 載入獨立保存的舊 SSOT bytes，驗固定基準 revision/hash；載入批准提交中的提案 bytes，驗批准記錄綁定的兩份 hash。這份 old source 可以是 Git blob 或已驗 hash 的不可改 baseline fixture，不能從當前 `before` 拼湊。
2. 原 `validate_proposal(old_source, approved_map, approved_markdown)` 必須仍完整通過，產生 expected adopted source。保留缺條、假 before、Markdown/JSON 同時刪改、M 尾段遺失等負測試。
3. P1 另檢查「目前 SSOT 的 LF bytes = expected adopted source」與固定批准 hash；before/provenance 不變。不要用環境變數或自動偵測目前檔案來跳過 old/current 二選一；明示採納狀態及批准內容是必要資料。
4. 新負控至少包括：只有目前 SSOT 偷改一字；改 after 同時改 Markdown；改 before 同時改獨立來源；刪掉一條／一章；批准收據缺失／指向不同提案；原行尾以外的空白差異。全都必須被拒絕。
5. 保留 P0 原始 log、guard-removal 突變原件與收據；P1 改過裁判後重新產生當前裁判的負控證據，不能沿用 P0 的綠燈宣稱新裁判健康。

採納 validator 的製作與採納本身分開說明。若採納只批准條文，而 implementation 尚未完成，新的「核心可獨立使用」測試應保持為待實作驗收項；不能以資料表、空 callback、簡化幾何 helper 或固定木工繞道充作完成。

## 4. 重建整份 SSOT 與白話

以舊 SSOT 的真實章節／段落位置套用批准 map 的完整 replacement；保留所有章節標題與段落分隔，不能用 `after` 清單直接以兩個換行串接成新文件。P0 `source_layout()` 與 `validate_proposal()` 已提供獨立解析及在記憶體重建的範例。

先驗重建結果的 204 個唯一條號、原順序、完整前言與排除章及 LF hash，再以檔案工具／Python 二進位寫入 `公理層.md`。Windows 檔案使用 CRLF：先將源 bytes 正規化成 LF，最後只做一次 LF→CRLF。不得用 PowerShell 文字編碼預設或 shell heredoc 生成補丁；不要新增 BOM、改字或改最後換行。寫回後獨立讀 bytes，確認沒有裸 CR、沒有 CRCRLF，再將 CRLF→LF 與批准 expected 全等比對。

`geometry-guide/公理層-白話.md` 逐條忠實同步這 103 條的 K/M 職責；101 條未改者不因這次重新遣詞。新增總說明要清楚表達：K 是完整幾何、typed graph、精確求值與候選交易；woodworking/1 固定注入既有產品入口；模板決定材料、角色、截斷資格與木工流程；H 管專案、儲存及編輯流程。模板不複製核心演算法。不可把既有零槽空間、紅燈填板、未完成草稿等合法中間態改說成一律非法，也不能把全固定邊覆蓋完成目標說成建立時不變量。

白話的「規格已採納」與「功能已實作」要分清楚；不得因採納新核心介面契約，就把舊功能狀態批量改成已完成。保留條號讓讀者直接對照 SSOT；例如 D7 角材與 D36 斷面構件看似同樣長方體，適用的角色、L 來源及碰撞契約仍不同。

## 5. 模型公理版本必須兩個提交收尾

目前 `geometry-core/modeling/__init__.py:19–20` 的 current tuple 是：

```text
("651c661b2c4c224c58bb4a2ed0a42ed929a16aa6", "ab31dc36d5416762ac44932940a94f6142b72e831ceb62c0bc67375512109004")
```

`_axiom_hash()`（122–138）每次讀真 SSOT 並做 CRLF→LF；`verify_package()`（217 起）以完整 revision/hash tuple 檢查，再以真 adapter 重建 definitions/request/derived。這些閘門必須保留。

第一個採納提交 A：SSOT、白話、唯一正典、批准收據與 P1 裁判；同時更新 `AXIOM_SHA256` 為批准 after 的 LF hash。新增一個明名的 `PRE_DECOUPLING_AXIOM_VERSIONS` 集合，只有上面的真實舊 current tuple，加入版本接受集合及以下六道年代能力豁免：section profile、source subdivision、stagger、parameter、infinite grid、finite grid。集合名可依正式程式風格調整，但接受範圍只能是已驗證的完整配對。

不能只更新最上方接受集合，否則舊包雖通過總版本守門，仍會在某一能力年代檢查誤拒；也不能刪掉年代檢查，讓更早的舊版本冒領它原本沒有的來源能力。保留全部既有 18 個歷史 tuple 與對應限制，不加入 revision/hash 混搭配對。

第二個提交 B：將 `AXIOM_REVISION` 改為 A 的完整 Git SHA。提交 A 無法知道自身 Git hash；不得猜值、用分支名或給目前未來 HEAD 字串。這是既有 `3ad8012`／`263235f` 採納慣例，參考 `geometry-core/panel-fill/plain-language.md:217–244`。

A 與 B 是同一採納工作，B 完成前不可發布／重啟產品服務、交付當前版本證據或凍結新 producer fixture。A 中暫時存在的舊 revision＋新 hash 不是真實已發行配對，禁止將它加入歷史相容集合；正式驗證、套件收據及版本報告以 B 的完整樹執行。

本輪純分層不得新增檔案格式、持久化 template ID、能力字串或 UI 選擇。`SCHEMA`、`PROFILE`、`CAPABILITIES`、現有 token 及生成器版本不因詞彙搬移而任意改動。若後續真正核心實作需要 generator version 變更，須單獨記錄合理原因，不靠改版本掩蓋幾何差異。

## 6. 舊包、見證與收據的更新邊界

### 模型包與完整專案

舊 `.json`／`.gcanvas` 原件一律保留；採納後用候選執行器讀原件，不把 manifest 改成新版本再測。至少讓 651c661b 舊 current 生產的真實包涵蓋斷面、來源子規則、交錯、參數、無限／有限網格；與 baseline executor 比對 geometry、typed refs、完整來源定義、diagnostics、能力、拒絕條號／代碼及原子世界不變性。

現有直接凍結舊 producer 的回歸包括 `tests/fixtures/model-package-main-a393a0f0.json`、`model-package-main-d1db88ae-profile.json`、`q38-legacy-space-model.json`／同名 `.gcanvas`；`test_engineering_model_compatibility.py` 及 `test_section_profile_modeling.py:338–399` 會真重建，後者只允許新產物的兩個公理版本欄位更新。完整資料盤點及未接線缺口由 fixture inventory 另列，不能把「149 個 archive 存在」寫成「149 個 archive 都重開通過」。

幾何未變時，definitions/request/derived、source/geometry hash 不應因 SSOT 說明變更而改變。舊包的 manifest 留下原 provenance；新建包才使用新 tuple。負控仍需拒絕未知版本、兩邊交叉混搭、重算 geometry hash 後偽造幾何、舊版本冒領新來源，以及開檔失敗時替換目前 context／World 的情形。

### 31 個正典見證

`geometry-guide/witness.py:98` 只確認條號存在；`_sha():133` 用於 fixture scene 的 LF bytes、截前 16 位；SVG `scene-sha256`（604）不是全篇 SSOT hash。manifest 的 31 項目前全是 scene 見證。SSOT 分層文字修改且條號不變，本身不應讓 SVG、接點 JSON 或 scene hash 改變。

以驗證過的候選核心執行：

```powershell
python geometry-guide/witness.py --check --exe <verified-temp-core-exe>
```

這會實際重跑場景並逐 bytes 比對 SVG／接點；若變動，先判斷 fixture、拓撲或幾何原因。不可先跑 `--build --force` 把差異洗掉。只有明確批准且可說明的圖形變更才使用 `witness.py` 重新生成；禁止手改 SVG 或 HTML。圖上的木工名稱及 gist 是這個木工案例的真實語義，不需要機械換成中性詞。

`tests/build_assembly_generation_witness.py` 只是既有 native placement 的三個 AR-06 提案見證，自己明示不是 assembly generator；它的 `sceneSha256` 亦不是 SSOT hash。不能拿它代替新的可獨立核心／模板隔離驗收。

### 歷史 rule-case 與 runtime 收據

`geometry-core/rule_cases/runtime.py:42–52` 的 executor identity 會納入真 SSOT `axiomHash`。採納後新執行收據自然帶新 hash，舊收據的 freshness 必須依 `refresh_receipt()` 判定，不能批量改寫舊收據的 axiomHash 使它看似新跑。`geometry-web/model_update.py:174` 同樣讀真 SSOT hash。舊 archive、rule-case provenance、reviewed evidence 的身分與重新關聯狀態保留；新 hash 不等於同一回驗證已重新做完。

## 7. 唯一正典閱讀器與必要驗證

在白話、SSOT 與 trace metadata 準備妥當後，只執行這三條正式命令：

```powershell
python geometry-guide/sync_axiom_reader.py
python geometry-guide/sync_axiom_reader.py --check
python tests/test_axiom_reader.py
```

三者不能互代。重建會執行 PatchLog；`--check` 只驗現有 HTML，報告 `patches: 0` 正常；41 個 reader 測試包括 byte-idempotence、批註保留、補丁及資料一致性。記錄實際 clauses/blocks/patches，不用舊 blocks／patches 數字作固定預期；條號集合本次仍應是同順序 204 條。

同步器必須以真 SSOT 解析 subs、blocks、clauses，並經五道 assert 與獨立 SSOT 對照；不能只讓兩份 JSON 相等。保留未變 block 的 identity、現有批註及原 sourceSnapshot；同步失去批註 anchor 時先處理，不得刪批註讓重建過關。不要自動 resolve 或認領歷史批註。

CLI 通過後仍要以真瀏覽器檢查桌面／手機：長 M 條文、原文／白話、搜尋、折返引用、hover 及固定參照、批註定位、見證圖、深色預設及 light 切換。§9 所列完整前言及 §四的原位同步是 P1 必做驗收，不能假設目前同步器已顯示它。確保新增文字沒有讓 DOM textContent/inline 算繪 assert 失敗；無需新增可見 UI 入口。

## 8. 最小回歸與完整收尾

先跑 P1 採納完整性與其負控、三個 reader 命令、31 個 witness check，再用 freshness 合格的 TEMP native binaries 跑下列現有 suites（本表是 17a25 清冊，執行時再讀 runner）：

| Suite | 既有發現數 | 用途 |
|---|---:|---|
| `py:test_domain_decoupling_proposal` | 29 | P0 裁判；遷移後的 P1 新測試必須另外記錄 |
| `py:test_axiom_reader` | 41 | 唯一正典與五道 assert／冪等 |
| `py:test_modeling_runtime` | 46 | 真 SSOT hash、18 模型向量、精確幾何及拒絕 |
| `py:test_modeling_transport` | 3 | CLI／HTTP 真 adapter、live World 不變 |
| `py:test_section_profile_modeling` | 20 | 斷面及真 Q38 舊包相容 |
| `py:test_space_modeling` | 40 | 保存空間模型 replay 與舊版本 |
| `py:test_modeling_degenerate` | 24 | 退化、精度與拓撲 |
| `py:test_witness_diagnostics` | 2 | 診斷見證 |
| `py:test_witness_marks` | 6 | 見證圖幾何節點檢查 |
| `py:test_engineering_model_compatibility` | 29 | 真舊 producer、版本年代限制、混搭配對拒絕 |
| `py:test_engineering_model_sources` | 4 | 工程來源閉包與獨立手算幾何 |
| `py:test_model_update` | 26 | 模型更新、當前 producer/公理身份 |
| `py:test_scenario_verify` | 37 | 隔離 verifier 與模型 replay |
| `py:test_rule_case_executor` | 40 | 原生收據、版本與 stale 狀態 |

上述數量已從 `tests/run_all.expected.json` 只讀確認，採納後如新增測試再按實際 census 更新。Windows modeling runtime 要給已用 MSVC 編成的 `GEOMETRY_MODEL_BASE`；transport 另需 `GEOMETRY_TEST_BRIDGE`。不能接受 BASE_COMPILER 遮蔽、skip 或 SAC 阻擋被報為功能通過。

完成新增測試後跑完整 `python tests/run_all.py`（需要時依 registry 先 build stale/missing binaries）。不能以 `--allow-skip` 或 `--only` 宣稱完整通過。`run_all.expected.json` 只有在完整跑可當可信 census 時，才用 `--update-expected` 明示更新並解釋增減，不能直接調小數字消除失敗。完整非瀏覽器 runner 不等於必要真瀏覽器／owner integration 已完成。

文字採納階段沒有 app.js 行為變更仍需驗閱讀器；後續真正分層改到 app.js，必跑 cdp_test，空間工作區另跑 space_model_test。完整專案相容性依 fixture inventory 選 baseline/candidate 真重開、凍結舊 producer、保存→全新→chooser 重開及 reject-atomicity，分層報告 static／VM／native／browser 證據，不合併成一個虛假的全過。

最終收據至少記：批准內容與基準 hash、A/B 完整 commit、當前 SSOT LF hash、生成器與 binaries/court 指紋、reader 三段原始 log、witness 逐檔比對、舊包／完整專案 bytes 及 replay 差分、正反控、實際測試數／skip／環境阻擋、尚未實作的核心介面項。條文採納、既有行為相容、實際 domain decoupling 三件事分別作結論。

## 9. 標題／詞彙斷言及一個閱讀器呈現缺口

獨立只讀盤點已完成，沒有執行測試或產品：

- `tests/test_domain_decoupling_proposal.py:147–191` 的 P0 status／current=before 守門，依 §3 正式遷移；保留 204 條、D69/I76/R59、四個章節、原順序、全部 before、Markdown/JSON 逐字一致與 M 原文尾段守門。不能移除 aggregate 註冊。
- `tests/test_axiom_reader.py:54` 要求 D1 含「D31 的參數值」；批准 D1 仍保留。`:551–554` 的 I23 `(a) 網格重宣告` 與末段不誤塞進 sub c 也仍保留。這兩個不是預期會壞的詞彙測試，不應自動刪改。
- `sync_axiom_reader.py:536–558` 的粗體 D／普通 I/R／尾字母條號及 `## 四、` 解析語法仍相容；批准標題自然重解析，無須放寬 parser。`:797–817` 的獨立 SSOT hash/body/plain/subs/line 驗證失敗時，要修同步與資料，不可只改 expected。
- **非條文呈現缺口及必做驗收**：`source_clauses():536–551` 不回傳前言，並在 `## 四、` 截斷；`validate()` 雖雜湊全篇 SSOT，卻只逐條驗可見 body。故目前三個 reader 命令通過並不能證明新的 K/M/W/H 前言及排除章 scope table 已可見。HTML title（1409/1430）是一般「公理層 · 文字 rN」，不是 SSOT H1。P1 必須讓完整批准前言及 §四在唯一閱讀器可見、可搜尋並由真 SSOT 同步；這是同步規範閱讀器的必要工作，不另開使用者選項或批准回合。下面固定最小原位方案，現在只提出接線，不實作。
- `axiom_matrix.py:234–238` 明說 coverage 是「被提及」而非「已實作」；見證 manifest 也只查條號與 fixture 引用。條號不變就不需要稀釋 trace/witness 守門，但現有綠燈不能證明新中性核心 API 已存在。
- `test_modeling_runtime.py:681–711` 的真 SSOT hash／CRLF 正規化／內容漂移 `AXIOM_VERSION / I32` 拒絕，及 engineering/section capability 年代測試，屬實質契約。只按 §5 授權更新 current tuple 與一個真歷史 tuple，不能放寬拒絕條件。

任何失敗都先分類為合法 metadata 同步、既有格式相容、或真實實作缺口，不以全文木工詞彙掃除作為通過條件。本次維護中的 Python GEO-261 suite 仍是 proposal-integrity；新 kernel API／固定模板注入的驗收必須另外完成。

### P1 非條文原位呈現方案

經只讀核對，當前 HTML 的兩個既有位置可直接取代，不需新入口：

1. `#reader-source-status`（正典目前第 151 行）是 `#document` 前的常駐短同步說明，桌面／手機皆可見。現文是「條文與白話已由目前專案來源同步；歷史批註保留原始快照。」將它由短 `<p class="hint">` 原位改為同 ID 的文件前言容器；從真 SSOT 的開頭到 `## 一、` 之前抽取完整前言，含批准 K/M/W/H 定義、固定注入、相容不變量及 204 條作用域清冊。舊同步／版本狀態短句合併為同容器最後的一條來源說明，完整規範本體使用正文排版，不沿用 hint 的小字。章一標題仍由既有 D 群組區負責，不重複成兩份。
2. `.page-footer`（正典目前第 4397 行）緊接 `</main>`，現文是「原文為準，白話輔助閱讀。桌面／手機共用同一份條文與批註；匯出新檔才會把修改帶走。」以同一 footer 原位顯示真 SSOT 從 `## 四、` 到 EOF 的完整文字：新責任層表及全部原 19 項限制均保留。將舊頁尾中的來源、白話非規範及必須匯出才保存批註的語義合併到上面的單一來源列，不保留第二份重複說明。正文用可讀字級；現有 CSS 把 `.page-footer` 設 12px，且列印樣式以 `display:none!important` 隱藏它，需用具名、scoped 補丁調整這個規範 footer 的字級及 print 顯示。

BACKLOG 的本次減項寫明：**拿掉原 `#reader-source-status` 與 `.page-footer` 兩份靜態重複說明，合併成前言末端一條來源列；既有兩個版面位置改由完整 SSOT 內容佔用，沒有新增按鈕、導覽項或常駐操作教學。** 兩個規範區塊不是新增兩個操作指示區；操作說明總量不因這次增加。所有文字留在長頁 DOM，不以折疊、分頁或切換代替；Ctrl+F 能直接找到層定義、作用域表與 §四限制。

實作位置只在 `sync_axiom_reader.py`：新增真來源區段抽取及渲染，於 `rebuild()` 對兩個既有位置做「先移除既有／上次生成區塊，再插入新內容」的資料式補丁，兩處各登記可見且唯一的 `PATCHES.expect_present(...)` 標記，例如擬新增 `data-ssot-section="preamble"`／`"exclusions"`。現有同步器 1635–1643 產生來源狀態且只辨認舊 `<p class="hint" id="reader-source-status">`，必須一起改為兼容首次舊 `<p>` 與下次新 `<section>`，不能留在尾端把新區塊再覆寫。footer 以 tag 與完整 `page-footer` class token 辨認，不能誤中 `clause-footer`；缺少或重複預期位置就明確失敗。不能以 `force()` 的舊新形狀判斷讓內容凍結在首次 hash。新增 CSS 用 `inject_css()` 登記。實際重建後確認 patches 計數包含新增標記，並再驗 byte-idempotence。

既有 `inline()` 只處理行內語法，不解析 Markdown 表格；兩區須有確定性的標題／段落／清單／表格渲染，再讓儲存格和行內文字經相同 inline 規則。不得把原始管線表直接當成已完成表格，也不可把正式文字只放隱藏 JSON 或待 JS 執行才建立的節點。新區段另記 source 切片與 hash；既有 `documentHash` 仍按明訂的 blocks 公式計算，不偷換語義。

`#document` 的重建（同步器目前 1580 行）會覆寫其全部子元素，不把非條文區塊插進去又期待下一次保留；上述兩個位置都在它之外。亦不要使用 `#static-note`：成功增強時 JS 會隱藏它，fallback 會改寫文字，export 還會切換，不能承載必須可見的規範。既有 204 條 clauses、計數、條文順序、批註 block identities 與五道 assert 維持。

新增的資料一致性驗收必須從獨立讀取 SSOT 抽出兩個完整區段，比對來源 hash 以及經閱讀器 inline 規則渲染後的 DOM textContent；表格需逐列驗 19 項、作用域與界線完整，不能只驗「K/W/H」關鍵字存在。新增負控：只改其中一個可見詞／表格格子、刪一個排除項、來源已變但保留上次生成區塊、只更新內嵌資料、複製一份相同容器，均要失敗。只修改非條文來源後也必須正確刷新，接著二次重建仍 byte-idempotent。真瀏覽器驗桌面／手機／停用 JS／列印預覽／既有 HTML 匯出後都可見、Ctrl+F 命中、跨條引用與原批註仍可用；不得用 `--check` 的 whole-file hash 代替這組呈現驗收。
