# 下一個工作階段：先讀本檔，再接續各 PROGRESS

專案尚未全部完成。不要從頭重跑；先 fetch main 與 handoff/codex-takeover-20261021，讀 handoff/pr-reviews/*.md 的最新 ChatGPT 審查。只有最新審查明確允許合併，才標 READY-TO-MERGE #N；不得由雲端合併 PR。全程繁體中文、英文 commit、不 force push、不改決策佇列。公理只限已核可事項且須同步唯一閱讀器與三項檢查。

## 已完成的 #288 驗收交付

- 產品 F：`3d681636902371ecc528b20f51eea33e272581c9`。
- 完整驗收不可變快照 E：`5a76d815c843d7ffb06bd1be769d4c5255c72b66`。
- 本次交接寫入前整合分支證據 head：`a05a21a5ed4b4403e8bfece0fd29d36d29d45336`；分支 `architecture/geo261-integration-20261016`，只由主代理寫入。
- 正文分支 `codex/geo261-final-prbody-20261023`，D=`e008dc52510d8cdb34fe07c796835f2667e0ebaa`。`PR_BODY.md` SHA-256=`77fad4a11a92827d4b5d2b95423215c98dc13ecccce5c33e8c70e156c688e1f8`。已普通推送，尚未透過 API 改 live PR 正文。
- P88 歷史三輪為 1/0/0，屬間歇紅；新 F 三次完整 canvas 均 2267 pass、0 fail，85 個 golden 全符。新 F 受控原生 rAF 撤回自證為 0/1/0。未把受控位移說成歷史唯一根因。
- 新 F grid、四組受影響 native、P52 formal/verifier/runtime、P73、Chromium 154、oracle 全部完成；P52 runtime、P73 與 oracle 反證均已附原始輸出及獨立對抗審查。原 mutate --check=0、架構三項=0/0/0。未受影響的 F13/F2 正式項保留真實執行 SHA，沒有冒充新 F 重跑。
- 最新審查為 handoff `b7e23a2579c5bdcf057d3ad6d04b064ac098a5c6` 所收錄、2026-10-23 14:37:58Z 對 head a05a21a 的審查。產品／驗收阻擋已關閉，唯一須改是把已準備的 current-state 正文真正套到 live PR。雲端 API 仍403，正文尚未套用，不標 READY。`p88_priority` 專職追蹤及處理 #288。
- main 仍 `feb502d7b3bade2334733a4349c87ff91b88621e`；#288 尚未合進 main。

## 活躍工作線

| 工作 | 分支 | 產品來源 S | 已推進度／下一步 |
|---|---|---|---|
| #323 | codex/geo261-load-residual-20261020 | b2445b5a270d60fdf48b07f6edddbe91266d8aa2 | 原 baseline native 正在跑；不得重啟。175 三方比較通過，N64/main=1.1608619523 綠；N32/base=1.0008656474 與 source calls 64/32=6.1549962284 紅。必要 suites 有兩個負控制漂移，PF3 原 execution=0。全部收齊後一次套入已對抗靜審的 memo+controls 四檔候選，再做自證與正式驗收。 |
| #314 | codex/geo314-one-axis-stagger-20261022 | 3b0b634feb54266700cc61f26c34d7aeac4c0314 | 證據 E=ed1ab195aa5cd6a7d03de708ff63724404fcbbf6；六 native suites 103 方法、原 inspector、M99–M121 的 v2 外部工具已靜審，尚未執行。M110 必須保等價判定；P72B 真 Chrome 另跑。 |
| #299+#316 | codex/geo299-316-combined-20261022 | 6cad1a3cb76d7bd910125a1d70ecfffdc9183813 | E=ebbd6d19ddf64ac64fd3c902eec6e40f4484582d；M89–M98 與原九 suites／166 core scenes 的實際 CLI 已準備，新 S 動態驗收仍待跑。 |
| #318 閱讀 A | codex/issue318-reading-a-20261023 | ae74e51bba1efef48949c077635966273a9e8990 | E=c5445caf5d26592ee870f884e5c0441a2a7b640f；三 reader 原 0/0/0，unit 51 方法全過。D=261b30afde6af452c46446387fe5332bafff6299。其後原 native7及11組0/1/0已完成、待peer/public；oracle13原0。繼續逐毫米與579凹角／528及1056／真 CLI 放置順序、架構。 |
| 不帶木工模板 | codex/kernel-without-woodworking-20261023 | 9b201164ed31069843a2b9f3787ea8ae8e22e231 | E=6f2e5e27d2f949ef63d198ceac0630a352f6b397；13 tests 與七 phase 自證已準備，尚未跑。使用原 self-R3，不另改鎖。 |
| #324 | 既有 PR 分支待確認 | 待 fresh fetch | 已交 #314 owner 清點最新審查及重疊檔；不冒稱已修。 |
| #333 | grok/woodworking-field-rules-20261023 | 02cb11b9762da429a3dbb0eed9151f45a65ed620 | 已普通推送：僅刪 .gitignore 審查指定兩行，FIELD-RULES 逐字保持。真 git check-ignore 反證 fixed0／withdrawn1／restored0、原 capture exit0；獨立審查與證據／正文發布進行中。 |

各已推分支的 evidence 及 PR_BODY 為該線詳細原件。#323 最新正文 D=`b63add264735613b42b065e98ee5e6b1b4afc677`，明列目前紅燈與未完 native，不是最終全綠聲明。

## 排程與接棒

1. #288 始終至少一位專職子代理。每做完一步先 fetch 並查新審查；沒有新阻擋就持續其他線，不重抽已綠測量。
2. 最新使用者收尾優先級：#288 進 main 後依 #318、#314、#299+#316、#323、不帶木工模板、#324，再 #300 容量512與其他 open issues。尚未進 main 前先做可獨立推進的驗收與修正。
3. 目前已公開 source stack 的合入方向為 #323→#314→combined→#318→kernel。這是已存在歷史，不表示新收尾優先級。共享檔同步與 main retarget 由主代理根據實際 diff 指定；不得反向 merge 下游把整條產品混入前棒，不改寫既有歷史。
4. 最多兩個重工作；性能與完整 canvas 獨占。#323 原 baseline remaining session18009／scheduler PID1305238 正持原 R3，完整 native 從14:30:38開始，勿重啟或解除原鎖。結果目錄 `/tmp/geo323-baseline-b2445b5a-v3-r1`。
5. 已封存 checkout 的純環境維護已全部原 exit0：三個 /tmp checkout 約回收965MB，兩個 workspace P73 checkout 約回收604MB；原件與 Git objects/refs 全保。slot2 的 #318 native7與oracle13已0，接續 oracle-mutants／quick及CLI與架構；有原self-R3的golden proof仍等鎖。之後slot2交 #314。維護專用鎖 `/tmp/geo261-completed-checkout-maintenance.lock`，沒有變動任何原測試 R3。
6. 子代理不各自整份重產突變帳本。最終來源確定後由主代理統籌全帳本與架構；過期結果必須如實標記，不能用 partial mutation 冒充全 ledger 綠。
7. 每個修正保留正常反證／還原、原指令、環境、完整 streams、exit、可解析 SHA；各產出交另一子代理專找錯。原失敗與環境修正不覆寫。

## 授權與未完成邊界

- 木工規則推理前先讀 main 的決策佇列 2026-10-12～15、2026-10-22、2026-10-23 各節，以及 PR #333 的 `geometry-templates/woodworking/FIELD-RULES.md`。已讀 PR333 source=3d9bd947；該頁只是引文彙整，不取代公理層。
- #318 閱讀 A 已核可；其它未核可公理／鎖定決策衝突／新數值門檻，寫 QUESTIONS.md 與該 PR 正文，接著做不受影響工作。
- Git fetch/push 已恢復，不能稱尚未推送。GitHub API 仍 403；以 handoff 的同步審查與可讀 Git refs 推進。尚無可核對的完整即時 open issue 盤點，不能宣稱全部 issues 已結案；等待轉入 repository 的盤點時先做既知工作。
- #288 唯一剩餘審查項是 live 正文；本機可 fetch `codex/geo261-final-prbody-20261023`，確認 `PR_BODY.md` SHA-256 為上列77fad4…，再執行 `gh pr edit 288 --repo ZhiQiYang/geometry-axiom --body-file <該PR_BODY.md路徑>`。這是套用已驗正文，不是合併。雲端未成功執行此操作；不把檔案已推送冒稱 live PR 已更新。
- #213 的既有交接明列使用者自行處理；不要擅自關閉。合併由本機 Claude／使用者處理。
- #300 的先決仍含 contact_order 線性查找、擋面 O(n²) 去重、geo_eval_depend；先補已知前置驗收，不自行放寬性能門檻。

## 雲端原件位置

- root repo：`/workspace/geometry-axiom`；主狀態：`/workspace/geo288-main-merge-20261023/ACTIVE_P88_PRIORITY.md`。
- #323：`/tmp/geo323-merge-20261023`，巨型 merge stdout 205298659 bytes 保留在 `sync-b74f9a2a/subcommands/000013/stdout.bin`，SHA-256 `778f023db9aba56fa84bd85b8ff32c016aec5bb0d9470b445653b0bd3989e174`；不可刪。無損64MiB分塊工具已獨立靜審，尚未封存執行。
- #314：`/workspace/geo314-owner-20261023/fixed-source-tools-v2/README.md`。
- #318：`/workspace/geo318-formal-ae74e51b-round1`、`/workspace/geo318-reading-a-prep/formal-tools/`。
- noWood：`/workspace/kernel-no-wood-prep/NO_WOOD_FORMAL_REQUEST.json`。
- 真正 Chrome156 在 `/workspace/geo261-environment/bin` 前置 PATH，Node24.19.0，Noto CJK 已裝。不要因預設 shell PATH 找不到 Chrome 就重新安裝或誤判不能跑。

這份 NEXT 是接續記錄，不是全專案完成報告。
