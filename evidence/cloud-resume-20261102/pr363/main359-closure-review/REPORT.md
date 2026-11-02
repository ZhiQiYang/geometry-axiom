# R06 F4 與 main R08 的只讀三方閉包審查

觀測 UTC：2026-11-02T13:51:30.709280+00:00。固定 merge-base **df7eb43af3389ff2afc1a73aaf4e57580ae612fc**；已核收 R06 F4 **7a876ed6a772f3bb5fff0f9644421d6ec6e6cea4**；新 main **fca3f1a80f1dab564f5dd4c01c9e1226eaf09e2d**。本小審查沒有修改、merge、checkout、push 分支，沒有執行 native／Chrome／產品／任何下載的 ELF。

## 實質結論

原 F4 三項修復不重開、原 12 CI 收據不改標。新 main 與 F4 同時修改25個非根 evidence 路徑，包含原生來源介面、保存／重開 API、transaction、正式裁判與 golden；**不能以舊 API mergeable clean 宣告最新來源閉包**。

根據 root 已保存的 REST metadata，#363 的 base.ref 雖為 main，base.sha 仍 df7，merge_commit_sha 仍 F4 舊合成 **946ba6274e0cbcfab20b8fc0433386e187870d83**。這只描述該舊 PR 快照；本審查不以它推定 fca3 的實際可合或驗收。

兩項明確的合流 API 交會：

1. **readerCapabilities 參數互不相容**。F4 project-store.js:339 接受 `nativeCapabilities,nativeProfiles,manifest,scene,recordProfile`，以43個有限原生子能力、`/19`、真正重複開間定義、`panel-fill-native/1`／`complete:false`／三種 supportedRecords 與既有 engineering／parameters 守門，才額外承認 R06 所需的 PF-H source-only replay。main project-store.js:298 第二參數則為 `{cutting=false}`，切斷未授權 reader 隱式廣告 cutting capability。只取 F4 會漏 cutting opt-in 守門；只取 main 會丟 PF-H profile／revision／有限記錄認證。這是具體合流契約交會，不代表已執行的合流產品紅燈。
2. **prepareProjectScene 同一接線行**。F4 reference-workspace.js:1935–1942 先讀 panel-fill-read、再次確認 writable/current lease 與 native revision，再傳五個 PF-H 輸入；main :1936 則傳 `{cutting:true}`。新來源必須保留兩個能力判斷，並保留 R08 import-confirm 的 pending／dirty／definition-changed/history 接線，不能用開放白名單替代。

其他四個實讀原生 leaf 的合流邊界：

| leaf | F4 應保留 | main 應保留 |
|---|---|---|
| woodworking/native/assembly_sources.c | bay SourceKey 13/21 byte 解碼與所有權、result `at.edgeKey` 原生輸出／讀回（:363–383） | `wood_assembly_sources_matches` 的 engineering `last_terminal` 身分檢查（:326） |
| application/native/reference_sources.inc | derived outer 邊 `edge_key`→R41 resolver、bay position/dependency callbacks（:301–410） | direct finish context 的 `last_terminal=NULL`（:211），不能讓新 K1 回呼越過 direct 路徑 |
| geometry-web/assembly_bridge.inc | bay capability、limits、身份 mapping、bayCells/具名錯誤 | 綁定欄位 `eng_resolve_terminal` 及 `terminal` JSON（:15–17） |
| geometry-core/transactions.inc | 既有內層 fast path 遇 `assembly->bay_required` 必須退出（:771） | R08 `definition_import` preview flag/reset 及一般 confirm 不得吃 import token（:4/:489/:579） |

## 可保留與不能宣稱沿用的範圍

- **可原樣保留**：F4 12 CI／其真 execution／所有修前紅燈與修後收據，仍明確屬 F4。既存原生／草稿／保存／fresh profile 修復已交付的歷史結論不撤銷。
- metadata 證明 main 相對 merge-base **未改** R06 assembly-workspace.js、assembly-provenance.js、native assembly.c/.h/assembly_sources.h、world_candidate.inc、current_geometry.c，以及原 R06 native/browser/mutation suites；一般 merge 若確實原樣保留這些 Git blob，可沿用其「原碼未再改」的身份證據。這不能單獨代表依賴它們的新 binary／新 import graph 已驗。
- **不得直接沿用為新整合綠燈**：整個 R41 reopen 鏈的 runtime、原生 aggregate／6 browser／整份帳本／架構。實讀6 leaf 均有兩側實質變化，且 run_all registry/expected、cdp driver/golden/bridge/index 也雙側改動；新來源須凍結後按原規則重驗。這個有界審查未讀所有 native include/import closure，不作 blanket closure PASS。

## 最小正式驗收／反例建議（全部 UNRUN）

1. 一般 merge 後先把 reader API 的 PF-H profile 與 cutting opt-in 改成明確不歧義契約；盤點全部呼叫者，不以任意 object 取代原來拒絕非 array profiles 的守門。保留23個其他非 evidence 交會路徑的雙側變更，不整檔選一側。
2. 沿原 R06 真入口保存 `/19`：PF-H host＋R41 外輪廓 primary＋pending 草稿；另一個獨立 Chrome profile、另一個乾淨服務重開，核來源鍵逐 byte、derived mapping、候選、取消零變更／成功一次 native history 及冷 replay／undo/redo。缺 profile、缺 supportedRecords／capability、revision 晚到須拒絕且不改現世界。
3. 同一新來源驗 K1 cutting capability opt-in 的保存／fresh reopen，再驗 R06＋cutting 共存；未 opt-in 的 reader 仍不得廣告 cutting。R08 import-confirm 的一次 history／pending／dirty 接線也要保存。沒有額外批准的 R06 匯入格式支援不得自行擴張；不支援時明示有限拒絕、零寫入。
4. 撤回其中一條合流接線時須各有具名紅，再恢復綠；撤回 PF-H／cutting 不能只靠單一寬鬆 unit mock。新參數契約可先純契約測試，真正兩 profile 的 runtime 測試仍需最後同源執行。
5. `mutate.py --check` 保留實際輸出；root 依既定 #366 工具做最終整份重產與架構三原裁判；舊 F4 的 execution.head 不改成新來源。正式 native／canvas／其他5 browser 照原 limits/golden/skip，未執行者明列 UNRUN。

## 範圍與資料

只實讀6個唯一 source leaf、各 base/F4/main 三版共18份，**1,250,221 bytes**；都與精確 Git blob id 相符，未額外取歷史 artifact。新增 source 導入模組與其他交會檔僅 Git metadata，本審查不推定其內部行為。所有新 runtime／正式合流／突變執行均 **UNRUN**。OWNER_PRECHECK 保存 F4 與 root 340 clean、共用 pool HEAD unborn 觀測；沒有變更 owner 或 branch。
