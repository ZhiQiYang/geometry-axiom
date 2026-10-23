# P88 真查詢診斷後兩 phase 補核

本補核只延伸 fixed 原審查，保留所有原判定。整輪原 driver 在 2026-10-23 11:06:13.901219 UTC 自然結束，退出碼 2、proof=false。fixed／withdrawn／restored 都未重現工具要求的錯目標位移，沒有成立 0/1/0。

| phase | outer／workflow／Node | 秒數 | P88 已通過／失敗斷言 | 原結果 |
| --- | --- | ---: | --- | --- |
| withdrawn（原 P88 bytes） | 1／1／1 | 216.247828908 | 99／0 | 位移工具前提失敗 |
| restored（v5 bytes 8106476b） | 1／1／1 | 223.698612802 | 99／0 | 位移工具前提失敗 |

兩份原 footer 均 completed=false、golden 未比對、未超 CI，fatal 為 `P88 original query schedule did not reproduce the original wrong-target displacement; this is not valid counterevidence`。這不是原 `document.activeElement===document.querySelector("#refGuideMode")` 斷言的紅燈，不能據此判產品或候選有缺陷。

兩 phase 都確實走到原 grid-rule-lines.js 的 query-return → paintQuery/query → renderer，node 5696 換成 5737，parentScroll 短暫 25→0→25；原中心點 (293.75,602.5) 最後仍命中 mode。withdrawn 的量測／renderer-return／scroll 恢復／工具終點序號為 7523／7529／7533／7534；restored 為 7525／7531／7535／7536。工具在初始量測的注入點就因位移前提不符而終止，未走到之後真正 mousedown，也沒有在該點驗證 v5 barrier。

原來源前後仍為 F13 `13d02c1db7022145a52ee063286a558e595eb212`、乾淨且不改 source；withdrawn 執行原 P88 hash c4725960，restored 執行候選 8106476b，helper bytes 相同。原 stdout bytes/hash 與原 receipt inventory 相符，trace stopped=true、兩層 errors 空。未重新 hash 約 55MB trace，保留原收據的 trace hash 與此限制。

`parsed_json_unchanged=true` 只證 parsed JSON 原樣回傳，不能寫成 HTTP wirebytes 相同。owner 摘要舊欄名 `response_json_unchanged=null` 已回報補正；原 trace 不改。

本案仍欠自然錯焦點單一因果及有效的撤回／恢復反證。這三次 P88-only 診斷不是正式 canvas/grid；新 F 的三次完整 canvas 與原 grid 應獨立列示，不能繼承本診斷為綠。
