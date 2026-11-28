# O467 / O1 v3：browser 定義與待跑範圍

基底 `48d5f3887e8cb8d222307db62dbdea287fda8442`。19個片段的source bytes/SHA、唯一anchor與JS syntax可在本機驗。
本輪沒有執行Chromium；以下沒有任何browser killed或L4宣稱。未改任何golden、段計數或byte pin。
原13個R16定義取自`tests/diagnostics/r16_height_mutations.py:63`，仍是P1231完整矩陣；追加3個高度錯誤。
#448新增固定高度／控件專道與既有R11、R03等合流，不推論每個排版宣告已有獨立突變。

| ID | 基底目標行 | 原裁判 | 類型 |
|---|---|---|---|
| O467_PF4A_LABEL_COLUMN_95 | `geometry-web/panel-fill-workspace.css:25` | P1284 / `PF4A_DISPLAY_390_1400` | 既有完整段計畫，待真Chromium |
| O467_R03_PREVIEW_LENGTH_FROM_A | `geometry-web/framing-template-workspace.js:37` | P2052 / `PREVIEW_TABLE` | 既有完整段計畫，待真Chromium |
| O467_R03_SOURCE_PRESELECTED | `geometry-web/framing-template-workspace.js:8` | P2052 / `SOURCES_BLANK` | 既有完整段計畫，待真Chromium |
| O467_R16_NORMAL_200PX | `geometry-web/workspace-height.css:21` | P1231 / `R123H_HEIGHT` | 原P1231 runner可執行，待真Chromium |
| O467_R16_RESIZE_FREEZES_HEIGHT | `geometry-web/workspace-height.js:75` | P1231 / `R123H_HEIGHT` | 原P1231 runner可執行，待真Chromium |
| O467_R16_SPACE_QUARTER_HEIGHT | `geometry-web/workspace-height.css:193` | P1231 / `R123H_HEIGHT` | 原P1231 runner可執行，待真Chromium |
| R123H_DOCK_BACK_OVER_CANVAS | `geometry-web/workspace-height.css:76` | P1231 / `R123H_UNOBSCURED` | 原P1231 runner可執行，待真Chromium |
| R123H_MOBILE_AT_768 | `geometry-web/workspace-height.css:9` | P1231 / `R123H_HEIGHT` | 原P1231 runner可執行，待真Chromium |
| R123H_RESTORE_GRID_340PX | `geometry-web/workspace-height-dialogs.css:32` | P1231 / `R123H_HEIGHT` | 原P1231 runner可執行，待真Chromium |
| R123H_RESTORE_SIDEBAR_DOCK_OCCLUSION | `geometry-web/workspace-height.css:59` | P1231 / `R123H_ENTRY_CONTROL_REACH` | 原P1231 runner可執行，待真Chromium |
| R123H_RESTORE_STATUSBAR_BREAKPOINT_GAP | `geometry-web/workspace-height.css:25` | P1231 / `R123H_STATUSBAR_CONTAINS_COMMAND` | 原P1231 runner可執行，待真Chromium |
| R123H_VISUAL_VIEWPORT_DENOMINATOR | `geometry-web/workspace-height.js:55` | P1231 / `R123H_DENOMINATOR` | 原P1231 runner可執行，待真Chromium |
| R123H_WITHDRAW_320_LESSON_CLIP | `geometry-web/workspace-height.css:448` | P1231 / `R123H_320_LESSON_CLIP` | 原P1231 runner可執行，待真Chromium |
| R123H_WITHDRAW_DOCK_WHEEL_OWNER | `geometry-web/workspace-height.js:19` | P1231 / `R123H_DOCK_SCROLL` | 原P1231 runner可執行，待真Chromium |
| R123H_WITHDRAW_FACE_GUIDANCE_INTRINSIC_WIDTH | `geometry-web/workspace-height.css:253` | P1231 / `R123H_CONTROLS` | 原P1231 runner可執行，待真Chromium |
| R123H_WITHDRAW_FACE_TOOL_END_GUTTER | `geometry-web/workspace-height.css:246` | P1231 / `R123H_CONTROLS` | 原P1231 runner可執行，待真Chromium |
| R123H_WITHDRAW_LENGTH_PAINT | `geometry-web/workspace-height.css:182` | P1231 / `R123H_LENGTH_DISPLAY` | 原P1231 runner可執行，待真Chromium |
| R123H_WITHDRAW_MODEL_HEIGHT | `geometry-web/workspace-height-dialogs.css:91` | P1231 / `R123H_HEIGHT` | 原P1231 runner可執行，待真Chromium |
| R123H_WITHDRAW_THREE_VIEW_SCROLL_CLEARANCE | `geometry-web/workspace-height.css:236` | P1231 / `R123H_CONTROLS` | 原P1231 runner可執行，待真Chromium |

## 執行界線

預檢：`python -B tests/diagnostics/o467_browser_mutations.py --preflight`。

R16完整0/1/0：在提交T+P且乾淨的測試分支，用原CI編好的bridge/model-base：
`python -B tests/diagnostics/o467_browser_mutations.py --repo . --bridge <bridge> --model-base <model-base> --output-dir <repo外新目錄>`。
沿原runner的900秒上限、原P1231完整結果、原具名失敗、exact restore、進程清理；本片不修改workflow。

另3片沒有generic per-case結果契約，故只交精確來源替換與原完整段裁判計畫：
- PF4A：`GEOMETRY_PANEL_FILL_ONLY=1`，原P1284之`PF4A_DISPLAY_390_1400`可讀性／命中斷言，完整同scope golden不變。
- R03兩片：`GEOMETRY_FRAMING_JIG_ONLY=1`，原P2052完整28項，分別須紅在`PREVIEW_TABLE`與`SOURCES_BLANK`。

套用端須在隔離且確定來源的server/profile做原baseline→一個source替換→還原原bytes，三輪使用同一未改的原scope。保存原stdout/stderr、畫面、完整計數、失敗具名、清理結果及三輪0/1/0；進場錯誤不算kill。若原計畫未命中，回報survived並補裁判，不能改golden消除差異。
沒有新增canvas段、沒有成本手填，也不把3個計畫當成已自動接入原browser receipt格式。
