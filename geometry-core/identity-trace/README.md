# K3 識別與追溯：採納紀錄

本目錄保存 K3 r5 的提案與五輪審查來歷。行為驗收仍以 `公理層.md` 為準；提案中的「尚未寫入」「不改 repo」及 scratchpad 路徑是起草時紀錄，不是現在的狀態或執行指令。條文已依 2026-10-09 決策 K／授權 L 採納，**核心、宿主、保存與介面尚未實作**。

基底：P-049 澄清版 PR #199，head `7ad9cef15b0813ed214cb342d67f475820f2cbc3`，AXIOM_REVISION `209a7278d3acadfe89374714e821018dcba10adc`。前置整理基準是舊 K2a `0745cab5853b11386df1c27caf525a59167d96c2`；本次重新核對全部錨點及介面，依內容定位，不沿用過期行號。

## 配號與逐條差異

| 佔位 | 正式條號 |
|---|---|
| D⟨K3-1⟩ | D59 |
| D⟨K3-2⟩ | D60 |
| D⟨K3-3⟩ | D61 |
| D⟨K3-4⟩ | D62 |
| I⟨K3-1⟩ | I70 |
| I⟨K3-2⟩ | I71 |
| I⟨K3-3⟩ | I72 |
| R⟨K3-1⟩ | R56 |
| R⟨K3-2⟩ | R57 |
| R⟨K3-3⟩ | R58 |

| Δ | 條目 | 改動 |
|---|---|---|
| A0 | 檔頭 | 授權、配號及尚未實作說明 |
| A1 | D59–D62 | 七種身分鍵、存在期、區段配號、外部身分引用 |
| A2 | I70–I72 | 完整性、啟用守門、保存與去身分輸出 |
| A3 | R56–R58 | 提交結算、五態比對、外部觀察值採用 |
| B1 | D9 | 記號非定義但屬 World，跟隨保存與復原 |
| B2 | D25 | 交換包來源與快照不帶身分帳 |
| B3 | I8 | 指令提交結算及群組失敗回滾 |
| B4 | I8a | 兩處補啟用使預覽過期，確認重比身分 |
| B5 | I32 | 能力另行宣告；不宣稱尚未實作的支援 |
| B6 | I39 | 完整專案保留、參數包新配 |
| B7 | R4 | 全部定義與 canvas-pos 後輸出記號 |
| B8 | §四 | 首版以外型別與沿革等未定案 |
| 回填 | D54(f)、I66(f) | 依 K2b C20 恢復存在期記號類及匯入規則 |

B1 接在 K1 的 D50 段後；B5 接在 K2b 能力段後；B6 接在 K2b 的 D54 分類句後；B7 接在 PF-0 dump 段後。記號位於**全部**定義與 canvas-pos 之後，自然也在 PF-0 定義之後，無須改提案字句。除 D60 的「R8 拆出的新片……」續行增加兩格縮排外，所有 A／B 條文僅替換佔位條號；縮排用來避免閱讀器將續行誤認為第二條 R8，不改字詞或語意。D54(f)、I66(f) 依 K2b 原文回填。未改閱讀器 parser 或測試期望。

## 相容性核對

- PF-0 的衍生承載面仍是 placement 鍵；K1 D46 專案層設定和 K3 World 身分帳分屬不同資料，幾何與內容指紋不變。D48 的餘料 key 政策未改。
- D34／D58 依實例與配置鍵識別組構分件，仍不以角材 id 判身分，所以維持 K3 首版排除。D54 未列舉身分的拒絕規則不變。
- D51 的專案整份替換是一筆專案交易；D61／R56 的「不是提交」限身分結算：直接還原載入帳、不拿新提交規則重發記號。復原／重做同理還原原帳；R54 仍執行草稿掃描，I68 的窗內整筆還原與窗外保留旗標均不變。
- P-049 的 I64 純 D12 位置例外不受影響；I8a 的 K3 啟用過期是明示新規則。I66 的 (d) 名稱與共用例外原文保留，新增 (f) 不涵蓋 spec 記號。
- 其餘前置整理列出的既有引用條款逐條核對；不存在條號衝突或需自行改案的語意衝突。共改既有 9 條、新增 10 條，其餘既有 182 條保持不動。

## 版本與能力

- 條文 commit / AXIOM_REVISION：`d73d56fac2f69c7d97341c7f35880d163b672df7`。
- AXIOM_SHA256（LF 正規化）：`6a05255820f5758e9cc9d21b2d7d1051f254d1572c20903451cd142a5fdf89a1`。
- PRE_IDENTITY_TRACE_AXIOM_VERSIONS：`(209a7278d3acadfe89374714e821018dcba10adc, 5ccbbc0cd512acd60412427794cf16baf36af4e1ceed40730fb8144697f8ac1d)`。加入接受集合與六處既有豁免（含 section-profile），保留全部舊集合。
- 不新增任何執行器 capability；`identity-ledger/1` 仍未實作。實作依序 K3-L → K3-48 → K3-44，無新可見 UI 入口。

## 保存的來源

僅複製頂層 PROPOSAL.md、AXIOM-DIFF.md、decisions-provisional.md 與五份 review*.md，逐位元保存；r0/r2/r3/r4/src 等中間目錄未收入。AXIOM-DIFF 檔頭仍標 r4，r5 審查明定條文逐位元不變；實作段以 PROPOSAL 與 decisions 的 r5 修訂優先。

| 檔案 | 來源 SHA-256 |
|---|---|
| `AXIOM-DIFF.md` | `6fa83381a2c1beed942135f2d3fccf5f75e6a387df60736bf70a43fad0eacb83` |
| `decisions-provisional.md` | `1918d83d738d5f39cf2768725a86dcfacd7bc3f6e15308a3b81545dd3f66a7b8` |
| `PROPOSAL.md` | `c4226c5b885660a9c44621b2ffc45288804c45e813047081ce1cca42dda771a8` |
| `review-findings-main.md` | `600b43e47d8a6b553c956fc46730f66746b4fb518966cba5f69f12f40505974b` |
| `review-round2-findings.md` | `f577e81e9e664f1b252d0734b7550846dd19bbf340f6ab861aedc0ccac552522` |
| `review-round3-findings.md` | `4b4510532f5422aa67ee549f2266340b8bddc3ad147fcbcb2a08f0c1495938cf` |
| `review-round4-findings.md` | `fef5b7af8946901275df91fc578c9962731790f5242ac27e6e6099ffb62ca098` |
| `review-round5-findings.md` | `b060a273865ce79d33d7297979294d8dc61cc686eca9c86a182cc7b4f939d56f` |

## 驗證

- 正典同步、`--check` 均通過：201 條、836 blocks、5 筆批註、31 張見證圖、63 組例圖；五道 assert 與獨立 SSOT 核對通過。重建套用 84 patches；`--check` 不執行重建，因此 patches 為 0。
- `python tests/test_axiom_reader.py`：41/41 通過（820.994 秒），包含位元組冪等、批註保留及補丁／資料一致性。只有既有 DeprecationWarning／ResourceWarning。
- 條號與範圍：201 條唯一、零懸空引用；新增 10 條、既有 9 條修改、182 條原文不變；白話 201/201 覆蓋。A0–A3／B1–B8 獨立逐字比對提案，除配號與已記錄的 D60 縮排外相同；八份來源檔逐位元相同。
- 排版修正的突變：移除 D60 的兩格縮排後，解析器拒絕重複 R8；還原後 201 條通過。parser 和既有測試均未修改。
- `python -B -m unittest tests.test_modeling_runtime.AxiomSourceIdentity`：3/3 通過。D59 與 R56 各改一字分別觸發 AXIOM_VERSION；逐次還原後 3/3 回綠，沒有 BASE_COMPILER 遮蔽。
- 相容集合探針：目前／澄清版／K2a／K2b／K1／PF-0 通過版本閘；未知與七個已撤回的中間版本被 AXIOM_VERSION 拒絕。移除新增集合、分別移除六處豁免，共七個突變均在對應版本閘拒絕；還原後恢復。探針刻意用錯誤 generator 停在 PACKAGE_SCHEMA，證明版本閘已通過，不冒充原生求值驗收。
- 受保護行：以 K2a head `49c391f2afbcee17bb2647fce74c3c5532a01527` 為基準，決策佇列 74 行、BACKLOG 46 行內容與順序全保留，並再次對照澄清版基底。兩檔各做改字／刪除／調序突變，共六案均被檢查器拒絕；實際檔案未受突變影響。
- WSL 全量由整合者另跑；本次未執行原生建置、K3 功能流程或桌面／手機操作驗收。無新可見 UI 入口。

最需後續核對：本 PR 不實作身分帳，尚無 K3 原生流程驗收。提案 §9.2-10 的恢復時再讀完整 dump 屬後續 K3-L 實作議題，採納條文本身不指定該呼叫次數。
