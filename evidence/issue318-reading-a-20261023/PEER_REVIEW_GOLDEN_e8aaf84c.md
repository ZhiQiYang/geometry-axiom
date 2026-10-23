# #318 e8aaf84c：golden 非空見證對抗審

不可變被審來源：`e8aaf84c7311d05cc1b2fe5ece8fb56be8e227d0`。本代理只讀 Git／封存觀察、解析 AST/JSON 與比較 bytes；沒有執行 oracle、generator、selftest、原生核心、reader、突變或掃描。獨立 metadata audit 原 exit 0，完整讀取指令／輸出／hash見 `review318-golden-e8aaf84c/receipt.json`。此 0 是證據核對，不是 e8 的正式驗收綠燈。

先 fresh fetch handoff 得 `7bd61a43210bbad0abf95709e1a0205cd8760cac`；318 review hash仍 `0b1ddba6a201e9bdb779ca8733d5fb7d20e96f1067cde62efd3a0dd5c020cb66`。未把舊審查冒稱新留言。288 新審查已另通知 root，與本 source golden 的身份分開。

獨立核對結果：

- 原小樣觀察執行來源確為 `2039b477a9669a9e3fcaad740283605b8de8a8f4`，記錄 clean、8 build、exit 0。原觀察三個 Python source hash逐一與該 Git source相符，原 observer工具本機 bytes 也符合已封 receipt的 hash。e8 的 `framing_oracle.py` 與觀察 source逐位元組相同；沒有重跑或把觀察執行 SHA改標e8。
- FZ120 左上Y／左下Y current與withdrawn 的60支料、兩軸縫、conflicts、problems、P182逐欄完全相同。唯一 core-limit 變更是移除固定段 id3 的 I19；id1 的 `CORE_LIMIT_EXTENSION_END_FREE`／end1000仍在。id1矩形 `[1000,3645,4100,3672]`、延伸 `[1000,1450]`，id3矩形 `[0,3648,1000,3675]`，符合既有手算與I22未獲改動的界線。
- 新 witness 的整筆種類／矩形排序、縫與觀察投影相符，唯一精確四元組是 `[CORE_LIMIT_EXTENSION_END_FREE,1,1000,[1000,3645,4100,3672]]`。該料真正排序 index2，index1是另一支，原 id≠index 的反證仍有牙齒。
- 從 JSON 的 `params` 起至檔尾，前後 bytes 完全相同；原8房64排法所有欄位不變。新 FZ120 僅在獨立 `core_limit_witness`，沒有送進64場景房間清單，也沒有把整份 snapshot包在withdrawn policy。
- STEP20觀察當前 buildable／空core_limits，但種類／矩形及兩軸縫與舊非空 witness完全相同。generator保留原非空assert並新增精確I22單筆assert；selftest保留四元組綁定、id不是排序index、舊三元組必報UNBOUND的反證。
- FZ114左上X在封存觀察中第一可行仍3544，trace仍 `[(3656,false,true),(3604,false,false),(3544,true,false)]`；e8恢復原數值與完整trace，沒有為尚未跑的新政策預期3656而放行I22或改P182偏好。

未見這次 golden 遷移確立的新靜態阻擋。它是人工審過原觀察後只換維護見證，不是執行正式generator／selftest／64逐支比對的替代。正式新source的0/1/0、矩形逐毫米、579凹角、528/1056凍結正例、native、reader、架構與真CLI次序仍待；維持原 QUESTIONS，不能因此宣告complete baton或全綠。

另只靜讀了未提交 `prove_golden_witness.py` 草稿：其精準還原STEP20常數、保持原非空斷言，並以原traceback最後一行定位正常AssertionError，設計可作維護fixture的targeted反證。正式前已告owner補四檔source輸入／隔離／hash與末clean、正向PASS marker、R3外層鎖及相關環境收據；此草稿審讀不作不可變e8通過範圍，也不冒full64。
