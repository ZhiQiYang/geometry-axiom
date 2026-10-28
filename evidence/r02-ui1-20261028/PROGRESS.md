# R02 UI-1 進度

## 目前狀態：2026-10-28 17:38 UTC

固定最新產品／驗收來源 F2：`74d638686edc9861e9ed9d3409af4adf02350f8e`（已普通push）。D44產品缺漏已修；不標READY，UI15仍未達合併條件。

- **五組真UI反證已完成**：來源F1 `a66b2022aa9603b5b2a6fc7b201d6b68a0d54bc6`，入口、preview HTTP、confirm回執、8mm預填、原生不足紅色各具名0／1／0。六份正向各377／0／0、五份指定紅、全部來源恢復；整輪1293.054秒exit0，raw hash逐項核收。不是F2重跑。
- 其後對抗審查發現來源準備的啟動競態：等待engineering-read時使用者真切另一面，晚回覆仍退出新面並開舊草稿。`0f37836d524c1314b26246b9d557110c21e2124a`真重現6pass／1fail、4.700秒exit1，具名UI05_D44_PREPARATION_OWNER；FATAL_UI保留focus=null、active=paramName。
- `a7a05ecf13076f0dcf5fd89d1ef6c8a9118ac836`修補在第一個await前綁request／navigation／focus，自己的導航只接受預期序號。真完整PF專項381／0／0、203.807秒、exit0；唯讀對抗審查無新增阻擋。F2僅再登記測試hash與P128=381，產品／測試相同。此新增修補的完整撤回／恢復仍在原獨立checkout進行。
- F2三原architecture裁判均exit0：604檔／798edges／0diagnostics，205與18 tests；Linux scan／receipt／report已更新。F2參數回執16／0／0、exit0。`mutate.py --check`仍exit0、0stale：70killed／1crashed／4equivalent／3retired，不把crashed算killed。
- F1 Node aggregate748＋PF契約21＋參數回執16＝785／0／0；不改標F2。F2與F1之產品差異僅上述共用參數建立owner守門；新版完整canvas將驗既有P76與新P128，原85段golden仍全等。
- 新版完整canvas**尚待執行**，將在來源守門反證收齊後獨占。舊 `82257ab8…` full為2616／0／0、86段strict matched、1906.993秒exit0（round6），不移標。
- native原完整census的5221pass／4fail／1允許GDI skip、exit1，及原三套修復763／0／0，分開保留。grid356／0／0、space242／0舊來源原件不移標。
- **UI15未跑／未達合併條件**：#343→#346→#347仍未閉合；WSL、實體IME／觸控、另一原生程序重開未驗。沒有修改SSOT、其他PR分支，沒有merge main。

round8包含五反證原件、來源準備競態原紅／修後與最新輕量裁判。為保存餘下原件，只回收本任務退役mutation cache內一份逐byte等於Git正典的PDF worker副本，實測釋出2,232,320 bytes；未刪原件／fixtures／Git objects／native ELF，詳D44_CACHE_RECLAIM.json。以下為歷史紀錄，不代表現在終態。

基底：`405f8c5e1a637a16cbe47470faf5ae1fa02b8676`。
工作分支：`codex/r02-ui1-panel-fill-20261028`。
唯一實作 owner 為本 Codex 任務；不修改 #352、#353、#354 分支。

## 2026-10-28 — 接線與隔離實作

- 讀取 #128 [採納 A](https://github.com/ZhiQiYang/geometry-axiom/issues/128#issuecomment-6436162095) 與[完整設計](https://github.com/ZhiQiYang/geometry-axiom/issues/128#issuecomment-6435620807)。
- 已核對 130 個 codex/grok/feat 分支的 production root JavaScript：209 個不同 blob，沒有 `panel-fill-read`、`/panel-fill/preview` 或 `PanelFillWorkspace` 呼叫；詳 OWNER_SCAN.json。不以分支名稱代替實作核對。
- 面內入口合併為「面設定…」；投影定義與建立空間仍可達。PF confirm 接共用可寫守門、requestId、確認 lease、history 及 definition-changed。
- 原生契約另列 UI-1 supportedActions、scope、精確十進位 wire 與 completeForScope；全域 `complete:false` 不變。保存以獨立、有限的 definition reader 能力核對三種記錄，不冒稱 PF 全功能。
- 保存單元與撤回自證已在獨立候選執行；真正原生／瀏覽器整合尚未完成，不能以單元綠燈代替。
- 原生 bridge/core/model-base 建置已啟動；表單及真 UI 測試仍在整合。此進度提交不是可用功能或驗收全綠聲明。

## 未達合併條件

#343 → #346 → #347 尚未同源閉合；UI15 未跑。#347 目前 head 為 `8bb0359331365c6f3a96872620427cf7847fcb50`，先前受測來源 `324034812bb6effca68e0413bc0468595337b317` 不能充當本分支整合驗收。

UI01–06、UI11–14 的正式真 UI 結果待後續收據。沒有執行的項目一律未驗；不將 CI 未派 runner 當產品紅綠。

## 2026-10-28 — 已執行結果與目前紅燈

Draft PR：[#355](https://github.com/ZhiQiYang/geometry-axiom/pull/355)。
第一批原件：[receipts-round-1.tar.gz](receipts-round-1.tar.gz)，逐檔 SHA256 見 [manifest](receipts-round-1.json)。起迄 UTC、完整命令、來源 SHA、環境及退出碼均保留於各 run 的 result.json／receipt。

| 執行來源 | 實際驗收 | 終態 |
|---|---|---|
| `1b63a0498bf941da5b83866d7234afb25d7aefb4` | 新 native 契約初輪 | 8 項，exit 0，無 skip |
| 同上 | finish-surface／layout／host／support 四套原生 | 92 項，exit 0，無 skip |
| `11217428a8ebe6fa255892c5919a18c0c43af62c` | 新增精確 X 後 native 契約 | 9 項，exit 0，無 skip |
| 同上 | 第一版完整 PF 真 UI 專項 | 59 項斷言，exit 0，0 fail／0 skip；真下載 `.gcanvas` 並於全新 BrowserContext 正式重開 |
| `b6ad7134e0743862effb503bce335abff3aa311f` | 擴充後 PF 真 UI 專項第 6 輪 | exit 1；候選已正確失效，但 Undo/Redo 後 dump 新增 host 卡片的 `canvas-pos`，尚待確認後場景刷新修復 |

保留的原失敗分類：Chrome 第 1 輪未啟動（0 斷言，額外執行沙箱問題）；第 2 輪 preview 暫停按鈕後焦點落背景，390px Esc 只關抽屜（產品問題，修後第 3 輪綠）；第 4 輪測試錯點背景主畫布 Undo（改為實際 faceUndoButton，斷言保留）；第 5／6 輪為上述 host 呈現同步問題，尚未標過。

Chrome 156.0.8078.73、Node v24.19.0。改用既有雲端執行器與獨立可寫設定目錄後 Chrome 原沙箱正常，未修改系統 mount／quota／安全設定。

目前處理：既有 host 編輯的 I8a 下游前後影響揭露；候選 frame／材料改動須顯示角材舊／新中線、長度、host、world pose。精確 X 已在較新表單呈現，新增真 DOM 斷言待跑。原生來源已固定，整份突變帳本重產中；不是完成結果。

下一步：收齊擴充案例與修復，完成三項必要 UI13 撤線及新增產品修復反證；最終架構三原裁判／完整 canvas 尚未跑。UI15 仍受來源鏈未閉合限制，不能把前述 partial 專項或跨 SHA 原件宣稱完整整合綠燈。

## 2026-10-28 UTC：真 UI 主流程與支撐見證

受驗來源 `2a2ded3d534a7632bbf292d89bce7efecf50101e`：`python3 /tmp/r02-browser-run.py pf`（原 CDP、Chrome156 原沙箱）154.619 秒，307 pass／0 fail／0 skip，exit 0。確認前既有宿主與角材前後影響、畫面 X=17/2、PF05/23/24、保存 fresh BrowserContext 重開均實跑；不是完整 canvas，也不是 OS 對話框／實體 IME 驗收。

基準7/8的測試前置失敗原件保留：背景重複 projection selector、相互重疊的獨立柱 fixture。已限定真 face inspector 並整組平移世界框架／障礙，原面內幾何與所有期望不變。表單／保存38單元 exit0。

全帳本首輪1851.084秒 exit2：core60已完成（52 killed／1 crashed／4 equivalent／3 retired）；bridge18在clone前置受阻，未冒稱已跑。已以相同HEAD的獨立clean worktree核完整source closure，原裁判不改，僅接續這18項。

下一步：補UI05三項明列生命周期與UI11已建角材完整保存比較；六組具名撤線、架構三裁判、完整 native／canvas。UI15仍未達合併條件。收據差額封包見 receipts-round-2.json；已完成原件不重跑或覆寫。

## 2026-10-28 UTC：固定驗收來源與三條架構裁判

UI基準10來源 `f7d8802cc7a01c76d35f173473cbe45a80165c89` 真349/0/0、198.350秒、exit0。新增專案切換與Undo、同id來源重建、晚A／新B交錯均通過；保存重開完整dump逐byte與references逐欄相同。仍是fresh BrowserContext／同原生服務，不冒稱另一原生程序、實體IME或OS picker。

固定受驗來源 `fdd94809e9e2bce05a7be5c1f6dbef6eae2bf92f`：原架構CLI exit0（604 executable／335 owned／269 exclusions，0 diagnostics）、test_architecture_contract 205案exit0、test_product_architecture 18案exit0。Linux scan／receipt與本片報告已更新，歷史PRODUCT-ARCHITECTURE.md完全保留。原85段golden保持相同；只加入實測P128=349，尚不代表full canvas通過。

六組UI具名反證已在上述F的獨立clean checkout啟動。bridge重產環境另查出：舊cache ELF嵌入不同checkout絕對路徑，來源指紋相同仍與baseline逐byte不同；原二進位相等守門正確擋下。保留原件，使用既有MUTATE_CACHE選項的全新隔離cache重產18項；不降低守門、不刪舊ELF。不把中斷與BLOCKED列為killed。最終check與native須使用同一已記錄cache。

下一步：收完六反證／bridge18，驗帳本新鮮度，完整native census與相關browser。UI15仍未跑／未達合併條件。

## 2026-10-28 UTC：六組反證與完整帳本完成

F `fdd94809e9e2bce05a7be5c1f6dbef6eae2bf92f`：六組真UI撤線均有各自具名紅並恢復綠（入口、preview HTTP、confirm回執、預覽焦點、I8a下游影響、確認後場景同步），13次實際CDP程序包含7次349/0/0基準／恢復及6次具名exit1；外層exit0、1544.301秒。獨立核收各CDP_RESULT、raw hash與還原產品bytes，見UI_FINAL_AUDIT.json。

原帳本78筆已全部重產（core60＋bridge18），在 `ffa22ad9245021c17c0a827847270bc5882cbb69` 執行 `MUTATE_CACHE=/tmp/r02-ledger-final-cache python3 tests/mutate.py --check` exit0：70 killed、1 crashed、4 equivalent、3 retired，stale0／blocked0／survived0。M20三次SIGSEGV另計crashed，沒有偽稱斷言殺死。18個bridge全部具名killed／恢復27methods，1017.946秒exit0；185份原始子程序文字／sidecar保存在封包內的original-subprocess-records.tar.gz。舊cache與失敗全部保留，沒有放寬裁判。

完整native已於2026-10-28 15:16:24 UTC從乾淨 `ffa22ad9245021c17c0a827847270bc5882cbb69` 啟動 `python3 tests/run_all.py --build --update-expected`，原2100秒守門、16MiB stack；suite完成即寫持久gzip tar。grid亦已啟動，至多兩項重測；fullcanvas等native結束後獨占。此段不是native/grid已過。

本收據暫由同owner的receipts分支發布，避免完整native執行中變更受驗HEAD；結束後一般merge回原PR分支。UI15仍未跑、draft／未達合併條件。
