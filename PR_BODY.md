# K provider hint：保留 256 槽，以通用 provider 混合減少快取碰撞

目前 PR #338 的列車效能仍未通過；本切片將 K 的 hint 槽改為固定 Knuth 乘數之高位元組，保留原首／尾 key 位元組、256 槽、完整來源相等判斷與所有配置／失敗順序。沒有新增完整 key hash、配置或二路快取，也沒有改公理語意。此分支供主列車一般 merge，無須另開替代 PR。

## 唯一 current-state 矩陣

| 範圍 | 固定 SHA／狀態 | 結果與界線 |
|---|---|---|
| 原基底與原正式效能 | `2bbe54f19b2d19e8a816530f0c4edca950629a34` | R6 原 36 樣本保持：N64/main、N16/base 紅；原三個 compare stdout 差異仍在。沒有重抽樣或改判。 |
| 本次產品與測試來源 S | `1449d430d1c4734bb1bc3a9f91f3851c845cc0f3` | 已普通 push；產品只改 source.c 的 hint provider 混合，原 source-index 17 方法保留，新增 1 方法，registry 17→18。 |
| 證據 head E | `4d3ac4bf42f431c23833c8841e4a7a597d275dbd` | 本段 E 僅新增收據；受測來源仍是 S。 |
| 原 source-index 18 方法 | S；exit 0、0 skip | 66 編譯／連結全 0，51 原生執行；原 10 控制各相鄰 0/1/0、原 edge 整刀 21→31→21 均保持。 |
| 本次整刀撤回／恢復 | S；正常 0/1/0 | 三份真正編譯 source；完整身分／順序／guards 三態皆 0，交替來源工作計數 0→16→0，撤回精確 `ASSERT:provider-hint-cross-family-cache`。這是確定性工作量反證，不是 wall-time 通過。 |
| 本次身分控制 | S；兩項正常 exit 1 | 全寬 provider、middle-byte key 分別在精確具名斷言轉紅；不冒稱每個細控制各有獨立重編譯恢復。真正未對齊位址由 union 與 uintptr_t 斷言確認。 |
| 相關核心／產品原 runner | S；exit 0／0／0、0 skip | 原 native_sources 9、describe 7、context 8 全部通過，維持 NativeBuild、K/W/H、bridge 與原時限。 |
| 完整 native、6 browser、專項、架構、帳本 | 新列車 final 尚未完成 | 由主代理合流後依影響與原清單驗收；本切片不自行重產全量帳本。不把此處 18 項冒充完整 native。 |
| 正式效能 R7 與 required CI | R7 未跑；本 head 的 CI 未讀 | 正式效能必須在主列車新 final 以原門檻跑；歷史 train CI 的付款／額度啟動問題保留，不能推定本 head 的 CI 狀態，也不以本機結果代替。 |

## 根因與驗證

原 F 的純觀測在不改 K 回傳／順序的情況下，核對原 N64 loadfile 的 stdout 與非診斷 stderr 逐位元組相同、真 hint 鏡像與計數守恆。固定單一通用 provider 混合候選的命中由 626,713 增為 1,827,044；這是同一執行的 shadow 統計，並非另一份正式效能樣本。全 key 相等比較仍存在，沒有從命中率推論已達原 1.3 門檻。原 6-byte 取樣外稿未執行；來源／標籤更正與原稿一併封存。

公開 S81 已保留，S144 以一般後繼提交補強未對齊見證；所有正式 18 方法在 S144 重跑。原先 S81 的工具出版紀錄不移標。alignment 出版 R1 僅因 workspace 32 MiB 空間守門停下，未執行 Git；R2 將自己的 source/index/object/輸出放到 TMP，保留原空間門檻與原始失敗。

獨立對抗審查：產品／測試 70/0、233/0；來源出版 708/0、195/0；正式 18 方法與原子流程 1579/0；相關 24 方法與原子流程 2563/0；單包逐原件完整性 9904/0。完整收據保存原指令、環境、SHA、退出碼、stdout/stderr 與實際編譯輸入，明確區分原 bytes、原 Python 解碼文字與工具合併輸出轉錄。

尚不可標 READY-TO-MERGE：主列車 R7、完整 native／架構／帳本與 required CI 仍依上表。沒有新增待使用者拍板的公理或數值政策。
