# G07 根因追蹤：既有上游 guide resolved 修正的瀏覽器撤回證據

**分類為產品缺陷，已由上游 `1987af507c6f387d7986325da6c29b2ec6246944` 修復。** 在同一個 e9＋診斷基底，只撤回該提交恢復 guide resolved 旗標的七行，原 G07 再次轉紅；保存格式一直是 `/8`，失敗是未完成草稿仍保留 `guideId=1`，而測例已用真鍵盤選取「請選擇」。本次只增加診斷與證據，不另做重複產品修正，不改原 G07 斷言或格式預期。

這是 [已發布 e9 診斷報告](https://github.com/ZhiQiYang/geometry-axiom/blob/fb6dff89ed41a77ef79401b55b408d268d043e2c/evidence/geo261-codex-fix-assembly-g07-20261018/README.md) 的後續證據；保留前份報告當時「未重現、待定位」的歷史原件。本資料夾使用新的 evidence 前綴，不覆寫舊報告。正控 source 是 `89c269bf68724f9a8b003ac792875f96414d9c3d`；既有報告 commit `fb6dff89...` 另含證據檔，不冒充受測 SHA。

## 真實執行順序與結果

下表依 UTC 真順序排列。先跑含修正的 e9 正控，再回 e64 重現，最後回同一 e9 基底只撤回上游七行。**沒有第四輪恢復後的 browser 執行。**

| UTC 起迄（2026-10-18） | 受測 SHA／內容 | 原退出與斷言 | 建置／harness／整個 job 秒數 |
|---|---|---|---|
| 14:35:38–14:40:15 | `89c269bf68724f9a8b003ac792875f96414d9c3d`；e9＋同一診斷 | exit 0；150 通過、0 失敗；completed=true；P77=134、P82=16 | 75.660／197.752／277.583 |
| 14:54:45–14:59:22 | `082baff4e2cb07dbb6ca1e91ca0d8242a20213b1`；e64＋同一診斷 | exit 1；115 通過、1 失敗；completed=false；P77 G07 | 79.201／192.315／276.072 |
| 15:00:23–15:04:06 | `2585fa9aef20366086dc3334012d70e204e2a669`；89 正控只撤上游七行 | exit 1；115 通過、1 失敗；completed=false；同 P77 G07 | 68.611／149.530／222.278 |

三輪都沒有逾原 CI 15 分鐘上限，skipped=[]。兩輪失敗在 G07 即 fatal，後續 P77／P82 沒有執行；skipped=[] 不能當後續已覆蓋。150／115 是斷言數，不是端到端情境數。

各輪原件：[正控 result](e9-positive/assembly/result.json)／[原 log](e9-positive/assembly/test.log)、[e64 result](e64-reproduced/assembly/result.json)／[原 log](e64-reproduced/assembly/test.log)、[撤回 result](e9-withdraw-upstream/assembly/result.json)／[原 log](e9-withdraw-upstream/assembly/test.log)。每輪 result 保留實際 `npm run build`、start_local、runtime probe 與 `node geometry-web/cdp_test.js` 命令、環境、起迄、退出碼與清理記錄。scope 固定 `GEOMETRY_ASSEMBLY_ONLY=1`，CDP 9367、私有服務 18839。

## 原 ZIP 已排除格式預期過時

用 Python 標準函式庫唯讀解析原 ZIP，不呼叫產品 pack/unpack、不重打包。三包都只有 `manifest.json`／`world.scene`，entry 名稱唯一、CRC 可讀，sources=[]，sceneHash 等於原 scene bytes 的 SHA-256。三份 scene **逐 byte 完全相同**：3,740 bytes，`c153068b840159f9b3af64c1c581b822da780dc83ad7e6e6ddffdcdeef5d8d27`。

| 原件 | 真 format | 第一個 instance draft member guideId | `.gcanvas` SHA-256（皆 5,200 bytes） |
|---|---|---:|---|
| [e9 正控](e9-positive/assembly/artifacts/geometry-tests/assembly-generation-g07-before.gcanvas) | `geometry-canvas/8` | 0 | `2984678981fbe9705a40f37464507eb0ec3bb5b5908769b2b931302929688930` |
| [e64 重現](e64-reproduced/assembly/artifacts/geometry-tests/assembly-generation-g07-before.gcanvas) | `geometry-canvas/8` | 1 | `5f575dceeb7c43f221bfbd46b95eb2b8e83bb351464206e735a2eb494341d032` |
| [同 e9 撤回](e9-withdraw-upstream/assembly/artifacts/geometry-tests/assembly-generation-g07-before.gcanvas) | `geometry-canvas/8` | 1 | `bcdec30e5fee00f47ef0747af481feca869df21507683395db284ad6cc8a029a` |

各同次診斷 JSON 的完整 format／drafts 均與 ZIP manifest 完全相等。兩個紅包的 manifest 差異只有隨機草稿 UUID、updated_at；與綠包相比，再多一個 `data.members[0].guideId` 的 1／0 差異。其餘欄位完整相同，沒有刪草稿、改版本或放寬比較。機器結果與逐欄 diff 見 [results.json](results.json)。

兩輪紅的 FATAL_UI 均記錄點按 `select#asmInstanceGuide1` 時文字為「請選擇」，接著只有名稱 input 的 change，沒有該 select 的 change。這是原 log 的觀測；當輪沒有另封存 `references` response body，不把源碼推導冒稱為已錄得 null 回覆。

## 同基底七行撤回建立因果

[withdraw-upstream-guide-resolved.patch](withdraw-upstream-guide-resolved.patch) 是 `git diff 89c269bf... 2585fa9a...` 的完整原 bytes，SHA-256 `3f21c72a6fc7ee6d5c94ea5bfeaa30f8c3b5d57117579dd276817839146a26a4`，與原 Topic 03 撤回 patch 精確相同。唯一變更路徑為 `geometry-app/native/reference_sources.inc`；其餘產品檔、診斷、測例、golden 不變。全部 56 個 browser pin 仍符合相同 Topic 14 契約；三輪真正 preflight 均為 compatible_reviewed_topic14、clean 指定 SHA，沒有忽略差異。

固定源碼機制可核對為：

1. `reference_rebuild` 清除 resolved，而同一候選來源圖已 memoize 的 guide 不重跑 provider。1987 七行只在返回座標與已存 offset 相同時恢復該旗標。
2. `geometry-web/reference_bridge.inc:25` 對 !resolved guide 輸出 null；`assembly-workspace.js:184–185` 過濾 null，只建立剩餘 guide 選項。未列出的原 guideId 不會被此渲染函式改寫成 0。
3. 原 `assembly_workflow_test.js:9` 用真 Home／Enter 選 0。當畫面已落在「請選擇」，沒有 change 就不會觸發 `assembly-workspace.js:186` 更新草稿資料。因此畫面預設與草稿保留值脫節；本次兩個紅包確實保存 1，正控保存 0。

同 e9 基底唯一七行撤回再次造成同名 G07、同 `/8`／guideId 1，支持此上游產品缺陷是本案原因；不再以「格式已升到16／17」猜測。I8 要求候選完整求值與提交，I8a 的宿主契約包含 guide 方向／座標等可見結果；缺少已求值 guide 不能靠測試過濾或前端改預期掩蓋。沒有條文變更。

原 e64 baseline 沒有 saved bytes；本次 e64＋同診斷重現同名紅，且 e9 同診斷正控／單點撤回給出因果控制。診斷仍只是封存同一份保存 bytes、把 saved 加到 check 第三參數，原 AND／斷言數／timeout／golden 全未改。

## 環境、完整性與未驗項

三輪均為 Debian GNU/Linux 13.6、Linux 6.18.55、gcc 14.2.0、Python 3.12.14、Node 24.19.0、真正 Google Chrome 155.0.8059.84、16 MiB stack；每輪 [environment](e9-withdraw-upstream/environment.json) 與原結果另存。Chrome 為官方驗證套件的外部安裝，不是 CI `/usr/bin/google-chrome` 路徑，原差異保留。

各輪前後 SHA／狀態一致且 clean；port 啟動前無 listener，兩個成功 runtime probes 均 fresh=true 且 PID 是該輪自建 server。第一個 readiness probe 都曾 exit 1，後續兩次成功；兩個成功 probe 都在 harness 前，沒有宣稱執行後再 probe。只清理自己擁有的 process groups；server -15 是 SIGTERM 清理結果。

原 assembly partial 模式不比完整 canvas golden。正控 footer uncaughtBrowserExceptions=0 不是所有 console.error 的全域守門；紅輪 footer 沒有此欄位，不推定為 0。三輪記錄的 `Injected lost success response` 都是原測例預期注入，不另當產品缺陷。

[inventory.json](inventory.json) 逐檔列 source／destination／bytes／hash。三輪原 artifact manifest 的全部檔案與實體集合均重新核對；公開原 logs、真專案／JSON、截圖、runtime 指紋與 smoke 場景，binary／cache／鎖保留 hash 與排除理由。runner 原省略的 profile/cache/socket 僅保留原省略記錄，不宣稱逐檔驗證。沒有收整個工作區、憑證、repo `.codex/` 或使用者 feedback。

未驗：本次撤回後恢復的第四輪 browser、此 SHA 的其他五個瀏覽器 job、完整 canvas golden、後續最終組合全量、Windows／實體裝置。上述三輪足以提供本問題原紅／已含上游修正綠／單點撤回再紅，但不代表 GEO-261 整體驗收已完成。
