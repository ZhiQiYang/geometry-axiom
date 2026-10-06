# T4 驗收回報(流程8 保存 → 全新環境重開)

> 由主迴圈依 T4 最終回覆存檔(T4 寫報告檔被擋)。合成圖,未驗真實案場。main d6b4b450d741fcbbfd75c51631915d3082926990,埠 8834;保存測的是下載備援分支(File System Access 原生對話框分支未測)。已寫檔:`roundtrip-table.md`、`*-capture.json`、截圖、`downloads/*.gcanvas`(12 個)。

## 中斷復原
- 22:25 前後 8834 bridge 消失(放置面時「橋接器連線中斷」),原因未確認。probe fresh:true(`probe-8834-after-interruption.txt`,session <session>,bridge 子行程在);之後每次重啟 `probe-8834-fresh-restart{,2..5}.txt` 皆 fresh:true、root D:\geometry-axiom-qa。
- 中斷前專案整個作廢,22:27 起以正式 UI 全部重做;本報告所有結果皆為中斷後重跑;保存→重開也都在重跑之後。
- 只用 stop_server/start_server 處理自己的 PID,未按名稱殺程序;worktree status 為空。

## 已實際通過
1. 完整專案:匯入 A3 PDF、校準 5000、ROOM_A 5000×4000(候選 4983×3983 → 以核對尺寸寫入 5000/4000)、ROOM_L 6000×5000 缺右上 2000×2000(PDF 端點吸附+鍵入長度)、兩面放置、L 形牆高 2700(70.2 m³、牆 6.048 m³ 與手算相符)、A 形 60 m³/5.52 m³、無限網格、配置綁面1 頂點3 cell(0,0) 並套用承載面、子網格 cell(2,3) u×3 v×2、參數卡 寬915/長1830 綁到網格 u 間距。
2. 保存:manifest geometry-canvas/10;sources/ 內 PDF sha256 7bf8a34b… 與原檔相同;校準點/5000/mmPerPx 在 source-rooms/2;models 2 個;「保存」與「另存新檔」兩檔 world.scene/manifest 位元組相同。
3. 全新 profile+重啟服務:先確認預設世界、無恢復資料;正式「開啟專案」(38 s)後逐項對照 22 項全一致(roundtrip-table.md):PDF 底圖/校準、輪廓與凹角方向、空間模型面數/牆高/體積、網格/子網格/參數、卡片相對位置。pre-capture.json vs post1-capture.json 僅差狀態列/tooltip/游標讀值。
4. 第二輪:改 ROOM_L 邊 6500(鄰邊同步 2500)、再建空間(82.5 m³、牆 7.02 m³ 相符)、Ctrl+Z 一步只撤空間模型(3→2),再 Ctrl+Z 撤邊長,校準/房間不受影響,Ctrl+Y×2 還原;再存 → 全新環境重開仍完整;第三代(手機重存)與第二輪檔 world.scene/manifest 位元組相同。
5. 對「開啟專案」Ctrl+Z:回預設世界並提示「已復原:開啟專案」,Redo 2.5 s 內整份回來(含 3 模型)。
6. 守門:外環草稿中保存 → 拒絕「外環草稿尚未套用…」無下載;校準已選點未套用 → 拒絕「校準尚未套用…」;dirty 時開別檔 confirm 取消=世界不變且不開選檔,確定=替換成功;損毀檔 4 種(非 ZIP/截斷/PDF 竄改/world.scene 竄改)皆拒絕且世界不變;examples/space-model-v1.gcanvas 可開(65 s,3 模型)。
7. 同分頁重新整理:自動恢復完整(名稱、2 模型、底圖),但約 35 s 內畫布不可編輯;與正式開檔分開記錄。
8. 390×844 全新 profile 開同檔:無橫向溢位;保存鈕僅圖示 44×44(aria-label=保存專案)可用且下載成功;抽屜/空間庫/面內底圖(校準 5000 mm、ROOM_A 標籤、網格)正確;console/pageerror 0。
9. 加測:十邊樓梯形(14 m²)含牆預覽被拒 I33 SPACE_CAPACITY(21/16)並提示取消牆;取消牆後 12 面 42 m³ 建立,存 → 重開一致(format /3)。對應 #119「十邊保存重開未驗」,此合成案例通過。

## 失敗
- T4-01 資料遺失(次要;已記 BLOCKERS.md):走「以此底圖連續新增房間」(#77 路徑)後保存,manifest.faces=[]、format /10,底圖不透明度與鎖定未存;重開後 0.75→0.5、已鎖→未鎖(旋轉 90、X=120 有保留)。對照組:一般匯入路徑(format /1)有存 opacity 0.84/locked true/crop。預期依據 docs/REFERENCE-PROJECT.md:28。原因(推論):geometry-web/reference-workspace.js:1093-1098 manifestData 只在 g.pages.length 時才寫 faces。證據:downloads/t4-ulset-save4.gcanvas、ctrl-plain-import-op-lock.gcanvas、ul-reopened-face1.png。已知對照 #77。
- T4-02 次要:新增房間(ROOM_L)後第一次按「← 物件畫布」落在面 1 工作區,要按兩次(2/2)。同 T3-01。
- T4-03 次要:面內「顯示全部參考線」計數同場景 21/21(保存前、開檔後)vs 20/20(重新整理恢復、Redo 開檔),原因未追查,信心中低。
- T4-04 次要:截斷檔訊息為英文原始例外「invalid zip data」。
- T4-05 次要:確認/放置後 toast 顯示核心原文(boundary 1 outline … / placement 1 on …)(s016-roomA-confirmed.png、ten-02.png)。同 T1-04/T2-02/T3-04。
- T4-06 次要:面內工作區 DOM 有重複 id(placeOX/placeSubmit/edgeLength0… 兩份)。
- T4-07(環境/負載,原因未確認):CPU 94–100%(他人負載)時開 3 模型檔偶發「未能完成開啟專案:signal timed out」(世界不變),8 次中 3 次失敗、重試成功;reference-workspace.js:1212 等處為固定 30 s 逾時;模型逐個驗證 15–45 s。非確認的程式缺陷。

## 尚未測
File System Access 原生保存分支;真實案場 PDF;多頁/加頁 PDF 與 crop 非預設的保存;iOS 實機;asymmetric-ten.pdf 實檔;Edge。

## 被環境阻擋
22:25 bridge 消失(見上);其餘無 SAC 阻擋。

## 其他觀察(非缺陷)
預設放置(天花 u+x v+y)與編輯圖 v↓ 相反,3D 俯視把 L 缺口翻到右下;空間建模內有提示與「依原圖對齊放置方向」鈕,按後缺口回右上(GEO-244 設計,可發現性風險;另見 V1 複驗)。ROOM_A 在建立網格配置後出現「基準或邊界變更·需複核」並隨檔保存(觸發動作未釐清)。
