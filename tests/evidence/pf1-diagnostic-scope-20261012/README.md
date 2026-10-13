# PR #190 M1：拒絕分類的入口界線

本輪依 [審查6115524959](https://github.com/ZhiQiYang/geometry-axiom/pull/190#issuecomment-6115524959) 更正完成聲明。先前正文及6115302508「缺件／重複／非法型別仍 INVALID」應限於已驗的 **scene 障礙清單**，不是兩入口的一般保證。

同一來源 `687e2c2305b8d380ba1b179b47d723275dc0454c` 的 JSON `fs_from_json` 先拒絕 `count>64` 為 `UNSUPPORTED/CAPACITY`，不繼續驗型別／唯一性／存在性；scene 先逐件驗 typed reference、存在性及唯一性。因此現存c1的65個重複引用：JSON容量拒絕、scene非法拒絕，兩者都零提交。名稱完整 UTF-8／字元驗證後判96-byte容量的原證據適用兩入口，不能拿它推成障礙清單也有相同優先序。

本輪有限原生對照保留六組输入，每組走兩入口：重複c1／重複不存在c99／重複非法型別x1，各2項及65項。2項三組均非法拒絕；65項JSON三組均CAPACITY，scene三組均INVALID。每次JSON preview無效、confirm拒絕；scene載入拒絕，所有dump／read state／revision逐字相同。多個錯誤可以同時存在，這個對照不聲稱已定義某種錯誤的語義優先，也不把重複c99的拒絕原因冒稱純缺件。原stdout保存完整violation及載入診斷。

`scope-probe.py` 使用原 `BASE`／`surface()`／真fresh registry bridge及其sidecar，actual exit0；有斷言驗兩入口診斷與零提交。這是六組有限功能對照，不是新增unittest計數、產品mutant或正式七job。產品、C include、SSOT／白話／正典／🔒、原測試／expected／runner、核心帳本與原323證據檔全不變；不重跑不變的76定向測試或全核心表，不移植先前通過聲明到新的產品來源。

正文、舊完成留言的限縮文本及本輪逐項回覆已備具體JSON草稿。GitHub API於本輪回報HTTP401，公共GET及Git讀取仍可用；不能把未送出的API更新當作已發布。Git分支推送與API發布分開核收，API操作恢復後再發布草稿；勿在聊天提供token。

B1正式同最終整合SHA七job仍由既定owner按落地順序補，沒有排WSL全量。PF11真瀏覽器／完整.gcanvas、I53 layers pending及共用橋接增量待整合的界線保留，未擴充政策或PF能力。
