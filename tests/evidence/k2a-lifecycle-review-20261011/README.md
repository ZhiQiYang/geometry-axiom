# K2a-A：永久缺失與容量審查收據

本目錄追加 PR #201 審查收尾；保留先前 `k2a-20261011/`、`k2a-review-20261011/` 全部證據。審查 M1/M2/M3 分別是 lost 純移除、生命週期容量與原生三態，不是提案的 M01/M02/M03。

對應意見：6110957129、6111166078、6111290072；容量例外授權：使用者批准已展示的五行補丁，以及 6111339026（P-055 延伸）。SSOT D57/I68/R54 只准改指不同物件；PROPOSAL 曾容許 pure removal 的字句與 SSOT 不一致，本實作採 SSOT，沒有修改規格或公理檔。

## 修改前後

* lost 引用純移除：writer 逐一匹配不同的新物件身分，無替換即原子拒絕；同參數卡換欄位也拒。選空來源在 ParameterUI target handler 前攔截，raw、lost 及歷史均保留。`capacity-before.log`、`native-parameter-target-listener-failure.log` 保存真紅；指定 writer 與 UI 突變均命中 assertion，還原綠。
* 容量：預留每引用 `,"lost":true` 的 12 bytes、orphan IDs/分隔符、single→collection 外殼、附件及完整 manifest 的增量。分別驗 128 KiB、1 MiB value/record、8 MiB manifest；record 測試先證明 value 可接受，避免 value guard 掩蓋 record guard。`approved-project-store.diff` 正是額外授權的 5 行。接納不足容量的草稿在原生呼叫、dirty 與 undo 前拒絕。健康單份集合的容量推演保留 collection 格式，禁止產生負預留抵銷其他附件；projection-before.log 是指定突變的真紅。
* 原生：刪除→Undo→Redo 同時核 World、lost/orphan、raw、dirty；Undo 後 objects/render 掃描不再補標，舊 preview token 不能恢復 World。lost 草稿的既有預覽按鈕在發送原生 preview 前拒絕；有效態原生 preview 與 owner confirmation preparation 通過。Redo 狀態真 ZIP 重開保留。
* 邊界 ZIP：20 個合法 grid-binding 引用（I37 容量 32），刪除後草稿恰為 128 KiB、20 lost、1 orphan；真 ZIP 在另一原生 session 冷開，raw、旗標、完整 dump 相同。初次 grid-system 夾具超過 I37 的 16 上限、required-preview 與冷開自動 layout 的失敗均保存，沒有改 byte oracle；在保存前透過正常 UI 排版建立 canvas positions。

## 驗證與身分

乾淨受測 head：`78727a1f9a223285394e6b563d24f856934659cc`；1719 個產品／裁判來源，完整閉包 SHA-256：`6c266f2c4efc6c6b6df05f804c1ec4eb8d0379d72d7f3a816d5be5f97d429bea`。完整 CDP 在 `ce2a28ab26de6efc6d21aa8b1589a7fd0b96c420` 為 84 段、2207 pass、0 fail、0 skip，golden 未改。最終 head 沒有重跑完整 CDP；其後僅容量 helper 一行及測試／driver／expected 三檔改動，inventory.cdp.final_source_delta 保留四檔前後 SHA。P38 刻意注入一次例外以驗回報。五個正式登記 gates：drafts 27、native 42、source 14、ZIP 25、rule 35，共 143 個真 Chromium assertions。native gate 的正式原始紀錄採生命週期突變基準綠（同一完整 gate，不另灌入計數）。before/after head、tree、status、source hashes、runtime/session、bridge path/PID/hash 均逐項一致；stack 為 16 MiB。`/proc/PID/exe` 在 sandbox 不可讀，收據明示 cmdline/launcher 檔案核對的限制。

完整非瀏覽器 83 suites：2641 pass、0 fail、1 具名允許 GDI skip，Node 676/676；expected 由完整 `--build --update-expected` 自動更新。本輪完整非瀏覽器已含最終 helper 修正；五個 browser gates 在最終乾淨受測 head 重跑，完整 CDP 的原 head 與差異如上明列。瀏覽器不計入非瀏覽器 aggregate。

本輪重跑 39 個指定突變：20 JS、8 Chromium、3 格式、6 生命週期 JS、2 生命週期 Chromium。每個 baseline/build/red/restored 都保留；單一指定 test/assertion 的紅才計 kill，setup 錯誤及非 assertion 的早期突變嘗試不計。原有 2 個原生刪除回執突變沿用 `../k2a-review-20261011/native-receipt/`：其 producer 與 judge 未變，未稱本輪重跑；合計 41 個反例。`results.json`、raw logs、inventory 的來源/裁判與 stored/raw SHA 可重算，`.gz` 解壓是逐字原始收據或 mutant JS。

`current_geometry.c` 未改：**mutate 無新覆蓋**。原 48 筆 ledger 僅 `--check`：40 killed、1 crashed（M20）、4 equivalent、3 retired、0 stale；不是新跑 48 變異，未手改 ledger。

## 驗收範圍

| 提案驗收 | 本線結果 | 原因與證據 |
|---|---|---|
| M01 | 過 | 兩份並存、無取代對話框；drafts browser 與指定反例 |
| M02 | 過 | 真 ZIP、不同原生 session 冷開、raw 逐字與 collection capability |
| M03 | 過 | 原 draftId 續開；新 ID 突變 |
| M04 | 過 | 真原生 confirm 只清本份，Undo 還原；native/ZIP |
| M05 | 過 | 舊 pin 拒預覽、明選現況重取；source/owner |
| M06 | 過 | 原生删除回執、Undo/Redo、objects scan、World/raw/dirty 同步 |
| M07 | 過 | 非孤兒同目標整份拒、duplicate-target 突變 |
| M08 | 過 | 第 17 份拒、不截斷 |
| M09 | 過 | inputRefs 指草稿拒 |
| M10 | 過 | 單份、orphan/lost 集合分派；邊界 single→collection 真 ZIP |
| M11 | 過 | 降版/剝能力/schema/orphans/lost 位置與值負例，容量預留負例 |
| M12 | 過 | 舊 flush/舊 API/同 key 清 lost/純移除均拒；實際 UI 空來源拒 |
| M13 | 過 | 真 1280/390、44px targets、無水平溢出 |
| M14 | 過 | 同 ID 同內容新物件不讓 orphan/lost 復活 |
| M14b | 過 | lost 真 ZIP、同 ID 重取拒、不同 ID 檢閱；三態與邊界重開 |
| M15 | 過 | 基底只做兩方比較，取消不變；規則修改/刪除及合法同值/非法原文 |

以上「過」限 Linux、本線真 Native/Chromium/ZIP；正式 exact-head WSL 7/7、雲端 CI、OS 檔案選擇器、K1 真合併樹及正式 app 共存、其他具名 browser owners **未驗**。K1 pinned validator 的契約組合測試不能冒充真合併樹。CI 受帳號計費阻擋,正式合併裁判由本機 WSL 收據提供。

GEO-219：**無新入口**。base 為 axiom/adopt-drafts-topology-k2a-20261011；K2a-B 疊在本分支。#199 尚未合併，已讀澄清 diff，合併後須用 merge commit 納入。本輪依看板只處理 #201，K2a-B/PF 暫停；PR 保持 draft，不合併、不 force push、不關 PR/issue。
