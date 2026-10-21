# combined（#299＋#316）→ #314 只讀預審

這是後續列車的來源與設計預審，沒有實作、套補丁或驗收。#288 仍優先；正確帳本 L 到位後立即先處理來源綁定。本文不表示 #299、#316、#314 可以合併，也不替使用者決定公理或 HANDOFF §7。

## 固定來源與本輪界線

- 主樹分支：`codex/geo261-closeout-20261021`；本輪讀取 HEAD：`cd4ac98f44174729fb3a2f1c291c6c258c9a239a`。這是**未採用、未推送的歷史帳本 L1**，產品與架構仍為 A：`7159530c0e494d3211e6ab1764eb691137211707`。不把 L1 說成最終受驗版本。
- 交接來源：`handoff/codex-takeover-20261021`，commit `59796b1af9259eb23d30134c2ce5a56317a06091`。`/workspace/geo261-handoff/handoff` 是匯出目錄；本輪使用主 repo 的 `git show <commit>:handoff/<path>` 逐一對照 16 個來源，原 bytes 全相同。未合併交接分支。
- 草稿原基底：`09ab5f793e97a6be1a0a9e0c13d6ec7677d382e1`；交接所述重定基底：`546e2eb2142ebf19859489c5391b57cbb8413d10`。它們均不是未來 #288 合入後的 main。
- 已完整讀 HANDOFF、combined README 與重定基底補丁、#314 的 DESIGN（286 行）、TESTS（270 行）與補丁（90 行）。兩名支援代理分別完整讀 `_gen` 全 8 檔（1123 行）及獨立複核 #314 的三處語意，沒有執行它們。
- 只讀資料收據：`combined-314-readonly-check.json`；核對程式原文字：`combined-314-readonly-command-code.txt`。這兩份與本文都在 repo 外，不是新增產品／測試工具。

## 列車順序與範圍

HANDOFF:66–75 已指定：#288 合入 main 後，**只使用 combined 一份補丁處理 #299＋#316，再接 #314**；不能先後套兩個單獨補丁。仍依 HANDOFF §2 的 #323、framing、#322 等優先序安排，不提前把後續列車塞進 #288。

combined README:12 描述的是舊基底「先 #314 再 combined」的歷史套用檢查，還明說沒看語意衝突；不能當作指定順序的本輪證明。HANDOFF:69 所載兩補丁可疊、#314 在 `current_geometry.c` 位移 −34 行，也只是當時記錄。本輪沒有重新做 `git apply --check`。

| 草稿 | 靜態看見的變更 | 必須保留的契約與缺口 |
|---|---|---|
| combined：17 個目標檔 | #299 讓 W 邊界檢查傳回邊索引，延伸範圍診斷追加邊／區間／超出方向；#316 刪三個 H 死包裝與無消費者的 footprint 介面，增加不同面同 UV 的合法場景，補 M89–M98 | `V_EXTENSION` 前綴保留；實際 I11 placement 路徑與 M13 不得連帶刪掉；診斷要求同一條錯誤同時包含期待欄位，不能把分散字串拼成通過。刪介面前須在新來源的完整受管來源與工具消費者重新普查。 |
| #314：4 個產品檔 | `current_geometry.c` 接守門；H `subgrid_world.inc` 取提交基線；W `grid_application.c/.h` 比較前後系統、相位差與參數來源 | 現補丁沒有完整測試、舊檔夾具改造、M99 起登記、架構四產物、全量帳本與閱讀器同步，不能視為可交付成品。K 不改、P177 守門流量不改的主張仍待證明。 |

兩份重定基底補丁的目標聯集為 20 個路徑。唯讀 `git diff --name-only 546e2eb2142ebf19859489c5391b57cbb8413d10 HEAD -- <20 路徑>` 結果只有 `geometry-core/domain-decoupling/product-architecture.json` 改過。這表示目前其餘目標檔仍與該舊基底同 bytes，**不是**所有補丁錨點都已失效；但架構 manifest 必須按現行 611 輸入狀態處理，未來 main 或前置列車仍可能繼續改動，不能憑本次比較保證能套用。

## #314 的三處語意疑問與 SSOT 判定

### 一、來源改變與同筆改卡：多數可由現行條文釐清

DESIGN:256–265 的原文：

> 「條文只明寫一句：『改那張參數卡的值不算改相位差值』。我把它實作成『同一個 (卡, 欄) = 值沒變』。沒寫的有四種情形，我選了『比求值』，但它們都可以有別的合理讀法」

DESIGN:263 又說：

> 「同一筆同時換引用又改卡值。我拿『前一個世界的快取』對『這次候選的快取』，所以結果取決於哪個值先被算出來。這個情形我沒有找到條文可以裁決。」

`公理層.md` I24:1387 已明定「相位差值以該系統自己的相位差欄位求出的值為準」，並明排除只改所引用參數卡的值。D29:630–638 允許逐欄引用及明示解除為當下有效整數。因此直接值與引用互換、改指另一欄但求值相同，不應僅因 token 改變就判相位差值改變；草稿相應正例有條文依據，仍須通過既有 I8a 及逐軸合法性。

I8:1174、I37:1521–1523、R33:2256–2257 要求完整候選先求值，再驗 I24。前後世界各自完成求值後再比較，不能讓偶發快取更新次序決定結果。這是應證明的實作順序，並非可任選的新語義。對前後最終定義及有效值相同、且兩種順序均合法的候選，應證明結果不受偶發快取重算次序影響；具順序語義的操作依既定次序判定，不新增普遍可交換規則，也不把當步凍結直接值與最終參數求值混為一談。同一引用只改卡值的明文例外仍須保留。

DESIGN:265、278 所稱「兩軸舊檔只能凍結或收斂到一軸」，若漏掉上述參數卡例外便不完整；不能據此收窄 SSOT。`決策佇列.md`:650–662 已記使用者更正後採「只守提交，整體取代不檢查、不新增版本語法」，並同意最終 D10b／I24 文字，不能恢復已撤換的全面版本制。

### 二、提交邊界：語義已明定，接線與覆蓋尚未證明

DESIGN:267–273 的原文要點：

> 「判定靠 `g_subgrid_before` 與 `g_parsing_scene_file` 這兩個全域，不是候選的屬性。」
>
> 「沒有基線時我選擇『不檢查』……這是讀碼結論，不是測過。」
>
> 「條文 R56 說『加入既有 World 的匯入確認』是提交。我只找到一條對應路徑……如果還有別的……入口，我漏看了。」

R56:2521–2523、2536 明列單行、歷史群組逐行、批次確認與加入既有 World 的匯入；D61:1073–1075 明列整體取代，並把互動清空另列為提交；I24:1387 明免整體取代、隔離重放、復原／重做。這些分類不用再代決。

草稿 H 的 `!g_subgrid_before || g_parsing_scene_file` 早退，只在**所有真正提交都有有效基線、所有非提交都確實豁免**時才符合契約。缺基線不能自動等同非提交。須按完整入口清冊追到候選發布，分別驗單行、預覽確認、批次、匯入、內建場景、恢復資料、快照及回滾；新增入口也必須有分類。

DESIGN:94／138 已承認內建場景整體取代卻走逐行提交路徑。TESTS:216 的 C-6 只釘「目前內建場景沒有 stagger」，無法證明它依 D61 永遠是非提交。不能把目前夾具恰不觸發拒絕寫成分類正確；後續須讓被載入／被取代進來的內容包含合法雙軸系統，證明整體取代豁免，而非收窄整體取代的資料內容。僅起始世界為雙軸、取代後反而無雙軸，仍無法辨別錯誤的提交守門。

### 三、同筆與同份網格：同筆可澄清，同 id 刪除重建仍待審

DESIGN:277：

> 「『同一筆』我解成『一個 R56 提交』：一行指令，或一個橋接器批次；歷史群組內的兩行是兩筆。」

這與 R56:2521–2523、2536 一致。移除一軸並同筆改剩下那軸可按提交後狀態驗；歷史群組不能當成一筆批次。R60:2573–2574、D29:638 與 I24:1387–1388 亦足以釐清整卡換軸：不動相位差仍可提交，但必須按新節距重驗全部值域，不能新增「物理位置改變就禁止」規則。

DESIGN:279 的原文：

> 「『同一份網格』我按系統 id 比。同一筆批次裡『刪掉系統 5 再用 id 5 新建』會被當成同一份（與 D60 的『刪除後同鍵重建 = 新存在期』是兩回事）……這是更嚴格的方向，沒有漏洞，但跟身分帳的語意不一致。」

這段有兩個不能直接採納的前提。D59:1050–1054 的七類受涵蓋物件**沒有 grid-system**，1049 又明定記號不參與幾何驗證；不能把 D60 的存在期結算直接擴張到網格。其次，若原系統雙軸、同批刪除後同 id 重建且兩軸值相同，草稿按 id 對照會放行；若按 I24「新建」處理則拒絕，前者比後者寬，不是草稿宣稱更嚴。

**尚未定案的具體問題**：上述同一批次的刪除重建，在 I24 比較中是否算新建系統。現有來源足以指出草稿論證有誤，尚不足以在本輪自行新增刪除追蹤／網格存在期，或宣告現按 id 邏輯已獲授權。實作前須將這個具體前後世界與預期結果送語義複審／確認。HANDOFF §7 的其他使用者待決事項完全未處理或代決。

## 編號、夾具與 P72B 50 題

HANDOFF:71／74 的規則優先於 TESTS:22／234 的舊「M89 起」、228 的「會動 golden 與測試數」。combined 已安排 M89–M96（#299）、M97–M98（#316）；#314 從 **M99** 起，再以真正合入基底的完整清冊檢查無撞號。本輪主樹只有 78 個定義、最大 M88，不代表可把 combined 預留的編號重用。

P72B 正式 golden 是 `geometry-web/cdp_sections.golden.json` 的 `sections.P72B = 50`（77 行）。本輪 hash 為 `0ba98dde2ee69d342eb7efc76b86b858e17835437d6e63290fecb546ff72f041`。不得改成 48／新增 skip／修改 golden 來容納守門。

`geometry-web/grid_inspector_rename_test.js` 的兩組雙軸夾具現在在 59／62 行，並非 TESTS:228 所指 36／39；fixture 的互動 `line` 入口在 23 行。後續只把這些舊雙軸前置世界改走合法載檔／整體取代路徑，保留 rename、undo／redo、跨進程載回與現有斷言。A 已修的導航新文件 marker、complete／ready 等待與 20 秒上限仍須保留，不能以舊整檔覆蓋回去。上述只是設計要求，本輪沒有改夾具或跑瀏覽器。

TESTS §7 的 MS1–MS9、MP1–MP4 仍只是候選突變。尤其 MP3 不能因草稿寫「單獨不會紅」就直接登錄 equivalent；須有真基線、單撤回、組合 MP1＋MP3、還原，以及可達性證據。MS2 的早退撤回是否真的抵達目標路徑也須實跑。該文件的 L1–L14 是「舊檔測試案例編號」，與本次未採用帳本 L1 無關。

## 產生器的具體風險

| 位置 | 只讀發現 | 正式執行前要處理的事 |
|---|---|---|
| `build.py`:8–22；`verify_all.sh`:17 | 只產生 299、316、all，沒有 #314 產生器；build 還會刪除輸出目錄再寫檔 | 不宣稱設定 BASE_REV 就能重產整個列車；#314 測試與路徑普查仍須完整實作。 |
| `fetch_base.sh`:5–25；`checks.py`:15–16；`reader_impact.py`:17–18 | 預設 `D:/geometry-axiom`／09ab5f79，固定擷取 18 檔、不清舊 base、不存來源清單；build 自身只讀同目錄 base | 明指定新基底與 repo，重新擷取完整來源、保存 SHA／檔案清單及工具 hash；不能只改環境變數後直接 build。 |
| `checks.py`:43–46、149–152 | problems 只累積並列印，沒有失敗退出碼；migration 數量只列印 | 不把外層 exit 0 當檢查全部通過。 |
| `verify_all.sh`:12–13、19–43 | 無 `set -e`／`pipefail`，pipeline 可掩蓋失敗；apply-check 失敗只印 FAIL 並繼續；blob mismatch／順序衝突不強制失敗，最後 unset 可回 0 | 正式工具需逐步保存命令／stdout／stderr／退出碼並失敗即停；本輪沒有執行或修它。 |
| `verify_all.sh`:16 | 假定 `.git` 是目錄，直接引用 `.git/objects` | 不適用 linked worktree 的 `.git` 指向檔；須透過正式 Git 路徑解析再隔離工作，不依 D 槽絕對路徑。 |
| `checks.py`:55 | `re.fullmatch(r"M\d\d", id)` 只收兩位數，M100 起會漏掉編號／錨點檢查；`reader_impact.py`:53 已用 `M\d+` | #314 從 M99 延伸會跨 M100，必須先修正盤點工具並自證漏登記會失敗。 |
| `edits299.py`:126–150、344–360；`edits316.py`:227–283 | 固定 M89–M98、M88 表尾、migration 28→36 再加 2、core 165→166、contact_world 10→9 等數字 | 這些是舊靜態產物值；新基底須獨立重新盤點，不能為跑綠回填計數。 |
| `lib.py`:13–18、30、40–44、62–65、145–150；`edits316.py`:98–143 | 產品以原 bytes 與 surrogateescape 保留 CRLF；部分定位依完整 CRLF 行與固定文字；checks 卻先正規化 LF | 保留 `current_geometry.c` 的 CRLF，不以全檔轉行尾掩蓋錨點失效；精確匹配失敗應重新審補丁。 |
| `edits299.py`:358–360；`edits316.py`:282–283；`reader_impact.py`:27、40–50 | 只改 manifest 部分識別詞，未重產架構其餘三檔；reader impact 用基底 axiom_matrix 的 code_sites 讀單一 current_geometry.c 與根場景 | 不當作完整拆檔來源追溯、架構收據或正典閱讀器同步；正式管線另跑。 |

## 之後可採用的實作與驗收順序（尚未執行）

1. #288 完成使用者 PR 操作並合入 main 後，依 HANDOFF §2 推進前置工作；固定實際新基底，重查兩份草稿的來源／消費者／錨點。只採 combined，不把交接分支合入。
2. 將本報告三處語意分成可按現行 SSOT 落實的部分，以及同批刪除重建的具體待確認部分；後者在釐清前不實作未定案行為。
3. 修正／替換產生器的失敗退出、基底記錄、worktree 路徑與 M100 盤點問題，保存實跑工具 hash；補 combined 與 #314 的完整測試和反控制，不執行未審查的刪目錄腳本。
4. 維持 P177 流量與 P72B 50 題，改舊雙軸前置世界的建立途徑並保留既有結果。完成正反例、逐入口分類、單撤回及還原證據後，再固定產品／測試來源。
5. 重產架構 manifest、scan、report、receipt 四檔並做真驗收與登記反控制；照 HANDOFF:72 執行唯一正典 `sync_axiom_reader.py`。AGENTS:164–176 要求同步、`--check`、`tests/test_axiom_reader.py` 各自執行，僅 `--check` 不證明重建、補丁或冪等。
6. 按固定來源完整重產全部 mutation 帳本與 bridge 裁判，再跑七項整合及適用的 Q38、§7 等正式要求；預設編譯命令環境要與正式 `--check` 一致。不得複用 #288 的帳本證明後續 C／測試更動，也不得把 execution.head 改成帳本提交 SHA。
7. 保留來源、帳本、整合受驗與文件交付各自完整 SHA、精確差異、命令及退出碼。PR 開立／正文／留言／合併仍需先寫成分支上的可審閱檔案，回報逐項列出使用者應在對應 PR 執行什麼；本次沒有新增此類外部操作。

## 驗證紀錄、未驗範圍與最不確定處

本輪輕量來源核對可重現命令：

```sh
python /workspace/geo261-evidence/combined-314-readonly-command-code.txt
git -C /workspace/geometry-axiom diff --name-only 09ab5f793e97a6be1a0a9e0c13d6ec7677d382e1 HEAD -- 公理層.md 決策佇列.md
git -C /workspace/geometry-axiom diff --name-only 546e2eb2142ebf19859489c5391b57cbb8413d10 HEAD -- 公理層.md 決策佇列.md
git -C /workspace/geometry-axiom status --short --untracked-files=no
```

來源核對的等效 `python -c` 實跑退出碼 **0**；16 份交接原 bytes 相同、20 路徑聯集已列入收據、P72B=50。兩組 SSOT／決策檔差異查詢退出碼皆 **0** 且輸出空；本輪讀取後主樹 tracked 狀態仍空。最初只讀盤點誤取 golden 根層 `P72B`，退出碼 **1**（KeyError）；改讀正式 `sections.P72B` 後重跑為 0，不是產品測試失敗，也未修改 golden。匯出目錄本身 `git rev-parse` 曾回 128，隨後改用主 repo 中固定交接 commit 的 blob 完成來源核對。

**沒有執行**：生成器、`git apply --check`、補丁套用、編譯、任何產品測試／瀏覽器、突變／還原、架構驗收、閱讀器同步、完整帳本、效能測量。沒有改主 repo／交接來源、commit 或 push；沒有本輪產品突變自證，表中候選突變不可報成已 killed。

最大不確定處是 I24 對同批刪除後同 id 重建的認定；第二是兩個 H 全域是否確實涵蓋每條提交與非提交路徑，須動態證據補足。草稿「無可感知效能增加」亦未經本輪量測，不能替使用者放寬 P-186／P-189 門檻。

## 原始來源 SHA-256

下列均為原 bytes 雜湊。SSOT 另依 AGENTS 的規則先 CRLF→LF 計算，結果為 `7794a7782ea87347c8b1b2f3721287c954ee3a3fa74caab570f87f066d1f892d`；本次 Linux bytes 本來即 LF。SSOT 與決策檔在 09ab5f79、546e2eb2、本次 HEAD 之間均無差異。

| 交接相對路徑 | SHA-256 |
|---|---|
| `HANDOFF.md` | `6404126064a169e685b8774c447f96b3ebbdf02e3e1278042d7881ebfa5965c0` |
| `drafts/combined/README.md` | `59445468623593e1f8b612f3297d13c29c81017dab9bb0c1ad1d7b0947e4bcd3` |
| `drafts/combined/patch.diff` | `7ca70ab90fb245a8d2de01a2410ff68af00a743e76767e773d1dbf3bf03ea702` |
| `drafts/combined/rebased-546e2eb2/patch.diff` | `422946025137ba719ef4e42da1a527ba5bc07bbf8e52b28e687392061074fef6` |
| `drafts/issue314/DESIGN.md` | `c7ecdea31d56215dd170d529ed790b3aa4fa6f418194aaea42c4a148fa5f2e7d` |
| `drafts/issue314/TESTS.md` | `04ada3ea10bcfe1a9c1f483877d8b649164df913412bbdca913d19a35300f729` |
| `drafts/issue314/patch.diff` 與 `rebased-546e2eb2/patch.diff` | `925434e75085d82501326784079b9413c2b6ef342387d7a863711b1b10295e61` |
| `drafts/_gen/build.py` | `4ed66e952bd43d3319dafc198f43563cf2de2a515e93ddf578846d3075c13b75` |
| `drafts/_gen/checks.py` | `93bc60bf0f8a9455fa1bd75b4874cfc943133337182190f1fc7fac1a4a8f5d50` |
| `drafts/_gen/edits299.py` | `c64cc6c77e89763ee849f144e43b1373cb9e185947cdbc4324213be42a3a4b96` |
| `drafts/_gen/edits316.py` | `7e79b701122fbf45155d7af8607a2a7b61f3454a4bad0e53d3cdf700e9ad4c64` |
| `drafts/_gen/fetch_base.sh` | `51ada3c98f3434c3f1a19797208ff2da12c3f74850d124aa687c6a31222409e1` |
| `drafts/_gen/lib.py` | `5da605c803ee2fad1c863defe90dbb4a18810c8ba8399f8b6f11c8029310ca00` |
| `drafts/_gen/reader_impact.py` | `44e4d088f813664ae5142e923612a81263c01c1db8e26567c6159c75fd21f4cb` |
| `drafts/_gen/verify_all.sh` | `f814dc8fa6a2c49e40f7034d678604c59540ed799a3f387f6aaaeacf6bef73ab` |

本輪主樹參考檔：`AGENTS.md`=`d3fcb30f0e711a4130f032a2ae8edab70c0cd69897c37ae504cd5f3416d3cbca`；`決策佇列.md`=`c3387507597afafbdf1962b5374d5cfd8187165e6638b7b33c92bb3f794d9f72`；`geometry-web/grid_inspector_rename_test.js`=`8cc65bb4b187ae7e49d4be83561ed1a4143618e9e229f29aa3d310da9770cab6`。
