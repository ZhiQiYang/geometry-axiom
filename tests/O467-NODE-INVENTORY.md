# O467 / O1 v3：Node 控制器與文字呈現盤點

基底 `48d5f3887e8cb8d222307db62dbdea287fda8442`。這12筆不加入168筆native ME。Node VM、受控clock與transport不能取代CDP／實體觸控。

| 功能 | 原有覆蓋 | 缺口與新增裁判 |
|---|---|---|
| #433 / R11 | `tests/canvas_touch_regression.py`與`tests/diagnostics/r433_touch_regression.py`已有registration/compatibility/new-touch/scroll的CDP撤回；`r433_touch_compatibility_test.cjs:158`有Node單例 | 舊Node相容性裁判對6個新控制器突變都存活。新6例把500ms、150ms、8/9px、pinch、drain、stale操作直接拆開，時間由受控clock推進，無sleep。 |
| #443 / PF4A可讀表 | `test_panel_fill_grid_ui.js:91`原PF4_NATIVE_IMPACT已有精確大整數、零值、原始資料與唯讀檢查；CDP P1284另量可讀欄寬 | exact、zero原裁判已能殺；未逸出文字在原13例存活。新惡意字串透過真renderer，須是文字且輸入不變。 |
| #438/#445 host | `framing_template_host_mutation_check.py:23`原3撤回只跑選中方法 | 新入口跑完整22例且零skip。cancel撤回原先混有FT_H13/FT_H21未處理拒絕，分類blocked；在既有兩例加doesNotReject語意斷言，保留所有原assert，才形成純assertion kill。 |

## 突變

| ID | 基底目標行 | 具名斷言 | 全檔例數 | 實際錯誤 |
|---|---|---|---|---|
| O467_PF4A_HTML_AS_MARKUP | `geometry-web/panel-fill-workspace.js:194` | `O467_PF4A_TEXT_NOT_MARKUP` | 13 | Native display text is injected as markup instead of escaped cell content. |
| O467_PF4A_ROUND_EXACT | `geometry-web/panel-fill-workspace.js:170` | `O467_PF4A_EXACT_DECIMAL` | 13 | Coerce a signed exact native decimal string through lossy Number. |
| O467_PF4A_ZERO_IS_MISSING | `geometry-web/panel-fill-workspace.js:164` | `O467_PF4A_ZERO_IS_VALUE` | 13 | Zero identity/value is shown as absent. |
| O467_R11_DRAIN_REPLAY | `geometry-web/touch-gestures.js:143` | `O467_R11_MULTI_DRAIN_NO_SINGLE` | 6 | Remaining touch is wrongly replayed as a single tool gesture. |
| O467_R11_HOLD_EARLY | `geometry-web/touch-gestures.js:6` | `O467_R11_HOLD_500MS` | 6 | A long press opens too early. |
| O467_R11_MOVE_THRESHOLD | `geometry-web/touch-gestures.js:6` | `O467_R11_MOVE_CANCELS_HOLD` | 6 | Movement that should begin a tool still opens a menu. |
| O467_R11_MULTI_RATIO | `geometry-web/touch-gestures.js:133` | `O467_R11_MULTI_CAMERA` | 6 | Pinch ratio is inverted while midpoint math still executes. |
| O467_R11_RING_EARLY | `geometry-web/touch-gestures.js:6` | `O467_R11_RING_150MS` | 6 | Press-ring feedback begins before its adopted boundary. |
| O467_R11_STALE_SINGLE | `geometry-web/touch-gestures.js:43` | `O467_R11_STALE_SINGLE_CANCELLED` | 6 | An ownership change fails to retire the in-flight single tool operation. |
| R03A_HOST_COLD_OPEN_SEARCH | `geometry-web/framing-template-session.js:20` | `R03A_HOST_COLD_OPEN_NO_SEARCH` | 22 | Preserve the existing dedicated host withdrawal; run the complete shared session file with zero skip. |
| R03_HOST_CANCEL_WRITES | `geometry-web/framing-template-session.js:77` | `FT_H10_CANCEL_NO_WRITE` | 22 | Preserve the existing dedicated host withdrawal; run the complete shared session file with zero skip. |
| R03_HOST_COLD_OPEN_SEARCH | `geometry-web/framing-template-session.js:20` | `FT_H11_COLD_OPEN_NO_SEARCH` | 22 | Preserve the existing dedicated host withdrawal; run the complete shared session file with zero skip. |

`node_mutation_fragments.py`經`diagnostics/o467_node_reporter.cjs`讀Node真正的逐案事件。
每片定義釘完整case名稱順序與失敗case→具名error.message首行的精確對照；逐案ordinal必須1到N且不重複，summary、exit與逐案實況須相等，零skip/cancel/todo。
所有失敗都必須是實際error record的AssertionError／ERR_ASSERTION／testCodeFailure，且每個真正message首行都精確符合定義；指定primary marker亦須在真正首行開頭。
stack、expected、actual、訊息後方的比較diff、另一例名稱、全域log或深層偽造code都不能借用；額外／漏失敗、重複ordinal、任意非零exit、TypeError或timeout不能算killed。
補上的R11及host連帶斷言只有具名message變更，判式與預期值不變；完整失敗集合在12份JSON，並非只要其中一例有指定marker就放行。
重算：`python -B tests/node_mutation_fragments.py --out /tmp/o467-node-new`。
這不涵蓋觸控裝置噪訊、OS相容性事件、真命中、focus／sheet排版；那些仍沿原CDP與L5驗收。
