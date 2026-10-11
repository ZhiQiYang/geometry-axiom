# PR #190 容量分類複核

受測樹為 `26a7c443b9bd10ae036b0956bd99233f594b5395` 加未提交的本輪 C include、橋接器及測試修改；`source-binding.json` 綁定實際 bytes。收據由 `subprocess.run` 直接取得退出碼，不把後續提交 SHA 冒稱為先前已執行的 head。原 `current_geometry.c` 468,081 bytes／13,067 CRLF／0 bare LF／0 NUL，公理、白話、正典、BACKLOG、決策、PF12 五份凍結 dump、原核心裁判皆未改。

## 修正及實跑

- D41／I33：完整 UTF-8／可列印字元驗證先於 96-byte 儲存容量。JSON 與 scene 的合法 97-byte ASCII、99-byte 中文、1024-byte 名稱均拒絕為 `UNSUPPORTED/CAPACITY`；空名、C0／C1 控制、非法 UTF-8、非法 hex 仍拒絕。原始 JSON 非法 UTF-8 在解析器拒絕，沒有冒稱其頂層錯誤是候選 violation。
- 96-byte 名稱可以確認、dump，再以全新 bridge 行程重開：706-byte dump、definition hash 與 read state 全同。超限／非法候選不能確認，scene 不置換已提交 dump／revision，redo 恢復原修改。這是保存定義及歷史的斷言，沒有冒稱完整 World struct 的 memcmp。
- scene 的第 17 完成面也保留容量分類；每次 load 重設診斷類別，前一筆 CAPACITY 不污染後一筆普通語法錯誤。缺失引用仍保留原具名 I52 診斷；原測試及期待未削弱。
- 完整定向回歸 **76/76：PF-1 native 22、transport 7、HTTP 47，0 error／skip，exit 0**。native 使用 fresh registry binary／sidecar；transport／HTTP 的 callback／mock 邊界依原裁判，沒有把它們冒稱真原生幾何。expected 僅 19→22 對應三個新增方法，原方法未刪。
- 五個指定突變編譯全 exit 0，測試全 exit 1 且只有具名 `AssertionError`：名稱容量誤判 6 fail、scene 集合容量誤判 1、非法名稱誤判容量 9、非法引用誤判容量 1、遺漏 scene 診斷重設 3。測試樹與產品原 bytes 未被私有突變改寫，還原後原生控制綠。

## 第 65 個障礙的界線

正式產品最多 32 柱＋32 樑，共 64 個不同來源。第 65 個不同引用缺件，重複又不是合法集合；本輪未聲稱存在正式產品可達的合法 65 件反例，也未把缺件／重複／非法型別統一改成 CAPACITY。正式 64 件正例、65th 缺件／重複／非法型別負例均在原生測試內。

容量 guard 在儲存前，且先驗證引用／唯一性。為執行合法集合超限的分支，僅在 `/tmp/geometry-tests` 的私有來源複本將 `FS_OBSTACLE_MAX` **64→63**：原生來源上限保持 32＋32，63 件正例、64 個存在且不同的來源超限為 CAPACITY。這個控制版本三題先綠，單獨把集合容量診斷退回 INVALID 的突變才真紅；正式頭檔 bytes／宣告 64 未改。`receipts/final-targeted-v2/targeted-mutants.json` 明列這項 instrumentation，不能拿它當正式 65 件成功或正式產品驗收。

## 核心帳本及執行環境

修改 C include 使原帳本 stale，保留 `ledger-stale` exit 1。本輪用原 `tests/mutate.py` 重產全表，M01 暖機後五個互斥 ID 群組各寫自己的結果；合併只採實際執行紀錄，再由原 `--check` 驗 freshness。不是手編 verdict，也沒有減少核心 inventory／改裁判／逾時。

最終 **48＝40 killed＋1 crashed＋4 equivalent＋3 retired**；45 個非 retired 重新編譯／執行，各組基準原 139 場景全綠。M20 重複 SIGSEGV 仍只列 crashed。driver exit 0，原 `mutate.py --check` exit 0／stale 0；原裁判、inventory 及全部幾何期望未改。

首次原基準因 8 MiB stack 受阻；相同二進位的原 139 場景為 125 pass／14 SIGSEGV infrastructure／0 assertion fail，exit 2。`diagnostic-baseline.fingerprint.json` 綁定該較早中間樹的實際二進位，它不是最終來源 binary。相同 binary 只改 stack 至 16 MiB 後 139/139、exit 0；最終來源重新編譯並以 16 MiB 執行全表。stack 收據記原／新資源限制；沒有以崩潰當 killed、放寬原測試或變更期望。

## 保留的失敗與範圍

原始 `before` 用超過 32 柱的測試場景，四紅包含一個輸入建構錯誤；更正成 32 柱＋32 樑後，`corrected-input-original-product` 原产品三方法 12 AssertionError／exit 1。該階段的 65th CAPACITY 期待後來依完整審查更正為正式缺件 INVALID，不能把歷史 12 紅全當最終裁判反例。`before-corrected` 名稱誤標，但其來源 hash 清楚是初步修後樹，兩题 exit 0，不冒稱修前。

`earlier-scope` 五突變及 76 綠屬早期語義；後續先恢復缺件／重複 INVALID，`final-native-transport-http` 抓到舊具名 I52 診斷被取代的一紅，已恢复原斷言要求。`prior-targeted-attempt` 的 stale-scene-kind 真存活，使 driver exit 1；補入 CAPACITY 緊接普通語法錯誤的對照後該突變真紅。所有早期原始 log／receipt 保留，只有 final-v2／final-full 的收據用於本輪通過聲明。

`web_bridge.c` 通用 loadfile 路徑只有 **3 個新增行**，使 scene 容量原因可以結構化且不殘留前次分類；依看板的小例外記錄這項區段外正確性修改，native／HTTP／stale-kind 突變直接驗證。其餘產品修改在 PF-1 自有 `finish_surfaces.inc`；沒有新增 UI 入口或改 SSOT／reader／鎖定政策。

正式七 job 仍由既定本機 owner 按 #184 等疊加順序凍結最終整合 SHA；本輪沒有排 WSL 全量，也沒有排他環境驗收或 Windows 原生編譯。PF11 真實瀏覽器及完整 `.gcanvas` 保存、I53 分層（仍 pending）、PF-2～PF-6 都未完成，不因本輪定向綠燈解除。#201 的工程橋接衝突仍由整合 owner 同時保留 finish_batch 與 deleted-fields，未合併或改寫其他 PR。

全部 payload 的 bytes／SHA256 在 `manifest.json`。脚本中的 `/workspace`、`/tmp` 是本輪原始執行位置；重現時需要對應 checkout，私有編譯與所有二進位均寫 `/tmp/geometry-tests`。原件 diff 存為 JSON UTF-8 字串，保留原 bytes，避免 Git 把 patch context 行當成新文件 trailing whitespace。
