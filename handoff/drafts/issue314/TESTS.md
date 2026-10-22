# #314 測試計畫（草稿，未編譯、未執行）

配套文件：`DESIGN.md`（路徑編號 C1–C9、D1–D7 與訊息 M0／M1／M2 沿用該稿）、`patch.diff`。
基準：`grid_inspector_rename_test.js` 的行號與內建場景 `AppDefaultReplay` 改以 `546e2eb2` 為準。這份計畫裡所有程式碼片段都是草稿，沒有編譯過。其餘片段最初對照 `09ab5f79`，這次沒有重編譯。

## 0. 原則

1. 每條提交路徑各一組正例與反例；反例必須釘住拒絕理由（用 `reject(cmd, why=(…))`，不要 `why=None`），否則「預覽被突變放行、確認仍然擋住」這類假綠抓不到（`reject` 的第一個斷言對預覽式回應 `ok:false` 恆成立，其餘只看最後 `confirm` 是否失敗與世界是否不變；預覽階段被突變放行時，只有理由釘住那一條會變紅）。
2. 預覽式回應（既有 id 的 `grid-system` 重宣告、`engineering` 單行、橋接器批次）反例要同時斷言三件事：`preview.valid` 為 false、拿該 token 去 confirm 失敗、拒絕前後 `dump`／`objects`／revision 逐位元不變。
3. 舊兩軸世界一律用「未打補丁的 bridge 產生、補丁後 `loadfile` 載入」的路徑建（見 §4.1），**不要**用互動提交建，否則補丁後建不出來。
4. 數字用手算的獨立常數，不用被測程式的輸出當 oracle（沿用 `test_infinite_grid_contract.py` 的紀律）。
5. 突變：拿掉檢查必須紅；一條路徑一個專屬突變（拿掉該路徑的基線），證明不是靠別條路徑代跑。

## 1. 要新增與要擴充的檔案

| 檔 | 內容 | 需要二進位 |
|---|---|---|
| `tests/geo261_grid_application_harness.c`（擴充）加 case `stagger-commit` | W 決策表 W01–W18，只用兩個 K store | 否（只需 K+W 物件，同 `test_geo261_wood_grid_application.py`） |
| `tests/test_geo261_wood_grid_application.py`（擴充） | `test_stagger_commit_decision_table`、W 突變 | 同上 |
| `tests/test_geo314_stagger_commit.py`（新增） | §3 每條路徑的正反例、§4 舊檔回歸，真 bridge | bridge、model-base |
| `tests/test_geo314_commit_paths.py`（新增） | §5 普查：純靜態，不編譯 | 否 |
| `tests/mutate.py` + `tests/mutation_bridge.py` | §7 突變登錄（下一個編號 M99 起；M89–M96 為 #299，M97–M98 為 #316） | bridge |
| `tests/run_all.py`（`PY_NEEDS`）與 `tests/run_all.expected.json` | 登錄新 suite；測試數用 `unittest.defaultTestLoader.loadTestsFromName(...).countTestCases()` 數，不要從成功執行回填 | — |

新測試檔必須登錄，否則 `run_all.py` 判 fail 並指名（`tests/README.md`）。

## 2. W 單元測試（`wood_grid_stagger_commit_valid`）

兩個 `GeoGridStore`（before、after），各放 0–2 個系統。每格系統兩軸都是 `REPEAT`，phase 0、step 100（沿用 harness 的 `system_value(id,true)`）。`u/v = (設不設, 值)`。

| ID | before | after | 預期 | 釘住的標記（`CHECK_NAMED`） |
|---|---|---|---|---|
| W01 | 無此系統 | `u=400, v=30` | 拒絕；訊息含「I24」「同一份網格只能有一軸錯開」與系統 id | `stagger-new-two-axis` |
| W02 | `u=40` | `u=40, v=30` | 拒絕（M1） | `stagger-add-second-axis-v` |
| W03 | `v=30` | `u=40, v=30` | 拒絕（M1） | `stagger-add-second-axis-u` |
| W04 | `u=40` | `v=30`（只剩另一軸） | 通過（換方向） | `stagger-switch-axis` |
| W05 | `u=40, v=30` | `u=40, v=30` | 通過 | `stagger-legacy-unchanged` |
| W06 | `u=40, v=30` | `u=45, v=30` | 拒絕（M2）；訊息含「先在同一筆編輯裡移除一軸」「u」「40」「45」 | `stagger-legacy-u-changed` |
| W07 | `u=40, v=30` | `u=40, v=35` | 拒絕（M2）；訊息含「v」「30」「35」 | `stagger-legacy-v-changed` |
| W08 | `u=40, v=30` | `u=45, v=35` | 拒絕，報第一個變動的軸 u | `stagger-legacy-both-changed` |
| W09 | `u=40, v=30` | `v=35`（移除 u、改 v） | 通過 | `stagger-remove-one-and-edit-other` |
| W10 | `u=40, v=30` | 兩軸皆無 | 通過 | `stagger-remove-both` |
| W11 | 兩軸皆引用，`u→(901,1)` 快取 400，`v→(901,2)` 快取 300 | 同引用，快取變 401／301（卡改值） | 通過（S7） | `stagger-ref-card-edit-is-not-an-edit` |
| W12 | `u→(901,1)` 快取 400，`v` 直接 30 | `u` 直接 400（解除引用，值同），`v=30` | 通過 | `stagger-unbind-same-value` |
| W13 | 同 W12 | `u` 直接 401 | 拒絕（M2） | `stagger-unbind-different-value` |
| W14 | `u→(901,1)` 快取 400，`v=30` | `u→(901,3)` 快取 400，`v=30` | 通過（另一個引用，值同） | `stagger-repoint-same-value` |
| W15 | 同 W14 | `u→(901,3)` 快取 401 | 拒絕（M2） | `stagger-repoint-different-value` |
| W16 | 兩個系統：A 合法一軸，B 新增兩軸 | — | 拒絕；訊息指名 B 的 id，不是 A | `stagger-names-the-offending-system` |
| W17 | `after == NULL` 或 `before == NULL` | — | 拒絕（M0），不崩潰 | `stagger-missing-store-fails-closed` |
| W18 | `REPEAT_PANEL` 軸（K 的列舉名是 `GEO_GRID_SOURCE_REPEAT_BODY_GAP`，用 `body/gap/anchor`）兩軸 | 同 W01／W06 | 與 REPEAT 軸結果相同（規則不看排法） | `stagger-repeat-panel-same-rule` |

harness 草稿（未編譯）：

```c
static GeoGridSystem staggered(uint32_t id,bool u,GeoCoord su,bool v,GeoCoord sv)
{
    GeoGridSystem s=system_value(id,true);
    s.axis[0].stagger_set=u;s.axis[0].stagger=su;
    s.axis[1].stagger_set=v;s.axis[1].stagger=sv;
    return s;
}
static GeoGridStore *store_of(const GeoGridSystem *a,const GeoGridSystem *b)
{
    GeoGridStore *s=geo_grid_store_create();
    if(s&&a&&!geo_grid_systems_put(s,a)){geo_grid_store_destroy(s);return NULL;}
    if(s&&b&&!geo_grid_systems_put(s,b)){geo_grid_store_destroy(s);return NULL;}
    return s;
}
static int stagger_commit(void)
{
    char error[256];
    GeoGridSystem none=staggered(7,false,0,false,0),two=staggered(7,true,40,true,30);
    GeoGridStore *before=store_of(&none,NULL),*after=store_of(&two,NULL);
    CHECK(before&&after);
    CHECK_NAMED(!wood_grid_stagger_commit_valid(after,before,error,sizeof error),"stagger-new-two-axis");
    CHECK_NAMED(strstr(error,"I24")&&strstr(error,"同一份網格只能有一軸錯開"),"stagger-new-two-axis");
    /* …其餘列照表；ref 列要設 axis.parameters[5]={true,901,1} 與 stagger 快取… */
    geo_grid_store_destroy(before);geo_grid_store_destroy(after);
    return 0;
}
```

每個標記對應一個 `test_*` 突變（§7 的 W 類），用 `case(name, exe, marker)` 要求精確標記，錯的標記不算殺死。

## 3. 每條提交路徑的正反例（真 bridge）

共用小工具（沿用現有）：`infinite(id, name, u, v, main)`（`test_infinite_grid_contract.py`）、`reject(cmd, why)`、`commit(cmd)`、`snapshot()`（`test_grid_system_contract.py`）、R60 的 `grid()`、`swap()`、`unbind()`、`parameter()`、`self.apply(ops)`、`self.reject(ops, reason, label)`（`test_grid_card_reference.py`）。

下表的「反例」都要檢查：拒絕理由含 `("I24", "<M1 或 M2 子字串>")`、世界與 revision 不變、預覽式的 token 不能 confirm。M1 子字串 = `同一份網格只能有一軸錯開`，M2 子字串 = `先在同一筆編輯裡移除一軸`。

### P-C1 DSL `grid-system`，新 id

P1-N1 是獨立的「互動新建雙軸 → 拒絕」反例。§6 的三個既有檔改走舊場景 `loadfile` 之後，這一筆仍留在互動提交上，釘住 I24／M1。

| ID | 指令 | 預期 |
|---|---|---|
| P1-N1 | `infinite(0, u="repeat 0 2000 stagger 400", v="repeat 0 1830 stagger 300")` | 拒絕 M1 |
| P1-N2 | `infinite(0, u="repeat-panel 400 gap 5 from -100 stagger 200", v="repeat 0 600 stagger 100")`（兩種排法混用） | 拒絕 M1 |
| P1-N3 | `infinite(0, u="repeat 0 2000 stagger param:1:1", v="repeat 0 1830 stagger param:1:2")`（先放卡 1：欄 1=400、欄 2=300，否則會先撞 K 的參數來源錯誤而不是 M1） | 拒絕 M1 |
| P1-P1 | `infinite(0, u="repeat 0 2000 stagger 400", v="repeat 0 1830")` | 通過；`dump` 只有 u 有 `stagger` |
| P1-P2 | `infinite(1, u="repeat 0 2000", v="repeat 0 1830 stagger 400")` | 通過（現有 `test_alternating_stagger_…` 已覆蓋，保留） |

### P-C2 DSL `grid-system`，既有 id（I8a 預覽 → confirm）

| ID | 前置 | 指令 | 預期 |
|---|---|---|---|
| P2-N1 | 系統 0 只有 v 錯開 | 重宣告成 u 與 v 都 `stagger` | 預覽無效 M1；confirm 失敗；世界不變 |
| P2-N2 | 系統 0 只有 u 錯開 | 同上對稱 | 同上 |
| P2-P1 | 系統 0 只有 v 錯開 | 一行重宣告成只有 u 錯開（換方向） | 預覽有效、confirm 成功；`dump` 只剩 u |
| P2-P2 | 系統 0 只有 v=400 | 一行重宣告成 v=500 | 通過 |
| P2-P3 | 系統 0 只有 v=400 | 重宣告成兩軸皆無 | 通過 |
| P2-P4 | 系統 0 一軸 | 只改名稱 | 通過 |

### P-C3 `engineering archive <base64>` 單行

載荷 `{"op":"put-grid-system","value":{"id":N,"name":"G","mainAlong":"none","u":"…","v":"…"}}`，行是 `"engineering archive " + base64(json)`（`test_parameters_core.py:545` 已有同樣寫法）。

| ID | 內容 | 預期 |
|---|---|---|
| P3-N1 | 新 id，`u`、`v` 都帶 `stagger` | 預覽無效 M1 |
| P3-N2 | 已有一軸錯開的系統，再加第二軸 | 預覽無效 M1 |
| P3-P1 | 新 id，一軸 | 通過 |
| P3-P2 | 一軸 → 另一軸（同一個 op） | 通過 |

### P-C4 橋接器批次（`engineering-transaction/1`）

用 `self.request(ops)`；反例用 `self.reject(ops, reason, label)`（它已檢查 `preview.valid` 為 false、confirm 失敗、狀態不變）。

| ID | ops | 預期 |
|---|---|---|
| P4-N1 | `[put-grid-system 新 id，兩軸相位差]` | 無效 M1，訊息出現在 `preview.violations[].message` |
| P4-N2 | `[put-grid-system 一軸]` 先提交；再 `[put-grid-system 同 id 加第二軸]` | 無效 M1 |
| P4-P1 | `[put-grid-system 同 id 兩軸 → 再 put-grid-system 同 id 一軸]`（批次內先兩軸後一軸） | **通過**（只比批次前後，不比批次中間狀態） |
| P4-N3 | 舊兩軸世界上：`[put-grid-system u 移除相位差, put-grid-system u 設回不同值]`（同一批） | 無效 M2（最終兩軸且值有變；證明比的是批次最終態） |
| P4-P2 | 一軸世界上 `[put-parameter …]`、`[import-parameters …]`、`[delete-parameter 無關卡]` | 通過（不動網格） |
| P4-P3 | 同一支 `batch_preview` 的 assembly／section-profile／panel-fill 批次（kind 1/2/3），在舊兩軸世界 | 通過（同一個重驗跑到新檢查，網格沒動） |

### P-C5 R60 整卡提交（#253／#298／#312）

起點：`self.apply([parameter(), grid()])`（卡 10：a=12, b=30；系統 4 的兩軸 `repeat … card`）。

| ID | ops | 預期 |
|---|---|---|
| P5-N1 | `put-grid-system` 新 id，`u='repeat -5 card stagger 6'`、`v='repeat 7 card stagger 4'` | 無效 M1 |
| P5-N2 | 已有 `u='repeat -5 card stagger 6'` 的 card 系統，再 `put-grid-system` 把 `v` 也加上 `stagger 4` | 無效 M1 |
| P5-N3 | 同上但 `set-grid-card-reference` 與 `put-grid-system` 在同一批，最終兩軸 | 無效 M1 |
| P5-P1 | 一軸 card 系統：`swap-grid-card-reference`（既有 `test_grid_card_reference.py:456-458` 已覆蓋，保留） | 通過；若對調後相位差是新節距整倍數則是**K** 的 `整數倍` 拒絕，不是 M1／M2（用來證明兩者分得開） |
| P5-P2 | 舊兩軸 card 系統（`u stagger 6`、`v stagger 4`，a=12, b=30，皆為 §4.1 夾具）：`swap-grid-card-reference` | 通過（6 mod 30、4 mod 12 都非零；相位差值不動） |
| P5-P3 | 同夾具：`set-grid-card-reference` 改映射、`unbind-grid-card-reference` 的 `direct` 與 `parameter` 兩種 | 各通過 |
| P5-N4 | 同夾具：`put-grid-system` 把 u 的 `stagger 6` 改 8 | 無效 M2 |
| P5-P4 | 同夾具：`put-grid-system` 把 u 的 `stagger` 拿掉（v 保留） | 通過 |

### P-C6 參數改值

| ID | 前置 | 動作 | 預期 |
|---|---|---|---|
| P6-P1 | 舊兩軸網格，u→`param:901:1`、v→`param:901:2`（§4.1 夾具） | `put-parameter` 把 901 欄 1 由 400 改 401 | 通過；`objects` 的 u 相位差 401；兩軸引用仍在 |
| P6-P2 | 同上 | 同時改兩欄 | 通過 |
| P6-N1 | 同上 | 把欄 1 改 0 | 拒絕，理由是 **K** 的「相位差為 0」，不是 M1／M2 |
| P6-N2 | 同上 | 一批內：`put-grid-system` 把 u 改成直接 `stagger 999` | 無效 M2 |
| P6-P3 | 同上 | `put-grid-system` 把 u 改直接整數 401（等於目前求值）、v 不動 | 通過（W12） |
| P6-P4 | 一軸網格引用參數 | 改卡值 | 通過（既有行為，保留） |
| P6-P5 | 舊兩軸，u 引用參數 A＝400、v 直接 300 | 同一候選內把 A 由 400 改 500，再把 u 解除為整數 500 | 通過（題 3 有序判定：400→500 歸改卡例外，解除是當下值 500→500） |
| P6-N3 | 同上 | 同一候選內把 A 由 400 改 500，再把 u 解除為 450 | 拒絕（解除後不是當下有效值 500；這段變動不是參數卡造成的） |

### P-C7／C8／C9 其他指令、歷史群組、拖曳

| ID | 前置 | 動作 | 預期 |
|---|---|---|---|
| P7-P1 | 舊兩軸世界 + boundary | 依序提交 `grid-binding`、`placement`、`grid … from-binding`、`guide`、`move`、`delete` 一個無關物件 | 每一筆通過（舊兩軸沒動就通過；證明沒有誤傷） |
| P8-P1 | 舊兩軸世界 | `history-begin`；行 1：u 移除相位差；行 2：v 改值；`history-end` | 兩行都通過；一次 `undo` 回到舊兩軸世界（復原不是提交） |
| P8-N1 | 舊兩軸世界 | `history-begin`；行 1：u 改值（仍兩軸） | 行 1 失敗、群組整組回滾、世界等於群組前 |
| P8-N2 | 舊兩軸世界 | `history-begin`；行 1：u 移除；行 2：u 設回新值 | 行 1 通過、行 2 M1、整組回滾 |
| P9-P1 | 舊兩軸世界 | `cmd_drag` 拖一條 guide | 通過 |

## 4. 舊兩軸檔仍可開（D61／R46／I31 與復原重做）

### 4.1 夾具

1. `direct`：`grid-system 0 name-hex <hex> main-along none u repeat 0 2000 stagger 400 v repeat 0 1830 stagger 300`（一行即可）。
2. `param`：兩軸皆 `stagger param:901:1`／`param:901:2` 的世界，卡 901 欄 1=400、欄 2=300。
3. `card`：`u repeat -5 card stagger 6`、`v repeat 7 card stagger 4`，卡 10 欄 3=12、欄 8=30，帶 `card-reference`。
4. `panel`：`u repeat-panel 400 gap 5 from -100 stagger 200`、`v repeat 0 600 stagger -400`（混排法）。
5. `bound`：direct + boundary 71 + `grid-binding` + `grid … from-binding`（用 `test_geo261_native_grid_product.py:source()` 的 `13／-7` 與 `[560,731]` 平移 oracle）。

產生方式：用**未打補丁**的 bridge（目前整合枝或 `e980cb0d`）互動建好，取 `dump` 凍結成 `tests/fixtures/legacy-two-axis-stagger-<名>.scene`，旁邊寫 provenance（產生者 head、bridge 編法、SHA-256），格式照 `tests/fixtures/model-package-main-e980cb0d-stagger.provenance.md`。同時驗：未打補丁的 bridge 對該檔 `loadfile` 成功且 `dump` 逐字相等（確認夾具本身是真舊檔）。

要做建模交換包版本，擴充 `D:/geometry-axiom-work/adopt-260-evidence/make_fixture.sh`（`generate` 目前只產 `profile`、單軸 `stagger 400` 兩份）：加第三份雙軸 `model-package-main-e980cb0d-stagger2.json`，同樣固定在 `e980cb0d` 的乾淨 clone 產生、`verify_package` 重驗、寫 receipt 與 SHA 釘。這份只在 L13 用，屬選配。

### 4.2 案例

| ID | 動作 | 預期 | 對應路徑 |
|---|---|---|---|
| L1 | `loadfile` 夾具 1–5 | `ok:true`；`dump` 與夾具逐字相等；`objects` 的兩軸相位差仍在 | D2 |
| L2 | `loadfile` 夾具 5 後，`dump` 存檔，再開一個新 bridge `loadfile` | 同 L1；平移仍 `[560,731]` | D2、D5 |
| L3 | `load-prepare` 夾具 → `load-confirm` | 準備、確認都成功；確認後世界等於夾具 | D3 |
| L4 | `source-inspect-file` 夾具 | `ok:true`、`complete:true` | D6 |
| L5 | 舊兩軸世界上 `default`（恢復內建場景）、`reset`（互動清空）、`replace-world` | 成功；之後世界是內建場景或空 | D4 |
| L6 | 舊兩軸世界上先做一個單軸編輯再 `undo`、`redo`（§3 P2-P1 之後） | `undo` 回到舊兩軸世界，`dump` 逐字等於編輯前；`redo` 回到單軸 | D1 |
| L7 | 舊兩軸世界 `rename`（只改名稱，保留兩軸相位差）／改間距 | 通過（P-C2 的兩軸版） | C2 |
| L8 | 舊兩軸世界改任一軸相位差值 | 拒絕 M2（u、v 各一個案例） | C2 |
| L9 | 舊兩軸世界一行重宣告成只有一軸，數值可改 | 通過；之後再加回第二軸 → M1 | C2 |
| L10 | 舊兩軸檔內含 `engineering archive` 的 `put-grid-system`（`card` 夾具），`loadfile` | 成功（檔案重放中的 C3 路徑被旗標擋下） | D2 |
| L11 | 一個檔案同時有「一筆單軸系統」與「一筆雙軸系統」，且雙軸那行在單軸之後 | `loadfile` 成功（逐行基線是半成品世界，旗標擋下） | D2 |
| L12 | 失敗的 `loadfile`（檔案後半壞掉）之後，世界等於載入前，且 `g_subgrid_before` 狀態不洩漏：緊接著做一次合法單軸提交成功、一次兩軸新建被拒 | 兩者行為正確 | D2 與 C1 |
| L13（選配） | 用 `model-package-main-e980cb0d-stagger2.json` 做 `verify_package`／重建 | 只更新兩個公理版本欄位；幾何逐位元相同 | D6（I31） |
| L14 | `tests.test_engineering_model_compatibility`（44）與 `tests.test_domain_decoupling_compatibility`（14）原樣 | 全綠；單軸 `stagger 400` 包不受影響 | D6 |

## 5. 普查測試（`tests/test_geo314_commit_paths.py`，純靜態）

目的：把 `DESIGN.md` §2 的分類固定下來，將來新增一個提交入口（或把整體取代改成逐行提交）會紅。

| ID | 檢查 |
|---|---|
| C-1 | 全樹（`current_geometry.c`、`geometry-core/*.inc`、`geometry-web/*.inc`、`geometry-web/web_bridge.c`、`geometry-app/native/*`、`geometry-core/model_base.c`）中 `app_world_candidate_publish(` 的呼叫點集合 = 寫死的清單，每筆標「提交」或「整體取代」；多一筆或少一筆都紅 |
| C-2 | `world_revalidate(` 與 `app_world_revalidate_staged(` 的呼叫點（檔、所在函式）集合 = 寫死的清單；新增呼叫點必須先分類 |
| C-3 | 所有 `g_subgrid_before=` 賦值點集合 = 寫死的清單（`DESIGN.md` §2 表中的基線欄位） |
| C-4 | `world_revalidate_candidate` 函式本體內 `grid_stagger_commit_valid(` 恰出現一次，位置在 `grid_systems_rebuild(` 之後、`grid_bindings_rebuild(` 之前 |
| C-5 | `subgrid_world.inc` 中 `grid_stagger_commit_valid` 的條件恰為 `!g_subgrid_before` 與 `g_parsing_scene_file` 兩項 |
| C-6 | `546e2eb2` 的 `transactions.inc:734` `app_default_replay_lines` 與 `:835` `reference_default_world` 的 `lines[]` 都不含 `stagger`，也不含 `grid-system`。這是目前內建文字的變更警報，不把「內建場景禁止 stagger」升成新規則；D61 的整體取代例外仍成立。普查同時認得 `AppDefaultReplay`（`:729`）、`app_default_replay_line`（`:781`）、`reference_default_world_owned`（`:858`） |
| C-7 | `grid_application.c` 去註解後不含 `World`、`Coord`、`scene_error`、`g_subgrid_before`、`g_parsing_scene_file`（重申既有 W 純度測試，確保新碼沒破） |
| C-8 | 補丁沒有動 `geometry-core/kernel/**`（K 不改的主張變成可檢查的事實） |

## 6. 補丁後會轉紅的既有測試（讀碼找到，需要先改）

這些測試用「互動提交」建雙軸相位差世界。補丁後那一步會被 M1 拒絕。處置：改成 §4.1 的舊檔路徑（`loadfile`），並把原本的斷言保留；這同時讓它們變成舊兩軸正例。

| 檔:行 | 內容 | 受影響的測試／案例 | 處置 |
|---|---|---|---|
| `tests/test_geo261_native_grid_product.py:16` `source()` 預設 `u="repeat 7 120 stagger 13"`、`v="repeat -11 80 stagger -7"`；`setup_binding`（`:41`）在 `:44` 以 `line` 提交 | `test_actual_host_keeps_role_sidecar_order_binding_bytes_and_undo_roundtrip`（`:67`，平移 `[560,731]`）、`test_parity_negative_control_changes_standalone_witness_and_actual_binding`（`:113`，`[560,731]`／變異 `[573,738]`，經 `binding_translation` `:49`） | 先提交 boundary 取指紋，再把 `dump` ＋ `source()` ＋ `grid-binding` 行寫成檔，`loadfile`。oracle 數字不變 |
| `tests/test_grid_inspector_contract.py:85`、`:88` | `test_six_rename_shapes_preserve_sources_segments_and_cancel_history` 的第 3 組（`repeat 0 600 stagger -400` ＋ `repeat-panel … stagger 200`）與第 6 組（兩軸參數相位差）用 `self.commit(infinite.infinite(identifier, …))` 建 | 這兩組改用 `loadfile` 建系統，其餘流程（boundary、binding、placement、grid、rename、undo／redo、跨進程載回）不動；rename 正是 §4.2 L7 的正例 |
| `geometry-web/grid_inspector_rename_test.js:41`、`:44`（`雙軸直接值`、`雙軸參數`；`546e2eb2`） | 瀏覽器版同樣的兩組。`fixture():23` 以 `apiRequest('line '+line)` 建，呼叫在 `:49–54` | 雙軸前置改走舊場景整體載入；`fixture():23` 與 `:49–54` 的呼叫要改到這條載入，更名、歷史、參數 400→401、完整專案保存與重開保留。P72B 維持 50。屬瀏覽器驗收，要在 WSL 排他時段處理 |
| 讀碼判斷不受影響，仍要實跑確認 | `tests/test_grid_inspector_command.js:10-24`、`tests/test_grid_inspector_stagger.cjs:80`（只組字串）；`geometry-web/grid_system_test.js:103`（草稿內加／移除 v 相位差，未存檔）；`geometry-web/grid_portable_browser_test.py:106` | 無需改；若實跑變紅再補 |
| 不受影響 | `tests/geo261_grid_store_harness.c:268` 與 `tests/test_geo261_native_grid_store.py`（K 層兩軸相位差，K 沒改）；`tests/test_geo261_staged_candidate_graph.py`（用未錯開的 `source(5,…)`） | — |

## 7. 突變（拿掉檢查要紅）

W 類突變照 `test_geo261_wood_grid_application.py::mutant(name, before, after)` 的寫法（改 `grid_application.c` 一個表達式，要求原文恰出現一次，重編物件並重連）；H 類突變登錄在 `tests/mutate.py`（`dict(id="M99", file=…, old=…, new=…)`），裁判是 `tests/test_geo314_stagger_commit.py` 的具名測試，登錄進 `tests/mutation_bridge.py` 的 `RESTORED` 清單。正式編號從 M99 起：MS1=M99、MS2=M100、MS3=M101、MS4=M102、MS5=M103、MS6=M104、MS7=M105、MS8=M106、MS9=M107、MP1=M108、MP2=M109、MP3=M110（`equivalent`）、MP4=M111。M89–M96 為 #299，M97–M98 為 #316。每個突變要證明：基線綠、突變紅（失敗訊息指得出病因）、還原後綠。

| ID | 檔 | before → after | 必紅的測試 | 備註 |
|---|---|---|---|---|
| MS1 | `current_geometry.c` | `if (!grid_stagger_commit_valid(candidate,grid_error,sizeof grid_error)) {` → `if (0) {` | 所有 P-C*「反例」、W 以外全部負例 | 拿掉整個檢查 |
| MS2 | `subgrid_world.inc` | `if(!g_subgrid_before\|\|g_parsing_scene_file)return true;` → `if(!g_subgrid_before)return true;` | L1–L4、L10、L11（舊檔打不開） | 拿掉「整體取代不檢查」 |
| MS3 | `grid_application.c` | `if(!old\|\|!(old->axis[0].stagger_set&&old->axis[1].stagger_set))` → `if(0)` | W01–W03、W16、P1-N*、P2-N*、P4-N1／N2、P5-N1／N2 | 拿掉 M1 |
| MS4 | `grid_application.c` | `if(wood_grid_stagger_value_changed(&old->axis[axis],&now->axis[axis]))` → `if(0)` | W06–W08、W13、W15、P5-N4、P6-N2、L8 | 拿掉 M2 |
| MS5 | `grid_application.c` | `if(prior->set&&current->set&&prior->parameter_id==current->parameter_id&&prior->field_id==current->field_id)return false;` → `if(0)return false;` | W11、P6-P1、P6-P2 | S7 的牙齒：卡改值被誤判成編輯 |
| MS6 | `grid_application.c` | `if(!(now->axis[0].stagger_set&&now->axis[1].stagger_set))continue;` → `if(!(now->axis[0].stagger_set\|\|now->axis[1].stagger_set))continue;` | W04、W09、P1-P1、P2-P1／P2 | 單軸也被當成「新增」而拒絕 |
| MS7 | `grid_application.c` | `for(int axis=0;axis<2;++axis)if(wood_grid_stagger_value_changed` → `for(int axis=0;axis<1;++axis)if(wood_grid_stagger_value_changed` | W07、L8 的 v 案例 | 只比 u 軸 |
| MS8 | `grid_application.c` | `return old->stagger!=now->stagger;` → `return 0;` | W13、W15（ref／直接來源互換） | 來源換了只看快取的那條 |
| MS9 | `grid_application.c` | `if(!after\|\|!before)return` → `if(0)return` | W17 | 缺基線 fail closed；預期 harness 以 NULL 觸發崩潰或錯誤標記，**崩潰不算殺死**（`case()` 要求精確標記） |
| MP1 | `transactions.inc:563` | `g_subgrid_before=call->before;` → `g_subgrid_before=NULL;` | P1-N*、P3-N*（新 id 與 archive 單行）；P2-N* 的預覽理由釘住（預覽無 violations，只剩 I8a 通用理由） | 專屬於漏斗 A：拿掉它，C1／C2／C3 紅，C4／C5 仍綠 |
| MP2 | `engineering_bridge.inc:158` | `g_subgrid_before=call->before;ok=world_revalidate(candidate);` → `g_subgrid_before=NULL;ok=world_revalidate(candidate);` | P4-N*、P5-N*、P6-N2 | 專屬於漏斗 B：C4／C5／C6 紅，C1／C2 仍綠 |
| MP3 | `current_geometry.c:6368` | `g_subgrid_before=&candidate->before;` → `g_subgrid_before=NULL;`（確認路徑） | **單獨不會紅**：預覽階段已拒絕，確認到不了。照 M56 的格式登錄為 `equivalent` 並寫證明；另做兩個組合觀察：(a) MP1 單獨：預期只有「理由釘住」那條斷言紅，「confirm 失敗」與「世界不變」仍綠，這證明確認路徑的重驗確實獨立擋住；(b) MP1＋MP3：P2-N* 的 confirm 成功、世界被改，必紅 | 縱深防禦的牙齒只能用組合證明 |
| MP4 | `transactions.inc` `reference_default_world` 行表 | 在內建場景加一行雙軸 `grid-system` | C-6 | 例外路徑的牙齒 |

表中的 `\|\|` 是 Markdown 對 `||` 的轉義，實際字串是 `||`。每個突變的證據格式照 PR #312 的表：突變、紅燈測試名、失敗訊息、還原後綠。

## 8. 執行建議（避開 WSL 負載）

1. 現在可以做、不需要 WSL 的：寫 §5 普查測試（純靜態）；在 Windows 上 `git apply --check`（已做）。
2. 需要編譯的（W harness、bridge）全部排到 WSL 空檔，由主迴圈排他執行；不要和瀏覽器驗收並行，否則測試時間偽紅。
3. 順序：`python tests/binaries.py build`（只重編 stale）→ §2 W harness → §5 → §3／§4 真 bridge → §7 突變 → `tests/run_all.py`（含 `mutation:check` 與新測試數）→ `python geometry-guide/sync_axiom_reader.py --check`（保險，不改條文所以應為 no-op）。
4. 帳本：實作 PR 落地後在 WSL 重跑 `python tests/mutate.py`／bridge 裁判刷新 `tests/mutants_results.json`（`DESIGN.md` §7.3）；再重產 `product-architecture-scan.json` 與收據。
5. 驗收「WSL 7 項」沿用 #312／#262 正文所列的同一份清單與收據格式；本稿不重述其內容。

## 9. 驗收清單（對照 issue #314）

- [ ] 每條提交路徑（C1–C9）各有正例與反例，失敗訊息含 `I24` 與 M1／M2 子字串（§3）。
- [ ] 題 3：P6-P5 放行（A 400→500，再把 u 解除為 500）、P6-N3 拒絕（解除為 450）。P1-N1 仍是互動新建雙軸的拒絕反例。
- [ ] 題 4 只寫在 `DESIGN.md`：將來開放刪除時，刪後重建依新建驗證。目前沒有 `delete-grid-system`，不為這條加既有路徑的測試。
- [ ] 附突變：MS1–MS9、MP1／MP2（與組合 MP3）、MP4，拿掉都紅，還原後綠（§7）。
- [ ] 舊兩軸 fixture 仍可開：L1–L5、L10–L12（§4）；建模交換包 L13／L14。
- [ ] 復原／重做不檢查：L6。
- [ ] 普查 C-1…C-8 綠（§5）。
- [ ] §6 所列既有測試已改且綠。
- [ ] WSL 7 項綠；帳本與盤點已刷新（`DESIGN.md` §7.3）。
