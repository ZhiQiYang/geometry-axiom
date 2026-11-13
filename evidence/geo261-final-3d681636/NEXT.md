# 階段停止交接：先讀本檔，再接續各 PROGRESS

本階段依使用者最新「階段性完成後停止，交給別人繼續」指示收尾。專案尚未全部完成；已停止啟動新測試與新修正，僅收齊原有階段並推送交接。下一位不要從頭重跑；先 fetch main 與 handoff/codex-takeover-20261021，讀 handoff/pr-reviews/*.md 的最新 ChatGPT 審查。不得由雲端合併 PR。全程繁體中文、英文 commit、不 force push、不改決策佇列。公理只限已核可事項且須同步唯一閱讀器與三項檢查。

## 已完成的 #288 驗收交付

- 產品 F：`3d681636902371ecc528b20f51eea33e272581c9`。
- 完整驗收不可變快照 E：`5a76d815c843d7ffb06bd1be769d4c5255c72b66`。
- 前次接續快照：`a3018515644451367ef94f667082c9bd4881538f`；已完成階段支援封存：`a5e7c2719a7a5c3af3db49b5ca409313e5cb190f`；分支 `architecture/geo261-integration-20261016`，只由主代理寫入。本檔後續提交仍只改 evidence，不是新的產品 F。
- 正文分支 `codex/geo261-final-prbody-20261023`，D=`e008dc52510d8cdb34fe07c796835f2667e0ebaa`。`PR_BODY.md` SHA-256=`77fad4a11a92827d4b5d2b95423215c98dc13ecccce5c33e8c70e156c688e1f8`。已普通推送，尚未透過 API 改 live PR 正文。
- P88 歷史三輪為 1/0/0，屬間歇紅；新 F 三次完整 canvas 均 2267 pass、0 fail，85 個 golden 全符。新 F 受控原生 rAF 撤回自證為 0/1/0。未把受控位移說成歷史唯一根因。
- 新 F grid、四組受影響 native、P52 formal/verifier/runtime、P73、Chromium 154、oracle 全部完成；P52 runtime、P73 與 oracle 反證均已附原始輸出及獨立對抗審查。原 mutate --check=0、架構三項=0/0/0。未受影響的 F13/F2 正式項保留真實執行 SHA，沒有冒充新 F 重跑。
- 最新審查為 handoff `b7e23a2579c5bdcf057d3ad6d04b064ac098a5c6` 所收錄、2026-10-23 14:37:58Z 對 head a05a21a 的審查。產品／驗收阻擋已關閉，唯一須改是把已準備的 current-state 正文真正套到 live PR。雲端 API 原 GET 回覆 Forbidden，正文尚未套用，不標 READY。`p88_priority` 已完成交接並停止，沒有持續監看。
- main 仍 `feb502d7b3bade2334733a4349c87ff91b88621e`；#288 尚未合進 main。

## 已停止的工作線與接手狀態

| 工作 | 分支 | 產品來源 S | 已推進度／下一步 |
|---|---|---|---|
| #323 | codex/geo261-load-residual-20261020 | b2445b5a270d60fdf48b07f6edddbe91266d8aa2 | E=4ea6c50796711ed1e79bae89c93d07037d317837；D=aed9c627053132fcd501dc187b8c950e117fcb95；本輪八階段全終態。完整225 suites：5200 pass／2 fail／1允許Windows GDI skip；native原exit1。紅項為兩個負控制漂移及mutation帳本stale；175三方比較通過、PF3原0。N64/main=1.1608619523綠；N32/base=1.0008656474與source calls 64/32=6.1549962284紅。四檔memo+controls候選已靜審但尚未套用／動態驗收。封存內容已由producer核對公開blob／stream覆蓋；本輪整包的獨立公開roundtrip覆核尚未完成，不冒稱已通過。 |
| #314 | codex/geo314-one-axis-stagger-20261022 | 3b0b634feb54266700cc61f26c34d7aeac4c0314 | E=f426be38fdf297d66296fb527309a7b8912ab034；D=f5669af88dcc62066aa2e5be3f16a2c3a82a81d3；六 native suites 103 方法、原 inspector、M99–M121 的 v2 外部工具已靜審，尚未執行。M110 必須保等價判定；P72B 真 Chrome 另跑。 |
| #299+#316 | codex/geo299-316-combined-20261022 | 6cad1a3cb76d7bd910125a1d70ecfffdc9183813 | E=ebbd6d19ddf64ac64fd3c902eec6e40f4484582d；D=92b3cdb38d73bc75faab3c14ac90b90edf2a52f0；M89–M98 與原九 suites／166 core scenes 的實際 CLI 已準備，新 S 動態驗收仍待跑。 |
| #318 閱讀 A | codex/issue318-reading-a-20261023 | ae74e51bba1efef48949c077635966273a9e8990 | E=9c534879b05058d2d62d8082be76038605ef0268；D=4e4e4f59cea41dbec018dd8779f2db190d320bd9；三reader原0/0/0、51方法；native7及11組0/1/0、oracle13均0。完整quick-r2終態exit1：39850次建構與逐mm／579間×8=4632、528／1056漏掃0與非buildable0均過，但保留下列三項前置oracle紅燈，不能稱整項綠。CLI／架構／golden-source-proof未跑；沒有開始修source。 |
| 不帶木工模板 | codex/kernel-without-woodworking-20261023 | 9b201164ed31069843a2b9f3787ea8ae8e22e231 | E=6f2e5e27d2f949ef63d198ceac0630a352f6b397；D=586caa52d97fef48a375794aea0a92f4bdacf4cd；13 tests 與七 phase 自證已準備，尚未跑。使用原 self-R3，不另改鎖。 |
| #324 | 既有 PR；下次 fetch 確認目前分支 | 4e176e830b691269cc72d021ce7e1bc0b167d621 | 已完成正確 PR-local 三檔清點，base=7dae5f21；不是寬 merge-base diff。尚缺合流來源全驗收及正文 41→45 更新；無新實作或測試。原件已收在 #314 E。 |
| #333 | grok/woodworking-field-rules-20261023 | 02cb11b9762da429a3dbb0eed9151f45a65ed620 | E=038928cf7a21110d6a2465883311052a46fb6386；D=a6a2aed6a6d9b326a92c73835970b834bb40e5a7。僅刪ignore兩行、FIELD bytes同；原政策0/1/0與176項peer通過。PROGRESS已標READY-TO-MERGE #333：最新ChatGPT可合併結論對3d9，後續02cb是更窄ignore修正且獨立覆核，兩者明列。未合併。 |

各已推分支的 evidence 及 PR_BODY 為該線詳細原件。除主 #288 正文分支外，各線正文分支名為產品分支加 `-prbody`。S 是產品來源，E 是封存證據提交，D 是正文檔提交；三者不可互代。#323 最終 E／D 已在表中；正文依 b7e23a25 的 2026-10-23 14:37:59Z／head b2445b5 審查改寫。舊 D=b63add264735613b42b065e98ee5e6b1b4afc677 是 native 尚未結束時的歷史正文，不能用它覆蓋本輪真終態 exit 1。最後獨立正文核對抓到審查引用舊時間，已以普通提交 aed9c627 補正；這不等於整份公開收據已獨立重驗。

## 排程與接棒

1. 本次已依最新停止指示結束所有工作線。下一位接手後先讀同步審查；恢復工作時再安排 #288 專職，不重抽已綠測量。本次不留背景監看或測試。
2. 最新使用者收尾優先級：#288 進 main 後依 #318、#314、#299+#316、#323、不帶木工模板、#324，再 #300 容量512與其他 open issues。尚未進 main 前先做可獨立推進的驗收與修正。
3. 目前已公開 source stack 的合入方向為 #323→#314→combined→#318→kernel。這是已存在歷史，不表示新收尾優先級。共享檔同步與 main retarget 由主代理根據實際 diff 指定；不得反向 merge 下游把整條產品混入前棒，不改寫既有歷史。
4. 下次仍最多兩個重工作；性能與完整canvas獨占。本次 #323 native已15:01:42真終態，scheduler1305238之後為Z，非仍在跑；UI傳輸失效後缺最外TOP RESULT，另有RECOVERY說明，不把未知launcher收尾冒0。原各stage/完整streams保留於 `/tmp/geo323-baseline-b2445b5a-v3-r1`，不用重啟舊stage。
5. #318 quick-r2已15:04:37真終態，原child/reaper/stage/launch皆1，414.317秒；runner／selftest／reaper已消失，舊launcher1350359僅Z。所有後續stage都未啟；本次兩個測試時槽均已釋放。已完成的環境維護保原件與Git objects/refs：三個/tmp checkout約回收965MB，兩個workspace checkout約604MB；不要重複退休或刪原件。
6. 子代理不各自整份重產突變帳本。最終來源確定後由主代理統籌全帳本與架構；過期結果必須如實標記，不能用 partial mutation 冒充全 ledger 綠。
7. 每個修正保留正常反證／還原、原指令、環境、完整 streams、exit、可解析 SHA；各產出交另一子代理專找錯。原失敗與環境修正不覆寫。

## 授權與未完成邊界

- 木工規則推理前先讀 main 的決策佇列 2026-10-12～15、2026-10-22、2026-10-23 各節，以及 PR #333 的 `geometry-templates/woodworking/FIELD-RULES.md`。已讀 PR333 source=3d9bd947；該頁只是引文彙整，不取代公理層。
- #318 閱讀 A 已核可；其它未核可公理／鎖定決策衝突／新數值門檻，寫 QUESTIONS.md 與該 PR 正文，接著做不受影響工作。
- Git fetch/push 已恢復，不能稱尚未推送。GitHub API 原命令仍回 Forbidden；以 handoff 的同步審查與可讀 Git refs 推進。尚無可核對的完整即時 open issue 盤點，不能宣稱全部 issues 已結案；等待轉入 repository 的盤點時先做既知工作。
- #288 唯一剩餘審查項是 live 正文；本機可 fetch `codex/geo261-final-prbody-20261023`，確認 `PR_BODY.md` SHA-256 為上列77fad4…，再執行 `gh pr edit 288 --repo ZhiQiYang/geometry-axiom --body-file <該PR_BODY.md路徑>`。這是套用已驗正文，不是合併。雲端未成功執行此操作；不把檔案已推送冒稱 live PR 已更新。
- 官方環境設定草稿已只補 `api.github.com`，原package_managers preset／install／start保持。工具回saved、requires_publish=true；尚未發布或套用，不代表API恢復。原件 `network-api-draft-20261023.json`；需要在環境設定檢閱、儲存並發布，或由本機直接套上述正文。不要盲重試API，也不要重啟已完成測試。
- #318的三個真oracle紅燈：`rc_through_reflex`預期的`C8_I19_BOUNDARY_END`未被抓到，只見`C8_I22_NON_BOUNDARY_EXTENDS`；`COLSTEP(3000)`與`FZ9`各有12個Y向配置被判core_limited而原期望buildable。PROPOSAL.md稀疏缺檔已按同S補物化後只重跑受阻項；初次失敗與r2均保留，沒有改assert或golden。下次先完成尚未跑的獨立項、一起診斷，再修／自證；若碰鎖決策先QUESTIONS。
- #213 的既有交接明列使用者自行處理；不要擅自關閉。合併由本機 Claude／使用者處理。
- #300 的先決仍含 contact_order 線性查找、擋面 O(n²) 去重、geo_eval_depend；先補已知前置驗收，不自行放寬性能門檻。

## 本階段其他交接與公開收據

- `READY-TO-MERGE #331`：最新審查 2026-10-23 10:40:32Z 對 `16801ae6983589bc1fac95db732e6b719619c6d1` 明確「可合併」。本輪只讀核對原 head、兩個草稿／checker 檔及 SSOT 未變，未新跑 checker；這不是替使用者採納條文分類，未合併。
- #333 的 READY 與修後政策反證見表格及該線 PROGRESS；live 正文只推成檔案，沒有冒稱 API 已套用。
- #288 子交接分支 `codex/geo288-p88-stable-click-20261023`：S=`8bce9239c014f070740455556c8ee1176c500af3`，E=`6418593fd0bcf802ceff2787c467d5f7d7b12d5f`，子正文 D=`03b61ca1e2ab3d6d6c0df782a575f43a948a979f`。這是子工作線交接；主驗收 F 與主正文 D 仍以上方 #288 欄位為準。
- P73 子交付 `codex/geo288-p73-final-20261023`：E=`77d1e3438d7e952230ce501bf3dddbd9a4e18580`，D=`1addc7930576e45444cb6399b05fef2ca0b3c532`；都已推。兩個 probe checkout 已完成稀疏退休，下次用前先物化來源，保留 Git objects／alternates。
- #318 最後獨立覆核為 1093 checks、exit 0、findings=[]，核原公開 bytes／hash、oracle 13 與控制，以及目前 quick 總 1 的邊界；不是新增 formal 綠燈。#314 工具與 combined 的目前來源動態仍未跑。
- 本檔旁 `handoff/` 收錄最終各線小型交接索引、獨立覆核及 #331 只讀原件；`HANDOFF_INDEX.json` 列每檔來源位置、bytes 與 SHA-256。大份完整原始輸出留在各線已推 evidence，不重包、不刪原件。
- 大型 stdout 已無損封存：#323 205,298,659 bytes 分四塊，#314 89,526,252 bytes 分兩塊；完整還原 hash 與原件相同。分塊不是重跑命令，歷史寬 diff 不可當成正確 PR-local 變更。
- 環境空間偏低；停止前約 /workspace 170 MiB、/tmp 727 MiB。不可為騰空間刪原收據、fixtures、Git objects 或 alternates。沒有未推的產品提交；外部候選與工具是否實跑須以各線交接為準。

## 雲端原件位置

- root repo：`/workspace/geometry-axiom`；主狀態：`/workspace/geo288-main-merge-20261023/ACTIVE_P88_PRIORITY.md`。
- #323：`/tmp/geo323-merge-20261023`，巨型merge stdout 205298659 bytes原件保留，SHA-256 `778f023db9aba56fa84bd85b8ff32c016aec5bb0d9470b445653b0bd3989e174`。`/workspace/geo323-merge-stdout-lossless-20261023`的四個gzip塊已真exit0、完整解壓串接同原bytes/hash；MANIFEST保存offset與每塊hash，不是重跑原命令。候選在 `combined-memo-controls-candidate-v1/`；修後三suite工具只準備於 `fixed-three-driver-preparation/`。
- #314：`/workspace/geo314-owner-20261023/fixed-source-tools-v2/README.md`。
- #318：`/workspace/geo318-formal-ae74e51b-round1`、`/workspace/geo318-reading-a-prep/formal-tools/`。
- noWood：`/workspace/kernel-no-wood-prep/NO_WOOD_FORMAL_REQUEST.json`。
- 真正 Chrome156 在 `/workspace/geo261-environment/bin` 前置 PATH，Node24.19.0，Noto CJK 已裝。不要因預設 shell PATH 找不到 Chrome 就重新安裝或誤判不能跑。

這份 NEXT 是階段停止交接，不是全專案完成報告。#325 尚未開始讀取／實作；尚無完整即時 open issues 盤點。下一位依本檔與各線 PROGRESS 接續。
