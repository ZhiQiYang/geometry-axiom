# #323 本輪停止點與接手

產品／測試來源 S：`b2445b5a270d60fdf48b07f6edddbe91266d8aa2`。base：`b74f9a2ae7ade1555b9be45283adecc097fb76e3`；原 main 比較分母：`adbaebf9c73ea6801d7b4d5214e4b846b132923b`。本輪沒有套入新候選，沒有新產品或測試提交。最新使用者要求階段性停止，本包只封存已跑完的基線，不開新修正或測試。

## 已完成

- 原三套 PARTIAL 診斷：load11/13、host22/22、contact15/15，48pass/2fail/0skip，原 primary/reaper/outer 各1。
- 原 v3 八 stage 皆真終態；prepare/build/compare/perf/profile 各 execution0、required-eight1、PF3 execution0、native1。perf/profile/後續 wrapper1保留累積紅，不能當成PF3紅。
- 175場景stdout、有序graph與guard counters三方等價；原36timings與4gprof一次完成，未重抽。
- N64/main1.160861952340483≤1.3綠；N32/base1.0008656473515014>1.0紅；source64/32=1044429/169688=6.154996228372071>4.5紅。N16/base0.7020541681432466與N48/base0.7354720650542408綠。
- 必要八套675項，673pass/2fail/0skip；完整native225suites共5200pass/2fail/1原Windows GDI允許skip；另mutation:check為closure STALE而FAIL。
- PF3 baseline20、19個具名正常assertion kill、restored20，0error/skip、原source不變。
- UI傳輸失效不重開stage；原內層exit/streams完整，scheduler殭屍且缺TOP RESULT保真見RECOVERY。這不是偽造補成功收據。

## 留給接手者

1. 先讀本包原`BASELINE_CURRENT_SUMMARY.json`、`RECOVERY.json`、完整原receipt與streams。源碼未改；baseline紅不可刪，不能重抽或放寬門檻。
2. 依root排程完成318→314→combined後，再接323；先確認目前final base/source closure。普通merge，不rebase、不force push、不合併PR，不改`公理層.md`／`決策佇列.md`。木工推理前讀最新origin/main決策佇列10/12–15、10/22/23與pr333 FIELD-RULES；本包已保本輪讀取的原Git bytes/hash，不代替未來新決定。
3. 未套四檔候選在`preparation/combined-memo-controls-candidate-v1/`，patch SHA256 `a44018ad1e3455af89dc9fbc19ea4ec3d9b0e4dfec56f9ddab5d2893d91871b0`。兩產品檔與已獨審memo v2完全同；兩測試檔修既知控制漂移並加contact hit edge/kind/order/id獨立反證，保13方法與所有原assert。54項靜審0 findings不是動態通過。
4. 修法不涉及公理語意：成功後才快取contact三欄；每hit仍為當前consumer發原placement depend。owner/dispose/reset、failed/sealed／原格式驗證都必須真跑。新contact-id與caller不借舊full-anchor控制冒綠。
5. 接手後若採候選，先固定並普通push新的乾淨可解析source SHA，再跑原三套及四個新具名0/1/0。prepared-only launcher 在`preparation/fixed-three-driver-preparation/run_three_fixed.py`，hash `fa3abc2561259e9d8cc930b9ee2101f3282bf32f2f744455ea22f4f8855bc12e`；CLI `--repo <repo> --sha <newSHA> --out <freshOut>`，原13/22/15與timeout/stack/env/reaper不變，未執行。
6. 再用原`preparation/acceptance-tools-v3/run.py`各stage一次完成全部原protocol。perf/profile要root獨占，原R3不可拔；同out不覆寫stage。先後差異若改source或tests須用新final SHA與fresh out完整收齊。不要由舊f43 profile外推收益；本輪新S原profile已在包內。
7. 最後帳本由root在最終stack一次check/必要時整份重產，children不各自重產；架構三條原裁判與四檔收據在final closure刷新。本輪incoming receipt不宣稱對新修正fresh。

本輪未跑：候選C／測試修改、四個新反證、修後三套、新final原v3、final帳本／架構刷新、323六browser。這些是使用者階段性停止後尚未開始，並非Chrome裝不上。既有Chrome156/Node24雲端環境不需升版。

## 原件還原

`preparation/sync-b74f9a2a/subcommands/000013/stdout.bin`原205298659bytes仍保留於原雲端位置，封包以同目錄lossless-map指向`large_merge_stdout/MANIFEST.json`及四個獨立gzip raw ranges。依parts順序各別解壓後串接，bytes必須205298659、SHA256必須`778f023db9aba56fa84bd85b8ff32c016aec5bb0d9470b445653b0bd3989e174`；原result.json出口0／原hash也保留。這是無損表示，不能當排除stdout。

其他命令metadata/stdout/stderr保原件；generic publisher若排除可重建ELF/cache會在excluded inventory逐筆列bytes/hash，不能吞原命令streams。候選、工具與所有原失敗版本保留，不冒稱產品已修好。
