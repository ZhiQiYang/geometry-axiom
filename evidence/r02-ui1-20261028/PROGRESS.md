# R02 UI-1 進度

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
