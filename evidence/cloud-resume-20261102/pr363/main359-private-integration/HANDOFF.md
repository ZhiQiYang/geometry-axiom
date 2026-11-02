# R06 × main359 私有一般 merge 候選

UTC 2026-11-02T14:15:59.476675+00:00。唯一 writer：`/root/r06_main359_closure`。本地分支 **codex/r06-main359-integration-20261102**；來源 **c2eb5edc99d2880a65583f46085617d99a6f191b**，parents 是 F4 **7a876ed6a772f3bb5fff0f9644421d6ec6e6cea4** 與當次固定 main **fca3f1a80f1dab564f5dd4c01c9e1226eaf09e2d**。普通二父 merge，未 rebase／force／amend；**未 push、未更新任何 PR、未合 main**。工作樹 `/tmp/geometry-r06-main359-integration-20261102` 在提交後及所有控制完成後均 clean。

## 修改與合流證據

- 嚴格保留兩種已存在的 reader API：K1 `readerCapabilities(caps,{cutting:true})`；R06 原五個 profile／manifest／scene／recordProfile 輸入。工作區真正 `prepareProjectScene` 以第六個明確 options 送 cutting opt-in；五參數中的非 array profile 仍拒絕，未知 options／非 boolean cutting 亦拒絕，預設 reader 不廣告 cutting。
- PF-H 的 `/19`、重複來源、`panel-fill-native/1`、exact三種 supportedRecords、complete:false、原 engineering／parameters 子能力與晚到 revision／writable/current lease 全部保留。沒有把 PF-H source-only reader 冒成 PF4/5/6 UI 能力。
- native assembly context 同時保 R06 position/dependencies/bay/external-reference 回呼與 K1 last_terminal 身分檢查；bridge 保 bay identities/capability 及 K1 terminal JSON；scenario verifier 把 definition-import 保為 bridge-only，不增加 scene/project requirement；timber schedule 同時保 R06 identity 與 K1 terminal＋CSV不泄入terminal規則。原 R08 pending/dirty/definition-changed/history 與 cutting undo/highwater 保留。
- 全部14個真 conflict與逐block hashes、來源3方資料在 `MERGE_RESOLUTION_DECISIONS.json`。`GOLDEN_THREE_WAY_ROWS.json` 記每個 key 的三方值；88個原 section值完全不變，僅 union total=2360 作一致性 metadata，**新 full canvas UNRUN**。
- `EXPECTED_THREE_WAY_ROWS.json` 保各原suite數值；唯一真衝突 node:tests-js 仍留 main 原 **740**，明確 **stale／未測得合流真數**，沒有相加／max／手填。root 將用原完整 `run_all --build --update-expected` producer 產真檔。新 diagnostic 放 `tests/diagnostics/`，不混入平面 aggregate、不改任何舊斷言。
- 原 main ledger／scan／report／receipt bytes 只是待重產保留，沒有新 stamp 或假 freshness。manifest 的 conflict 為 dedicated cdp_test.js 排除識別；保 reason/hashMode，按已合流 test driver exact LF hash 更新。最終 #366 整份帳本及架構三原裁判待 root。

## 已實跑的範圍

| 指令／收據 | 真實結果與來源 |
|---|---|
| Node24 `--test tests/test_assembly_project_store.js tests/test_cutting_project_store.js tests/test_timber_schedule.js tests/test_definition_import.js` | `contracts-baseline/`：**51/51、0skip、exit0、0.314s**。執行於提交前的實際合流工作樹；未把 execution HEAD 改標為後來的 P。其產品檔在 P 前後未再變更，這不是一份先於執行的完整 input seal |
| 新 diagnostic 初輪 | `diagnostic-initial/`：7/7、exit0；逐輸入 hash 記該未提交合流狀態，追加 highwater 第8案後不再把它說最終8案 |
| P 固定 8案 contracts | `private-controls/fixed/`：**8/8、exit0**，pre-execution FIXED_INPUTS 綁已提交 P、7個相關檔 hashes、16MiB stack、60s控制限 |
| 撤有限 PF-H reader | 私有 source copy，**exit1、6pass/2fail**；具名 `R06_MAIN359_PFH_AND_CUTTING_ARCHIVE`（另有 prepare 同一依賴後果），原輸出不丟 |
| 撤 workspace cutting option | 私有 source copy，**exit1、7pass/1fail**；具名 `R06_MAIN359_PREPARE_FORWARDS_BOTH_CONTRACTS` |
| 撤 cutting opt-in 防線 | 私有 source copy，**exit1、6pass/2fail**；具名 `R06_MAIN359_CUTTING_OPTIN_REMAINS_EXPLICIT`（另有 archive 反例後果） |
| 恢復 P | 原產品檔從未被寫成 mutant；清除私有 override 後 **8/8、exit0**。五輪實際0/1/1/1/0，原 source 前後 hash／clean 全核，無重試取好樣本 |
| 既有 R06 mutant anchor preflight | 39cases／42patches 每個原 sequential anchor 精確匹配；**沒有執行這39個 mutants**，亦無改 catalog 或原斷言 |
| 原 POSIX bridge flags 編譯 | `cc -std=c11 -O2 geometry-web/web_bridge.c -lm -o <private>/compile/bridge`：**exit0、24.062383789s**，300s編譯限、16MiB stack；輸出1,220,520B／SHA256 `936a6049cd9b844be7130599a1661b0c02c94db0df91bbc45cddd2a6a0af75c2`，**ELF未執行**，共享 `/tmp/geometry-tests` 未修改 |

Diagnostic 的 archive／reader／ContextHistory 都用真正來源；工作區測試執行真正 `cancelProjectScene`／`prepareProjectScene` 函式文字，但 transport/candidate/lease 為受控 fake。保存重新讀取含 R41 key 與 cutting record、R08 readForImport 不丟資料、readonly／late-profile 必取消且不送 confirm、local history一次與跨R06草稿的 cutting key highwater 都有具名原斷言。**這不是 Chrome fresh profile，也不是真 native World 零寫入的證據**；取消只證 request protocol無 `/upload/confirm`，不把 fixture中的 unchanged marker當原生快照。

## 未驗與下一步

新 P 完整 native、原完整 census/Node aggregate、真 fresh-profile browser、其他5 browser、整份 mutant execution、三條架構裁判、#366 freshness 都 **UNRUN／待 root**。舊 F4 12CI原件不重跑收件、不移標 P。P 尚非 GitHub 可解析 source，root 採入且正常推送後才能對外引用。

root 接續原完整 producer（不以局部 Node 數填 expected）；最後產品／測試固定後整份 #366、架構，真正 R06 fresh profile＋cutting共存與全部正式 gate，再交獨立審查。此候選沒有新增幾何／公理／使用者決策。

`R06_INTEGRATION_OVER_MAIN.diff` 是相對精確 fca3 的可審差異（583,274B、SHA256 `159e3406ba6c929824af7d243511a409b32b62b78a9185187a4dc8a397469152`）；`PRIVATE_MERGE_FROM_F4.diff` 是相對 F4 的完整私有採入差異（4,290,352B、SHA256 `0b46b92c48d404c8b31b63dbb15ba701d33cd7bc0376c8b3b152d22ef81f1474`）。兩份不包含根 evidence；不可只用 patch 取代二父 merge 歷史。最小重建方式是保留本地 P commit＋兩個已發布 parents；未向外發布。
