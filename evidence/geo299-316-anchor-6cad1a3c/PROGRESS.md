# #299＋#316：接回 #314 單行 anchor 維護

目前產品／tests source S：`6cad1a3cb76d7bd910125a1d70ecfffdc9183813`。這是一般merge，parents為本棒舊E `1722b55445b53ac37b6eac1be7b379e79c73eaa8` 與#314精確source `3b0b634feb54266700cc61f26c34d7aeac4c0314`；不merge其後純evidence E，不帶#318產品。source已一般push且ls-remote同，commit／push／查核原exit0、工作樹clean。

唯一非evidence差分是 tests/test_geo261_wood_grid_application.py 的既有突變控制anchor由過期2參數更新為當前真6參數callsite。完整舊檔只做該唯一字串替換精確得到新檔，與#318原1cd2該檔逐bytes相同；if(0) replacement、其餘全部斷言、23個方法不變。公理層／決策佇列／mutate／expected／原ledger／架構四檔blob保原，沒有放寬測試。原#314-refresh的12份歷史evidence隨source祖先合入，保原bytes，不把它們冒成本次動態結果。

最新handoff已fetch為7bd61a43210bbad0abf95709e1a0205cd8760cac；314最新留言仍為先前設計追蹤回覆，未冒稱有新產品審查。36條原Git子命令完整argv／cwd／退出／stdout／stderr／hash在raw包，封包逐member reopen驗bytes/hash；兩段頂層heredoc未另錄caller streams的限制明列INVENTORY，不冒原捕獲。full cached whitespace check原exit2來自合入原evidence/geo314-refresh-8033aa75/LATEST_REVIEW.md末尾空白行，保原內容；唯一test路徑check0。

#323 reviewer不可變靜審已完成，未見確立遺失／假綠：核正確parents、唯一單字串差分、23方法與全部其餘assert／if0、10個保護blob一致。這只接受source維護與待驗標示，不是產品動態通過。原報告bytes/hash在peer-review。

沒有跑測試、編譯、scan、Chrome、benchmark、帳本check或重產；原M89–98、M99–121 registry、原110 records與M121未跑身分不動。新source各產品suite／每fix0／1／0含M121、帳本freshness及root最後整份重產、架構三裁判／四檔與reader三條都仍待最終排程，不把舊S15或F5bf綠燈改標本S。

共享source已交回#318，它確認已有同anchor內容，可先依此靜審普通merge新S再交無木工owner。本代理此後只寫own evidence與-prbody，不碰共享source、root整合branch/index。不force push、不合併PR。
