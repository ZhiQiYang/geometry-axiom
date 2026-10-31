# R8 三個跨版本 stdout 差異：唯讀根因紀錄

結論：三差由同一個已存在的 I22 診斷缺口修正引入，沒有發現 H 初始化修正造成的判定倒退。固定舊 base 的訊息本來就沒有履行其自身 I22 對定位邊／超出區間的要求。**原跨版本 exact 仍是 exit 1；目前沒有同時保留已批准語意、既定正反例與原 base bytes 的產品修法。** 本次不改產品、測試、golden、比較器、公理或決策佇列，不重跑 R8。

| 身分 | 完整 SHA |
|---|---|
| R8 fix／F8 | `75a1e93811a52b69385cbdaf6a09d773ed9052ad` |
| 原 comparator 的固定 base | `b74f9a2ae7ade1555b9be45283adecc097fb76e3` |
| 引入三差的提交 | `6366304eb787b2a50282e4132f45e51eb7d21290` |
| 引入提交的直接 parent | `4b665fae21ab63aaffb7d84f6a32d5a469ba1675` |

「期待」下文專指原 comparator 使用的固定 base 實測 bytes，並非宣稱它符合現行或當時 SSOT。

## 精確失敗與完整原件

原 `/tmp/g337323R8/tools-frozen/verify_linux.py:156`：`assert not failures,failures`。`equivalence.json` 的 failures 精確為三個 `[scene,"stdout"]`；原 compare/outer exit 1 不變。比較器先對 stdout、完整有序來源圖、五個 guard counts 做逐場景比較，再在末尾 assert。它不把 base/fix stderr 列入這三個比較欄位；stderr 的相同三組新增診斷也在本包完整保存。

每組命令都是 `loadfile /tmp/geo323-final-r8-source-20261024/<scene>\ndump\n`。下列呈現完整第一行 JSON；**完整兩行 stdout（含 dump）、完整 stderr、六份完整 graph 壓縮原件、原命令／exit／hash** 分別位於 `raw/<scene>/{base,fix}/` 和 `FACTS.json`。沒有截短或覆寫原件。

### 1. `_role_priority_mutant.scene`

原 base 期待：

```json
{"ok":false,"error":"line 8: V_EXTENSION：非 boundary 角材（1）的 footprint 超出定位邊範圍","status":"INVALID","code":"SCENE_INVALID"}
```

F8 實際：

```json
{"ok":false,"error":"line 8: V_EXTENSION：非 boundary 角材（1）的 footprint 超出定位邊範圍——定位邊 e2 [2000,4000] mm，低端超出 [0,2000] mm","status":"INVALID","code":"SCENE_INVALID"}
```

完整 stdout 1092→1152 bytes；SHA256 `f2a7fb6c0e175bdb5f4e4cc3e1e04925ef70026a53f130331b4cf11a158ba0e7` → `61823d285e3335511d34714e2d08dd8869e995c336fc75144942107ee01ca0f9`。新增的資訊是料件1定位邊 e2、邊區間[2000,4000]、低端超出[0,2000]。仍為同一行8的 `SCENE_INVALID` 拒絕，第二行 dump bytes 不變。

### 2. `_s1_p8_l_room_primary_through_reflex_extension.scene`

原 base 期待：

```json
{"ok":false,"error":"line 15: V_EXTENSION：非 boundary 角材（3）的 footprint 超出定位邊範圍","status":"INVALID","code":"SCENE_INVALID"}
```

F8 實際：

```json
{"ok":false,"error":"line 15: V_EXTENSION：非 boundary 角材（3）的 footprint 超出定位邊範圍——定位邊 e3 [3000,4800] mm，低端超出 [27,3000] mm","status":"INVALID","code":"SCENE_INVALID"}
```

完整 stdout 1093→1154 bytes；SHA256 `1588124a410c2920e9eccbe938754341c6a434c80d3b8649501aad1d382e8e3f` → `ce2c3f1d6e4e02576cd8f66a64a938b984fc237e215ad62b2f485a024f19a581`。新增 e3、[3000,4800] 與低端[27,3000]；沒有憑空加高端。仍為同一行15拒絕，第二行 dump bytes 不變。

### 3. `_s1_p8b_l_room_primary_through_reflex_extension_hi.scene`

原 base 期待：

```json
{"ok":false,"error":"line 12: V_EXTENSION：非 boundary 角材（3）的 footprint 超出定位邊範圍","status":"INVALID","code":"SCENE_INVALID"}
```

F8 實際：

```json
{"ok":false,"error":"line 12: V_EXTENSION：非 boundary 角材（3）的 footprint 超出定位邊範圍——定位邊 e1 [0,1800] mm，高端超出 [1800,4773] mm","status":"INVALID","code":"SCENE_INVALID"}
```

完整 stdout 1093→1153 bytes；SHA256 `3e907bbee2d6e639137c9f56deb53bb541ce6ac3514818e711ef2356189e57e4` → `330b619f44194bb25f283b14b4398d43bcf38934ff24bfebc29b6365ff43635c`。新增 e1、[0,1800] 與高端[1800,4773]；沒有憑空加低端。仍為同一行12拒絕，第二行 dump bytes 不變。

三組 base/fix 原程序與 trace 均 exit 0；這是程序狀態，**不等於場景接受或 compare通過**。三組各自的 base/fix 完整圖 hash 都相同（原圖64845 bytes）；guard counts 逐組相等。這些事實限於已跑的原件，不宣稱 compare assert 後尚未到的 audit 已通過。

## 引入提交與既有批准規格

1. `git log -S '——定位邊 e%d' F8 -- geometry-templates/woodworking/native/contacts.c` 只有提交 `6366304e…`。其直接 parent 為 `4b665fae…`，且它是 F8 的祖先。`INTRODUCING_COMMIT.patch` 保存該診斷相關五檔的完整選定範圍 `git show` diff：`geometry-templates/woodworking/native/contacts.c`、`contacts.h`、`contact_world.c`，以及 `tests/run_tests.py`、`tests/geo261_contacts_harness.c`。它不代表該提交全部檔案的 diff；此處歸因以 Git 內容與祖先關係為據，不是推測或僅憑 PR 標題。
2. 該提交在 `wood_member_span_extension_check` 增加 `edge_index` 參數與兩段帶端點的診斷；`has_edge && role != boundary && (span_lo < edge_lo || span_hi > edge_hi)` 拒絕條件不變。直接 parent 與固定 base 都沒有該後綴；當前 F8 保留它。呼叫端傳遞定位邊編號，以及低／高／雙側與錯側排除測試，均在該提交同一份 diff。
3. **舊 base 的 I22（1339–1353行）和 F8 的 I22（1346–1360行）整條逐字相同。** 共同末句是「違反本條 → 拒絕（V_EXTENSION），訊息指名料件、定位邊與超出的區間。」本包保存兩份完整 Git SSOT 原件與抽取範圍。該要求早在 `1ee76768b1a8123d04083eac4710603f43aaeb84` 已入層；查詢原流在 `SSOT_DIAGNOSTIC_HISTORY.txt`。
4. 2026-10-23 已核可的 #318 閱讀 A 明寫「明確不改：I22」，2026-10-24 RC 面量法也沒有授權刪除 I22 診斷。`FIELD-RULES.md` 本身明示不是公理層，不可據現場引文越過這個契約。
5. 現行 `tests/run_tests.py:249–265` 明確驗 P8 的定位邊、低／高超出區間與錯側不存在；`tests/geo261_contacts_harness.c` 另釘完整低／高／雙側文字。撤掉資訊會破壞既定測試與 SSOT。把資訊只搬到不可供 bridge/UI 消費的通道，或按測試身分選擇舊字串，也不能作為合法修正。

## 可執行界線與未驗項

沒有修改 F8 或比較器，也沒有新編譯、產品回歸、突變、效能樣本。此次只有對原件的唯讀重算與 Git provenance，**不是新產品修正或新驗收綠燈**。保留原 exact 紅，其他 F8 帳本與驗收可繼續。具體待決選項及各自需要重跑的範圍見 `QUESTIONS.md`；目前維持 A 的原紅狀態，沒有採用 B′ 或具名差異等新比較政策。

本次收件指令：`python3 -B /tmp/geo337-r8-exact-three-triage-20261025/collect.py`，exit0；每個 Git 讀取完整 stdout／stderr／exit／環境在 `git-originals/`。`FACTS.json` SHA256：`bbb66b1f5f19ede946a10ce40987569cda71c75578e597e7557fd5d0b5b00849`。
