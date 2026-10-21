# A2 全量帳本與 L2 發布證據

分支為 `codex/geo261-closeout-20261021`。完整 ledger 實際來源是 A2 `cbefb39b47fb0edcfaf003d2c1101929fea244c8`；其後 L2 `249571fe2477845d5330f6190dad965bf327f43b` 唯一父提交為 A2，且只變更 `tests/mutants_results.json`。75 筆 execution.head 保留真正 A2，沒有改標成在 L2 重跑。

`python3 -B -u tests/mutate.py`、`python3 -B tests/mutate.py --check`、`python3 -B tests/mutate.py --check --killers` 三階段均真碼 0；supervisor finally、父 launcher 真 wait、互動工具最後回覆及必要 validator 也都是 0。78 筆為 70 killed、僅 M20 crashed、4 equivalent、3 retired；逐 ID verdict 與 A2 原帳本完全一致。M20 是同場景三次 -11，屬偵測到崩潰，不能稱斷言殺死。

原帳本 5,170,289 bytes，SHA256 `6bda315331050bd3478ed65211a8263508cb1a1f6f67cee3f35df377506e7f0b`。57 個核心 execution 的基準為 165/165；18 個 bridge execution 的 baseline/restored 各完整 27 方法，還原 bytes 與 binary identity 已核。全新 detached A2 worktree／空 cache，CC 與 PYTHONOPTIMIZE absent，預設 cc argv，stack 16 MiB、core 0。362 份來源／oracle 原件、184 個 source closure 檔案和 165 個場景均在執行前綁定 Git A2。

03:25 左右曾發生工具傳輸短暫斷線，原進程持續，沒有重啟 writer。03:26 原 session 仍可讀，最後 session 12445/chunk706db3 真 exit 0。啟動收據未保存 starttime tick，後來的程序 tick 只能配合 PID／argv／父子鏈與 boot 時間對照，不能冒稱有歷史 tick 逐值比對。相關原觀察完整保留。

L2 發布保存了逐命令 raw、終了碼、原 JSON Git blob、default check 0、普通 push 0 與 remote exact。最外層 importer 工具觀察由 root 轉錄實際回覆，清楚保留不是 raw transport／不是重新 wait 的界線。此包不重新執行 ledger、check、發布或產品測試。

獨立審查定版接受器真碼 0；之前兩次接受器核對誤判也保原碼／工具觀察：第一次錯把只保尾 3000 字的 failure.detail 當完整輸出，第二次未處理 FAIL 標頭後的測試說明文字。改核完整 mutant stdout 的具名 FAIL／AssertionError 後通過；沒有重跑或改寫正式 ledger。獨審沒有再雜湊 75 個 cache binary，此項由既有正式 validator 核對，不能把兩者說成同一次檢查。

核心原始證據的限制：既有工具沒有另外保存每個核心子程序的原 stdout/stderr，只保存結構化 oracle result 與其 SHA256。頂層 mutate.stdout 無法補足缺口。bridge 及 sidecar 原件依正式工具紀錄逐 bytes 收錄。工具歷史自測是相同 supervisor 的先前自測，不冒稱 A2 當輪重做。

`執行原件` 是原 frozen publish 的完整快照，保留其原 publication-index 與 SHA256SUMS。`後補收據` 收入 publish 完成後新增的真碼／審查，不修改原包。歷史準備計畫、啟動時方法與 A2 發布收據保留當時「尚未完成」的文字；本 README 說明此次帳本已完成，不據此宣稱 L2 其他驗收已完成。

本包原件清單只列逐 bytes 複製的原件，不把自己列入自己的雜湊；根 SHA256SUMS 精確涵蓋除自己以外的全部檔案，包含生成說明與巢狀索引。所有檔案 mode 為 0644；外部 Python 方法以 .txt 保原 bytes，沒有新增產品工具或可執行副本。封裝／獨審最終退出碼與本包驗證收據另置包外，避免自含循環。
