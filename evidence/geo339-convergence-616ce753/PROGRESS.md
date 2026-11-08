# 一般來源合流進度（2026-10-24）

- #340 已一般 merge L `7af8c5d80d34cb4f49d01ba67deb78a3a6d725db`，source S1 `175cee44c56c89871803d955c0c525236727ba65`，原 parents 舊 S `4d3a17c306cad42057589c5cfd964f1c32b755c4` 與 L；remote exact。
- #339 已一般 merge S1，source F1 `616ce7538d23fbe7f3bbefae7f2a04e25ebd75a4`，原 parents 舊 evidence E `1d94ab77ab29952d5b73ec5b262dfd239819fe25` 與 S1；remote exact。
- 原 R1 exit 1：新 `--no-checkout` worktree 未初始化 index；沒有刪檔。完整 3,000,230 bytes 原 status 與失敗守門保留。依授權的 R2 dry-run/read-tree 初始化後，兩條普通 merge／push 均 exit 0。
- 原 L 帳本 blob `fb470f96399093f6b25b2b2358011d26f3c36898` 完整採入；未執行 `mutate.py --check`、未自行重產帳本。新兩分支唯一非 evidence 相對舊產品差異都是 ledger，11 個 kernel inputs 全同，230 項 expected 保留 #340 kernel13／host39、#339 kernel13／host45。
- 原 bfb checkout clean 且未改；原 F38da 的 142／三反證、bfb 的 13／七階段均保留原 execution SHA。新 S1 已另以原 selected aggregate 實跑13／13、0 fail／skip、strict expected exit0；F1 與完整 native／六 browser 仍 UNRUN，沒有移標舊執行，沒有 READY-TO-MERGE。
- 最新讀到 handoff `d2ed8e6efe2760ca562ab7d28f4a2ac09a404fd5`：#339 最後審查仍 00:39:36 head e9ee6d0；#340 新審 02:38:33 head4d3。已補 #340 B1 原 aggregate row；B2 required jobs 和 C1 後續 base evidence 邊界未解除，#339 B1／B2／B3／C2 仍未齊。
- 下一步：root 在最終統一列車指定帳本、架構與七項正式驗收；本線依受影響來源保留 kernel13／142 與原反證。所有後續來源都採一般 merge，不改寫歷史。
- #340 原 selected aggregate：`python3 -B tests/run_all.py --only test_rectangular_template`，原 runner、strict13 與1200／120／10秒不改；NativeBuild 真編，35原命令含4預期negative1，329來源初末同，三個舊rowlogs還原、globalcache無修改。原外層七階段不重跑，依新審以11來源＋registry同bytes保留舊bfb原實績。
- 依最新 root 裁示，F38da→F616 全 493 原 inputs＋5 Markdown 的 Git mode/type/blob/size完全相同，非 evidence 只有 ledger 差異；有效原142／三刀沿用原 execution F38da，這輪不為單純ledger重跑。原 aggregate 與受後續C產品改變影響的項目留 root 最終統一來源。
