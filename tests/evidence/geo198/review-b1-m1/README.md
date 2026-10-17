# PR #202：B1／M1 審查收據

產品修正 `f32f57449c8cb6df983aba035115159be91677f8`，M61 定義修正
`865f543028c2b657ef09f98e358b4a6d36a13211`；完整 native 的實際 head 見
[`aggregate/checkout-before.json`](aggregate/checkout-before.json)。這是 Linux 補充驗證，
不是 WSL、強制獨占隔離或最終整合 SHA 的正式七 job。
交付提交只加入數量表、文件與 raw，不冒稱交付 head 已受正式裁判。

## 輸入、完整 dump 與二進位

[`comparison/base.json`](comparison/base.json)、[`previous.json`](comparison/previous.json)、
[`fixed.json`](comparison/fixed.json) 保留所有指令、stdout 協定 JSON、前後完整 dump、
bridge exit 與 binary SHA-256。B1 用審查原輸入 origin z=0；M1 用 z=100。

| 案例 | 精確 base 635dd86 | 舊 head fc4859b | 修正後 |
|---|---|---|---|
| B1 矩形＋孤立線，c1 c2 | 拒絕，dump 相等 | 錯誤成功，dump 改變 | R7 拒絕，dump 相等 |
| B1 同型 cut-strip | 拒絕，dump 相等 | 錯誤成功，dump 改變 | R7 拒絕，dump 相等 |
| 孤立點 | 錯誤成功，dump 改變 | 錯誤成功，dump 改變 | R7 拒絕，dump 相等 |
| M1 未裁切 strip | 成功，dump 相等 | R7 拒絕 | 成功，dump 相等 |
| M1 後續缺項 | 拒絕，dump 相等 | 提前 R7 拒絕 | R15 拒絕，dump 相等 |

base binary 由 [`remove-fix/results.json`](remove-fix/results.json) 綁定精確基底來源；
舊 head 的獨立最小 source fixture 只從 git archive 取得編譯閉包，沒有 worktree／閱讀器副本。
[`comparison/metadata.json`](comparison/metadata.json) 包含全部 source hash、實際 O2 編譯 argv／cwd／returncode。
第一次最小 source fixture 漏包含 web inc，編譯失敗；原 log 保留 `previous-build-attempt1.log`，
補齊精確 include 閉包後才實跑，不以失敗編譯冒充測試。

## 先紅後綠與回歸

`before/` 是新增測試先行、產品仍為 fc4859b 的實跑：native 164/166，reference 48 tests、6 fails。
`after/`／`final/` 是修正後 native 176/176、reference 48/48、兩個 runner returncode 0。
後來加入的閉合佔用格 oracle 並非先紅批次的一部分；它獨立驗原始格集合的點／邊接觸。
舊 1 mm 寬足跡的額外底邊接觸仍保留原輸入驗拒絕，另加真正單矩形正例，兩種 winding 都測。

`remove-fix-clean/` 暫時移除整個產品修正，測試不變：native／bridge／scene 均 returncode 1，
且原 A/B 指名轉紅；逐 byte 還原後均 returncode 0。原 C 檔由 finally 保全。
[`scenes-clean/original-comparison.json`](scenes-clean/original-comparison.json) 核對原 143 份 TESTS
規格全部相同、原接受／拒絕變動 0；現行 153/153 通過。
`stack-8m-attempt/` 保留一次漏設 16 MiB stack、且與首輪 remove-fix 啟動重疊的場景探針，18 個異常 -11，
探針的 Python exit 0 並不表示場景通過；首輪 `remove-fix/` 也不當作獨占實驗。
後續 `scenes-clean/` 明確設 16 MiB 並直接記錄 returncode；`remove-fix-clean/` 在其他測試／服務停止後才重跑。

## 突變

`mutations/` 首輪實際 returncode 1：46 killed、1 crashed、1 survived、4 equivalent、3 retired。
舊 M61 的「只留一段」被新增閉合邊防線補住，故 survived；沒有把它計入通過。
改 M61 為「以 bbox 冒充多段交集」後，`mutations-final/` 全量重跑，實際 returncode 0：
55 筆＝47 killed＋1 crashed＋4 equivalent＋3 retired，survived／invalid／stale／blocked＝0。
[`verification.json`](mutations-final/verification.json) 核對 4 worker ids 不重疊，52 個非 retired
全部各真編譯、真執行；M35／M51／M55 只驗退休依據。M61–M65 的具名 killer 亦列在該檔。
每筆執行收據及 source／oracle／binary 身分存於 versioned 帳本及 `mutations-final/ledger.json`。

## 瀏覽器、完整 native 與限制

`browser/targeted/` 六個 fixture、33/33：原 B 柱／cut-strip 樑／390px 手機均經原按鈕成功拆片，
原 A 與混合案例拒絕、rollback 為直接 API 驗證；M1 由原套用按鈕實際回 ok，完整 dump 不變。
沒有冒稱 A 的錯誤清單能由 UI 選擇另一合法項；樑 cut-strip 後的 bbox 鬼影限制仍在。
`space/` 跑未修改的原完整 harness，無 filter、七群 completed，228/228，實際 returncode 0。
該次 before／after HEAD 均為 f32f574，C 來源與既有二進位 bytes 不變；
後續變更突變定義及帳本的完整 native 另綁其實際 head，不冒稱最終整合 SHA 七 job。
`run.json` 退出碼直接來自 Popen.poll，沒有由 passed/failed 推算。

完整非瀏覽器 `python3 tests/run_all.py --build --update-expected`：83 suite 全部執行，2731 個有計數項為 2721 pass、9 fail、1 個具名允許 Windows GDI skip，實際 returncode 1、784.51 秒。9 fail＝reader 5 紅＋原 Node workspace races 4 個 5 秒 test timeout（不是 suite 逾時）。數量表只增加 native 164→176、scene 147→153、reference 40→48；沒有刪除斷言或豁免失敗。其後以未修改原設定重跑整個 `node:tests-js`，651/651、0 skip、exit 0；另原 races 檔 fresh native 控制為 61/61、0 skip。補跑均為限定範圍，不能拼成 83 suite 全綠；原 4 個逾時未重現、成因未定，沒有 main 同案例失敗證據或正式豁免。

`node-isolated/` 首輪是 60 pass／1 skip，因沒有提供 fresh bridge 而未跑 native ABA，不計完整通過；`node-isolated-fresh/` 使用 runner 相同 fresh 環境後 61/61。`node-repeat/` 只保留該次所選 Node 的 suite log，未把 cache 中未重跑的其他 suite log 冒充新結果。

`process-samples.json` 為週期 /proc 觀察，記錄樣本時間與 process argv；
無強制獨占或 namespace 隔離，短程序可能漏看，不能推稱全程無 foreign 干擾。
自有測試服務 runtime session／PID 綁定於 `runtime-before.json`、`runtime-after.json`，
保存 `server-final-dump.json` 後只停止該服務，退出碼 130；瀏覽器由各 harness 正常關閉。
本輪 server log 有 1 次 BrokenPipeError；無 request 時間／命令收據，未定位成因或豁免。
console／page exceptions 空並不代表服務整體健康。舊原 space 13/2 與 6 次 BrokenPipe 均保留在歷史證據。

正典唯一 owner 仍是 PR #192；它須在最終整合 head 原位 sync → --check → 原 41 tests，
包含本 PR R7／R12／R14／R15 追溯，不直接複製尚未含本次來源的上游 HTML。
`reader-diagnostic/` 在記憶體比較精確親代，新增追溯差異現為 753 字元（先前為 238），
非追溯內容相同、重建冪等、批註身分保留；正典 bytes 未寫入，沒有第二份 HTML。
這是同步範圍診斷，沒有冒稱 sync 落檔或原 reader 41/41 通過；五紅不豁免。
正式七 job、Windows GDI 及強制隔離仍待；CI 受帳號計費阻擋;正式合併裁判由本機 WSL 收據提供。
無新 UI 入口。sha256.json 綁定本目錄所有 payload；exe、Chrome profile 與下載檔未版本化。
