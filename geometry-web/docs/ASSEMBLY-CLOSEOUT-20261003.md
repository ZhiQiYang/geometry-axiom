# 組構收尾驗證（2026-10-03，PR #52）

基準 main `fc4f08bd5ecb31f26179334b9b35a21de21e928d`；修復程式 commit
`a685dd32a09744e87521b494184208aa562b8721`。
文件與見證的後續 commit 不修改這份已驗的正式程式。

## 改動及既有 PR 的處理

| 項目 | 處理 |
|---|---|
| #51 新增草稿身分碰撞及編輯意圖 | 已合併，保留正 uint32 回繞、live＋draft 占用檢查、binding_intent |
| #50 原生新增／編輯防護 | 由 #52 接續：create 拒絕占用，edit 核對 canonical binding 指紋 |
| #50 高水位配號、永不重用、identity capability／實驗 format 8 | 不整併；與 #51 合法 MAX 回繞有行為衝突，留待獨立契約核准 |
| Q30 舊模型雜湊阻塞 | 現行上游已修，重新測試確認；舊診斷留存於歷史 |
| #20–#23 | 已結案；總工單勾選與現況同步 |
| #19／#24 A24 | 保留 open：實體手機鍵盤、OS 選檔與下載位置仍未驗 |
| #25 | 精確有限契約、D34/I42/R35 提案及現有幾何見證已提供；生成器未實作 |
| #43–#49 | 路線與探索提案保留，不冒稱已選定實作 |

UI 沿用既有預覽／編輯與拒絕訊息，不新增入口或常駐說明。
格式 7、既有例檔與 legacy put-binding 相容；後者仍可 upsert，正式 UI 使用 guarded API。

## 本機可重現驗證

以下命令 exit 0；全數使用隔離服務／暫存專案，未重置使用者服務。

```sh
npm run build
ulimit -s 16384
python3 tests/run_all.py --build
python3 geometry-guide/sync_axiom_reader.py --check
GEOMETRY_TEST_BRIDGE="$PWD/.build/web_bridge" python3 tests/build_assembly_example.py --check
GEOMETRY_TEST_BRIDGE="$PWD/.build/web_bridge" python3 tests/build_assembly_generation_witness.py
```

- 非瀏覽器 38 suites：1289 pass、0 fail、1 named Windows GDI platform skip。
  本次增加 native assembly 6 項（32 total）與 workspace 1 項（20 total）；expected 只增加，未放寬。
- 正典閱讀器 check 通過；公理与正典內容未改。
- ASan/UBSan fresh bridge：32 assembly tests 通過，含 leak detection；無 sanitizer 診斷。
  編譯：`gcc -std=c11 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer geometry-web/web_bridge.c -lm -o /tmp/assembly-asan`。
  執行：`GEOMETRY_TEST_BRIDGE=/tmp/assembly-asan ASAN_OPTIONS=detect_leaks=1 python3 -m unittest tests.test_assembly_rules`。
- 故障注入在隔離 source copy 刪除 create 占用 guard、edit 指紋 guard，分別被新增的
  `test_explicit_create_rejects_live_id_including_identical_content`、
  `test_stale_explicit_edit_rejects_even_with_current_revision` 行為斷言抓到；不是編譯或啟動失敗。
  未修改正式 source；原始版本兩測試重新通過。
- upstream workspace 對新增 missing-fingerprint 測試 fail 1（錯誤地送出 fetch），修復版完整 20 pass。

## 遠端瀏覽器與限制

[程式 commit CI run](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/37085406781)
包含 native 與六個 browser jobs；以 PR 上目前結果為準。
已完成的 assembly 108、grid 138、documents 47、space 183、timber 79 斷言各為 0 fail。
canvas 完整組 1684 pass、0 fail、0 skip；74 段逐段與 golden 相符。全部七 jobs success。
不把分組斷言當端到端情境數。

本機没有 Chrome，瀏覽器驗證使用同源 CI。390px 自動化與實體手機是不同門檻；
A24 未驗。Windows GDI 不在本次 Linux 實測範圍，歷史 Windows 證據不代表本版全套已驗。
隔離環境未取得使用者原機 F8 回報，不能宣稱原機沒有未處理回報。

## #25 的具體下一步

[待核准契約](../../geometry-core/ASSEMBLY-GENERATION-PROPOSAL.md)列明三 member、來源、
兩端支撐、所有權 mapping、更新、能力與保存，以及逐條公理新增與 G01–G10 未執行驗收。
[原生見證 JSON](assembly-validation/ar06-native-witness.json)可由上方腳本重建；
它只使用現有 place/reference/scene API，沒有新增生成入口或 AssemblyInstance。

依 AGENTS「條文未定案前不得實作」，取得使用者對具體差異核准後才進入生成器實作。

Canvas `uncaughtBrowserExceptions:1` 是測試明確注入並登記的預期例外（同上游基準），
不是未登記的程式例外；不得改寫成原始 exception counter 為零。
