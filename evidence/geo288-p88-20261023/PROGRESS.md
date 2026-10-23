# P88 候選修正進度

目前尚未宣稱 #288 全綠。原固定 F13 三次完整 canvas 已確認間歇紅；單檔候選修正已推送及合入。新的公開 F 為 `3d681636902371ecc528b20f51eea33e272581c9`，三次完整 canvas 正在同一 F 依序執行，之後另需一次 grid。

| 項目 | 受驗來源 | 結果 |
| --- | --- | --- |
| 原完整 canvas 1 | `13d02c1db7022145a52ee063286a558e595eb212` | exit 1；P88=99；原 exact-focus predicate 逾時；1071.906 s |
| 原完整 canvas 2 | 同上 | exit 0；2267/0；P88=143、P73=69；golden matched；1754.826 s |
| 原完整 canvas 3 | 同上 | exit 0；2267/0；P88=143、P73=69；golden matched；1739.477 s |
| 診斷 fixed／withdrawn／restored | F13 + 明列記憶體 source variants | 原測試 exit 1／1／1；driver exit 2；proof=false；工具位移預條件未成立 |
| source 語法／diff 檢查 | 候選 P88 bytes `8106476b6eb2271111caa835a863b72eced4bab3b2ef77244f28534d83ca0a52` | `node --check geometry-web/grid_rule_lines_test.js` exit 0；`git diff --check` exit 0 |
| source 普通推送／remote 核對 | `8bce9239c014f070740455556c8ee1176c500af3` | exit 0／0 |
| 新 F 正式驗收 | `3d681636902371ecc528b20f51eea33e272581c9` | 三次完整 canvas 已啟動，結果待跑完；不得將候選診斷或原 F13 綠燈冒充此項 |

原失敗 assertion：

```text
UI condition timed out at === P88. 原生來源子線顯示、完整引用、兩面及正式重開 ===: document.activeElement===document.querySelector("#refGuideMode")
```

原失敗後 active element 為 `refGuideRatio`。原三輪沒有 pointerdown 目標追蹤，因此不能直接宣稱當次一定是滑鼠先點錯，而非點後重排／焦點轉移。三次結果完整保留，皆在原 35 分鐘內。第一輪 launcher 未將 `NODE_OPTIONS` 列入環境白名單；未設定 preload，但不能用事後 shell 狀態證明原 process 的環境。第二、三輪明確 `env -u NODE_OPTIONS -u PYTHONOPTIMIZE`。

候選只改 P88 的定位準備，使用原 helper 的 probe hook 等待版面與確認 hit target；沒有改產品、其他測試模組、原 check 行、golden、12 次嘗試上限或 CI 時限。準備與 exact-focus check 共用原 25 秒，新增的矩形觀測並非新增嘗試次數；沒有 DOM focus／click 或寫值。主代理已合入 immutable source commit，帳本與架構影響由主代理依規則統一處理。

真查詢診斷的守門沒有成立：查詢回傳後確實觀察到 `paintQuery`／`renderFaceInspector` 換節點、scroll `25 → 0 → 25`，但釋放後兩 frame 的舊點仍命中 `refGuideMode`，沒有後續目標 mouseDown。工具自己拋錯，不能稱為「拿掉修正，原斷言轉紅」；fixed／restored 也尚未走到該位置的穩定 probe。未再改工具、人工移位或重抽湊 0／1／0。原自然紅的精確觸發仍未證，最終判定依使用者對間歇案例要求的連續完整驗收。

原三輪完整 stdout／stderr／commands／environment／SHA 已由主代理推至整合分支 `evidence/geo261-final-13d02c1d/`。本子分支另附三階段診斷的完整原命令、收據、streams、trace、來源變體與工具快照之壓縮封存，`MANIFEST.json` 列每檔 bytes／SHA256，`ROUNDTRIP.json` 證實解壓後逐檔一致；僅排除 phase/tmp 的編譯執行檔、Chrome profile/cache 與 runtime scratch，沒有刪原機器檔案。

獨立對抗審查已核 source `8bce9239` 與候選 v5 全等，未見放寬斷言、golden、嘗試上限或時限；三個真查詢診斷階段未證成因果的限制也各有審查。主代理已在 F 上跑原帳本檢查及架構三條，全部 exit 0。三輪 canvas 使用已審 `98025b20…` 錄製器，獨立埠、暫存目錄與 profile，所有結果保留；不重跑未受影響項目。

摘要欄名更正：v1 摘錄使用不存在的 `response_json_unchanged` 而輸出 null；原三個 trace 的正確欄名為 `parsed_json_unchanged`，其值均 true。`ACTUAL_QUERY_OBSERVATIONS_v2.json` 使用正確欄名；v1 與原壓縮包保留，沒有改原 trace 或測試判定。此處只核對 parsed JSON，沒有宣稱 HTTP wire bytes 完全相同。
