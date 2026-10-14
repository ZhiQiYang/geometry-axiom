# PF-2 R10 E1/E2：進度證據

看板指定任務15，base main 79412a858f712981fa0ba15a6b293c3e0bf06f21。只修合法整數厚度的來源讀取容量與兩處過時 transport／診斷文字；P1～P5另議。

首紅：63-byte 的「9.＋61個零」通過；64及127-byte各在 PF2_THICKNESS_VALUE_9／I52具名斷言變紅，1個測試方法、2個子案例 failure，errors/skips=0，實際OS exit1。before-identity綁原binary、source及裁判hash。後來另一個舊方法增加12.5負例；oracle-binding確認新增的厚度方法逐字未變。

修後：PF-2 18/18、完成面22/22、工程核心18/18，OS exit皆0。三個等值表示皆讀回9，材料原字串與獨立重算指紋保持不變；缺值、9.5、12.5拒絕。

撤修：隔離編譯把consumer恢復64-byte，修正版0／撤修1（僅64/127兩個具名assertion，error/skip=0）／還原0。未改工作區產品來跑變體；current_geometry.c只以binary讀取，隔離副本保留CRLF。

標準突變因來源閉包更新而真正重編／執行：45份可執行變異及3份退休紀錄，40 killed／1 crashed／4 equivalent／3 retired，整表check actual0，stale0／blocked0。基準139/139；每個批次actual0，原results分檔後才合併。沒有修改mutate.py、定義、oracle或舊證據。

現在固定提交執行完整native（stack16MiB）；新增方法的期望數將由run_all --update-expected完整census從17更新18。native尚無終局，本文件後續補完整原件。未跑WSL，不合併PR，不改SSOT／白話／正典／鎖定內容。
