# Codex 提示詞:K2a 實作(K2a-A 草稿集合 → K2a-B 重複開間)


## 0. 公理澄清(必讀)
- 公理澄清 PR #199(分支 axiom/stack-clarify-20261011)修正了 PF-0/K1/K2b/K2a 多條措辭(D41、D43–D45、D48、D57、D58、I63、I64、I66、R49、R53–R55 等)。行為以澄清後的條文為準:#199 合併前先讀它的 diff;合併後把它 merge 進你的分支(merge commit,不 rebase)。

## 1. 任務與規格位置

- Repo:`ZhiQiYang/geometry-axiom`。
- 規格:`geometry-core/drafts-topology/` 整份,在分支 **`axiom/adopt-drafts-topology-k2a-20261011`**(PROPOSAL.md、AXIOM-DIFF.md、decisions-provisional.md)。驗收:M01–M15+M14b 在 §A6、BR01–BR16+BR03N+BR10b 在 §B;`wsl/` 見證場景(br_rect.scene、br03_lroom.scene、br07_hole.scene)為確定 oracle。
- 公理條文 D56–D58、I68–I69、R54–R55 已寫入同一分支 `公理層.md`——SSOT,不得從既有程式碼反推。

## 2. 分支與 PR base

- base:`axiom/adopt-drafts-topology-k2a-20261011`(鏈頂,疊在 K2b axiom 之後)。
- 兩個 PR:
  - **K2a-A**(grid 編輯草稿集合:M01–M15):`git switch -c feat/k2a-drafts-collection axiom/adopt-drafts-topology-k2a-20261011`,PR base 設 axiom 分支。
  - **K2a-B**(assembly-bay-repeat:BR01–16):從 K2a-A 切出,PR base 設 K2a-A 分支。

## 3. 必守事項

- **先讀 `AGENTS.md` 全文**;`公理層.md`、白話、閱讀器、`BACKLOG.md`、`決策佇列.md` 一行不動;`current_geometry.c` 統一 CRLF(K2a-B 需改 C 時**一律二進位模式讀寫**,不許用會吃跳脫的 heredoc 產生補丁;見 AGENTS.md 地雷節)。
- **GEO-219 減項**:PR 正文寫「無新入口」或逐項減項。
- **測試先行**;每個驗收項的「要打掉的變異」做突變驗紅再還原。
- K2a-B 改 `current_geometry.c` → **`tests/mutants_results.json` 必須在合併樹上重跑 `tests/mutate.py` 重產,不得手編**;K2a-A 未改 C 照實寫「mutate 無新覆蓋」。
- 新測試檔登記 `tests/run_all.py` + 更新 `run_all.expected.json`;wsl 見證場景可移入 `tests/` 當原生見證。
- **不合併、不 force push、不關任何 PR 或 issue**。

## 4. 並行注意

- `feature-attachments.js`(K1/K2b/K3-48 共用):只加集合 validator、`orphans`、`inputRefs[].lost:true`、能力 `grid-editor-drafts/1`。
- `project-store.js`(全員共用):格式選擇、/1 與 /2 互斥拒、降版拒、能力上限。
- `reference-workspace.js`(九方共用,最高衝突):`readGridDrafts`/`setGridDraft`/`repinGridDraft`、`lost` 不可抹除、孤兒掃描、confirm 以 draftId 清除;K2b 提案明寫此檔同 owner 不平行改——你的寫入只動 A7 列的區段。
- `web_bridge.c`(K3-L/PF 共用):只補核心確認回執「本交易刪除的物件」欄位。
- `app.js`(多方共用):`geometry-definition-changed` 草稿清單。
- `grid-system-workspace.js`:大概率你獨佔(K4 未列此檔)。
- **K2a-B**:`current_geometry.c` 原生序列——提案明寫排在 K3-L 之後、與 PF-2~6 並列;改動限 BR 相關節。

## 5. 溝通方式

- PR 留言開頭加 **「【Codex】」**;「【WSL 裁判】」=Claude 驗證、「【dot】」=整合者審查;不得假稱跑過 WSL。
- PR 正文:工單/條號、前後證據、突變結果、WSL 收據路徑或「CI 受帳號計費阻擋,正式合併裁判由本機 WSL 收據提供」、未驗項、GEO-219、疊加關係。

## 6. 回報格式

- commit 與 PR 不要加 Claude 的署名或標記(你不是 Claude)。
- 【Codex】留言:head 完整 SHA、改檔清單、驗收項過/未驗與原因。

## 測試規格摘要(test-specs 摘錄;oracle 以 PROPOSAL 為準)

**K2a-A(M01–M15)**:M01 兩草稿並存無取代對話框;M02 真 ZIP 重開兩份 raw 逐字+`grid-editor-drafts/1`;M03 續開同 draftId;M04 確認該份移除、一步 undo 同還原;M05 pin 來源被改→預覽拒、明選重取;M06 刪來源→同步標孤兒、undo 回有效;M07 兩份非同孤兒同目標→整份拒;M08 第 17 份拒不截斷;M09 inputRefs 指草稿→拒;M10 三種保存格式分派(單份/孤兒集合格式/含 `lost` 集合格式);M11 降版/剝能力/未知 schema/假 orphans/`lost` 非 true/`lost` 在 baseRef/單份出現 `lost` 全拒;M12 晚到舊 flush/舊介面/抹 `lost` 全不生效;M13 瀏覽器閘 1280/390px;M14 同 id 同內容新物件不使孤兒復活;M14b `lost` 保存重開旗標在、同 id 重取得拒;M15 重新取得基底只做兩方比對、取消不變。

**K2a-B(BR01–16)**:BR01 主支 500/1500/2500→3×2960、副支 4×973、owned 7;BR02 加貼牆 e3/e1→5×2960、460/973/973/1459、owned 13(見證 br_rect);BR03 L 形兩實例+y2 零生成合法(見證 br03_lroom 16 支;全域排序相鄰突變必紅);BR03N 自我支撐→`SELF_SUPPORT` 指名路徑;BR04 插主支→mapping 鍵四新兩舊、長 473(三突變必紅,`SPAN_BETWEEN_BLOCKED` 待原生實跑);BR05 既有 at-face 引用整筆拒;BR06 間距改→key 保 timberId;BR07 孔不帶 omit 恰列阻擋格、帶 omit 成功(見證 br07_hole);BR08 部分覆蓋拒指名;BR09 各槽位 UNSUPPORTED;BR10/10b 輸入拒絕與合法零生成;BR11 56 owned/記錄 >8191 bytes→CAPACITY 不部分新增;BR12 保存重開+能力/format 負例;BR13 undo-redo/過期 token/遺失回覆沿 G07/G08;BR14 真 UI;BR15 回歸;BR16 拖參考線→新建列來自原生 `json_reference_preview`(`before:null` 或 `change:"created"`,非前端補列)。

## 7. 回饋處理
- 收到「【dot】」或「【ChatGPT 審查】」意見:成立就修(測試先行+突變),不成立附條號與證據回覆;回覆開頭「【Codex】」。
- 合併時若與其他線衝突,在你的分支用 merge commit 解決,不 rebase 已推送的歷史。
