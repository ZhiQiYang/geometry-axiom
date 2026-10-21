# L 五項 browser 正式證據包

來源分支 `codex/geo261-closeout-20261021`，完整 SHA `43f85313c32410ac01406ab585846bbacafea278`。先讀 `run/報告.md`、`run/final-verification.json`、`run/independent-review.json` 與 `run/artifact-independent-review.json`。

五項 assembly／documents／grid／space／timber 依序實跑，通過斷言為 150／47／350／242／79，各原 node 與結果核對 exit 0；原總上限 900／600／900／900／1200 秒從各自 build 前起算。job 實耗 178.905884／16.221137／447.672032／193.419530／91.236736 秒。每項來源前後 L clean、154 個記錄來源與 Git L 相符、runtime 前後同一自有 PID/session/fresh，清理無 live／zombie 且 HTTP／CDP 全拒絕連線。

assembly／grid 原 harness 為 partial，原 goldenCompare 明說沒有比完整 golden；外層另外精確核本 job 指定區段。documents 沒有 golden/completed 欄位，依47具名原斷言逐序核。space／timber 沿原固定 group census 與各自 scope，沒有放寬或合併省略組。原 intentional lost-response metadata、peer 初次浮點差值檢查 exit 1 及改核原 deadline 建構式的結果均保留。

`run/` 保留五項原 stdout、命令、前後來源/runtime、建置/native身分/sidecars、原結果、接受器與cleanup、suite manifest、81張PNG及原wrapper產物。`declared-artifact-capture.json` 另保留完成後複製的7份grid原下載及documents合成PDF輸入，連同原wrapper已保存的assembly／space各1份，共9份gcanvas與1份合成PDF；PDF不是下載。所有原件逐bytes保留。事後證據整理不冒稱在原job時限內，原suite manifest沒有被回改。

`launch/` 包含真 wrapper wait 的 `.exit-code`、launcher-receipt、原 stdout/stderr、實際 parent-command 與工具觀察到的 launcher 程序 exit 0。`exec-observation.json` 保存 session29349/chunk5aace0 的實際工具回覆，沒有從產品 passed 推算退出碼。父命令明示 `env -u CC -u PYTHONOPTIMIZE`；兩層程式原bytes都保存為文字。`preparation/` 包含凍結計畫、靜態檢查與假子程序0／7／-15控制；這些控制不是產品測試。外部wrapper與launcher不是新增正式產品工具。

每項 build及服務入口都經正式start_local/require_fresh；三個native binary均reused，沒有宣稱重編。Chromium與CJK字型實際版本/雜湊有原紀錄。五browser部分時間與native並行，耗時不能當P-189效能證據；未逐張人工目視81張UI。本包沒有新增產品修改或撤回突變，也不宣稱native、Q38、§7、P-189或使用者複審已完成。

`原件清單.json` 明列來源、長度與SHA-256；`SHA256SUMS` 包含除自身以外全部檔案，可用 `sha256sum -c SHA256SUMS` 重核。未收錄的兩個可執行副本另列；原程式 bytes 可由對應文字快照還原。封包與外層核對資料相互分開，避免自我雜湊。
