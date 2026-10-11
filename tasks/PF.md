# Codex 提示詞:PF-2→PF-6(panel-fill 產品實作)


## 0. 公理澄清(必讀)
- 公理澄清 PR #199(分支 axiom/stack-clarify-20261011)修正了 PF-0/K1/K2b/K2a 多條措辭(D41、D43–D45、D48、D57、D58、I63、I64、I66、R49、R53–R55 等)。行為以澄清後的條文為準:#199 合併前先讀它的 diff;合併後把它 merge 進你的分支(merge commit,不 rebase)。

## 1. 任務與規格位置

- Repo:`ZhiQiYang/geometry-axiom`。
- 規格:`geometry-core/panel-fill/` 整份,在分支 **`axiom/adopt-panel-fill-pf0-20261010`**:
  - `AXIOM-DIFF-r2.md`:條文差異+§6 驗收表 PF01–PF24(逐行 oracle)。
  - `amendment-r2.1-R43.md`:R43 承接判定修訂+§4 的 E1–E3 確定數值(PF23/PF24 的 oracle)。
- 公理條文 D41–D45、I52–I57、R41–R46 已寫入該分支 `公理層.md`——SSOT。
- PF-1 已完成在 PR #190(分支 `feat/pf1-finish-surface-20261011`),實際檔案清單見其 diff:`current_geometry.c`、`engineering_commands.inc`、`finish_surface_types.h`+`finish_surfaces.inc`、`transactions.inc`、`modeling/common.py`、`engineering_bridge.inc`、`engineering_transport.py`、`panel_fill_bridge.inc`、`serve.py`、`web_bridge.c`、`tests/test_panel_fill_finish_surface.py` 等。

## 2. 分支與 PR base

- base:`feat/pf1-finish-surface-20261011`(PF-1)。
- 依序建議五段(或合併成較少 PR,但每個 PR base 一律是上一段或 pf1 分支,不 base main):
  - **PF-2** 障礙集合/裁切/預覽(PF04、PF18)
  - **PF-3** D43 縫線/R41 兩層/I53 開區間/R43 承接(PF02、03、08、09、14、23、24)
  - **PF-4** R42–R46 試排/候選/角色(PF05、10、15、17、20、21)
  - **PF-5** DSL/dump 層:at-face 鍵、from-fill(PF19、22)
  - **PF-6** 前端/保存/驗收端到端(PF11 殘項等)

## 3. 必守事項

- **先讀 `AGENTS.md` 全文**;`公理層.md`、白話、閱讀器、`BACKLOG.md`、`決策佇列.md` 一行不動。
- `current_geometry.c` 統一 CRLF——**一律二進位模式讀寫**;補丁腳本用檔案寫入工具,不用 heredoc。
- **GEO-219 減項**:PR 正文「無新入口」或逐項。
- **測試先行**;PF18/PF20/PF23/PF24 的 oracle 文件自註「依條文推導未實跑」(R-9)——先照提案數字寫測試,實跑不符**回報**,不得逕改預期。
- 改 `current_geometry.c` → `tests/mutants_results.json` 在合併樹重跑 `tests/mutate.py` 重產,不手編。
- 新測試檔登記 `run_all.py`+`expected.json`(比照 `test_panel_fill_finish_surface.py` → PY_NEEDS `bridge`)。
- **不合併、不 force push、不關任何 PR 或 issue**。

## 4. 並行注意

- `current_geometry.c`:原生序列**排在 K3-L 之後、與 K2a-B 並列**;你的改動限 panel-fill 相關節(finish_surfaces、panel_fill 判定、I53/R41/R43/R45 路徑)。
- `transactions.inc`(K3-L 共用)、`engineering_bridge.inc`(K1-a/K3-L 共用)、`web_bridge.c`(K2a-A/K3-L 共用)、`serve.py`(K1-a/K3-L/Q38j-a/W-R3a 共用)、`run_all.py`+`expected.json`(全員)。
- `project-store.js`(K1-b/K2b/K2a/K3/Q38j-b 共用):PF-6 的保存層改動限 panel-fill 附件/能力區段。

## 5. 溝通方式

- PR 留言開頭加 **「【Codex】」**;「【WSL 裁判】」=Claude 驗證、「【dot】」=整合者審查;不假稱跑過 WSL。
- PR 正文:條號/驗收編號、前後證據、突變結果、WSL 收據路徑或「CI 受帳號計費阻擋,正式合併裁判由本機 WSL 收據提供」、未驗項、GEO-219、疊加關係。

## 6. 回報格式

- commit 與 PR 不要加 Claude 的署名或標記(你不是 Claude)。
- 【Codex】留言:head 完整 SHA、改檔、驗收項過/未驗。

## 測試規格摘要(test-specs 摘錄;oracle 以 AXIOM-DIFF-r2 §6 + amendment §4 為準)

- **PF04**:缺角/孔/障礙裁切分片為獨立 ordered loops、不重疊不漏區;共面障礙(側面與輪廓邊共面)**不裁切**(I53 開區間);預覽逐障礙列 R_k 與 F 關係+兩層各自判定。
- **PF18**:房中柱成孔(孔邊無邊材候選、主/副支端頂孔邊合法);貼牆/角柱成凹口(凹口外環邊有 boundary/邊界主支候選);凹角全選→整批 `V_CUT_PRIORITY` 拒(I19/I22+K8);取消該 boundary→鄰牆邊界主支頂外輪廓邊同拒。
- **PF02**:板寬 100/縫 3/a=0 → 縫中心精確 **101、204**(非 .5),與 D10a/D29 REPEAT_PANEL 一致。
- **PF03**:起排點內外/負索引;交丁 p 奇數列平移 δ **不累加**(j=1 +δ、j=2 回 0、j=3 +δ)。
- **PF08**:樑 z[2500,2800]、t=9、h=30;完成面 2600→兩層遇樑;2400→兩層通過;2480→面材通過角材層遇樑,邊材沿樑側、主支停在邊材側面。
- **PF09**:2491(板背=樑底)→面材通過角材層遇樑;2461(角材頂=樑底)→兩層通過;垂直面不只比 z;無手動豁免。
- **PF14**:h=33→B=33/+N 成立;B=27 或 −N → `V_DERIVED_TIMBER`;改 h 未同交易改角材→整批拒。
- **PF23**(E1):F=[0,1000]×[0,300]、板 915×1830/縫 0/a=(−815,−100)、直排;障礙 R=[105,200]×[50,100]、W=[−2400,9];足跡 [90,120]×[0,300]、X=8 → 三段 (0,50)d=(10,20) 綠、(50,100)d=(10,5) **承接不足**、(100,300)d=(10,20) 綠;X=5 全綠仍三段。
- **PF24**(E2/E3):R=[125,200]…(距足跡外緣 5mm)與 [120,200]…(恰貼)→ 皆合併一段 (0,300) d=(10,20) 已承接,與無障礙逐字相同。
- **PF05**:X=8 綠、7/9 紅且指出不足子段;X=9 使 8/8 變紅仍可保存(D44 門檻≠合法性)。⚠ 夾具與 X 值組合驗收表未給全,實作需先實跑定值。
- **PF10**:候選=外環邊材+合法跨距板縫材,不補中間支撐;FREE 邊列出;R6/I19 拒絕不因 Q40 略過;失敗無部分角材。
- **PF15**:樑橫貫垂直主支軸;u 縫 primary、v 縫 secondary→牆邊/樑側得 boundary+邊界主支、全選可提交;反選整批拒;刪一支 boundary→I19 整批拒。
- **PF17**:交丁試排導出 D29 值快照;改試排不動快照。
- **PF20**(Q47 248 型):房 4000×3000、板 915×1830/縫 3、樑 v∈[700,1000] z∈[2500,2800]、完成面 2480 → 面材通過角材層遇樑;u=916 縫有效段 (0,1830)/(1833,3000),與 G_角材層 交得 (0,700]/[1000,1830)/(1833,3000);樑兩側各一支 primary(v[27,673] 與 [1027,2973]);u=1834/2752/3670 同理;全選可提交。
- **PF21**:交丁被錯開軸選 primary→輸入檢查整批拒;secondary→副支落在各 band 板背區間內。
- **PF19**:at-face 引用邊被障礙切成兩段→鍵不相等整批拒;只平移樑→依 I8a 預覽重算。
- **PF22**:s=−1 建 from-fill 主格不被 I10 拒;signed k 識別;頂點引用拒、衍生邊鍵引用成立。
- **PF11 殘項**:已確認角材保存重開不丟;衍生承載面只存保存欄位、重推導一致。

## 7. 回饋處理
- 收到「【dot】」或「【ChatGPT 審查】」意見:成立就修(測試先行+突變),不成立附條號與證據回覆;回覆開頭「【Codex】」。
- 合併時若與其他線衝突,在你的分支用 merge commit 解決,不 rebase 已推送的歷史。
