# 公理疊加鏈澄清（P-049／P-058）

依 2026-10-11 指定的 [ChatGPT 審查](https://github.com/ZhiQiYang/geometry-axiom/pull/191#issuecomment-6107489606) 與 P-049 裁決，在 K2a 跟進後的 `49c391f2afbcee17bb2647fce74c3c5532a01527` 上最小修文。共 20 項：18 項修訂、2 項核對後維持（C1、R7）；不新增條號。所有本次裁決均為 **暫定(依 2026-10-09 授權 L)**，不擴大功能實作授權。

| 項 | 條號 | 舊句 → 新句 | 依據 | 裁決 |
|---|---|---|---|---|
| C1 | D48／I61 | D48／I61：已是 P-047：方案、預覽、匯出，以及其他操作的復原不改餘料；宣告本身的編輯及其復原／重做可改清單 → 核對成立，保留原文 | [審查留言](https://github.com/ZhiQiYang/geometry-axiom/pull/191#issuecomment-6107489606) | P-049；暫定(依 2026-10-09 授權 L) |
| C2 | I66 | I66：；名稱、顯示順序與畫布位置不是身分 → ；非 D54(d) 類的顯示名稱、顯示順序與畫布位置不是身分 | [審查留言](https://github.com/ZhiQiYang/geometry-axiom/pull/191#issuecomment-6107489606) | P-049；暫定(依 2026-10-09 授權 L) |
| P1 | I63 | I63：D3 經已配對的其他交易改變，該房間轉為需複核 → D3 經已配對的其他交易改變，且該房間原狀態非「需重新關聯」時，該房間轉為需複核 | [審查留言](https://github.com/ZhiQiYang/geometry-axiom/pull/191#issuecomment-6107489606) | P-049；暫定(依 2026-10-09 授權 L) |
| P2 | R55 | R55：兩個被點名擋面的 fixed 座標 → 兩支被點名支撐材之唯一相向側面的 fixed 座標<br>R55：先算出它們、再扣除將刪者求值，不會循環。之後的正式求值 → 先算出它們、再扣除將刪者求值，不會循環。無法唯一確定相向側面時拒絕。之後的正式求值 | [審查留言](https://github.com/ZhiQiYang/geometry-axiom/pull/191#issuecomment-6107489606) | P-049；暫定(依 2026-10-09 授權 L) |
| P3 | D41 | D41：及兩層判定結果 → 及各引用試排／衍生承載面可求值之對應層判定；尚無所需 t 或 h 時列出缺項 | [審查留言](https://github.com/ZhiQiYang/geometry-axiom/pull/191#issuecomment-6107489606) | P-049；暫定(依 2026-10-09 授權 L) |
| P4 | D57、R54 | D57：編輯草稿的基底狀態分三種，只由基底與尚未缺失的來源引用決定： → 新建意圖不檢查基底，僅依尚未缺失的來源引用判定有效／過期。<br>編輯草稿的基底狀態分三種，只由基底與尚未缺失的來源引用決定：<br>R54：或交易結果中基底不存在者，標為孤兒 → 或具有編輯基底且該基底於交易結果中不存在者，標為孤兒 | [審查留言](https://github.com/ZhiQiYang/geometry-axiom/pull/191#issuecomment-6107489606) | P-049；暫定(依 2026-10-09 授權 L) |
| P5 | I64 | I64：任一改變即過期並拒絕，不改提交另一份候選。 → 任一改變即過期並拒絕（純 D12 畫布位置變更除外），不改提交另一份候選。 | [審查留言](https://github.com/ZhiQiYang/geometry-axiom/pull/191#issuecomment-6107489606) | P-049；暫定(依 2026-10-09 授權 L) |
| P6 | D48 | D48：key 在清單內唯一。高水位只增不減，刪除後也不重用，因為寫在實物上的標記（R49 的 R&lt;key&gt;）日後不得指向另一段料。 → key 在清單內唯一。同一專案提交沿革內，高水位只增不減，刪除後也不重用，因為寫在實物上的標記（R49 的 R&lt;key&gt;）在此沿革內不得指向另一段料。<br>復原與重做不回退 key 高水位；開啟另一份（含較舊的）完整專案依 D51 整份替換目前專案，不承諾跨檔不重用。 | [審查留言](https://github.com/ZhiQiYang/geometry-axiom/pull/191#issuecomment-6107489606) | P-049；暫定(依 2026-10-09 授權 L) |
| P7 | R53 | R53：D31 卡片沿用 I39 參數包匯入的規則（自 0 起、只增不減的計數器取第一個未用號） → D31 卡片取得 I39 要求的新身分；每次匯入自 0 起，以本次配號內只增不減的計數器取第一個未用號 | [審查留言](https://github.com/ZhiQiYang/geometry-axiom/pull/191#issuecomment-6107489606) | P-049；暫定(依 2026-10-09 授權 L) |
| P8 | D58、裁決 B-3 | D58：故兩個 primary member 必須同槽位 → 本版限定兩個 primary member 同槽位<br>裁決 B-3：【推論】 → 【選擇】 | [審查留言](https://github.com/ZhiQiYang/geometry-axiom/pull/191#issuecomment-6107489606) | P-049；暫定(依 2026-10-09 授權 L) |
| P9 | D45 | D45：不能形成連續的 primary → 不能以同一縫段跨越多個 band；本版建議流程限定該軸為 secondary | [審查留言](https://github.com/ZhiQiYang/geometry-axiom/pull/191#issuecomment-6107489606) | P-049；暫定(依 2026-10-09 授權 L) |
| P10 | R49 | R49：鋸縫總耗損、修整總耗損 → 件間及末刀耗損（不重計修整內鋸縫）、實際端修整總耗損<br>R49：可留用剩料、廢料。<br>    可留用剩料只列在方案中 → 可留用剩料、廢料。兩個耗損欄位互斥；修整只計起端 h 與實際執行的末端修整 t。<br>    可留用剩料只列在方案中 | [審查留言](https://github.com/ZhiQiYang/geometry-axiom/pull/191#issuecomment-6107489606) | P-049；暫定(依 2026-10-09 授權 L) |
| P11 | D43 | D43：縫線兩端無限延伸 → 未錯開軸的縫線兩端無限延伸；被錯開軸的各段止於所屬 band 邊界 | [審查留言](https://github.com/ZhiQiYang/geometry-axiom/pull/191#issuecomment-6107489606) | P-049；暫定(依 2026-10-09 授權 L) |
| R1 | D56、D42、§四、I66 | D56：D32–D34 的組構規則、配置與實例草稿 → D32–D34 的組構規則、綁定與實例草稿<br>D42：**D42 面材試排（PanelFill；panel-fill/1）**：保存 → **D42 面材試排（PanelFill；panel-fill/1）**：亦稱鋪排；為已提交的 World 定義。保存<br>§四：承載面套用的草稿 → 將網格套用至承載面的草稿<br>I66：(a) 類共用者除外。 → (a) 類共用者及 (d) 類明選改用既有者除外。 | [審查留言](https://github.com/ZhiQiYang/geometry-axiom/pull/191#issuecomment-6107489606) | P-049；暫定(依 2026-10-09 授權 L) |
| R2 | D51、R50、D57 | D51：「跨專案匯入」依 D55 把另一份專案的選定定義加入目前專案，不替換。 → 「跨專案匯入」依 D55 把另一份專案的選定定義加入目前專案，不替換。<br>context 是完整專案在目前分頁中的執行期實例身分，不是保存的 projectId；新建或整份替換專案會換用另一個 context。<br>前端歷史窗內的復原可回到原 context，但復原／重做會建立新的 history frame（當前歷史框架身分），先前操作不因此恢復有效。<br>project revision 是同一 context 內的變更序號；World 或專案層資料（含附件）變更，以及復原／重做均會推進，不隨內容恢復而回退。<br>它不是條文版本，也不只計 World 變更；不同 context 的序號不互相比較。context、history frame 與 project revision 共同核對操作所屬狀態，皆為執行期資料，不隨專案保存。<br>R50：專案 context 與 revision → 專案 context 與 project revision<br>D57：只有復原造成缺失的那筆交易，且該復原仍在前端歷史窗內 → 前端歷史窗指仍保留完整專案歷史快照、可連同附件整筆復原的歷史範圍。只有復原造成缺失的那筆交易，且該復原仍在前端歷史窗內 | [審查留言](https://github.com/ZhiQiYang/geometry-axiom/pull/191#issuecomment-6107489606) | P-049；暫定(依 2026-10-09 授權 L) |
| R3 | D46、D47、D44 | D46：k 是一次鋸切從料上移除的長度 → k 是宣告的完整鋸路寬度；末刀實際耗損依 D50<br>D47：非零 uint32 key、名稱、截面 (A, B)、材料鍵 → 非零 uint32 key、名稱、D1 範圍內的正整數 mm 截面 (A, B)、材料鍵<br>D44：作為對照，實寬 27 mm 角材置中於 3 mm 縫下時兩側各壓 12 mm，那是常態參考，不是第二道門檻。 → 實寬 27 mm 角材在 3 mm 縫下以幾何中心對齊作對照時兩側各壓 12 mm，那是常態參考，不是第二道門檻。at-line 的實際承接寬度仍依 I13／R42／R43 求值。 | [審查留言](https://github.com/ZhiQiYang/geometry-axiom/pull/191#issuecomment-6107489606) | P-049；暫定(依 2026-10-09 授權 L) |
| R4 | D57／裁決 A-3、R54／裁決 A-12 | 裁決 A-3：【推論】 → 【選擇／依需求採用】<br>裁決 A-12：【推論】 → 【選擇·更新粒度】 | [審查留言](https://github.com/ZhiQiYang/geometry-axiom/pull/191#issuecomment-6107489606) | P-049；暫定(依 2026-10-09 授權 L) |
| R5 | 檔頭 PF-0 | 檔頭 PF-0：&gt; 及同日依授權 L 的暫定裁決（PF-0 r2）；其中 I53 的接觸政策（改為開區間）與 R45 的邊材及主支角色，是依授權 L 對 §7 原案、<br>&gt; 🔒Q45／Q46 字面的暫定改變，待使用者確認。 → &gt; 及同日依授權 L 的暫定裁決（PF-0 r2）；其中對 §7 原案、🔒Q45／Q46 字面的改變分別為：<br>&gt; I53 接觸政策仍暫定（改為開區間）；R45 邊材與主支角色的偏離已於 2026-10-10 由使用者確認。 | [審查留言](https://github.com/ZhiQiYang/geometry-axiom/pull/191#issuecomment-6107489606) | P-049；暫定(依 2026-10-09 授權 L) |
| R6 | §四 | §四：幾何位置一律引用，設計決定必須具名 → 參考線位置使用引用式，其中有單位的尺寸常數必須具名 | [審查留言](https://github.com/ZhiQiYang/geometry-axiom/pull/191#issuecomment-6107489606) | P-049；暫定(依 2026-10-09 授權 L) |
| R7 | I68／D48 | I68／D48：已區分草稿局部復原與前端歷史窗內整筆復原；餘料標記已使用 R&lt;key&gt; 模板 → 核對成立，保留這兩處原文 | [審查留言](https://github.com/ZhiQiYang/geometry-axiom/pull/191#issuecomment-6107489606) | P-049；暫定(依 2026-10-09 授權 L) |
| R42(承接 #184 B1,P-058) | R42 | 捏合點取最左轉 → 按材料內部連通分片；材料在左的閉走訪在重訪頂點依字典序拆成簡單環；按走向分外環／孔並穩定排序 | [P-058 裁決](https://github.com/ZhiQiYang/geometry-axiom/pull/184#issuecomment-6111299860)、[指定本 PR 承接](https://github.com/ZhiQiYang/geometry-axiom/pull/199#issuecomment-6111300221) | P-058；定義推論，暫定(依 2026-10-09 授權 L) |

## 兩項政策選擇

| 項 | 選項 | 採用 | 理由 | 如何推翻 | 狀態 |
|---|---|---|---|---|---|
| P5 | 沿 I8a 的純畫布位置例外；或首房交易一律因 World 變更過期 | I64 明寫「純 D12 畫布位置變更除外」 | 保持既有幾何預覽例外，位置展示不改首房候選的幾何或附件 | 明示改採更嚴政策，修訂 I64 並同步白話、閱讀器與對應驗收 | 暫定(依 2026-10-09 授權 L) |
| P6 | 同一專案提交沿革內不重用、跨檔整份替換；或另存跨檔高水位、承諾跨檔不重用 | D48 明寫復原／重做不回退高水位；開啟另一份（含較舊的）完整專案依 D51 整份替換，不承諾跨檔不重用 | 保留 P-047 的復原保護與 D51 完整替換，且不引入未定義的跨檔實物沿革帳本 | 明示擴大跨檔承諾，另定高水位的保存範圍及整份替換例外，再修 D48／D51／I62 與驗收 | 暫定(依 2026-10-09 授權 L) |

## 執行期名詞依據

R2 依 [模型快照料單契約](../../geometry-web/docs/MODEL-SNAPSHOT-SCHEDULE.md) 的 context／history frame／project revision 核對。
身分與更新條件另核對 [專案工作區](../../geometry-web/reference-workspace.js) 的 getProjectState、getModelOperationState、dirty、tryLocalHistory，以及 [完整歷史](../../geometry-web/project-store.js) 的 ContextHistory.restore：復原可回到原 context，仍產生新的 frame，revision 不隨內容回復而倒退；附件變更也推進 revision。這些都是執行期護欄，非持久化物件或新能力。
前端歷史窗只定義完整快照與附件可整筆復原的範圍，不把實作筆數升格為公理。

## P-049 原採納版的歷史身分與驗證

- 前一採納版：`e04a63cb3e1280715cd6c24504a37f3522fa43c7`／`2c20fd3d401e4246e59191f72f978c0a81a6ad34d3a297fe54abf4783e666c20`；加入 `PRE_STACK_CLARIFY_AXIOM_VERSIONS` 與全部六道既有豁免閘（含斷面拉伸），既有集合保留。
- P-049 歷史 `AXIOM_REVISION`：`209a7278d3acadfe89374714e821018dcba10adc`（僅對應當時條文）。
- P-049 歷史 LF 正規化 `AXIOM_SHA256`：`5ccbbc0cd512acd60412427794cf16baf36af4e1ceed40730fb8144697f8ac1d`。
- `python geometry-guide/sync_axiom_reader.py`：通過；191 條、788 blocks、5 筆批註、31 見證、63 例圖、84 patches；textRevision 34，五道 assert 與獨立 SSOT 對照均通過。
- `python geometry-guide/sync_axiom_reader.py --check`：通過；此路徑不重建，patches 為 0。
- `python tests/test_axiom_reader.py`：41／41 通過，含位元組冪等與批註保留。既有 DeprecationWarning／ResourceWarning 不影響結果。
- 條號與差異：191 個唯一條號；未新增或刪除；20 條指定條文有修訂、其餘 171 條內文逐字不變；另依授權修檔頭與 §四。191 條白話全覆蓋、無懸空引用；逐項替換清單由基底重放後與成品全等。
- `python -B -m unittest tests.test_modeling_runtime.AxiomSourceIdentity`：3／3 通過；P5、P6 各改一字均因 AXIOM_VERSION 預期轉紅，逐次還原後回綠，未被 BASE_COMPILER 遮蔽。
- 相容探針：當前版、K2a 跟進版、K2b、K1、PF-0 均通過版本閘，停在探針故意設置的不合法 generator（PACKAGE_SCHEMA）；未知版與 7 個撤回版均因 AXIOM_VERSION 拒絕。拿掉新增集合、或逐一拿掉六道閘的豁免，共 7 個突變均在相應版本閘轉紅，還原後回綠；不代表原生完整重建已驗。
- 鎖行：決策佇列 74 行、BACKLOG 46 行的內容與次序均保留；每檔各自的改字、刪行、換序共 6 個記憶體突變全數拒絕。決策佇列舊檔完整前綴保留，BACKLOG 全檔未改。
- 純 Python 收據與牙齒腳本：本次交接 scratchpad 的 `axiom-clarify-codex/`，包含 scope／compat／hash／lock 結果、reader-tests.log 與 axiom-diff.patch。
- 初採納時未跑 WSL；後續 7ad9cef 的七 job 六綠一個 space 紅燈已公開，本段不將其改為全綠。
- 無新入口；只同步既有唯一正典閱讀器，不產生第二份閱讀器。

## P-058：R42 確定拆環與 PF04 承接

依上表兩份裁決，本 PR 只改 R42 的邊界走法，白話同步；保留每環簡單、分片追溯鍵及其餘條文。PF04 後續實作須包含下列驗收，本次僅寫入規格，未執行尚未實作的 PF04：

| 例 | 輸入／操作 | 必須得到 |
|---|---|---|
| 兩孔角接 | F=[0,100]²；柱 [20,40]² 與 [40,60]² | 一個材料分片、外環 1、孔 2、面積 9200 |
| 兩材料分片角接 | 兩塊材料只在一點相接 | 維持兩個分片 |
| 拆環突變 | 拿掉重訪頂點的拆環步驟 | 第一例必須失敗；還原後回綠 |

本次正典三段經 WSL v3 實跑通過：191 條、788 blocks、84 patches；五道 assert、獨立 SSOT、41/41 閱讀器測試與重建冪等通過，18 次取樣無外來程序。相對 P-049 只改 R42 及白話，其餘 190 條不變。條文 commit／AXIOM_REVISION `6992607d0463bba8fae4c409af57a61066dafca2`；LF AXIOM_SHA256 `c878c355c0c233119686ee1ca2b0ddd2c2fbdb7eb2c8b88896a3a8a6d37cb6ad`，原件在本次交接 `SP/board-local-codex/pr199-p058/`。上節只描述舊 P-049 採納版；舊 head 7ad9cef 的七 job 為六綠、一個 space 紅燈，原件保留，不能當成本次 head 的裁判。無新入口；未改產品演算法、能力或相容集合。

三段命令各 exit 0；原 WSL wrapper 在末尾搬移護欄因 Windows CRLF／Git LF 差異 exit 1，原收據與日誌保留。另以 Git 原件核對差異僅行尾、五份凍結輸入與受測 clone 完全相同後，搬移經測正典並再跑 --check 通過；搬移紀錄獨立保存，未將原 wrapper 改記成功。

P-058 版本回填只改當前兩個常數，其他 Python AST、全部舊相容集合、六道豁免及 capabilities 不變。身分來源 3/3；R42 的拆環順序與外／孔分類各改一處均在 AXIOM_VERSION 轉紅，逐次還原回綠。原相容探針與七個去除突變通過；被取代的 P-049 `209a7278…`／`5ccbbc0c…` 明確在 AXIOM_VERSION 拒絕，沒有新加相容項。探針停於刻意無效的 generator，不代表原生重建已驗。決策佇列 74／BACKLOG 46 行內容及順序保留，改字／刪除／換序六個反例全拒絕。


## P-063／P-064：匯入閉包與單份容量例外

本節記錄最新採納；上面的 P-049／P-058 版本及測試數字保留為歷史證據。依 [P-063 寫手指派](https://github.com/ZhiQiYang/geometry-axiom/pull/187#issuecomment-6123283824)、[#187 原修文](https://github.com/ZhiQiYang/geometry-axiom/pull/187#issuecomment-6114893235) 與 [P-064 裁決](https://github.com/ZhiQiYang/geometry-axiom/pull/201#issuecomment-6123284265)，在本分支接續寫入：

| 裁決 | 條文 | 修訂 |
|---|---|---|
| P-063 | D55、白話 D55 | 閉包白名單明列 D32 規則版本，限作為綁定的閉包依賴；根型別及其他白名單不變。 |
| P-063 | 白話 D54(a) | 同一穩定身分／版本且內容指紋相同才共用；不同穩定 id 不因內容相同而合併。 |
| P-064 | I68、白話 I68 | 集合縮成一份時，內層合法、僅舊單份外殼超限者保留一份集合；原字串、內層與集合容量上限不變，保留集合能力。縮小到單份可容納且無孤兒／曾缺失標記時，下次保存須轉回單份。 |

D56 已委由 I68 規定保存格式，R54 的局部歷史、保存與旗標轉集合規則也無衝突，兩條及其白話均不再修訂。相對 `e837a9308642a54ba55d7d399eb66805e1d5984e`，191 個條號維持；正式只改 D55／I68，其餘 189 條逐字相同；白話只改 D54／D55／I68。BACKLOG、決策佇列、同步器及原 41 題測試全檔不變。

| 檢查 | exit | 秒數 |
|---|---|---|
| sync | 0 | 23.73 |
| check | 0 | 1.626 |
| tests | 0 | 309.634 |

三條原命令於擁有的 worktree 原位經 WSL v3 執行，外層 wrapper exit 0；22 次取樣無外來程序。正典 191 條／788 blocks／84 patches；五道 assert、獨立 SSOT、41/41 原測試、冪等與批註保留通過。正典 SHA-256：`dd965752eee3252df9fe45c289a812545f37202e477729807840b152ab7086e8`。沒有第二份閱讀器，HTML 只由同步器生成。

文字契約修前 8 項缺漏，修後通過；五處各自撤回都能指出對應政策缺漏，還原通過。另有版本來源 3/3、兩個改字反證、七個既有相容集合／豁免反證、六個保護行反證；決策佇列 74、BACKLOG 46 個保護行的內容與次序不變。文字反證只證文件契約，相容探針停於刻意不合法的 generator，均不冒充產品執行結果。

### 當前版本與相容表

| 版本集合 | AXIOM_REVISION | LF AXIOM_SHA256 | 接受情況 |
|---|---|---|---|
| 本次採納 | `a393a0f01284433ca20fe8b10d9f21111026e7f1` | `b06ffecf4f3b7a907a50d329f2073799d9514daa26b9056380f62ad37e5725ee` | 當前來源，已核對條文 commit 與 LF bytes |
| `PRE_STACK_CLARIFY_AXIOM_VERSIONS` | `e04a63cb3e1280715cd6c24504a37f3522fa43c7` | `2c20fd3d401e4246e59191f72f978c0a81a6ad34d3a297fe54abf4783e666c20` | 保留既有接受條件 |
| `PRE_DRAFTS_TOPOLOGY_AXIOM_VERSIONS` | `d787146d501b98931cc66caccdbed0006c5ca25f` | `2348373fa4182f984489c068b1762725f3d9eaa4087418b0ffb5182c763213e4` | 保留既有接受條件 |
| `PRE_ZERO_ROOM_AXIOM_VERSIONS` | `ca3790ce7e87e1a9190cb17fb63bbe42f501f7a5` | `267a308698954ca610814d3956b5b837463ccaec8d4d074236de9f9df7f8a050` | 保留既有接受條件 |
| `PRE_CUTTING_PLAN_AXIOM_VERSIONS` | `8a8b56424407bb758de0d16e66c94e21eb79aa41` | `d8a0b4a1c108197f4abb5c67d73fa22aa7fa4288769f605a5a9372fd93aa7b52` | 保留既有接受條件 |
| `PRE_PANEL_FILL_AXIOM_VERSIONS` | `3ad8012b6f01f9f46795a28a410ee444c5cce1a0` | `29ad0c657e53d364347862fddac23ba26a248a4fd8f83487d86f9e648bd1eaf2` | 保留既有接受條件 |
| `PRE_SECTION_PROFILE_AXIOM_VERSIONS` | `73b9ba1d417c1b6c9885951b24139b67f8550312` | `d4bd69cd3dcbcef10802dd401a66b293afdaa09abccc6853d7a39f478cefe29a` | 保留既有接受條件 |
| `PRE_SUBDIVISION_AXIOM_VERSIONS` | `cc6adff4c9c783ce78bcbd849754b69254690cab` | `d5eb43d077e7408fb032ee09f552795215fbf5fb7b097b57f7ac7ef6f2ed08f7` | 保留既有接受條件 |
| `PRE_GENERATION_AXIOM_VERSIONS` | `ccbec5fe9e4b056bcd5673fb9f69a54e888ea4e6` | `264d8c5d2fa4e513418fbd611f2ef6f8d597def51d89805a75e9e21d0d24e8fe` | 保留既有接受條件 |
| `PARAMETER_AXIOM_VERSIONS` | `802f9bda1b1b8ab046f059e115dbf05a44da10df` | `b19009682ba5b3e7150341ae1b5190629cb03985d500d382aa918438fb548c0b` | 保留既有接受條件 |
| `PARAMETER_AXIOM_VERSIONS` | `82074011fabdccb5918a580eef737aa227536d01` | `8b3afe498b0050a50b020a3a6fc3018abfecf9f9502fccf742a32e0bc499cc03` | 保留既有接受條件 |
| `LEGACY_AXIOM_VERSIONS` | `494660068ceb884c1a96884a2b704e3bcf5d24ca` | `bc01cf0db266f97255156e28e40fb235833031fb95f1f234ad6d90a9f08240f8` | 保留既有接受條件 |
| `ENGINEERING_AXIOM_VERSIONS` | `5698f8501d539ed3a6f0644dab854e62e3bafb1a` | `1843e3e9f6a3a6db07ceaa8f62fad693039296d519791af98c2a433554308bcf` | 保留既有接受條件 |
| `FINITE_GRID_AXIOM_VERSIONS` | `b4fe75f7f03ed81b4bc9f85a044282f91bd27cb6` | `2d31868524cb2776c2c405367fa69087b8f43371f320f12f3405fb14ce9fdf28` | 保留既有接受條件 |
| `INFINITE_GRID_AXIOM_VERSIONS` | `f34c0aeb56a4d2c639be924b289e3572756807d8` | `b2b3ebde32f693e3853ace3d39a8618e5717d42e437019510505b3453ae87c75` | 保留既有接受條件 |
| 已取代 P-049 草稿 | `209a7278d3acadfe89374714e821018dcba10adc` | `5ccbbc0cd512acd60412427794cf16baf36af4e1ceed40730fb8144697f8ac1d` | AXIOM_VERSION 拒絕，未新增相容 |
| 已取代 P-058 草稿 | `6992607d0463bba8fae4c409af57a61066dafca2` | `c878c355c0c233119686ee1ca2b0ddd2c2fbdb7eb2c8b88896a3a8a6d37cb6ad` | AXIOM_VERSION 拒絕，未新增相容 |

當前兩常數以外的 Python AST、全部相容集合、六道既有豁免與 capabilities 均未變。上述接受是版本閘的結果，各版本既有能力限制仍適用。原件位於本次交接 `SP/board-local-codex/pr199-p063-p064/`。

後續產品驗收由 #201／#191 實作線承接：內層 130956、131072 bytes 的大份在捨棄另一份後，保存為一份集合且冷讀 raw 不變；縮到 130955 bytes 或以下後再保存轉為單份；拿掉容量例外時捨棄須回到被拒。這些是裁決指定的待驗情境，本 PR 沒有執行該產品測試。#187 的匯入實作同樣須隨整條堆疊承接；本次未跑新 head 的正式七 job。CI 受帳號計費阻擋，以本機 WSL 收據代替；無新 UI 入口。
