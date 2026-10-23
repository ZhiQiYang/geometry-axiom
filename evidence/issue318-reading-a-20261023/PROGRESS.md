# #318 閱讀 A：目前進度

目前已實作第一批專有來源：核可 SSOT 四處差異、oracle 建構／C8 獨立三態政策、固定 528／1056 正向 coverage 資料與 12 個專有測試方法。只做 AST／JSON 與 hash 靜態檢查 exit0；沒有執行測試或正式掃描。詳細範圍與未完成項見 `SOURCE_PHASE_ONE.md`。

尚未到完整 source baton：原生 common/caller、canonical、正式 sweep 接線與舊 selftest/golden 預期仍待完成。root 已授權本代理 17MB sparse worktree；heavy 仍由 #288 獨占，不能宣稱任何 native/oracle 新綠燈。以下保留先前準備歷史，不作目前未改產品的聲明。

## 先前準備歷史

狀態：權威與逐條 diff 已備，**產品尚未實作，正式驗收未跑**。這是子代理自己的準備分支，沒有寫整合分支，也沒有合併 PR。

- 先 fetch handoff 至 ea2748248d47563f8559638ccb70ec0ed21910d9，讀 #318 留言 6357744513 第 3 版及 main feb502d7b3bade2334733a4349c87ff91b88621e 的 2026-10-23 核可閱讀 A；metadata 指令 exit 0。
- D11 一句、I19 例外三、R6(d)(e) 的逐條候選 diff 已備。原公理 blob c34e8d6acf862455db2d47978feb04cd43324284；本提交不改原公理，不同步 reader。
- 無木工 owner 已獨立重套四處修改、驗 candidate hash 與可逆原 bytes，純文字對抗審未見 blocker；不是產品驗收。
- repo 外 W tri-state 與 oracle predicate 草稿、正反例表已備，未編譯／未執行；不將 free-gap 當實際 RC 面長度，不追加對方料長軸限制。
- 已對 #323 5c29eba3 與無木工候選做純靜態對抗審，尚無可確立 blocker；實際收據未取得，舊 1.3 量測紅燈未改判。
- root #288 持有重工作鎖，且磁碟待清理；本輪沒有 clone／worktree、compile、Chrome、bench 或全帳本重產。

下一步：等 root 提供專有 sparse worktree 與測試槽，按 #323→#314→combined→#318 的普通 merge 順序交棒；再落公理、唯一 reader、oracle 與核心，跑正反例、原始 0/1/0、完整掃描與正式驗收。共用 canonical／C／registry 尚未動。M89–98 屬 combined，M99–121 屬 #314；#318 暫保留 M140+，尚未落 registry。全帳本只由 root 在共同最終 SHA 整份重產一次。


## 第二批準備（仍未實作／未跑產品）

已補 caller 整合備忘、repo 外 C/Python 草稿（以 .txt 封存，不是產品來源），包含 R6(e) 先行 full-width gate、between 的完整配對、returned FEATURE 真值負控與禁止 PARTIAL 早回傳跳過碰撞。對抗審要求已記入計畫，正式 caller 尚未實作，不能算整體審過。

另直接從固定原 expected-data blob 913772d5875526be7c84f9911fd2fe6d175bbd1b 抽出 528/1056 ID/layout 作未來必須逐筆 buildable 的正向見證候選（資料抽取 exit0，沒有執行 oracle）。這避免只把不可施工清單清空，導致漏掃房間也假綠。quick/full 的矩形逐毫米方向差異已明記，不能把 quick 冒成 full。

目前仍等 root 的專有 sparse worktree／資源槽，以及 #314→combined 的真 source baton。此提交只有 evidence，產品／SSOT／canonical／共同 registry 原 bytes 均未改。
