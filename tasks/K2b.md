# Codex 提示詞:K2b 實作(K2b-1 零房+能力 → K2b-2 UI+生命週期)


## 0. 公理澄清(必讀)
- 公理澄清 PR #199(分支 axiom/stack-clarify-20261011)修正了 PF-0/K1/K2b/K2a 多條措辭(D41、D43–D45、D48、D57、D58、I63、I64、I66、R49、R53–R55 等)。行為以澄清後的條文為準:#199 合併前先讀它的 diff;合併後把它 merge 進你的分支(merge commit,不 rebase)。

## 1. 任務與規格位置

- Repo:`ZhiQiYang/geometry-axiom`。
- 規格:`geometry-core/zero-room-id/` 整份,在分支 **`axiom/adopt-zero-room-id-k2b-20261011`**(PROPOSAL.md r4.1、AXIOM-DIFF.md、decisions-provisional.md)。驗收表 ZR01–ZR12、PC01–PC21 在 PROPOSAL §1.6,逐行 oracle 以此為準。
- 公理條文 D51–D55、I63–I67、R51–R53 已寫入同一分支的 `公理層.md`——以此為 SSOT,不得從既有程式碼反推行為。

## 2. 分支與 PR base

- base:`axiom/adopt-zero-room-id-k2b-20261011`(公理寫入鏈,疊在 K1 之後;K2b 的實作分支從它切出)。
- 建議切兩個 PR:
  - **K2b-1**(零房建立+能力/格式守門:ZR01 能力面、ZR06、ZR10、PC04、PC11、PC12):`git switch -c feat/k2b-zero-room-impl axiom/adopt-zero-room-id-k2b-20261011`,PR base 設該 axiom 分支。
  - **K2b-2**(UI+生命週期:ZR02–05、07–09、11、12、PC01–03、05–10、13–21):從 K2b-1 分支切出,PR base 設 K2b-1 分支。
- 若決定一個 PR 做完,base 一律是 axiom 分支,不 base main。

## 3. 必守事項

- **先讀 `AGENTS.md` 全文**:`公理層.md` 是 SSOT 不得擅改;閱讀器只准有一份;`current_geometry.c` 統一 CRLF(本切片不改它);`公理層.md`/白話/閱讀器/`BACKLOG.md`/`決策佇列.md` **一行都不動**。
- **GEO-219 減項**:PR 正文必須有「無新入口」或逐項減項說明。
- **測試先行**:依下方規格先寫測試;每個「要打掉的變異」實做突變驗紅、驗完還原。
- **`tests/mutants_results.json` 不能手改**:你的切片若在 mutate 涵蓋範圍改動了 `current_geometry.c`(本切片不應改),要在合併樹重跑 `tests/mutate.py` 重產;若沒改 C 也照實在 PR 寫「mutate 無新覆蓋」。
- 新測試檔必須在 `tests/run_all.py` 登記(PY_NEEDS 或 NODE_TEST_FILES/NODE_EXCLUDED),並更新 `tests/run_all.expected.json`。
- **不合併、不 force push、不關任何 PR 或 issue**。

## 4. 並行注意(共用檔,勿越界)

- `geometry-web/project-store.js`、`geometry-web/reference-workspace.js`、`tests/run_all.py`:提案明寫**同一整合 owner、不平行改**——K2b-1 與 K2b-2 依序做,且注意其他線(K1、K2a、K3、Q38j、W、PF)也在動這些檔;寫時只動自己需要的區段。
- `feature-attachments.js`:K1、K2a、K3-48 共用;你的變更是 `assertKind` 白名單加 `room-candidates`、envelope records 上限 4→5、`capabilities()` 回 `room-candidate-drafts/1`、本 kind 單筆 1 MiB、`boundedJSON` 對 `room-candidates` 的 rawInputs/rowKey 放寬到 20,000(比照 legacyGeometry 路徑;PC05 靠它)。
- `app.js`:K1-b、K2a-A、K3-L、W-R3a、K4 共用;只動 `nativePending`/`apiRequest`/`geometry-definition-changed` 事件掛接與 `definition-import` 命令正規式區。
- `source-plane.js`、`room-collection*.js`、`room-outline*.js`:你的獨佔檔。
- **不改 `current_geometry.c`**(能力守門在 project-store/feature-attachments 層)。

## 5. 溝通方式

- PR 留言開頭一律加 **「【Codex】」**。
- 「【WSL 裁判】」是 Claude 的驗證留言(綁 SHA 的綠/紅判定);「【dot】」是整合者的審查留言。回覆它們時不要假裝自己跑過 WSL。
- PR 正文要寫:對應工單/條號、修改前後證據、突變測試結果、WSL 收據路徑(若無就寫「CI 受帳號計費阻擋,正式合併裁判由本機 WSL 收據提供」)、未驗項、GEO-219 減項或「無新入口」、疊在哪個 PR 上。

## 6. 回報格式

- commit 與 PR 不要加 Claude 的署名或標記(你不是 Claude)。
- 完成後在 PR 留言(【Codex】開頭):head 完整 SHA、改了哪些檔、哪些驗收項已過、哪些未驗及原因。

## 測試規格摘要(照 PROPOSAL §1.6 oracle;test-specs 內容摘錄)

- **ZR01**:無 source-rooms 附件;F=boundary 1(4000×3000)、來源頁 P;第 1 列「房 A」接受 → 附件 `source-rooms/3`:planes=[fromPage(P),basisRevision 1]、collections=[{planeId,roomIds:[A]}]、rooms[A] 各欄齊(boundaryRef.id、confirmed、acceptedBasisRevision 1、display{crop:[0,0,300,250],opacity,locked});boundary 1 dump 逐字不變;history 恰+1。
- **ZR02/03**:undo 後附件回「無 source-rooms」、session 失效;redo 逐欄相同。續接「房 B」→ roomIds=[A,B]、第 3 列 pending。
- **ZR04/05/06**:同 sourceId:page 已被 adopt→prepare 前拒;預覽後改校準(mmPerPx 10→12)→確認拒;256 planes→admission 拒。三者 World/附件/history/dirty 不變、零殘留 token。
- **ZR07–09、11、12**:confirm 回覆丟失→不重送、receipt recovery;命名取消→staged 退休、不建 plane;同外環→警告仍接受、F 與 D3 並存;舊圖頁校準改→basisRevision 不動、不違同頁唯一;未配對 `line confirm`→全部房間轉需重新關聯、記錄不刪。
- **PC01–21**(關鍵 oracle):PC01 原字串(`"1e"`、`" 003 "`)逐字 roundtrip+`room-candidate-drafts/1`;PC02 基準變→過期「共同基準已變更」;PC03 roomsPin 不符過期;PC04 format `/16`/刪能力/schema `/2` 三案拒開;PC05 20,000 可存、20,001 在釋放編輯器前拒;PC06 主案 native D3+房+草稿同一步、不為既有房送 `boundary`、nativePin 只重用 rcw:77 回執,(甲) 快取不可用→prepare 前拒、(乙) 群組內才失快取→整筆回滾不逐房補讀;PC10 analyzerRevision 不同→不過期+加註;PC11 全 accepted→附件寫 null、不升版;PC12 舊 `/16` 位元組不變;PC14 >1MiB→保存成功但候選未寫入+狀態列明示;PC15 新分析→「捨棄已保存的 N 列候選」確認框+一步可復原;PC16 同值同步無寫入不重蓋不退休+測試接縫負例;PC17 save/exportBytes/freeze/finish 各寫一次、ticket 不寫、無 await;PC18 stamp 變→不重蓋+「本分頁工作階段已失效」;PC19 persistSession/readScenarioProject 的 exportSnapshot 不寫候選;PC20 甲乙丙三案 session 續用各一步 history;PC21 130 房分 64/64/2 批+批間讓出事件圈、第 70 房失敗→「不可用」只可檢視/捨棄/重新分析。

## 7. 回饋處理
- 收到「【dot】」或「【ChatGPT 審查】」意見:成立就修(測試先行+突變),不成立附條號與證據回覆;回覆開頭「【Codex】」。
- 合併時若與其他線衝突,在你的分支用 merge commit 解決,不 rebase 已推送的歷史。
