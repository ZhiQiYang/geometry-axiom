# 收尾時仍需外部證據的精確邊界

2026-10-08 唯讀核對；文件基準 `1eb6ccbbef58e4c94c2f3a377db95cfd2dd848e8`。本頁把可完成的規格工作與歷史缺件／平台條件分開，不能拿此頁當新 head 的功能通過收據。實作及發布狀態由最終整合矩陣另行核收。

規格工作已提供具體結果：[PF-0 逐條差異](../geometry-core/PANEL-FILL-AXIOM-DIFF.md)可直接審閱；[#87 的既有契約與驗收邊界](ROOM-MULTI-CANDIDATE-IMPLEMENTATION-BOUNDARY.md)不新增公理，可在既有授權內實作。這兩件不要求重新提出 Q38、Q39–Q47 或 Q37 已決方向。

## 1. 原十項與舊 155 項

本次檢查已知專案 archive 的 member 清單、原始 receipts、可用 Git refs 的同名歷史路徑，以及專案 scratch／TEMP 中精確歷史腳本／fixture 檔名。沒有讀取憑證、私人 PDF 或 browser profile 資料；未連入使用者 Windows 檔案系統，搜尋結果不能代表那些裝置上也不存在。

| 範圍 | 找到的原件 | 仍未找回 | 本輪處理結果 |
| --- | --- | --- | --- |
| PR161 十項中途操作保護 | [PR161](https://github.com/ZhiQiYang/geometry-axiom/pull/161)的歷史說明與 TEMP 位置記載 | 原 guard-qa 腳本、十筆逐項 census、原命令／exit／runtime 前後收據；第十個 case id | 不能聲稱復原。現代測試應保留自己的 case id／oracle／harness hash，不為湊十項發明原稿 |
| 舊模型庫 155 項 | `historical/model-a49d/ui-settled-v2/ui/` 的 gate.log、receipt.json、runtime-before／after；155 個 pass:true 與 COMPLETE 155；實際受測 a49d2a5 | `browser_ui.py`、原 results.json、初始 World／修正後 World／diff／diagnostic 完整前序 | 原通過收據保留原 head；不能從文字回憶補造可重跑版本 |

原收據在 repo 的[歷史 archive](../tests/release-evidence/20261007/evidence.tar.gz)，SHA-256：`e06116c9c536e083256cb869c811c8bfbfa849841d4ed52177f52a57befc695e`；內部 prefix 為 `geometry-release-evidence/`。這個同一 archive 另有 A/B lifecycle 82、workflow 34、cases-app 76 的歷史驗收，**不能因十項／155 缺件把其他現存收據也寫成未驗**。

2026-10-08 新 35／33 項、native 80 suites、基準 CDP／Space／timber 的原始結果見[先前收尾摘要](../geometry-web/docs/AUX-REVIEW-20261008.md)，保留 `bc1f6fe`／`751471e` 的實際來源。完整外部包 `geometry-closeout-evidence.tar.gz` 的 SHA-256 為 `748086c26aaad1430f1bbd5052ccb41404ce85cb7c28124123519a7d75176375`；已交付，但不假裝已放在 GitHub 可下載位置。

[issue166 的有界 oracle 補強](https://github.com/ZhiQiYang/geometry-axiom/issues/166#issuecomment-6052946184)是本轮另行處理的當前工作。它不復原十項／155；修改哪支 harness，就為哪支保留新的負控制與完整 gate 收據，不能借舊的 35／33 數字宣稱新 oracle 已跑。歷史缺件保留為追溯限制，不無限重開已核對的同版項目。

## 2. Windows、實機、IME 與 OS picker

| 未驗範圍 | 現有證據能說什麼 | 要結案時必需的最小外部證據 |
| --- | --- | --- |
| Windows P70 拖曳及 390px P88 規則線 | 原 c0e58e2f 的兩次 Windows 嘗試都在 P70 拖曳不變處中止，P70 是當時失敗；未到 P88。舊 #134 的 390px 2／4 失敗與後來 Linux 全 CDP 成功各保留原 head | 在 Windows exact head/fresh binary 專用服務分開核 P70 與 P88，記真拖曳前後cx/cy、規則控制 rect／hit／焦點／scroll；不靠force click、無限重試或增加delay補綠 |
| Windows GDI／SAC | Linux native aggregate 的具名 GDI skip 不是 Windows pass；既有 identity 修復不等於該機驗收 | Windows fresh native／GDI harness 實際命令、exit、binary 身分；SAC 啟動結果照實，不更改系統安全設定 |
| 真手機觸控 | Linux 390px 是虛擬 viewport | 實體裝置型號／OS／瀏覽器、實際雙指縮放與操作紀錄；不能以桌面emulation替代 |
| IME | composition／repeat 的程式守門可在Linux核驗 | 真 IME 組字／候選選字／Enter 流程，確認未誤提交；記平台與IME種類 |
| 原生 OS Save picker | 新 gate 的真下載可證下載備援；stub可證 activation／取消／失敗控制 | 真瀏覽器使用者手勢打開 OS picker，成功／取消／拒絕或寫入失敗後的保存狀態與檔案核對；stub不是此驗收 |

本次可用環境是 Linux＋`/usr/bin/chromium`；查無 powershell／pwsh、Wine、adb、idevice_id，已安裝工具中未有 browser/computer/Windows/device 遠端執行入口。因此沒有可直接執行上述外部案例的現有通道；這不代表使用者沒有那些裝置，也不需要要求重傳私人圖。

## 3. Hosted CI：有 repo 權限仍不等於帳務已解除

唯讀回查 [run 37709064278](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/37709064278)，head `bc1f6fe`、attempt 1、completed／failure。七個 jobs 的 steps 均為空，七份 annotation 均含：

> The job was not started because recent account payments have failed or your spending limit needs to be increased.

所以此 run 沒有執行遠端產品測試；不記成程式紅燈或 CI 通過。Repository API 顯示有 pull／push／maintain／admin 等權限，**這不能推出帳務權限或授權調整付款／支出上限**。未查閱帳務／付款資料、未重跑此已知受阻 run、未修改 workflow／標籤／帳務。正常後續 push 若产生新 run，最終矩陣須記其新 id、head 與實際 jobs，不沿用此 run 當新版結論。

## 4. 最小交接物

- Windows／裝置 owner：上表逐項的 exact head、命令、版本／binary 身分、實際輸入、前後狀態、exit 與原始畫面；只填確實執行項目。
- 歷史原作者／保存處：若原 TEMP 原件日後仍可取回，按原 bytes／hash 收錄，不重新命名新腳本為舊檔；找不到就保留本頁的有界未回收結論。
- 整合 owner：PF-0 差異採納狀態、#87 新 gate、#166 受影響 gate、每個獨立 PR 的實際 head／來源覆蓋，以及最新 CI 各自列明。PR 數量不是未完成的功能數。

本輪機器可讀唯讀核對另交付 `historical-evidence-audit.json`：包含三份 archive 雜湊／匹配 member、155 原 receipt、目前工具能力、七個 CI jobs／annotations 與權限讀取範圍。它沒有替任何產品工單關單、核准合併或宣告部署。
