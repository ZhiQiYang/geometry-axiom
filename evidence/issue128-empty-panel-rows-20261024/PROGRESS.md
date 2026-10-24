# #128 P2 空板列舉：目前狀態

分支 `codex/issue128-empty-panel-rows-20261024`，產品／測試 SHA `324034812bb6effca68e0413bc0468595337b317`；base #346 `a5f1806fb3cad2dada1a56e79e01d54f9f86700f`。此提交只更新證據；全部新正式結果在乾淨 S324 執行，證據 head 不取代 product SHA。

## 唯一 current-state

| gate | 真實結果 | 邊界 |
|---|---|---|
| `python3 -B tests/test_geo261_panel_native.py` | **0：13 methods、0 skip** | 以已獨審被動 observer/runpy 封存原入口；原 60 秒單例時限 |
| NativeBuild compile/link | **93 次全部 0** | 原編譯旗標與 300 秒限制；沒有把 compile failure 當 mutation killed |
| 原十個 controls | **10 個正常具名 ASSERT exit 1**，同 suite 正例 exit 0 | 保留原 suite 順序；不聲稱每個原控制有額外恢復執行 |
| 三個新增 semantic controls | **每組真實 0／1／0** | 只查一相位、丟 raw seams、錯拒合法空板；精確 assertion 原文見 FORMAL_SUMMARY |
| 完整優化撤回／恢復 | **0／1／0** | 撤掉整段預檢與 loop guard，恢復重新編譯原候選 bytes |
| 外部獨立公式 | 0：1150 案、488 全空、19 首 phase 空後有板 | 純 Python，與 C 正式證據分列 |
| 產品／companion／公開 source 靜審 | 239/0、40/0、23/0 | 先前原件不改寫 |
| 先前公開 E/D 原件包／formal wrapper 審查 | 658/0、31/0 | wrapper 四個純 parser 負例拒絕假綠；不是產品 C 反證 |
| 正式執行原件／封存 roundtrip 獨審 | **621/0、3754/0** | 124 child 原件、93 build、全部 1250 archive members 與原 bytes 相符 |
| PF-1／PF-2／PF-3、完整 native、受影響 browser | **UNRUN** | 未借 train、#343、#346 或其他 SHA 的歷史通過 |
| 最終全帳本、架構三裁判／收據 | **UNRUN** | 主代理依最終列車統一重產；本子代理未執行 |
| 合併狀態 | **NOT READY** | 還需受影響正式整合、帳本／架構；此提交 E/D 的最後窄核另交同儕 |

## 成本反證的實際 C 輸出

兩輸入長度分別 10,000 與 100,000,000。fixed 的 phase calls 為 **2／2**；whole-withdrawn 為 **5,000／50,000,000**；restored 為 **2／2**。六次都保持 status 7（原 `WOOD_PANEL_SEAM_LIMIT`）、clip-status 0；輸出清空斷言也維持。撤回的精確 stderr 為 `ASSERT:empty-axis-work-independent-of-empty-row-count`，正常 OS exit 1。沒有新增時間比率、放寬 golden 或時限。

三個語意控制的正常紅依序為 `ASSERT:empty-first-phase-keeps-other-parity`、`ASSERT:empty-axis-zero-pieces-with-raw-seams`、`ASSERT:empty-axis-legal`。原十個控制也逐筆保存精確 assertion；未混入 crash、signal、timeout、setup failure 或 skip。

## 原件與隔離

`FORMAL_RAW_INDEX.json` 綁定 1250 個原件，archive `formal-panel-native-originals.tar.gz` 共 3308093 bytes，SHA-256 `ca40b62ec0462b02ecc1dd8727f4317bf03cf0a8ece286cf302b968725b0adda`。保留所有命令／exit／stdout／stderr、環境、S、Git前後身分、實際執行檔 hash、93條編譯紀錄、負例 C 源，以及 recorder/reaper/observer 原件和歷次封裝修訂。

來源 checkout 僅補 131 個實際 NativeBuild／helper／fixture 原 Git 檔，當時配置 8,273,920 bytes，原20 MiB預算內。formal OUT/TMP 在本分支私有 workspace，secondary 租約已釋放；全程未碰主線 native ROOT/global cache。正式後來源 HEAD/tree/工作區皆乾淨。

## 下一步與界線

正式原件與封存已由另一代理通過 621/0、3754/0；主代理依最終列車更新帳本／架構並跑 PF 與其他受影響正式項。分支順序 #343 → #346 → 本 P2 → 512，後續採一般 merge。

本片只略過 body 的全空外層，raw seam 原件與容量不改；staggered raw seam 的空外層仍未優化。#128 P1 JSON 精度、P3 UI 回執、P4 allocator 契約與 P5 舊工具另案。最不確定的是未跑的整合及最終帳本／架構；不能宣稱整個 PR 或 #128 已完成。

## 收據路徑更正（不改原件）

沿用的 driver 原 receipt 欄位 `native_execution_log` 與對應環境變數只是設定路徑，該 JSONL **未物化**。本 suite 的真 124 個 runtime 子程序原件在 archive 的 `formal/panel-native/observed/commands/`，93 條 build 在 `formal/panel-native/compile-retention/`。`FORMAL_LOCATORS.json` 列完整對照，不能把設定中的 JSONL 當成第二份執行證據。原 receipt、工具、archive 與所有 stdout/stderr 完整保留，未回寫或重測。

獨審完整 reports/checks/helpers 在 `formal-independent-peer/`。package peer 初次 helper 誤用索引鍵（實際為 `local`），原錯誤與修正前 helper 亦保留；僅修正 reader 後為 3754/0，不是產品紅燈。
