# 固定寬度解碼候選的效能預檢方法

此文件只規劃候選預檢；尚未啟動候選編譯或取樣。正式 L `43f85313c32410ac01406ab585846bbacafea278` 的 P-189 `check` 真結束碼為 1，N48 比值 2.1635003131764803、N64 比值 2.852459784097019，原件不變。

## 來源與最小可判結果

採用 architecture 代理完成契約測試後建立的獨立本機候選 commit；待其回傳完整 SHA，先核 parent 為 L、與 L 的完整 diff 只有已授權 `wd_read` 固定 1／4／8 位元組解碼，保存 full patch、Git blob 與載入來源 closure SHA256。候選標籤用真 SHA，不能寫成 L；不 push、不改主分支。

最小充分的性能預檢沿用既有完整 P-189 方法：固定 main `adbaebf9c73ea6801d7b4d5214e4b846b132923b`、base `3e600772076465fc65a26ac09055028301c0fb0b`、final 為候選真 SHA，原工具全新 out／work、三方新 archive 與新 O2 binary。相較重用既有 binary，新建三方可直接沿用原建置收據／來源判定，不需自行合成收據；約多 50 秒建置，完整預檢約 4 分鐘。

此輪能回答候選在同輪 main 對照下，四個 N 是否均符合原 2 倍門檻；若任一超標便如實判定候選尚不足以解除門檻。它不是完整可合驗收：候選尚未更新突變帳本及架構產物，後續仍由主代理依交接規則處理。不能以帶 `-pg` 診斷時間或歷史 main median 作分母。

## 固定執行順序

1. 完整 SHA、乾淨候選來源、單一變更 diff 與 closure 索引；新 out、new work、固定 gen 及其 calib 原 bytes。驗官方 runner SHA256 為 `fb42a801ce350e64444fcb2db433e59f8c2228546b4b594298581bdb365d0c44`。
2. generator selftest、runner `selftest` 的本輪 16 控制；不可借用歷史控制結果。
3. 原 runner `build`：三方 `gcc -std=c11 -O2 geometry-web/web_bridge.c -o bridge -lm`，完整新 archive；保存三方 binary／source／compiler 雜湊。
4. 原 runner `equivalence`：175 場景，保留三方完整 stdout／stderr。四生成場景要求三方有效載入及完整 stdout 相同；171 舊場景沿原 base／final 判準，main 差異只記錄。
5. timing 前逐 binary hash 對建置收據；記環境與 `STAT`。排除殭屍，不把歷史 `%CPU` 當即時負載；閒置服務用 CPU tick 核對。其他測試、編譯、瀏覽器、封包掃描全停，由主代理明確放行獨占。
6. 原 runner `timing`：N=16／32／48／64 各三輪，偶數 main／base／final、奇數 final／base／main，共 36 筆，不挑樣、不改 900 秒 timeout。t0 仍是 Popen 返回後、communicate 前；不宣稱包含完整 Popen 成本。
7. 原 runner `check` 才產生門檻真結束碼；timing 完成為 0 不能寫成門檻通過。任何紅燈保原件，不能覆寫或挑樣重跑。

每 phase 的共同 argv 形狀（完整候選 SHA 與新路徑取得後寫入實際 config，不能把以下佔位符當已實跑）：

```text
python3 -B /workspace/geometry-axiom/geometry-core/domain-decoupling/closeout-tools/p189_verify.py PHASE --repo /workspace/geometry-axiom --work NEW_WORK --out NEW_OUT --gen NEW_WORK/gen_scene.py --final CANDIDATE_FULL_SHA --timeout 900
```

16 MiB stack、core limit 0、移除 PYTHONOPTIMIZE、無 Python `-O`。每 phase stdout／stderr 直檔，`child.wait()` 真碼先落再整理收據；完整 argv、cwd、開始／結束時間及工具 hash 都保存。頂層調度由可等待的工具 session 持有並真 wait；避免用 launch-and-exit 產生可避免的 orphan。若 transport 異常，仍以先落盤 phase exit 為準，不重啟已存在 out。

## L 對照與診斷界線

此最小方案不另量 L；正式 L 原件只作歷史背景，不插入固定 main／base／final 方法。若之後需要同時段 L／候選的直接改善幅度，另開明確標成診斷的比較 out，固定原 L binary hash 與候選新 binary hash、交錯順序及樣本數，再取得主代理獨占放行。該對照不能改寫原正式 L 收據，也不能替代完整 P-189。

單次 L gprof 只證明此次載入的取樣分布。`wd_read` 已 inline，但正式 O2 caller 仍有 4／8 位元組迴圈；能否靠這一小改通過門檻須由候選原法實測判定。`contact_order`／memo 等 #323 與容量 #300 不納入此候選，P177 次數與時機不改。
