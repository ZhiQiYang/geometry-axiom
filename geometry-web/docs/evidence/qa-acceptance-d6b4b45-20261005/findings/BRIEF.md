> 本檔是本輪派給各驗收員的共用守則原文(已做路徑清洗),保留以說明方法與紀律。

# 驗收 agent 共用守則(geometry-axiom 產品驗收,2026-10-05)

QA = <QA>

## 被測對象
- repo ZhiQiYang/geometry-axiom,main 完整 SHA `d6b4b450d741fcbbfd75c51631915d3082926990`,獨立 worktree `D:/geometry-axiom-qa`(detached)。
- **不得修改 worktree 任何檔**(會讓 /runtime 變 fresh:false)、不 commit、不改產品程式、不改測試。
- 環境用法:`QA/env/ENV-README.md`(建置、`start_server.sh <port>`/`stop_server.sh <port>`、`qa_cdp.js` API 與 JSON CLI)。開工先起自己的埠並跑 `python D:/geometry-axiom-qa/geometry-web/runtime_version.py --probe <port>`,存檔;fresh:false 或指紋不符=不得開始。
- 只用指派給你的服務埠、Chrome 偵錯埠、profile 目錄。只停你自己起的服務。
- 🔒(使用者 2026-10-05 指示)重編或清理時只能結束自己啟動、已核對 PID 與命令列路徑的程序;**禁止按程序名稱一次關掉全部 bridge**(Stop-Process bridge、taskkill /IM 等),不得動其他 worktree 的服務。22:25 bridge 全滅事件原因一律記「未確認」。不得碰其他服務、使用者瀏覽器、repo 的 feedback/。
- 產品地圖(讀碼得出的入口/選擇器/預期,是線索不是規格):`QA/product-map.md`。已知問題索引:`QA/known-issues.md`——判新問題前先比對;已知者標「已知 #xx/GEO-xxx」。
- 合成資料:`QA/env/fixtures/`(含 `fixtures.md` 的精確座標與真實尺寸)。repo 夾具 `geometry-web/docs/fixtures/issue54-public-rooms.pdf`、`tests/fixtures/issue77-two-rooms.pdf` 可當輔助。全部是合成/公開夾具,報告須標明「合成圖,未驗真實案場」。

## 操作紀律(最重要)
- 像普通使用者:只用正式 UI 入口操作(滑鼠座標事件、鍵盤、點正式按鈕後才給檔、處理 confirm 對話框=使用者按確定/取消)。
- `evalReadOnly` 只准讀 DOM/畫面文字/元素位置;**禁止**呼叫 app 私有函式、改 window 狀態、直接打 /api 改世界、對隱藏 input 直接設檔。讀 /runtime 與對下載的 .gcanvas 解壓檢查可以(唯讀)。
- 每一步**先寫下預期**(依 product-map 的規格依據/公理層條號,沒有規格就寫「依產品常識」並標明),再操作,再記實際。
- 截圖:每個關鍵步驟與每個問題都要截圖到 `QA/evidence/<你的代號>/`,檔名有序號與描述。收 console 錯誤與 pageerror。
- 桌面 1440x900 與窄螢幕 390x844 都要跑(窄螢幕至少跑主幹流程)。390px 只算響應式驗證。
- 保存:qa_cdp 預設 `fsAccess:'none'`,所以測的是「下載備援分支」,File System Access 原生對話框分支**未測**——報告要寫。
- 幾何正確性要比數字:頂點座標、邊長、凹角位置、方向(PDF 上方 vs 畫面上方、是否鏡像)、面積/體積、高度。不能只看「有沒有生成物件」。
- SAC 擋 exe(WinError 4551、「橋接器連線中斷」)= 環境阻擋,等 15 秒重試;持續就記「被環境阻擋」,不當程式失敗。

## 發現問題時
- 每個問題寫進 `QA/evidence/<代號>/findings.md`,格式:
  - ID(<代號>-NN)、標題、影響程度(阻斷主要流程 / 資料錯誤或遺失 / 次要體驗)
  - 環境(commit、埠、視窗大小、入口)
  - 最短重現步驟(編號,可交給另一個 agent 照做)
  - 預期(附依據)vs 實際
  - 證據(截圖路徑、console 摘錄)
  - 重現次數、對照組(例如換另一個入口/另一份 PDF 是否也發生)
  - 已知對照(known-issues 中的相關項或「未見已知」)
  - 原因追查(可讀碼:檔案:行號 + 推論;標明是「已確認」還是「推論」)
- **阻斷主要流程或資料遺失**:發現當下立刻 append 一行到 `QA/BLOCKERS.md`(代號、標題、證據路徑),然後繼續測其他不受影響的流程。
- 被環境擋住的與程式失敗分開寫。

## 交付
- `QA/evidence/<代號>/report.md`:四段分開——已實際通過(附證據)、失敗(指向 findings ID)、尚未測(原因)、被環境阻擋。
- 結束前停掉自己的服務與 Chrome;確認 `git -C D:/geometry-axiom-qa status --short` 為空。
- 回覆 ≤60 行,只有結論與 檔案:行號;長產物存檔傳路徑;禁止貼大段原文或原始碼。一律繁體中文。
