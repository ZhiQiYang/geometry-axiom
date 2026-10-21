# framing oracle 分支唯讀預審

結論：**目前仍不足以宣告可合併。** 遠端內容與交接相同，已完成相當多分類修正與手寫回歸案例；本次另確認核心限制裁判缺少「限制種類 ↔ C8 理由」綁定，並發現輸出圖說漏標核心限制。原審查全文與第 22 輪正式收據未取得，原三阻擋一須改不可自行解除。

本報告只供 #288 等待驗收期間預備下一項工作，不修改產品、不合併、不開 PR、不推送，也不進 #288。`20261021` 沿用使用者交接標籤；本次讀取發生在 runner UTC 2026-10-20，不改寫任何舊紀錄日期。

## 來源與操作範圍

- 遠端分支：`fix/framing-oracle-review-20261020`。
- `git ls-remote origin refs/heads/fix/framing-oracle-review-20261020` 實得完整 head：`1126991c9dbd3de92d8cce6eab2419f8f7970e34`，exit 0。
- 三個提交依序為 `e9ca81e2e64f6ea8121daf9bcccff654c8fd8011`、`9b04a3c8b4e2c0395bf8740d8dbaecb748eb7669`、`1126991c9dbd3de92d8cce6eab2419f8f7970e34`。
- 直接基底：`adbaebf9c73ea6801d7b4d5214e4b846b132923b`（#307 合入後）。未將目前 #288 候選來源帶入。
- 已 fetch 該單一 ref；另建 detached worktree `/workspace/geo261-framing-review`，兩步 exit 0。審查結束時 `git status --porcelain` 為空。
- 相對基底共九檔變動：oracle 四份 Python、一份 README、兩份 JSON，加 core-probe 的產生器及其測試；其中 Python 程式共六檔。未改 `公理層.md`、`決策佇列.md`、`AGENTS.md`、`tests/run_all.py` 或 `tests/run_all.expected.json`。
- 已讀 HANDOFF、AGENTS、產品願景、#318/#319 的 DESIGN／TESTS／補丁、oracle 新增說明、相關 SSOT 與差異；另由獨立代理唯讀交叉檢查分類語義及消費端。
- 依交接記載目前沒有 PR；本次沒有 GitHub API，因此未把這句冒稱為即時查得的 GitHub PR 狀態。

下文行號均指上述固定 head，不指 #288 工作樹。

## 原三阻擋一須改：可核對到哪裡

交接 `handoff/HANDOFF.md:62` 指向 #251 的 head `3d858c3`，並說三阻擋一須改尚未完成驗收、審查。分支 `oracle/README.md:282` 同樣聲稱回應「阻擋 1–3、須改 4」，但可讀交接及分支沒有保存該次 ChatGPT 留言全文。

| 原項目 | 可讀的對應 | 本次判定 |
|---|---|---|
| 阻擋 1 | README:45、106–115：物理衝突與核心限制分開，528＋鏡像 1056 排法改列 core_limited | 已有實作及釘選案例；下列 R1 與 R2 仍限制結論，未重跑正式掃描 |
| 阻擋 2 | README:50、292–295：誠實執行的 SPAN_PARTLY_RC／C7_P182_FAIL_UNCONFIRMED | selftest:674–716 已列 FZ145／139／146 的原房與鏡像，共 72 排法，18 個舊失敗排法釘縫位與 trace；未在此 head 重跑 |
| 阻擋 3 | 僅 README:282 的總稱 | 未取得原文，不能猜它是某一個新測試或宣稱已解決 |
| 須改 4 | 同上 | 未取得原文，不和更早審查同名項目混用，也不自行關閉 |

後續形成新 PR 正文前，需取得 #251 該次原留言及相關最後推送後全部留言，逐項對照。不能把較早第 20／21 輪審查或這次發現的 R1 當成原阻擋 3。

## R1：核心限制配對只比端面，錯誤種類可以冒用另一種限制的佐證

位置：`oracle/framing_oracle.py:2027` 的 `core_limit_problems()`，特別是 2031–2037；結果傳至 `verdict():2052`，並供 `candidate_phys_ok():1262` 使用。

宣告與 C8 失敗只以 `(id, end)` 組成集合配對。宣告中的 `code`、`check` 沒有參與核對，因此同一料件、同一端面的不相干 C8 原因也被接受。這比 README:45 所說的「每筆失敗與宣告逐筆對得上」弱，可能把新的未宣告核心錯誤藏在既有合法分類之下，進而讓 P-182 把它當成物理可行的退路。

本次沒有執行 oracle 建構或掃描；只從實際來源 AST 擷取 `CORE_CHECKS`、`core_limit_problems`、`verdict`，傳入固定資料做純函式取樣，程序 exit 0。實得：

```text
宣告：CORE_LIMIT_BOUNDARY_END_FREE
宣告 check：C8_I19_BOUNDARY_END
id=7、end=2600

失敗 C8_I19_BOUNDARY_END，同 id/end → ('core_limited', [])
失敗 C8_I19_PRIORITY，同 id/end     → ('core_limited', [])
```

第二筆應是未被這種限制解釋的失敗；現在與正對照相同。這是裁判函式的可重現分類缺口，尚不是聲稱找到自然房型會產生此特定錯誤組合。

修正建議：由每個 `CORE_LIMIT_*` 定義可佐證它的 C8 原因集合，再核對理由、料件及端面；拒絕未知限制碼、理由錯配及未被允許集合解釋的額外失敗。**不能盲目改成一筆對一筆**：README:114 明載 `CORE_LIMIT_MAIN_ON_EXTENSION` 可同時由同一端面的 `C8_MAIN_ON_EXTENSION` 與 `C8_I19_PRIORITY` 佐證。此關係須明列、測正反例，不放寬 SSOT。

測試缺口：`selftest.py:1070` 只驗「宣告全刪」及「多一筆不同端面的假宣告」，沒有驗同端面理由錯配、錯碼或多出另一種 C8。新增這些反例後，精確撤回理由核對應由具名斷言轉紅；不得把語法錯誤或任意例外當 killed。

## R2：全部候選因程式缺陷被淘汰時，仍會被標成物理不可施工

位置：`framing_oracle.py:1243`–1249、`verdict():2049`；已知例子在 README:119–126。

P-182 沒找到核心可表示候選，也沒找到已宣告的 core-limited 候選時，一律把 `P182_NO_FEASIBLE_CANDIDATE` 放進 `conflicts`；`verdict` 看見 conflicts 即回 `unbuildable`。README 已承認有些候選只是 C11 的 2 mm 缺陷，或併料端面頂柱面料造成尚未分類的 I19 錯誤，物理不可行並未確認。

這是分支自己揭露的既有界線，本次不冒稱新回歸；但它與「conflicts 只放物理排不出的原因」的總述不完全一致。因此不能以 528／1056 的分類搬移宣告所有物理／核心／程式錯誤已分開。

後續應在明確限定的範圍內處理：至少令 `inconsistent`／未判定與真物理衝突在輸出及掃描統計可辨，或在正文逐項保留例外，不把尚未證明的房型寫成物理無解。不要藉此改 I19／I22 或替使用者決定牆階路線 B。

## R3：圖說把 core_limited 縮成無條件的「可施工」

位置：`oracle/render.py:106`–121。

表格已用 `label = 可施工(核心限制)`，說明也列限制碼；但圖說在 121 行仍以 `ok` 布林輸出「可施工」。`ok` 同時包括 buildable 與 core_limited，因此單看選中排法的圖會丟失核心不能接受的限制。

建議讓圖說沿用完整判定 label，並附必要限制碼；以有核心限制的固定房型檢查輸出 HTML，再精確撤回圖說修正確認具名斷言失敗。本次只讀模板字串，未產 HTML、未開瀏覽器，也不宣稱視覺驗收完成。

## 已有的有效測試設計與尚未驗證的範圍

- `Region.inside`（framing_oracle.py:214）針對 x 落牆線時轉用另一軸；selftest:478 起有十二個手寫室內／室外點，三間半寬凹角 L 房釘八種排法縫位，另有鏡像、轉置及 216 排法小掃描。這比只驗不崩潰完整，但本次沒有重跑。
- C3 `x_band`（framing_oracle.py:1569）沿碎塊交集維持連通 y 範圍；selftest:844–875 驗 H6 原向、轉置、左右鏡像的精確缺口與六個手寫矩形案例。鏡像正對照只要求 C3 無誤報；前兩項才要求整個候選全過，不能三項都寫成全檢查綠。
- 核心限制房 STEP20（selftest:1059–1066）釘宣告端面、十支副支的逐支區間及板端縫；FZ120／148M、FZ107／114 也有具名理由、縫位及候選偏好對照。這些能支撐特定規則，但不消除 R1 的理由配對缺口。
- `sweep_family():1117` 對沒有物理衝突的結果跑 `verdict`；`core_limited` 另列，`inconsistent` 加入 bad。`expected_for_scan():1161` 仍只在 CI 抽樣時過濾，quick/full 比完整預期清單。已具備集合漏項偵測設計。
- P-182 建構與裁判的候選重建仍共用 `build_candidate`（1256–1258），不是獨立實作；手寫案例與原始碼突變才是第二道證據。
- `_p182_family():1397`–1419 對只有 `C11_MAIN_NOT_BUTTED` 的結果另計已知缺陷、不令 suite 失敗。後續收據必列其數量；不能把 exit 0 寫成所有實際候選均通過完整物理檢查。
- `core-probe/gen_scenes.py:63` 已排除 `core_limits`，`test_gen_scenes.py:388` 有相應合成排法；目前 golden 的 64 排法限制欄都是空的，故只重跑原 64 場景不能證明新過濾有效。需精確撤回 `and not layout.get("core_limits")` 做具名負控。

## 原始收據與規格界線

README:283、298–299 引用外部 `round22/`、`run10.py`、`source-mutants.txt`，並把最終秒數、159 處原始碼突變的結果及等價證明留給尚不存在於交接中的 PR 正文。已在交接及本分支相關目錄搜尋，未找到這些原件。`handoff/drafts/oracle-318-319/TESTS.md` 是較早草稿：仍要求 step 528、step_mirror 1056 為「不可施工」，其原始 F1 邊界端面草稿亦已被後續路線取代，不能原封不動當本 head 的驗收腳本。

因此 README 裡 Windows 第 22 輪的綠燈只能記為歷史敘述，不能記作此處新重跑。尤其 X3 於舊紀錄靠 AssertionError 中止，原文已明說不是斷言轉紅；後續突變表應保留 crashed／invalid 與 killed 的區別。

SSOT `公理層.md:1318`–1330 的 I19 仍要求擋面優先級嚴格較小，`1339`–1353 的 I22 仍要求延伸端面有涵蓋全寬的擋面。分支沒有改公理，core-probe 排除核心限制的方向與此一致；oracle 的物理分類不能作為核心接受或正式模板建立授權。README:128–131 的併料／退縫代價、連續退縫及候選偏好仍須保留為待決或可推翻推論，不能由本次審查定案。願景也不是擴大授權。

獨立覆核另確認 R45:2423–2424 仍不自動補中間支撐、仍要求使用者明選後整批驗證；PROPOSAL:27、145–149 保留模板與既有 R45 的界線。custom 4 的先前授權在 `決策佇列.md:584`–600 記為使用者選 C「規則不改，換登錄」，不是本輪自行改優先序。R40:2327–2336 的重算契約未改，這九檔也未接 runtime 重算或提交流程；不能據此聲稱已做該執行期驗收。

目前基底尚無 #288 的 `geometry-core/domain-decoupling/product-architecture.json`。這是分支來源差異，不是檔案遺失產品缺陷；#288 合入且後續更新基底後，才按當時 manifest 核對這九個變動檔及可執行檔登記，重產四產物與三 gate。

## 本次輕量核對與結束碼

| 核對 | 結束碼 | 結果 |
|---|---:|---|
| `git ls-remote`、單 ref fetch、detached worktree 建立 | 各 0 | 遠端完整 head 與交接一致，未改既有分支歷史 |
| `git diff --stat`、`git log`、相關 SSOT／測試差異讀取 | 0 | 九檔差異，三提交；未改產品公理或 root native runner |
| 六份變更 Python 的 `ast.parse`＋JSON 靜態核對（修正後合併程序） | 0 | 只解析、不 import；golden 移除新增的 64 個空 `core_limits` 欄後與基底完全同值 |
| 預期清單靜態遷移核對 | 0（同上程序） | step 的 528、step_mirror 的 1056 個 `(房間,排法)` 與舊集合完全相同，移至 core 清單；新三份物理 unbuildable 清單均空 |
| R1 AST 純函式兩個固定輸入取樣 | 0 | 正例及錯誤理由同端面皆回 core_limited，確認守門缺口；非正式 suite 通過 |
| 第一次合併靜態核對 | 1 | 前段 AST／JSON 已完成；末段誤假定此舊基底存在 #288 manifest，FileNotFoundError。已按真實來源修正核對，未記為產品紅或 killed |
| `git status --porcelain` | 0 | 隔離工作樹乾淨 |

本次未執行 selftest、quick/full、原始碼突變、core-probe suite、native、任何 browser job、編譯或原生核心探針。沒有提交，因此沒有「本次修正 SHA」；報告只綁定所審查的完整 head。

## 後續驗收順序（尚未執行）

1. 先補齊原三阻擋一須改全文與 round22 原件，確認實際範圍；修正 R1、R3 或明確回覆其理由，R2 保留為具名分類限制。所有差異只留 framing 分支，不帶入 #288。
2. 在新的固定來源解析／編譯語法；跑 `python3 -B geometry-core/framing-template/oracle/selftest.py --mutants-only`，要求正常組 exit 0。新增 R1 理由錯配正負對照，並保留同端面合法多理由情形；撤回修正須以指定失敗行 exit 1。
3. 跑 oracle 預設 CI 與 `--quick`，記錄實際秒數、完整建構數、core_limited／unbuildable／inconsistent／C11 已知例外數及集合比較結果。預設模式自身目標 ≤300 秒，native runner 現在給該 suite 900 秒；兩種時限不要混稱。
4. 用 `make_golden.py` 寫專用暫存路徑，和提交 golden 逐欄及 bytes 比對；不可因輸出變動直接覆寫答案。quick 的預期集合應為本版的 core 分類，不沿用草稿的舊 unbuildable 數字。
5. 取得並審閱 run10 的 159 處定義後，在隔離副本逐案跑原始碼撤回；每個 anchor 必須唯一、基準與還原綠，保存 stdout／stderr、來源 hash、變異 hash、指定 killed 行。T2 等價須依目前 `_p182_audit` 重新核對，X3 類崩潰分列，不能沿用舊結論當新實跑。
6. 依 #319 的目的跑轉置掃描與 H6 的裁判獨立性對照；移除手釘併料的額外防線時，C3 仍應抓到 `BC_no_doubling_cand`。重跑 fz20 四種子時保留所有既有缺陷分類，不把新的紅直接寫入預期清單。
7. 跑 `core-probe/test_gen_scenes.py`、`core-probe/mutation_check.py`，另加核心限制過濾的精確撤回；核對提交的 scenes／index 不變。若聲稱核心接受，再另跑固定來源的實際 core-probe，容量拒絕與規則接受分開。
8. 依交接 P-176 的測試類範圍安排相關 native 驗收。若後續變更 `tests/*.py` 或 C include 閉包，必須整份重產突變帳本；若改產品行為，則按 HANDOFF §2 重跑七項，不用本次唯讀預審代替。

最大不確定性：原審查第 3 阻擋／第 4 須改的精確要求、round22 的實際完整結果，以及更廣房型中 R1 會不會把未宣告 C8 錯誤藏入既有端面限制。本次沒有新自然房型重現、重負載測試或正式獨立可合併判定。
