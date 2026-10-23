# 真 query 診斷 fixed 階段：未成立的反證

本輪 outer／原workflow／Node 真退出均 1，227.787 秒，未超 CI。原 footer 為 P88 99、completed=false、failedAssertions=0，fatal 是診斷預條件未成立，不是原 refGuideMode 焦點逾時。不得當作原斷言突變自證，也不得因 failedAssertions=0 稱通過。

原 F13 來源前後乾淨，記憶體實跑的 P88 bytes 確為已審 v5（8106476b），helper bytes 未改。這是明列省略兩個 grid 模組的 P88-only 診斷，不是新 F 的正式 grid／canvas。原 stdout 已比原 receipt inventory 的 bytes/hash；55MB trace 的原 phase hash 保留，reviewer沒有再重 hash 整檔。

serial 7523 真量測點為 (293.75,602.5)，mode y580.5、parent scroll25。7524／7525 放回同一原 parsed JSON；7526／7529 真 stack 指向 paintQuery/query，node5696換5737，mode短暫y605.5、parent0；7533恢復parent25／y580.5。7534舊點仍命中 mode，沒有接續真 mousedown。因此只有重建與短暫重排已觀測，錯點及原 focus 紅未重現。目標這次 v5 stable barrier 在初始 read 被診斷 throw 後沒有走到，不能拿此相位判定修正有效或無效。

靜態可見 renderFaceInspector 尾端原 rAF 會恢復 saved.scroll，與25→0→25一致；「量測在parent0短窗、其後恢復25」是更精準但未證的假說。自然原紅的627.5座標沒有在本輪形成 measure→wrong mouse 因果鏈，不能倒推成已證根因。

候選不可變 v5 的靜審接受維持；新的正式3次完整canvas及grid仍待真F原裁判。root決策保本次紅燈，不人工位移或重抽。withdrawn／restored尚屬後續階段，終態只另加addendum，不覆寫本固定相位原件。
