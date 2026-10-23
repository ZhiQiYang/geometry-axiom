受驗來源 `3d681636902371ecc528b20f51eea33e272581c9`；補充回應 handoff `acd1289228d490c68a139cf17e02fdc1f3cb247c` 所錄 2026-10-23T12:35:32Z、head `ee28481` 審查。這份分析不改原三階段排程、原工具、測試或判決。建立時 fixed／withdrawn 已終態，restored 尚在執行。

本次已證明一個測試使用過期座標的具體機制；目前尚未裁定是否另有使用者可見的產品位移。兩者不能由同一個 DOM 量測直接互相推論。

| 原事件 | 真實觀測 |
| --- | --- |
| 釋放既有查詢前 | parent scroll=25；模式欄 rect y=580.5、中心 y=602.5 |
| 原 query 成功後呼叫原 renderer | 節點重建；原 renderer 登錄既有 scroll-restore rAF |
| 真 native rAF 入口、原 callback 執行前 | 原量測僅求值一次，模式欄 rect y=605.5、中心 y=627.5，hit=refGuideMode |
| 原 callback 完成 | 同一新節點、parent scroll=25、rect y=580.5；舊點 y=627.5 現在命中比例列 label |
| 保留修正 | 重新觀測後唯一 mousePressed 使用 y=602.5，trusted mousedown 命中 refGuideMode；原 P88=143、exit 0 |
| 撤回修正 | 唯一 mousePressed 原樣使用 y=627.5，trusted mousedown 命中比例列；焦點為 refGuideRatio，原精確焦點 predicate 逾時，exit 1 |

`grid-rule-lines.js:102-106` 在既有 `source-inspect` 回應後驗所有權，再以成功路徑呼叫 `paintQuery()`；`:80-84` 由此重畫 inspector。`app.js:615` 起的 `apiRequest` 使用原 `fetch`／JSON 回應。本次工具把既有查詢回傳物件原樣釋放，沒有改資料或直接修改 scroll。

`app.js:8753-8763` 的原註解明載：details toggle 會在下一影格前完成，同步恢復 scroll 可能被中途較短的表單截短。因此產品原本就在 renderer 尾端登錄 rAF，並保留 seq、bid、parent scroll、pane scroll 四項 guard。此次原 callback 確實經 native rAF 執行一次，沒有手動另呼叫或繞過 guard。工具在該 native callback 入口前執行原唯讀量測；這定位了 DOM 的中間態，並沒有測到像素畫面。

目前沒有 Paint、compositor frame 或 screencast 紀錄，因此不能證明中間 y=627.5 是否曾呈現在先前的一個畫面，也不能證明所有真人輸入交錯都安全。`requestAnimationFrame` 這個名稱及回呼時點，不能單獨補足這份畫面證據。原自然 1/0/0 的失敗亦沒有 pointerdown trace，故不能把本次受控 query 指認為那次歷史失敗的唯一來源。

v5 每次 focusedCtl 的新增 settle、矩形觀測與目標命中檢查都在唯一一次真實 mousePressed 之前；沒有在一次錯誤點擊後再次點擊來救回結果。原 12 次上限指輸入前的可用性／穩定性嘗試，原精確焦點 predicate、25 秒共同時限與 golden 均保留。

本分析可支持「原 helper 在此同一真 renderer/rAF 序列使用 stale coordinate，修正先重新量測而通過」；它不把「產品對真人沒有版面問題」列為已驗證。若後續畫面／真輸入觀測證明產品在可見互動期間有錯誤位移，應另修產品，固定新 F，更新帳本／架構影響判定並重跑受影響項目。現有原始紅燈與這次工具結果都必須保留。
