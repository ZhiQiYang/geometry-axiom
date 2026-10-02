# 組構規則第一階段驗收（GEO-226／PR #26）

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
python3 tests/assembly_mutation_check.py
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
略過衝突檢查、略過尺寸來源解析、允許已取消預覽確認，均須由指定案例的 AssertionError 偵測。
編譯失敗、崩潰、skip 不算抓到缺陷；不修改工作區，也不覆寫既有全庫 mutation 結果。
另以 `GEOMETRY_ASSEMBLY_ONLY=1 GEOMETRY_ASSEMBLY_INJECT_SWAP=1` 跑 CDP，攔截交換按鈕、只改文字：
P77 的核心草稿身分斷言如預期失敗。正常執行不帶注入變數；完整模式禁止此注入。

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
