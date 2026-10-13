# 凍結映射後的補測附錄

以下結果新增於原條文映射之後。原 `frozen-mapping-manifest.json` 與補測前缺口表保持原樣；本附錄只依新腳本、實跑收據與獨立審查更新精確範圍。沒有以通過數替代條文內容。

## SR18 角色鎖因：已补證

root 唯一 native runner 於 clean `d8642b2e684038cbb8e24aba057c44e7aac1b231` 執行 [sr18-role-r1](gate-receipts/sr18-role-r1/receipt.json)，命令／gate／driver／自有 bridge 退出均為 0；[獨立來源與原件審查](sr18-probe/run-01-independent-review.json)判 `bounded-native-pass`。作者為 `assembly_mapping`，審查及執行由 root 負責。

新的正對照先有完整父 cell `[100,200,700,1800]`、真 boundary／primary 支撐及成功放置的 primary t9：完整 `at-line rule 10 0 1 -2 1 u 0`、`between t81 t82`、centerline 300、length 1560。之後只改同一已放 t9 的 role 為 secondary，拒絕精確為：

> timber 9，clause D17/I21，V_PRIMARY_AXIS：secondary 長度軸沿 v，與主支軸平行。

前後完整 dump、references、definition revision/hash 相等。這封住了舊例可能先被 `I13/R6`／缺失支撐拒絕的判定缺口；不把合法 primary 覆寫預設 secondary 當新禁令。原始 [role-rejection.json](sr18-probe/run-01/role-rejection.json)、[before](sr18-probe/run-01/before-role-change.json)、[after](sr18-probe/run-01/after-role-change.json)均保留。

腳本 [sr18_role_probe.py](sr18-probe/sr18_role_probe.py) SHA-256：`bb28f14fe23b15c2e1810f0554ff626dd62ae3a6c50101d86b9536e55aee8324`。实际載入 bridge SHA-256：`b76a6da590512722d6eda64cfc946392ccc2636f82ab187ef822c1e1606d68b5`。runtime version為 `82b45ea9cf53c10b2c4fd6591ce0dd45d055a9d8f0e7e4fb5765eeaf64075200`，完整命令、環境、head/dirty、前後runtime及源碼指紋在 gate receipt；實際 child binary另由 `/proc/PID/exe` 核對，沒有僅拿HTTP runtime冒稱native實際載入身分。

重現參數與先決條件見 [probe README](sr18-probe/README.md)。这是 native 角色拒絕專項；不聲稱瀏覽器角色UI、實機或 SR15 參數/anchor 已因此驗證。

## SR15 r1：保留判定失敗輪

clean `d8642b2e684038cbb8e24aba057c44e7aac1b231` 的 [r1實跑](gate-receipts/sr15-parameter-anchor-r1/receipt.json)命令／driver退出 1。此前具名檢查已觀察參數600→900、兩guide/direct、Undo/Redo與902非整除拒絕的狀態保全；單測未完成，不能宣稱整條SR15通過。

失敗行是probe `assertEqual({1}, preview.gridBindings IDs)`，實際列完整 `{0,1}`。raw中的binding0 before/after相等、binding1確實從1/2改1/3；來源核查後確認錯在probe要求transport只列已改記錄，原契約沒有此要求。原 [executed-probe.py](sr15-probe/r1/executed-probe.py) hash `618b878d96a3121d55c650ae4a42167ca3951da5be1cb6c4ae145a7f3c7c1af2`、[結果與traceback](sr15-probe/r1/result.json)、[wire](sr15-probe/r1/wire.jsonl)、[包manifest](sr15-r1-package-manifest.json)保留，後輪沒有覆蓋。此原腳本的歷史ROOT路徑原樣保留，r2已提供明確可攜repo入口。

## SR15 r2：參數／anchor限定原生範圍已补證

clean `d8642b2e684038cbb8e24aba057c44e7aac1b231`，[r2 receipt](gate-receipts/sr15-parameter-anchor-r2/receipt.json)與driver/native均退出0；[獨立審查](sr15-probe/r2-independent-review.json)由 `/root/report_finalize` 逐條核來源、wire與完整snapshots，判 `bounded-native-pass`。作者沒有執行probe，runner為root。原生載入bridge hash與SR18相同，前後clean身份均已保存。

更正依據是 `grid_binding_bridge.inc:219–237` 既有serializer列每份before binding再附新binding，`reference_bridge.inc:123` 呼叫它；I37/R32要求完整候選，沒有要求省略未變記錄。r2要求精確 `{0,1}`、兩者before均等live；A完整before/after相等，B明確U-anchor `1/2→1/3`、translation `[1450,-400]→[1600,-400]`，固定U main-lines `550/1450→700/1600`和整段端點相等，V與其餘身分字段保留。這不是簡單放寬集合。

新增完整原始結果證明 `param:1:1` 的U值600→900保留來源token，兩guide分別 `300→400`、`200→250`；direct V線位置應維持y400/y600、長540/240，完整typed refs及合法父cell仍在。B改anchor後其guide250→400，A全資料不變。兩次修改都驗preview/cancel不變、confirm改值、Undo/Redo恢復完整World且revision正向前進；參數902精確`DIVISION_NOT_EXACT`及anchor4/3精確D30/I37拒絕，完整World/refs/revision/hash不變。

腳本hash `29bc34b4dec9cb9b434a16e50553b2dd9197f5487a02d29cb49857cdb7356338`，[r1→r2 diff](sr15-probe/r2-preparation/r1-to-r2.patch)與[完整原件manifest](sr15-r2-package-manifest.json)保留；執行是一個完整native測試、14個具名檢查，不是14個使用者情境。這補native組合缺口，不冒稱參數／anchor正式browser操作或實機已驗。

## SR16／SR23：真 UI 限定閉環已獨審核收

root 在 clean d864 同源 runtime 以 script `b694cd73cdd53d50dff49eb907a3faea1a96834772f6a1b4cb891690512eda8c` 串行完成 1400 與 390，probe／gate／driver 退出 0。[獨審](sr16-sr23-browser/independent-review/independent-review.json)由 `/root/remote_inventory` 核對原始 trace、逐次 HTTP、正式 refs、完整資料、截圖及退出清理，判 `PASS_FOR_BOUNDED_SR16_SR23_FLOWS`。這是兩條工作流程，每寬 75 具名檢查，不是 150 個使用者情境。

第一面 guide23／direct timber103 先於第二 binding2 建立，第二面 guide24／timber104 也在來源修改前存在。SR16 將 U600 改為 U300，只出現 timber104 的實際 `R6/I5/I6` between-endpoints 診斷；timber103 的候選幾何仍合法，Confirm 禁用，pending／cancel 完整 raw World、revision 與原 history 身分不變。沒有把這個拒絕改標為 `I25a/CELL_SCOPE`。

SR23 將 U600/V400 改成 U900/V600，先驗 Cancel 不改完整資料，再確認一次共同交易；兩面 guide offset 300→400、direct centerline 400→500，正式 tuple 及真支撐長度 240/540 保留，原生 definition 只改兩個既有 pitch。Undo／Redo 恢復完整資料。正式下載 Save 的 manifest 與 World 取自保存前的獨立預期；兩個實際 archive 均為 `geometry-canvas/11`，只有 `manifest.json` 與 `world.scene`，未執行腳本準備的 /13 分支。New 完整清空原生與 project；新瀏覽器 profile 先驗真空狀態，再由 file chooser Open，Open 後 Undo 回原空專案、Redo 恢復全部保存資料。

[原始 receipt](sr16-sr23-browser/r1/receipt.json)、[包 manifest](sr16-sr23-browser-r1-package-manifest.json)保留原件與四份私有完整 trace 的 hash。boundary／placement／真支撐由 API 種植，其後來源、規則、binding、guide/direct 與保存開檔走 UI；下載 fallback 不代表 OS 對話框，390px 不代表實體手機／IME，也没有重啟服務或再跑完整產品套件的宣稱。

## #62 ASan／UBSan 與五項反證：新原件已核收，原 runner 失敗保留

本輪 clean d864 使用 [原 plan](sr62-sanitizer-mutations/preparation/plan.json)綁定的 54 份來源／測試／fixture，六次 unity sanitizer build 與十一個 oracle 程序串行執行。編譯使用 `-std=c11 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -fno-pie -no-pie -lm`，僅自有 oracle 子程序 stack 為 64 MiB；leak／halt／abort 皆啟用、無 suppression。新 baseline 的 41 subdivision 加 13 grid-system 方法通過，沒有 errors／skips／sanitizer 問題。這個 baseline 實際開 45 個原生程序，不是 54 個 native 程序，也不重現歷史缺件的 152。

[原始 summary](sr62-sanitizer-mutations/r1/summary.json)完整保留 `complete:true, passed:false`，[gate](gate-receipts/sr62-sanitizer-mutations-r1/receipt.json)與 driver 退出 **1**。M2／M4／M5 自動 `SEMANTIC_ASSERTION_KILL`；M1／M3 自動 `OTHER_FAILURE_NOT_A_KILL`。原因是私人分類器把既有 rejection helper 只 pin 在 187 行立即拒絕分支，而真正非法候選由同一原 helper 的 189 行 `assertFalse(preview.valid)` 抓到。這是 receipt 分類準備錯誤，沒有修改 fixture、產品驗收或既有測試來迎合產品。

[獨立語義審查](sr62-sanitizer-mutations/independent-review/independent-review.json)逐項核原命令、typed diagnostic、AssertionError、55 份原生 transport／stderr／binary hash、五次 pristine 還原，核收新 baseline 與五項指定反證；[接續核收](sr62-sanitizer-mutations/independent-review/recovered-sanitizer-review-acceptance.json)保留環境重接後 hash 回接。沒有重新編譯／執行、没有改原自動 verdict、没有宣稱原 runner 已通過。

| 反證 | 原測試實際觀察 | 還原後原測試 |
|---|---|---|
| M62-1 整除 | 600/7 非整除規則的 `preview.valid=true`，原 helper 189 行失敗；尚未 confirm 非法候選。 | 同命令精確 `DIVISION_NOT_EXACT`，退出 0。 |
| M62-2 序列化 | dump 缺少 `grid-source-rule 0 key 1`，原 918 行失敗。 | 規則身分保留，退出 0。 |
| M62-3 來源身分 | 更換到另一 source 的同 key 後，原 source guide 被錯誤接受為 valid preview，原 helper 189 行失敗；尚未 confirm。 | 同命令精確 `WRONG_SOURCE`，退出 0。 |
| M62-4 裁切 | u300 線錯誤跨完整洞口，和 literal 預期兩段 `[200,250]`／`[550,600]` 不符，原 537 行失敗。 | 正確洞裁切，退出 0。 |
| M62-5 capability | 無 capability 標記的新 highwater 語法 load 回 `ok:true`，原 955 行失敗；原測試在此停止，沒有再做完整 World 比對。 | 正確 preflight 拒絕，退出 0。 |

五次都把同一私有 active binary 路徑回復成 retained pristine bytes，hash 相同後重跑原 target 方法通過。M4 選既定 clipping 替代项，M5 選既定 capability-preflight 替代項，沒有冒稱 sample-index 或第二面 mutation。普通註冊 binary 與產品來源沒改。來源、五 patch、原 script／plan、全部 command／stdout／stderr／transport／合成 scene 及準備失敗輪見 [封存 manifest](sr62-sanitizer-mutations-r1-package-manifest.json)；二進位與重複來源副本只列 hash。

舊 sanitizer `/tmp/subdivision-repeat-only-sanitizers-valid.log` 的原件 hash `00766856e9148ff432cf7826e4b9958f29c48d30f1cd9b7aad3a38b54bf0c430` 仍未取得。舊 48 一般 mutation 不冒充這五項；本新證據也不把舊 152 描述成未曾執行或失敗。`preparation/README.md` 是原準備時態的原件，其「尚未執行」敘述由本附錄與新 raw 接續，而非改寫舊文或原結果。

## 本補測沒有解除的範圍

SR06／SR14 依現行 v1 只允一層、沒有使用者重排命令的界線解釋；既有 unknown-syntax 拒絕與 stable-key 原件保留，不擴張 nested/reorder 功能。A24 實機、#54 完整修正成本改善、非同步缺陷及完整安全 Resume 等仍在主報告分別列出。重現入口見 [REPRODUCE](REPRODUCE.md)；這份附錄不代表全部 #62 或整個產品可合併。
