# 組構規則第一階段驗收（GEO-226／PR #26）

**目前逐條索引：**[2026-10-04 #24 驗收證據](ASSEMBLY-ACCEPTANCE-EVIDENCE-20261004.md)。A11/A12 的窄 native 情境已補驗；A04 局部交換、A18 兩版本各自配置與 A23 空白390px流程已有真覆蓋。A24實機仍未驗。下方分日期的第一階段紀錄保留原貌；其中 #25「尚未實作／待核准」是當時狀態，有限生成器已由 PR #53/#55 合併，不代表任意自訂接合生成。

## GEO-240：固定來源的情境材料配置入口（PR69，2026-10-03）

本切片沿用已採納 D32/D33/I40/I41/R34；選取單一已發布規則後，既有 inspector 按鈕直接建立材料配置，沒有新公理、保存格式或生成語義。完整規則編輯仍由卡片雙擊／原有入口到達，配置 inspector 保持既有 open。Grid source＋boundary、未提交 grid 草稿附件與 F2b 擴大生成另案。

- `ContextOperations.resolveBindingCreate` 只接受固定 typed id/version/canonical fingerprint，核對原生成功 envelope、authoring 能力、唯一版本與 typed slot 身分。generation 能力不能替代 authoring；null 材料／接觸面／擺向表示 incomplete，仍可使用既有配置表單／原生驗證。
- `createBindingFromRule` 先在 detached owner 讀取／驗來源。成功前不 flush 舊輸入、不取消旧 preview、不換 owner 或寫草稿；配號仍由唯讀 native `newid` 與既有 reservation 防撞執行。遲到回覆受 project context、單一選取、卡片／pane、owner、generation 及關閉 serial 核對；連點只建立一份。
- 顯示卡片直接取得原生既有 fingerprint。同 tuple 刪除重建後，首次與重試都拒絕原 pin；若 native 在配號等待途中未通知又變更，草稿仍保存舊 pin，後續 preview 精確拒絕而不送 POST。沒有承諾連續快照或新增第二讀取契約。
- 原生三個 card fingerprint 回歸在 production/ASan/UBSan 各35/35；同三例在 immutable main baseline 皆 assertion red。前端 workspace42＋registry12=54/54；獨立快照79/79與額外時序／inspector10/10，移除 owner guard／fresh-hash repin 的合法 mutant 分別有1／3 assertion red。
- 正式 CDP 註冊 `assembly_context_entry_test.js` 的 P82，16項含桌面真 Enter／390px 點選、真 native preview/confirm、真 `.gcanvas` 保存重開、保留選取與原入口、同 tuple 換語義／latest新增、遲到配號／來源、連點與能力負例。能力和缺卡片 hash 的 fault injection 只作明示負例；正例均為 native 真資料。P77原128斷言保留，拖卡後由真雙擊開完整編輯。

同 exact head 的完整套件、無 filter CDP/golden、HTTP/runtime 閉包與剩餘未驗項以 PR69 實測紀錄為準。歷史 expected-count、服務來源變更與外掛動態字串／Enter 的失敗保留，不冒稱 green。A24實機仍未驗；390px不能替代手機鍵盤或OS檔案操作。

## 原第一階段基準（歷史紀錄）

起點：PR 草稿 `1ac155e`，整合既有主線 `17bd432`。條文定案與正典同步：`8207401`。
正式功能與驗證腳本在本文件同一提交；PR 使用 Refs #19，不自動關閉尚待實機驗收的總工單。

## 範圍

第一階段是自訂規則與固定版本材料配置。沒有施工角材生成器，也沒有放寬 D15/I19。
只有一個正式入口：「建立物件 → 組構規則」。草稿、發布版本、材料配置共用工作區與專案保存列。

## 驗收矩陣

原生案例位於 `tests/test_assembly_rules.py::AssemblyRules`；UI 案例為
`geometry-web/assembly_workflow_test.js`（完整 CDP 入口的 P77）。

| ID | 證據與觀察 |
|---|---|
| A01–A02 | `test_publish_without_geometry_and_native_identity`；P77 由空專案建立槽位、構件、接合，保存未發布草稿，不生成面或角材。 |
| A03–A05 | `test_orthogonal_split_and_geometric_loop`；P77 真正點選局部交換、端點與側面；旋轉縮放後定義逐字相同。A04 單次交換第一接合，逐欄核對第二接合未變，並完整比對發布及 `.gcanvas` 重開後的兩处定義。 |
| A06 | `test_duplicate_scope_and_endpoint_rejected`；P77 預覽指出兩個接合，World 不變。 |
| A07–A08 | `test_immutable_version_rename_reorder_and_fixed_binding`、`test_missing_duplicate_and_unknown_fields_rejected`；P77 改名重排不改身分，使用中槽位不得直接刪除。 |
| A09 | `test_orthogonal_split_and_geometric_loop` 接受四邊鄰接環。 |
| A10 | 首版無巢狀規則、規則求值引用；未知引用欄位在 schema 層拒絕。未宣稱有不存在的循環求值器。 |
| A11–A13 | `test_material_source_and_parameter_recomputation`、`test_unselected_binding_is_saved_as_incomplete`、`test_bad_dimension_sources_rejected_not_incomplete`；另由 `test_assembly_capacity.py` 驗材料型別／軸／固定版本、槽位8／構件12／接合16、發布版本32／配置64，以及 UTF-8 名稱／scope 的合法上界與下一筆原子拒絕。 |
| A14 | `test_canvas_move_preserves_preview_and_history`；P77 真拖卡片、旋轉縮放後指紋不變。 |
| A15–A17 | `test_copy_and_idempotent_publication`、`test_newid_wraps_past_max_in_independent_assembly_namespaces`、`test_immutable_version_rename_reorder_and_fixed_binding`、`test_cancel_and_protocol_tokens_do_not_commit`；Node workspace 驗 MAX 回繞、交錯 native／草稿占用、版本上限與來源變更拒絕。P77 `assembly_id_test.js` 真新增／複製／編輯、意圖保存重開、碰撞與刪後重建不覆寫；既有換版取消守門仍驗。 |
| A18–A19 | `test_scene_roundtrip_in_fresh_process`、`test_referenced_rule_delete_and_atomic_rebind`、`test_canvas_move_preserves_preview_and_history`；Node `test_assembly_project_store.js`；P77 保存重開、草稿復原及發布復原重做。正式範例的完整配置引用第1版、未完成配置引用第2版，逐槽核對來源、有效值及原固定版本。 |
| A20–A21 | Node assembly/project/parameter 格式測試，原生 `test_truncated_corrupt_and_duplicate_records_are_atomic`；能力遭移除、未知格式、殘缺記錄均拒絕，既有格式保留。 |
| A22 | `test_authoring_capability_does_not_enable_model_generation`；既有 138 個 scene 案例持續驗證 D15/I19。 |
| A23 | P77 桌面與 390px 真實輸入、點選、返回、保存重開；新增 `assembly_id_test.js` 從 390px 空白專案建立槽位／構件／接合，保存未發布草稿、重開編輯、發布並再重開，完整定義與預期全等。無水平溢出、表單按鈕至少 44px；不是 A24 實機。 |
| A24 | **待實體手機驗收**：手機鍵盤、OS 原生檔案選擇器與下載目的地。窄版 Chrome 不等於實機。保留 open 追蹤。 |

## A24 實機驗收交接（未執行）

#19／#24 保留 A24 追蹤；不因桌面測試或文件更新而關閉。先依下方命令啟動隔離測試服務，
由實體手機連到同一版服務。使用全新測試專案與隔離 feedback 目錄，記錄可達 URL、完整 commit SHA、
手機型號、OS／瀏覽器版本、直橫向與鍵盤種類。至少分別記錄實際支援的 iOS Safari、Android Chrome；
未取得的裝置標「未驗」，不得以其他裝置或模擬器代替。

| 步驟 | 實機操作 | 通過條件 |
|---|---|---|
| M1 鍵盤與輸入 | 空白專案 → 建立物件 → 組構規則；新增角色、構件、接合，以中文輸入法改名，再編輯材料尺寸。鍵盤開啟時捲動、切換欄位及返回；直橫向各一次。 | 組字完成後文字正確；焦點未跳到別欄；目前欄位及保存／返回入口可到達，不被鍵盤或底列永久擋住。 |
| M2 草稿保存與下載 | 未發布且未填完時按共用「保存」，在 OS 提示中選擇目的地／檔名；實際到該位置找檔案。 | 取得非空 `.gcanvas`，可辨識檔名及目的地；不只看到程式顯示已保存。記錄瀏覽器自動下載或系統選擇器的真實行為。 |
| M3 原生選檔重開 | 建立另一個空白測試專案，透過「開啟專案」的 OS 原生選檔器選 M2 的實體檔。 | 未完成內容、來源引用及卡片位置均恢復，沒有靠原頁記憶體假重開。 |
| M4 完整資料 | 以操作說明的範例開始，改名並保留兩個發布版本、完整／未完成配置及草稿；保存、換專案，再從 OS 選檔重開。 | 版本、來源與草稿未混淆，仍可編輯；只有 authoring 資料，不宣稱已生成施工角材。 |
| M5 取消與離開 | 在有未保存草稿時返回／切專案；分別取消離開提示、取消 OS 選檔及可取消的保存提示。 | 取消後仍是原專案與草稿；選檔取消不清空；放棄離開或丟棄草稿的選項效果與提示一致。 |

將以下紀錄填入 #24；如有失敗，附最短重現、截圖／錄影或測試專案，修復後重驗同一步。
不收集私有專案或個人下載目錄內容。全部預定裝置的必要步驟完成且剩餘缺陷處理後，再由擁有者確認 #24／#19 結案。

```text
A24 日期／驗收者：未填
commit SHA／測試 URL：未填
裝置／OS／瀏覽器／鍵盤：未填
M1：未驗（直向／橫向）
M2：未驗（實際檔名、目的地類型、大小；不需個人路徑）
M3：未驗
M4：未驗
M5：未驗
證據連結／失敗重現／待修工單：未填
```

施工構件生成 #25 依 2026-10-02 使用者決定繼續保留；最小求值輸入、公理差異與開工條件整理在
[既有契約的後續交接節](../../geometry-core/ASSEMBLY-RULES-CONTRACT.md#deferred-generator-handoff--25-2026-10-02)，沒有改動現行公理或啟用生成能力。

## 2026-10-02 A15 修復與補驗

起點 `4e90a1c89256a96ed28a7a1096c9ca627912fc91`（PR #42）。修正 JS 對 native 配號回繞只跳過草稿而撞上既有配置；native `newid` 本身沒有此缺陷，沒有修改公理或 Core。配置草稿新增可選的 `binding_intent`；來源與意圖保護、舊資料相容邊界見[既有契約](../../geometry-core/ASSEMBLY-RULES-CONTRACT.md#project-and-history)。

本輪驗證來源雜湊、命令、二進位雜湊與日志集中在[驗證紀錄](assembly-validation/README.md)及 [a15-provenance.json](assembly-validation/a15-provenance.json)。Linux 非瀏覽器全套 1282 通過／0 失敗／1 具名 Windows GDI 平台略過；ASan＋UBSan assembly 34 tests 無略過、無 sanitizer 診斷；Node assembly 三檔 41 tests 通過。舊 workspace 對新配號／碰撞三個 oracle 全部如預期失敗，正常版本恢復通過。

完整 CDP 完成 1684 功能斷言，原 exit 1 僅因 P77 計數表仍為 84、實得新增後的 108；其餘 73 段吻合。已依完整觀察值提高計數表且逐段比較相符，精確 PR head 仍由 CI 無 filter 全跑。UI 交換只改文字的故障注入如預期失敗，正常 P77 還原重跑 108／0／0、exit 0。原始結果、設定例外及剩餘 A24 分開記錄。

#19／#24 仍保留 A24 實機驗收；本次不使用 `Closes #19` 或 `Closes #24`。#25 及 #43–#49 不在本輪實作範圍。

## 2026-10-02 第一輪收尾查核（PR #42 歷史紀錄）

查核程式碼：`fd8f38b42bc0eb9eb8ea16595dfc76e83e7bdea2`（PR #41 已合併；首版 PR #26 已於 2026-10-01 合併）。
[同 SHA 的 GitHub integration](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/36972304794) 已完成：native 與 assembly、documents、grid、canvas、space、timber 六組真實瀏覽器工作皆 success。
這是既有 CI 的查核，不冒稱本輪在本機重跑完整瀏覽器或實體手機。

本輪 Linux 乾淨 clone 聚焦重現如下；所有命令 exit 0，沒有跳過測試。先設定 `ulimit -s 16384`，
原生測試使用 `GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge`、`GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base`。

| 命令 | 結果 |
|---|---|
| `python3 tests/binaries.py build core bridge model-base` | 三支由目前來源編譯，fresh。 |
| `python3 -m unittest tests.test_assembly_rules tests.test_assembly_parameter_refs` | 28 tests 通過，含固定版本不可替換、原子改綁、取消／過期 token、原生重放及參數身分範圍。 |
| `node --test tests/test_assembly_project_store.js tests/test_assembly_transport_context.js tests/test_assembly_workspace.js` | 32 tests 通過，含真正封包重開、確認期間專案守門、延遲／遺失回覆與草稿保留。 |
| `python3 tests/build_assembly_example.py --check` | 範例與原生重建一致。 |
| `python3 geometry-guide/sync_axiom_reader.py` | 99 個補丁、五道 assert 與獨立 SSOT 通過；正典未產生 diff。 |
| `python3 geometry-guide/sync_axiom_reader.py --check` | 現有產物檢查通過。 |
| `python3 tests/test_axiom_reader.py` | 25 tests 通過；既有矩陣讀檔產生 ResourceWarning，沒有失敗。 |

`feedback_cli.py list` 在這份遠端 clone 沒有回報，不能推論使用者本機沒有回報。
#20–#23 已有實作、同版 CI 與上述補查可供結案；#19／#24 仍需 A24 實機簽核，#25 保留後續規格。
本輪只更新既有交接文件，沒有改產品程式、公理、能力宣告或現行保存格式。

## 可重現命令

在 WSL／Linux，所有二進位都放 `/tmp/geometry-tests`：

```sh
ulimit -s 16384
python3 tests/run_all.py --build
python3 tests/assembly_mutation_check.py --out /tmp/assembly-mutations
GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge python3 tests/build_assembly_example.py --check
python3 geometry-guide/sync_axiom_reader.py
python3 geometry-guide/sync_axiom_reader.py --check
python3 tests/test_axiom_reader.py
```

啟動隔離服務，`GEOMETRY_FEEDBACK_DIR` 指向專用暫存資料夾；測試不可連到使用者正在工作的服務：

```sh
GEOMETRY_BRIDGE=/tmp/geometry-tests/bridge GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base \
GEOMETRY_FEEDBACK_DIR=/tmp/geometry-tests/fb-assembly python3 geometry-web/serve.py 8836
```

另一終端給相同 `GEOMETRY_TEST_URL=http://localhost:8836/` 與 `GEOMETRY_FEEDBACK_DIR`：
執行 `node geometry-web/cdp_test.js`（不帶 ONLY）、`node geometry-web/space_model_test.js`。
Windows Chrome 連 WSL 服務時加 `GEOMETRY_TEST_SERVER_PATH_STYLE=wsl`，feedback 路徑的兩種表示必須指向同一資料夾。

最終完整 CDP 使用 Windows 原生 bridge 與 model adapter（兩支均以目前 C 來源編譯），
避免跨環境每次請求的延遲。實際編譯命令見 [Windows build](assembly-validation/windows-build-command.txt)，
model adapter 使用 `tests/binaries.py build model-base`。PowerShell 啟動方式：

```powershell
$env:GEOMETRY_BRIDGE="$env:TEMP\geometry-tests\bridge-assembly-pr26.exe"
$env:GEOMETRY_MODEL_BASE="$env:TEMP\geometry-tests\model-base.exe"
$env:GEOMETRY_FEEDBACK_DIR="$env:TEMP\geometry-tests\fb-native-full-pr26"
python geometry-web/serve.py 8848
```

另一終端設定相同 feedback 目錄、`GEOMETRY_TEST_URL=http://127.0.0.1:8848/`，
執行 `node geometry-web/cdp_test.js`；Windows 原生服務不設定 WSL path style。

## 故障注入

`tests/assembly_mutation_check.py` 在暫存來源副本編譯三種故障，先跑正常基準。
略過衝突檢查、略過尺寸來源解析、允許已取消預覽確認，均須由指定案例的指定斷言偵測（判準見下方「killed 判準」）。
編譯失敗、崩潰、error、skip、逾時、別的斷言失敗都不算抓到缺陷；不修改工作區，也不覆寫既有全庫 mutation 結果。
另以 `GEOMETRY_ASSEMBLY_ONLY=1 GEOMETRY_ASSEMBLY_INJECT_SWAP=1` 跑 CDP，攔截交換按鈕、只改文字：
P77 的核心草稿身分斷言如預期失敗。正常執行不帶注入變數；完整模式禁止此注入。

### GEO-261 之後的錨點（2026-10-20）

整合分支 `7e36543b` 上，`tests/test_mutation_anchors.py` 報出 `conflict`、`missing-source` 兩個錨點已不存在：I40 的規則驗證與束縛解析搬進了 `geometry-templates/woodworking/native/assembly.c`。把工具實際跑起來，另外發現兩件閘門看不到的事：

1. **來源副本缺檔，基準線編不過。** 工具只複製 `geometry-core`、`geometry-web` 的 C 檔，而 `current_geometry.c` 現在 include `geometry-app/native/…` 與 `geometry-templates/woodworking/native/…`，gcc 報 `fatal error: geometry-app/native/legacy_json.inc: No such file`（8 秒就停）。現在一併複製這兩個目錄。
2. **`cancelled-preview` 的錨點還在，突變卻存活。** 只拿掉確認時的 `g_preview.ready` 守門，取消後的確認仍被擋下：取消現在還會丟棄候選（`app_candidate_discard`），候選失效後 `app_world_candidate_current` 為假。錨點存在不代表突變還咬得到，這一類只有實跑看得出來。

案例格式因此改成 `(名稱, [(檔, 前, 後), …], 殺手測試)`，一個案例可以對每一層各打一個補丁。這一輪 killed 判準沒有改（結束碼 1、有 AssertionError、沒有 errors 與 skipped）；那條判準的缺口與修法見後面的「killed 判準」。

| 案例 | main `adbaebf9` 原本打的位置 | 整合分支改打的位置 | 層數與對照組 | 為什麼是同一條規則、同一種錯誤 |
|---|---|---|---|---|
| conflict（I40） | `geometry-core/assembly.inc:65` `if(!strcmp(scopes[k],scopes[i]))` 換成 `if(false)` | `geometry-templates/woodworking/native/assembly.c:66` 同一段文字，函式改名 `wood_asm_validate_rule`、錯誤函式改名 `wood_asm_error` | 1 層，單層即被殺 | 規則是「同一個規則版本內，兩個接合點不得共用 junction scope」。迴圈、`strcmp` 與訊息「I40: joints %u and %u conflict at scope %s」都是整段搬家。殺手測試的 scope 變體在 `test_assembly_rules.py:218` 以 `preview.valid` 為 True 失敗，與 main 完全相同。 |
| missing-source（I40） | `assembly.inc:123` `(resolve&&!eng_resolve(…))` 換成 `false` | `assembly.c:115` `(resolve&&!(評估鉤子 ? 鉤子(…) : wood_eng_resolve(…)))` 換成 `false` | 1 層，單層即被殺 | 規則是「束縛的尺寸來源必須解析得出來（0、負值、不存在的材料或參數、application 來源），解析不了就拒絕，不能當成未完成」。GEO-261 把 `eng_resolve` 換成「來源圖的 slot 鉤子，沒有鉤子才直接 `wood_eng_resolve`」，整個 `resolve&&!解析` 項換成 `false`，與 main 的替換同形。殺手測試在 `:452` 以 `preview.valid` 為 True 失敗（slot 1 的 A 被當成 `None`），與 main 完全相同。 |
| cancelled-preview（不在原漂移清單，實跑時發現） | `geometry-web/engineering_bridge.inc:173` 確認時 `…||!g_preview.ready||!mine||…` 拿掉 `!g_preview.ready` | 同檔 `:197` 同一個守門；另一層 `:217` 取消時的 `app_candidate_discard(g_preview.transaction->control);` 一併拿掉 | 2 層。只拿守門：存活（XA1）。只拿丟棄：存活（XA2）。守門加 `:198` 的 `app_world_candidate_current`：仍存活（XA3），表示丟棄後的候選在重驗或發佈還會被拒（沒有逐一拆開確認是哪一道）。兩層都拿掉才被殺（XA4） | main 的取消只做 `ready=false`，確認的 `ready` 守門是唯一防線。GEO-261 在取消時多丟棄候選，所以守門單獨拿掉不再重現 main 的錯。兩層都拿掉後行為回到 main 拿掉守門的樣子：取消後的 `assembly-confirm` 回 `ok:true`，殺手測試在 `:472` 失敗，與 main 完全相同。 |

「與 main 完全相同」是實測：在 `adbaebf9` 跑 main 原本的三個突變，失敗位置與斷言都和上表一致（收據在下面）。

#### GEO-261 WSL 實跑收據（2026-10-20）

受驗提交是 `bda11f1430a19c88e0b0474dfe5034d3cf35b9f5`，`git status` 乾淨。環境：WSL Ubuntu-24.04、GCC 13.3.0，ext4 clone `/var/tmp/anchor-drift-geo261/repo`，經 WSL 鎖。

- `python3 tests/assembly_mutation_check.py` 結束碼 0，153 秒。
- 基準線 3 個測試 OK、0 skip。`conflict`、`missing-source`、`cancelled-preview` 各以 1 個測試、1 個 AssertionError 被殺，失敗位置依序是 `test_assembly_rules.py` 的 `:218`、`:452`、`:472`。
- 還原後基準線 3 個測試 OK，且還原後 bridge 的 sha256 與基準線相同（`ce9fd031…`）。
- 改錨前對照（`7e36543b`，工具未改）：基準線編譯在 8 秒內失敗。
- main 對照（`adbaebf9`，main 原本的三個突變）：三個都被殺，位置與上面相同。
- 單層對照組（同一提交，不進工具）：XA1、XA2、XA3 結束碼 0（存活），XA4 結束碼 1（被殺）。

收據沒有提交進 repo，在 `D:/geometry-axiom-work/anchor-drift-20261020/`：

| 目錄 | 內容 |
|---|---|
| `final-tools/` | 受驗提交的完整輸出，`assembly.out` sha256 `3ac2d1f0e40c3e7e74424ffb1c0fc81ab2e48a4c4e71cb885a085dd998229bf3` |
| `controls/` | XA1～XA4 與 PF3 的對照組，`cmd.log` sha256 `9675a07f85a493642d0f2f0f265f042cf2774f3e719853e9a3271fd2813451db` |
| `main-compare/` | main 的原突變，`cmd.log` sha256 `63a9f884d75b138e48148315c43d6b46b62ecb7222d51a6c1393e017ed88a3e3` |
| `before-tools/` | 改錨前的失敗 |

### killed 判準：每個突變綁定單一斷言（2026-10-20，PR #288 審查須改第 5 項）

上面那一輪的判準（結束碼 1、輸出含 `AssertionError`）只證明「這個測試的某個斷言失敗了」，不證明是目標斷言。實測證據：`control-wrong-assertion` 把 `assembly-cancel` 的回報改成 `cancelled:false`，同一個測試在更早的斷言失敗，舊判準照樣算 killed（收據裡 `legacyCriterionKilled: true`）。

現在每個案例是 `(名稱, 補丁, 殺手測試, 殺手標記)`。殺手斷言以 `tests/test_assembly_rules.py` 的 `killer(標記)` 當失敗訊息；工具讀子行程寫出的結構化結果（失敗、error、skip 各自的測試名、例外型別與訊息裡的標記），不再 grep 文字。killed 要同時成立：

1. 基準線（未改動來源）把所有持有殺手標記的測試跑一遍（現在是三個），全綠、沒有 skip，且測試檔裡**每一個**殺手標記都被執行過：要求的是 `TAGS` 的全部 8 個，不只案例綁定的 3 個；被執行到卻沒列在 `TAGS` 的標記也判紅（`unlisted-tag-reached`）。`killer()` 求值時記入 `REACHED`，所以斷言通過也記得到；標記只是躺在檔案裡、斷言卻跑不到，基準線就判紅。（2026-10-20 前的版本只要求案例綁定的 3 個，另外 5 個沒有人看守，見下面「第二次實跑收據」的更正。）
2. 突變版只跑殺手測試，恰好一筆失敗：是殺手測試、是斷言失敗（不是 error）、訊息只帶這一個標記；沒有 skip、error、橋接器死亡、逾時、第二筆失敗，二進位也與基準線不同。
3. 還原後來源樹與基準線逐位元組相同（逐階段比來源摘要），重編的基準線與第一次二進位 sha256 相同，三個殺手測試再度全綠。

其他結果一律 not-killed，並寫出原因：`survived`、`wrong-assertion`、`wrong-test`、`extra-failures`、`error`、`skipped`、`unexpected-outcome`、`bridge-closed`、`timeout`、`child-crash`、`child-inconsistent`、`identical-binary`。

| 案例 | 殺手測試 | 殺手標記 | 標記所在 |
|---|---|---|---|
| conflict | `test_duplicate_scope_and_endpoint_rejected` | `conflict:scope` | `:235` 傳給 `reject`，由 `reject` 的 `:99`（preview 必須無效）帶出；`end` 變體另有 `conflict:end`，不屬於這個突變 |
| missing-source | `test_bad_dimension_sources_rejected_not_incomplete` | `missing-source:literal-zero` | `:471` 傳給 `reject`，同樣由 `:99` 帶出；迴圈的第一個來源，測試在第一筆失敗就停 |
| cancelled-preview | `test_cancel_and_protocol_tokens_do_not_commit` | `cancelled-preview:confirm-after-cancel` | `:491`，取消後的 `assembly-confirm` 必須回 `ok:false` |

前一位 agent 用 main 人工比對的 `:218`、`:452`、`:472` 是加標記前的行號，在 `661d72bf` 是 `:233`、`:469`、`:489`（同一個陳述式；`:97` 是 `reject` 內同一條斷言）。`d3746972` 把 `killer()` 的說明加了 2 行，之後的行號都加 2，現在是 `:235`、`:471`、`:491`、`:99`；上表與下面的 `TAGS` 表用現在的行號，第二次實跑收據保留 `661d72bf` 的行號。標記讓比對不再靠行號。

#### 全部殺手標記（`TAGS`）與 `--check` 擋的事

測試檔裡一共 8 個標記，工具的 `TAGS` 逐一列出標記與持有它的測試方法。三個案例只綁其中 3 個，另外 5 個是同一個迴圈的後幾輪；它們不是裝飾，是「這一輪還在跑」的證明（基準線要求 8 個全部被執行）。

| 標記 | 持有它的測試 | 綁定的案例 | 釘住什麼 |
|---|---|---|---|
| `conflict:scope` | `test_duplicate_scope_and_endpoint_rejected` | conflict | 兩個接合點共用 scope 必須拒絕（標記字串在 `:233`，迴圈第一輪） |
| `conflict:end` | 同上 | 無 | 共用端點必須拒絕（迴圈第二輪）。conflict 突變只拿掉 scope 檢查，這一輪不是它的目標 |
| `missing-source:literal-zero` | `test_bad_dimension_sources_rejected_not_incomplete` | missing-source | 尺寸來源 0 必須拒絕（`:466`，迴圈第一個來源） |
| `missing-source:literal-negative` | 同上 | 無 | 尺寸來源 -1（`:466`） |
| `missing-source:material` | 同上 | 無 | 不存在的 material（`:467`） |
| `missing-source:parameter` | 同上 | 無 | 不存在的 parameter（`:468`） |
| `missing-source:application` | 同上 | 無 | application 來源（`:469`） |
| `cancelled-preview:confirm-after-cancel` | `test_cancel_and_protocol_tokens_do_not_commit` | cancelled-preview | 取消後的確認必須回 `ok:false`（`:491`） |

`--check`（每次執行前也是同一道靜態閘門）要求：

- `TAGS` 的每個標記在 `test_assembly_rules.py` 裡恰好出現一次，而且在 `TAGS` 指定的方法裡。刪掉某一輪（出現 0 次）、讓標記重複（2 次以上）、把標記搬到別的測試，都會被指名。
- 測試檔裡不得有 `TAGS` 沒列的 `family:name` 字串常數（新增而沒登記）。
- `killer()` 的第一個引數只能是 `family:name` 字串常數，或 `reject()` 傳下來的 `tag`；用組字串造標記，靜態看不到，直接擋。
- 每個案例綁的標記必須在 `TAGS`，案例的殺手測試必須與 `TAGS` 為該標記指定的方法相同。

靜態檢查只看得到「標記在檔案裡」。迴圈被改成不執行、`killer()` 所在的斷言走不到、或執行時才造出標記，靠基準線的 `REACHED` 與 `unlisted-tag-reached`。兩道合起來，刪一輪、重複、搬家、漏登記、整輪跑不到，各有一道會變紅。

負對照（`CONTROLS`）是真的故障，走和案例完全相同的編譯、測試與判斷，必須因指定原因被判 not-killed，否則整次執行判失敗：

| 對照 | 補丁 | 必須的原因 |
|---|---|---|
| `control-wrong-assertion` | `engineering_bridge.inc` 的 `bool cancelled=…;` 改成 `bool cancelled=false;` | `wrong-assertion`：同一測試更早的 `assembly-cancel` 斷言失敗，沒有標記 |
| `control-bridge-crash` | 取消成功時 `abort()` | `bridge-closed`：`BridgeClosed` 是 `AssertionError` 子類，unittest 記成 failure 而非 error，工具另外指認 |
| `control-error` | 取消回覆的 `{"ok"` 改成 `{ok`，不再是 JSON | `error`：`json.JSONDecodeError` |
| `control-hang` | 取消成功時 `for(;;){}`，測試時限 15 秒 | `timeout`：整組程序（含橋接器）被 `killpg` 殺掉。殺完之後工具再讀 `/proc`，看該 process group 與 session 還剩哪些程序（殭屍也算，最多等 5 秒），把殺前成員、殺後成員、等了幾秒記成這個階段 `record.json` 與 `tests/execution.json` 的 `processGroup`；殺後仍有程序、或讀不到 `/proc`，整次執行判失敗 |
| `control-single-layer` | 只拿掉 `cancelled-preview` 兩層裡的守門那一層 | `survived`（即上表 XA1） |
| `control-comment-only` | 在 conflict 案例的錨點（`assembly.c:66` 的 `if(!strcmp(scopes[k],scopes[i]))`）同一行後面加 `/* comment only */`，不改任何程式碼 | `identical-binary`：沒有加 `-g`、行數不動（`__LINE__` 也不會變），所以編出的二進位必須與基準線逐位元組相同；判決先比二進位 sha256，再看測試結果，所以這一階段的測試不論過不過都是 identical-binary。`--check` 要求這種對照的補丁只能是加 `/* */` 註解、不得增減換行；拿掉工具裡的二進位比對，這個對照會被判 `survived` 而讓整次執行失敗 |

不用補丁就能驗的部分在 run_all 的 `test_assembly_mutation_check`（12 個 test）：每個殺手標記（8 個）恰好出現一次、在指定的方法裡、沒有未登記的標記與無法登記的 `killer()` 引數、基準線要求全部標記且不接受未登記的標記、每個案例與對照的錨點仍存在且唯一、34 條判斷規則（含上表所有原因，`identical-binary` 也有）、註解對照只加註解、舊判準會把別的斷言當成 killed 而新判準不會、結果記錄器分得開標記、error、skip、橋接器死亡與子測試、被殺程序群組的查驗（`/proc` 解析、輪詢、殘留判定）。最後一項另有一個真的 `sh` 子程序樹被殺、殺後 `/proc` 乾淨的測試，只在 Linux／WSL 執行，Windows 上該測試直接回傳、什麼都沒驗；Windows 上驗不到的那一段由工具實跑的收據負責。`python3 tests/assembly_mutation_check.py --check` 與 `--selftest` 不需要編譯器。

#### 第二次實跑收據（2026-10-20，標記判準；表中行號是 `661d72bf` 的 `test_assembly_rules.py`）

受驗提交 `661d72bfa890fdf25818577dfbe66e2230656b1e`，`git status` 乾淨；工具 sha256 `206f12be…`、`test_assembly_rules.py` sha256 `690e4e22…`（都是 LF 形式，與收據 `judge` 欄相同）。WSL Ubuntu-24.04、GCC 13.3.0、Python 3.12.3，ext4 clone `/var/tmp/assembly-oracle-geo261/repo`，經 WSL 鎖。`python3 tests/assembly_mutation_check.py --out …` 結束碼 0，`ok: true`，`problems: []`，473 秒。跑前 `--check`、`--selftest`、`unittest tests.test_assembly_mutation_check tests.test_mutation_anchors`（10 tests）都通過。

| 階段 | 結果 | 失敗的位置與標記 | 舊判準 | 二進位 sha256 前 12 碼 |
|---|---|---|---|---|
| baseline | pass | 3 個測試全綠；`result.json` 的 `reached` 列出 8 個標記（更正：當時工具只要求案例綁定的 3 個，其餘 5 個是事後觀察，不是閘門） | | `a56a309f3fdb` |
| conflict | killed | `test_duplicate_scope_and_endpoint_rejected` `:233`→`:97`，`conflict:scope` | killed | `f925c8b6bba7` |
| missing-source | killed | `test_bad_dimension_sources_rejected_not_incomplete` `:469`→`:97`，`missing-source:literal-zero` | killed | `a7f6fcbd0f56` |
| cancelled-preview | killed | `test_cancel_and_protocol_tokens_do_not_commit` `:489`，`cancelled-preview:confirm-after-cancel` | killed | `cf361d2d4924` |
| control-wrong-assertion | not-killed／wrong-assertion | 同一測試 `:488`，無標記 | **killed** | `c02d327dbcc5` |
| control-bridge-crash | not-killed／bridge-closed | `:488` 的 `BridgeClosed`，橋接器已結束 | 不算 | `8370dd36f100` |
| control-error | not-killed／error | `json.JSONDecodeError`，errors=1、failures=0 | 不算 | `b5af3976b61e` |
| control-hang | not-killed／timeout | 15.01 秒後被殺，沒有結果檔（更正：原本這格寫「之後 `ps` 查無殘留程序」，但 `run2/` 裡沒有 `ps` 輸出，說法已刪；殘留程序的查驗由工具自己記錄，從第三次實跑起） | 不算 | `44df9c5a9591` |
| control-single-layer | not-killed／survived | 測試通過 | 不算 | `d47fb584cc22` |
| restored | pass | 3 個測試再度全綠 | | `a56a309f3fdb`（與 baseline 相同） |

每個階段都記了突變後與還原後的來源摘要：十個階段還原後都回到基準線的 `91364b349f4f…`，`originalSourcesUnchanged: true`。二進位 sha256 只能在同一次執行內比較：兩次執行的暫存目錄不同，同一份來源編出的基準線 sha256 也不同（先行的 run1 是 `9f810c80…`，run2 是 `a56a309f…`，來源摘要都是 `91364b34…`）。

收據在 `D:/geometry-axiom-work/assembly-oracle-20261020/`，沒有提交進 repo：`run2/out/` 每階段有 `patches` 與 `patchedFiles` 摘要、`build/` 編譯輸出、`tests/` 的 stdout、stderr、`result.json`（結構化結果）、`execution.json`、`record.json`；`summary.json` sha256 `ff38239c2139bba15f072f90653efcb7235bca3026d09d5aa5935edd25718f02`，`sources.json` sha256 `6adcf046fdd6202364e3b1424eb3868dc3c95c93c87aa5b1038f72b6b517be25`，`run2/assembly.out` sha256 `fa186917517f7dfbc2b28030ea0077c5ff02f54a7e415ae04724c9dca0dd44a8`。`run1/` 是同一天先跑的版本（`666f4654`，三個對照、說明文字較舊，全數通過），保留不當作最終收據。

限制：標記證明的是「失敗的是這一條斷言」，不證明它失敗的原因就是被注入的缺陷，那一層仍靠補丁與測試的對應。skip 沒有真實對照：橋接器的故障造不出 skip，只由 `--selftest` 與記錄器單元測試覆蓋。`missing-source` 的殺手是迴圈第一個來源，其餘四個來源（以及 `conflict:end`）的拒絕沒有被任何突變個別證明；第三次實跑起，基準線至少證明這幾輪每次都跑到且通過，有人刪掉或重複它們，`--check` 會指名。

#### 第三次實跑收據（2026-10-20，全部標記、unchanged-binary 對照、殘留程序查驗）

受驗提交 `d3746972b62d896ce09aae3b79f34a9b3e08b649`（這一輪的工具、測試與文件說明；之後的提交只改本文件），`git status` 乾淨；工具 sha256 `230010fa…`、`test_assembly_rules.py` sha256 `f29e1379…`（都是 LF 形式，與收據 `judge` 欄相同）。WSL Ubuntu-24.04、GCC 13.3.0、Python 3.12.3，ext4 clone `/var/tmp/assembly-oracle-geo261/repo`，經 WSL 鎖。`python3 tests/assembly_mutation_check.py --out …` 結束碼 0，`ok: true`，`problems: []`，392 秒，`schema: assembly-mutations/3`。跑前 `--check`（8 個標記、3 個案例、6 個對照）、`--selftest`（34 條）、`unittest -v tests.test_assembly_mutation_check tests.test_mutation_anchors`（15 tests，含只在 Linux 才實際執行的真實程序群組測試）都通過。其餘結果與第二次相同，多出 `control-comment-only`，並且 `control-hang` 多了殘留程序紀錄：

| 階段 | 結果 | 失敗的位置與標記 | 舊判準 | 二進位 sha256 前 12 碼 |
|---|---|---|---|---|
| baseline | pass | 3 個測試全綠；`reached` 與 `killerTags` 同為 8 個標記，工具要求的就是這 8 個 | | `a06cfd0d18a9` |
| conflict | killed | `test_duplicate_scope_and_endpoint_rejected` `:235`→`:99`，`conflict:scope` | killed | `557a5117f482` |
| missing-source | killed | `test_bad_dimension_sources_rejected_not_incomplete` `:471`→`:99`，`missing-source:literal-zero` | killed | `61b568b1ebce` |
| cancelled-preview | killed | `test_cancel_and_protocol_tokens_do_not_commit` `:491`，`cancelled-preview:confirm-after-cancel` | killed | `1e7d4b938572` |
| control-wrong-assertion | not-killed／wrong-assertion | 同一測試 `:490`，無標記 | **killed** | `9fb0d76de926` |
| control-bridge-crash | not-killed／bridge-closed | `:490` 的 `BridgeClosed`，橋接器已結束 | 不算 | `fc91a5b2ae02` |
| control-error | not-killed／error | `json.JSONDecodeError`，errors=1、failures=0 | 不算 | `4d0deff8cafc` |
| control-hang | not-killed／timeout | 15.01 秒後被殺，沒有結果檔。`processGroup`：殺前 2 個程序（`python3` 測試子行程 46715 與 `controls-control-hang-bridge` 46716，同一 process group、同一 session），殺後 0 個，第一次查就已消失（`secondsUntilGone` 0.0） | 不算 | `e7c0b4a865eb` |
| control-single-layer | not-killed／survived | 測試通過 | 不算 | `b078c68df6b1` |
| control-comment-only | not-killed／identical-binary | 測試通過（結束碼 0）；二進位與 baseline 逐位元組相同 | 不算 | `a06cfd0d18a9`（與 baseline 相同） |
| restored | pass | 3 個測試再度全綠 | | `a06cfd0d18a9`（與 baseline 相同） |

十一個階段還原後來源摘要都回到 `91364b349f4f…`（與前兩次相同），`originalSourcesUnchanged: true`、`restoredBinaryMatchesBaseline: true`。`control-comment-only` 的二進位與 baseline 相同，是在同一次執行內比較的結果；沒有加 `-g`、註解與錨點在同一行、行數不動，所以沒有改到 `__LINE__` 之類會影響輸出的東西，不必換成別的改法。

收據在 `D:/geometry-axiom-work/assembly-oracle-20261020/run3/`，沒有提交進 repo：`out/` 的結構與第二次相同，另有 `pre.out`（跑前三道檢查）與 `run.log`；`out/summary.json` sha256 `dce885d4ad0f30ea09011df17f39caa8675e812b45c87ebfd5b73eb034e23cbb`，`out/sources.json` sha256 `6adcf046fdd6202364e3b1424eb3868dc3c95c93c87aa5b1038f72b6b517be25`（與第二次相同），`assembly.out` sha256 `8a1dcd8df4442c2d47caf8bed0326a28651ec1661333d10b20275ef04c10f0b0`。殘留程序的收據是 `out/controls/control-hang/tests/execution.json` 與同階段 `record.json` 的 `processGroup`。

**拿掉新檢查會怎樣（突變自證）。** 逐一拿掉本輪新增的檢查，對應的測試、`--selftest` 或整次執行會變紅。Windows 端用 `python -m unittest tests.test_assembly_mutation_check` 與 `--selftest`、`--check` 逐項驗；M7 與 M11 另在 WSL 對 `d3746972` 的 `git archive` 拷貝上跑（收據在 `run3-mut/`，同樣沒有提交）：

| 拿掉的東西 | 變紅的是什麼 |
|---|---|
| M1 基準線改回只要求案例綁定的 3 個標記（舊行為） | `test_the_baseline_has_to_reach_every_listed_tag_and_nothing_else` |
| M2 `judge_pass` 不再擋未登記的標記 | 同上、`test_verdict_rules_reject_everything_but_the_exact_assertion`；`--selftest` 結束碼 1 |
| M3 `--check` 不再數標記出現幾次 | `test_a_tag_that_no_case_is_bound_to_cannot_be_deleted_repeated_moved_or_added_unnoticed` |
| M4 `--check` 不再找未登記的標記字串 | 同上 |
| M5 `--check` 不再檢查 `killer()` 的引數 | 同上 |
| M6 `--check` 不再要求標記在指定的方法裡 | 同上、`test_binding_problems_name_a_missing_moved_or_duplicated_tag_or_test` |
| M7 工具不再判 `identical-binary` | `test_a_comment_only_control_is_judged_identical_binary_and_changes_nothing_else`、`test_verdict_rules_…`；`--selftest` 結束碼 1（3 條 identical-binary 規則轉紅）；WSL 完整執行 `ok: false`、結束碼 1，`problems` 只有一條：`control control-comment-only was judged not-killed/survived, expected not-killed/identical-binary`（`m7-out/summary.json` sha256 `528ac759…`，372 秒） |
| M8 註解對照不再被限制只能加註解 | `test_a_comment_only_control_is_judged_identical_binary_and_changes_nothing_else` |
| M9 `control-comment-only` 從 `CONTROLS` 刪掉 | 同上、`test_cases_and_controls_are_bound_to_live_assertions_and_anchors` |
| M10 殺後仍有程序不算問題 | `test_what_is_left_of_a_killed_process_group_is_looked_up_and_a_leftover_is_a_problem` |
| M11 殺完不再查程序群組 | Windows 上沒有任何測試變紅（真實程序測試在 Windows 直接回傳）；WSL 上 `test_run_logged_kills_the_whole_group_and_records_that_nothing_is_left` 變紅：殺完立刻查，兩個 `sleep` 殭屍還在（`m11-unittest.out`） |
| M12 不算已離開 process group 但仍在 session 的程序 | `test_what_is_left_…` |

M11 那一行同時說明了為什麼殺完要輪詢：`SIGKILL` 剛送出時，子程序會短暫以殭屍的狀態留在 `/proc`，立刻查看到的是殭屍而不是乾淨。第三次實跑的 `control-hang` 第一次查就乾淨，不代表這個等待可以省。

## 環境限制與計數紀律

Windows SAC 仍阻擋部分預設路徑 core／bridge／完整性檢查執行檔；未停用安全設定。
WSL 的 Windows GDI 案例會 skip，該案例已另以目前原始碼重編 Windows GDI harness 實際通過。
Windows 專用路徑的 bridge 另跑 28 個組構／共用基準案例通過。既有全庫 mutation 結果因核心改動會 stale；
本次只宣稱上述三項新功能故障注入結果，不冒用舊結果。
新增 suite 的 19 個 test 與 Node 的 4 個 test，依完整執行實際 census 更新 expected；
自動更新因 GDI skip 拒絕，故本次明確只調整這兩個數量，保留 skip 守門及非零退出碼。
斷言、單元案例、scene 案例與 C 檢查點分列，不相加宣稱端到端流程數。

最終執行摘要、完整日誌、截圖與來源雜湊見 [驗證紀錄](assembly-validation/README.md)。

## 回歸中修復的缺陷

- 混合能力保存：原生回傳清單次序與專案的排序不同；比較前排序，仍拒絕真正缺失能力。
- Windows 確認交易：規則資料擴大 World，遞迴確認路徑的三份多 MB 區域副本導致堆疊耗盡。
  比對改為略過畫布區段直接比較原資料，保留原有版本與完整性守門；原失敗 datum 案例重新通過。
- 空間庫重開舊格式模型：`show → refresh → openRecord → show` 在舊指紋仍有效時遞迴。
  進入 show 前清除舊記錄指紋，正常模型載入再寫回；舊 v1/v2 開啟及牆高編輯回歸驗證。
- 小筆電／短螢幕：共用標題列的樣式優先序壓縮預覽；短螢幕的重複來源捷徑擠走確認。
  恢復 compact 標題高度，寬高皆 ≤720px 時收起捷徑，保留來源設定和返回入口。
- 空間測試仍要求已作廢的 56px 面工具列；改依 DOM-CONTRACT 的 116／122px 雙列配置，
  同時驗證視窗寬度、操作區不重疊及標題可見。
- 手機字級檢查誤把 0px 隱藏長文字當成可見內容；改量實際文字範圍與偽元素標籤，
  保留 11px 下限，也涵蓋真正顯示的精簡專案狀態。
- 網格測試開啟配置後未等待非同步頂點／承載面資料；改等載入完成，再以原斷言核對同邊界承載面。
- 畫布建立空間先請求空號，再提交與重畫；測試改等新空間出現在畫布後，再讀核心核對，避免在兩個請求之間誤判。
- 換版對應的槽位名稱須以文字插入；統一逸出欄位標籤，P77 以含 HTML 標記的名稱實際換版驗證。
- 參數手動試算未取消尚待執行的自動試算，兩者可能覆寫核心候選，導致確認憑證失效。
  每次試算先取消計時、清除舊候選並停用確認；P76 延後回覆超過原排程時間，驗證只發出一次試算，再真正確認套用。

追溯矩陣的紅黃綠量的是條號引用，不是測試結果；本次輸出 62 綠／23 黃／27 紅。
它仍未涵蓋所有獨立模組，組構逐條實測對應以上矩陣，不以修改燈號冒充覆蓋。


## 2026-10-03 原生新增／修改防護

最新增量、基準及 #50/#51 的相容性取捨見 [收尾紀錄](ASSEMBLY-CLOSEOUT-20261003.md)。
A24 實體手機鍵盤、OS 檔案選擇器與下載位置仍未驗收，不能以 390px CDP 取代。
#25 仍是[待核准提案](../../geometry-core/ASSEMBLY-GENERATION-PROPOSAL.md)，沒有已完成生成聲明。
