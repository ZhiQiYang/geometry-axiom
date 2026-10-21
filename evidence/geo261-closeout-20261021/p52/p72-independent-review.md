# P72B 導航候選與外部探針的獨立唯讀審查

## 實跑後修正與 v2 複核

初版「暫停真 Document 再取舊頁條件」實跑未能建立控制：Chrome 未回覆舊頁 Runtime.evaluate，最後是 20 秒導航等待及 120 秒標記清理的雙重逾時。`p72-fixed-stale-first.log` 為 46 pass／0 fail／0 browser exceptions、completed false，命令 exit 1；這是 **invalid 控制，不算產品紅或突變 killed**。下方初版靜態審查保留為歷史，不能用它宣稱初版控制已由真 browser 成功重現。

已完整唯讀複核外部 `p72_probe-v2.cjs`，SHA256 `6884e80a843834630b777d2add24e1c07c12ccc33f075a18f02403256d0dfcbc`，實際 `sha256sum` exit 0。v2 不改產品候選、原 `settle()`、50 題、預期 World 或幾何；只改控制排程。沒有看到須阻擋其受控驗證的靜態問題。

- 第 91–103 行在模組呼叫 reload 時只登記延後動作，尚未發送真正 CDP；呼叫端此時等到的是驅動器排程登記完成。這是明示修改導航發送時機，不能稱為透明未改動 CDP、純網路攔截或自然 race 的完整重播。
- 第 110–114 行在仍存活舊頁實際求值完整原 expression，再讀 complete／oc object／connection ready，要求撤回原版 true 或候選 false。沒有替代原布林值。
- 第 118–124 行才真送 reload；新頁 app.js 暫停後須讀到專屬 marker、非 complete 及 oc undefined，才把先前的真實布林值原樣返回。控制設置不符合時是 invalid，不能當 killed。
- 第 83–86 行一攔到 app.js 就安排三秒後釋放，避免因之後求值不回覆而永久堵住。若求值直到放行後才回來，前置核對失敗仍應分類 invalid，不以它證明產品缺陷。
- `hold-navigation` 第 115 行始終不送真 reload，僅證明沒有本次新文件時，舊頁 ready 不能滿足候選且就緒等待有截止時間；它不是 Document 網路請求卡住的測試。第 56 行拒絕舊 `hold-document` 名稱，避免混淆。
- 第 152–157 行仍跑完整 P72B 並強制 50 題；正常及錯誤路徑保留來源／有效模組／工具 hash 與專屬 browser 清理結果。

本次再讀原始 log／receipt 的分類如下。受驗來源均為 R=`c87c6d90bd06552b7b7b04e0d2aa42fd56f65eb3`，工作樹乾淨；以下是讀取其他代理實跑收據，審查代理沒有自行啟動 browser。

| v2 跑次 | 已核對原始證據 | 判定 |
|---|---|---|
| `p72-v2-fixed-stale-first` | memoryPatch none；舊頁真 false → 真 reload → 新 marker／loading／oc undefined → app.js 釋放 → 50 pass、0 fail、0 exceptions，receipt exit 0，browser exited true | 有效正控制 |
| `p72-v2-withdraw-stale-first` | 只在記憶體精確撤回導航等待；舊頁真 true → 真 reload → 新 marker／loading／oc undefined → 原 settle 的 `ReferenceError: oc is not defined`；46 pass、0 fail、0 exceptions，receipt exit 1，browser exited true | 有效撤回突變 killed；不是一般斷言計數 fail |
| `p72-v2-hold-navigation` | memoryPatch none；舊頁 complete／oc object／ready 但原 expression 為 false；沒有真正 Page.reload send；精確 20000 ms expected-navigation 逾時，46 pass／0 fail／0 exceptions，receipt exit 1，無 cleanup timeout，browser exited true | 有效就緒等待期限負控制；不是 pending Document 測試 |

正控制來源及有效模組 hash 同為 `8cc65bb4b187ae7e49d4be83561ed1a4143618e9e229f29aa3d310da9770cab6`；撤回後有效模組 hash 為 `74746482cb5d5072ce019bc66aa57a4574b4610885809f91da8da85091cc7e7e`，等於初版受審原模組。這使紅綠差異可以定位於導航等待撤回，沒有同步弱化 World、幾何或檔案斷言。

正常跨第二服務 50/50、exit 0 是初版工具在 `4fe18b8b2afe79c44f8a293dcbeb119c43f0e22c` 實跑的另一份有效證據，與 invalid 控制分開。完整 canvas／native 仍未驗，不能由 P72B 正負控制宣稱可合併。原始 WSL P52-5／P68 病因及自然導航中止的完整時序仍未被精確重建。

## 初版靜態審查留存

當時結論：候選在靜態上能排除「舊頁已 ready」誤當新頁完成；保留原本 50 題、正式保存／重開與 World／幾何比對。初版探針設計沒有偽造條件回傳值，但其 Document 攔截可否建立預期條件，已由後續實跑判定無效；原靜態結論不是瀏覽器驗收通過或可合併結論。

## 來源及範圍

- 主工作樹分支：`codex/geo261-closeout-20261021`。
- 審查時主工作樹 HEAD：`7dae5f21c7ca401e660450d437e60ba566218da8`，`git status --short` 無輸出。
- 本審查只寫這份外部報告，沒有修改主工作樹、提交、推送或啟動瀏覽器／高負載工作。
- 分支及交付標籤 `20261021` 沿用使用者交接命名；本 runner UTC 日期為 `2026-10-20`。原始收據時戳不得為了標籤而改寫。

| 檔案 | 本次核對的 SHA256 |
| --- | --- |
| `p72-navigation-candidate.patch` | `5eb80e3dbd33da084097e21a52117316a4627c91cb67bac9b212223fe974fbbb` |
| `p72_probe.cjs` | `11f85b9f10e296ea4864d7a8d9a8e460a1fe9a2070b6ab5271756b1f13f230ae` |
| 原版 `geometry-web/grid_inspector_rename_test.js` | `74746482cb5d5072ce019bc66aa57a4574b4610885809f91da8da85091cc7e7e` |
| 既有 `geometry-web/cdp_navigation.js` | `64be1d676aec784f275a27f621b17a5e5440fdb4f56a0c786036b2e3708692ae` |
| 既有 `tests/test_cdp_navigation.js` | `e305750a057dca812a4e3a38db7e848f1bd7ef5e9e204e635ff8c89eec5e19c9` |

候選作者回報的候選模組 SHA256 為 `8cc65bb4b187ae7e49d4be83561ed1a4143618e9e229f29aa3d310da9770cab6`；本審查沒有落地候選模組，此值須再由實際執行收據核對。

## 逐項判斷

1. **舊頁就緒不能提早通過。** 原版模組第 109–111 行在 reload 回覆後只檢查 `ReferenceWorkspace` 與 connection，可能在舊頁取到 true，再於新頁執行第 18 行 `settle()` 時遇到 `oc` 尚未宣告。候選 patch 第 7–15 行先註冊唯一 UUID 的新文件腳本，再送導航；沒有要求在當前文件立即執行。既有 `cdp_navigation.js:30` 同時要求 UUID 相符、`document.readyState === 'complete'` 與原 ready 條件，並額外要求 `oc` 已存在。舊文件即使已完成，也沒有本次 UUID。兩處導航（開檔前與第二服務返回）均採相同策略。

2. **標記的生命週期合理。** patch 第 17–23 行在成功或失敗後均嘗試移除「未來新文件要執行的腳本註冊」。這不會刪除已載入文件上的 `window.__cdpExpectedNavigationMarker`，該值保留到文件被替換；下一次等待使用不同 UUID，不能被上一次值滿足。它不是專案來源，不進入原有保存斷言。探針第 91 行另有專屬 `__p72ProbeDocumentMarker`，此腳本註冊、Fetch 攔截及停用快取只隨專用瀏覽器結束清除；不是產品候選的清理行為。探針第 125–136 行目前會記錄 `exited`，且在 SIGKILL 後再有界等待；正常流程未確認退出會轉紅。

3. **不把一般錯誤改成重試成功。** `cdp_navigation.js:12–18、39–44` 只允許三種精確的 `Runtime.evaluate`／`-32000` 文件銷毀協定錯誤重試。JavaScript 例外、其他協定錯誤、socket 關閉及命令逾時仍拋出。既有 `tests/test_cdp_navigation.js:60–92` 有對應的同一錯誤物件斷言；本次只閱讀，沒有重跑。patch 第 16–23 行保留原錯誤，若清理也失敗，以 `AggregateError` 同時保留兩者；原本會由 cleanup 蓋掉導航根因的問題已修正。

4. **原有 50 題沒有弱化。** patch 只增加本地導航函式及替換兩段導航等待，沒有改任何 `check`、fixture、expected、World 比對、正式檔案保存／開啟、原 `settle()` 或 golden。原模組 50 題由初始 1 題、七組各 5 題、其餘 14 題構成。探針第 145 行載入完整模組，第 146 行再要求總題數與 P72B 題數皆為 50；第 159 行拒絕其他 suite 篩選。未看到以只跑剩餘四題代替完整 P72B 的情形。

5. **撤回控制定位的是頁面替換競態。** 探針第 87–117 行以 Fetch 暫停真實 reload 的 Document，先在仍存活的舊頁取條件值，再釋放文件但暫停新頁 app.js。第 104–107 行明確要求舊頁 complete／`oc` 為 object／connection ready，且實測值必須為原版 true 或候選 false；第 112–113 行要求新文件專屬 marker 相符、尚未 complete 且 `oc` 未宣告。最後回傳第 103 行的實際值，沒有覆寫 true／false，也不改 `settle()` 或產品輸出。這是人工控制時序的真 browser 重現；它不是原 full canvas 自然失敗的完整事件重播。

6. **來源與控制的限制有明示。** 探針第 41–43 行只證明導航片段唯一；整檔來源仍須核對第 61 行的 source/effective/harness/probe SHA256。第 51–53 行要求磁碟來源已含候選，才允許稱為「撤回」；在原版上直接跑 stale-first 只能稱原版重現。控制目前只用同服務 reload；第二服務分支必須另外跑正常 50 題。

7. **逾時範圍應精確。** 20 秒是 `waitForExpectedNavigation` 自身的總等待期限，包含 pending evaluate，不是整個本地 `navigate()` 的耗時上限。前置 `Page.addScript...`、`Page.reload/navigate` 及後置移除腳本仍沿用 `cdp_test.js:220` 的 120 秒 CDP 命令上限。探針第 59 行已依審查改為「候選的導航就緒等待期限」；收據與說明亦須保留這個範圍。

## 驗收要求與尚未完成的自證

以下各跑次須獨占執行、各用自己的服務與 browser profile，保留原始 log、完整命令、結束碼、來源雜湊及清理結果。不能只看到 exit 1 就宣稱 killed。

| 跑次 | 必須看到的結果 |
| --- | --- |
| 已落地候選，無控制 | 完整 P72B 50 題、0 例外、exit 0，正常流程及清理完成 |
| 已落地候選，`P72B_NAV_CONTROL=stale-first` | 舊頁實值 false，新頁 marker 相符／尚未 complete／`oc` 未定義，app.js 釋放後完整 50 題、exit 0 |
| 同一候選來源，`P72B_WITHDRAW_NAVIGATION=1 P72B_NAV_CONTROL=stale-first` | 收據明示 `withdraw-navigation`；實測舊頁 true；新頁前置條件成立；原 `settle()` 以 `ReferenceError: oc is not defined` 失敗、exit 1。控制設置逾時、其他例外或程序殘留不能算這個突變被殺 |
| 候選，`P72B_NAV_CONTROL=hold-document` | 舊頁實值 false；文件始終被暫停；精確出現 20,000 ms 的 expected-navigation 等待逾時、exit 1；不能把控制設置錯誤算成逾時自證 |
| 候選，另設第二服務 URL | 完整 50 題、不同 PID/session 的原斷言通過，返回原服務成功、exit 0 |
| 最終來源完整 canvas | 未縮減範圍、golden 全數完成、exit 0；P72B 單模組成功不能代替此項 |

`tests/test_cdp_navigation.js` 的既有輕量錯誤分類測試亦應在候選驗收階段執行，特別確認新增 cleanup 路徑不會使一般錯誤成為綠燈。

## 本審查實際驗證與限制

- `git apply --check /workspace/geo261-evidence/p52/p72-navigation-candidate.patch`：exit 0；只檢查 patch 可套用，未套用。
- `sha256sum` 核對上列五個實際檔案：exit 0。
- `git rev-parse HEAD`、`git status --short`：exit 0；HEAD 如上，當次狀態乾淨。
- 本次突變自證：尚未執行；只有控制設計及斷言守恆的獨立靜態審查。
- 未驗：真 browser 的 stale-first／撤回／hold-document、正常與第二服務 50 題、最終完整 canvas、候選落地後來源雜湊，以及 GitHub 最後一次推送後全部留言。
- 最不確定處：CDP Fetch 在此環境實際暫停 Document 與 app.js 的順序能否每次建立指定條件。探針對條件不足會明確失敗，因此這項不確定性會阻擋重現證據，不會自動被算成產品修復成功。
