# 公理疊加鏈澄清（P-049）

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

## 兩項政策選擇

| 項 | 選項 | 採用 | 理由 | 如何推翻 | 狀態 |
|---|---|---|---|---|---|
| P5 | 沿 I8a 的純畫布位置例外；或首房交易一律因 World 變更過期 | I64 明寫「純 D12 畫布位置變更除外」 | 保持既有幾何預覽例外，位置展示不改首房候選的幾何或附件 | 明示改採更嚴政策，修訂 I64 並同步白話、閱讀器與對應驗收 | 暫定(依 2026-10-09 授權 L) |
| P6 | 同一專案提交沿革內不重用、跨檔整份替換；或另存跨檔高水位、承諾跨檔不重用 | D48 明寫復原／重做不回退高水位；開啟另一份（含較舊的）完整專案依 D51 整份替換，不承諾跨檔不重用 | 保留 P-047 的復原保護與 D51 完整替換，且不引入未定義的跨檔實物沿革帳本 | 明示擴大跨檔承諾，另定高水位的保存範圍及整份替換例外，再修 D48／D51／I62 與驗收 | 暫定(依 2026-10-09 授權 L) |

## 執行期名詞依據

R2 依 [模型快照料單契約](../../geometry-web/docs/MODEL-SNAPSHOT-SCHEDULE.md) 的 context／history frame／project revision 核對。
身分與更新條件另核對 [專案工作區](../../geometry-web/reference-workspace.js) 的 getProjectState、getModelOperationState、dirty、tryLocalHistory，以及 [完整歷史](../../geometry-web/project-store.js) 的 ContextHistory.restore：復原可回到原 context，仍產生新的 frame，revision 不隨內容回復而倒退；附件變更也推進 revision。這些都是執行期護欄，非持久化物件或新能力。
前端歷史窗只定義完整快照與附件可整筆復原的範圍，不把實作筆數升格為公理。

## 來源身分與驗證

- 前一採納版：`e04a63cb3e1280715cd6c24504a37f3522fa43c7`／`2c20fd3d401e4246e59191f72f978c0a81a6ad34d3a297fe54abf4783e666c20`；加入 `PRE_STACK_CLARIFY_AXIOM_VERSIONS` 與全部六道既有豁免閘（含斷面拉伸），既有集合保留。
- 本次 `AXIOM_REVISION`：`209a7278d3acadfe89374714e821018dcba10adc`（條文 commit；Git 內的 LF 公理內容與目前檔案雜湊相同）。
- 本次 LF 正規化 `AXIOM_SHA256`：`5ccbbc0cd512acd60412427794cf16baf36af4e1ceed40730fb8144697f8ac1d`。
- `python geometry-guide/sync_axiom_reader.py`：通過；191 條、788 blocks、5 筆批註、31 見證、63 例圖、84 patches；textRevision 34，五道 assert 與獨立 SSOT 對照均通過。
- `python geometry-guide/sync_axiom_reader.py --check`：通過；此路徑不重建，patches 為 0。
- `python tests/test_axiom_reader.py`：41／41 通過，含位元組冪等與批註保留。既有 DeprecationWarning／ResourceWarning 不影響結果。
- 條號與差異：191 個唯一條號；未新增或刪除；20 條指定條文有修訂、其餘 171 條內文逐字不變；另依授權修檔頭與 §四。191 條白話全覆蓋、無懸空引用；逐項替換清單由基底重放後與成品全等。
- `python -B -m unittest tests.test_modeling_runtime.AxiomSourceIdentity`：3／3 通過；P5、P6 各改一字均因 AXIOM_VERSION 預期轉紅，逐次還原後回綠，未被 BASE_COMPILER 遮蔽。
- 相容探針：當前版、K2a 跟進版、K2b、K1、PF-0 均通過版本閘，停在探針故意設置的不合法 generator（PACKAGE_SCHEMA）；未知版與 7 個撤回版均因 AXIOM_VERSION 拒絕。拿掉新增集合、或逐一拿掉六道閘的豁免，共 7 個突變均在相應版本閘轉紅，還原後回綠；不代表原生完整重建已驗。
- 鎖行：決策佇列 74 行、BACKLOG 46 行的內容與次序均保留；每檔各自的改字、刪行、換序共 6 個記憶體突變全數拒絕。決策佇列舊檔完整前綴保留，BACKLOG 全檔未改。
- 純 Python 收據與牙齒腳本：本次交接 scratchpad 的 `axiom-clarify-codex/`，包含 scope／compat／hash／lock 結果、reader-tests.log 與 axiom-diff.patch。
- 不跑 WSL（由協調端另跑）；原生與完整整合測試不是本 PR 的完成宣稱。
- 無新入口；只同步既有唯一正典閱讀器，不產生第二份閱讀器。
