# 交回

> 依 opus 審查與 ChatGPT 審查對 #297 的意見更正（2026-10-18）。更正處標「依 opus 審查更正」。
>
> **golden 已換成 oracle `60785906`（2026-10-18）：** 角材總數 3093 → 2957（淨少 136 支（極短料）），10 支主支改成貼住相鄰料，頂沿牆料的副支種類加 `:custom4`，64 個排法裡 24 個有變。下面凡是「現行」的數字都是這個 golden 的；「實跑結果摘要」是舊 golden（3093 支，`c2d218c2`）的實測，標明舊。

## 做了什麼

在 `geometry-core/framing-template/core-probe/` 新增探針，沒有改 oracle、核心、公理層、閱讀器或測試列車。

- `gen_scenes.py` 讀 `oracle/oracle-golden.json`。8 個房間 × 8 種排法裡，64 個都可施工，各產一個 `.scene`（`scenes/` 與 `index.json`）。
- 每支角材一個 `place`。沒有為了讓核心接受而改座標、縮短延伸段或改角色（唯一的角色改寫是下面「使用者拍板」那一項，它是角色宣告，不動座標）。
- **依 opus 審查更正：「矩形逐支相同，測試鎖住」這句原本講過頭。** 舊測試比的是產生器內部抄自 golden 的 rect，等於自己比自己。現在的範圍是：`scene_reader.py`（不 import `gen_scenes`）只讀場景檔文字，從錨（`at-face`／`at-line`）、截面寬、`between` 擋面獨立算出每支的 `[x0,y0,x1,y1]`，寬向與長度方向都和 golden 逐支比對。這份 golden 的 2957 支全部是 `between`，沒有 `through`，所以長度每支都推得出來。測試**沒有**涵蓋的是核心實際推導出的 L 與足跡，那要實跑，由 `parse_results.py` 的幾何等值檢查負責（見下）。
- 貼到外輪廓或孔、而且與該邊有正長度交集的料用 `at-face`。沒有貼邊的用 `at-line`，中線 = 寬向 lo + ⌊w/2⌋。
- 放置順序不是把全部邊界材機械地放在主支前面。依端面的全寬角材擋面做拓撲排序：不延伸的外輪廓 boundary → primary → 有延伸的 boundary → custom priority 3 → secondary（含改宣告 custom 4 的副支）。同階用 golden 原序。同階 boundary 的轉角互頂不建依賴。這份 golden 的環數是 0，沒有 `# probe-cycle`。
- **使用者拍板（2026-10-18，🔒，`決策佇列.md`「凹角沿牆料的排序」，#301）：** 端面頂到沿牆料（`rc_parallel:custom`，含 F1 與凹角牆線共線的併料）的副支，改宣告 `custom priority 4`，條文不改；沿牆料本身維持 custom 3。角色**直接讀 golden 的 `:custom4` 標籤**（`secondary:mark:custom4`、`secondary:seam:custom4`），現行 golden 共 63 支（F1 53、F2 10）。產生器另保留依實際擋面的獨立判定（`timber_stops`：端面座標相接、擋面角材在寬向蓋住整段，只拿 custom 3 當擋面），作為交叉核對：標籤與實際擋面不一致時，`build()` 回報 `disagreements`，`gen_scenes.py` 不寫出場景（結束碼 2），測試也紅。測試另用 `scene_reader` 從場景文字獨立算一次，所以是標籤、產生器判定、場景文字幾何三方互核。其餘副支仍是 secondary。`:custom4` 加在副支以外的種類上，產生器直接報錯。
- `mapping.md` 是種類對角色的對照，每列有條號，測試直接讀這張表當依據。
- `run_probe.sh` 給之後在 WSL 執行：編譯原生核心一次；整場通過就整場記接受；否則逐支前綴，被拒的不留在後面的前綴裡；被拒的保留條號與 stderr 原文。輸出在呼叫者給的目錄（預設 `/var/tmp/framing-core-probe`），不覆蓋 repo 裡的 `scenes/`。**依審查更正：** 拒絕只可能是結束碼 1（`current_geometry.c` 的 `main()` 只回 0 或 1），但 **1 也涵蓋參數錯、讀檔失敗、場景語法錯**，不一定是規則拒絕（ChatGPT 複審）。所以 rc=1 還要 stderr 第一行（去掉「路徑:行號:」）帶核心規則診斷才算「拒絕」，判定式 `V_[A-Z0-9_]+`、`[IRD]\d+` 加選用的字母或括號字母（`I25a`、`R6(d)`、`D7/I18`）、或「超過上限」。這是我對 `current_geometry.c` 與 `references.inc` 全部 `scene_error` 訊息字面的盤點：規則／驗證訊息都帶 `V_*` 違規碼（`V_CUT_PRIORITY`、`V_BOUNDARY_ROLE`、`V_PRIMARY_AXIS`、`V_EXTENSION`、`V_FREE_EDGE_END`、`V_GRID_LOCKED`、`V_DERIVED_TIMBER`）或條文編號，容量訊息是「…超過上限」；語法、參數、讀檔錯誤（「timber 行有多餘欄位」「不認得的指令」「無法開啟場景檔」…）都沒有這些記號。沒有記號的語意訊息（例如「這支角材不存在」）保守歸「錯誤」。其他非 0（139 崩潰、2、124 逾時…）與沒有規則診斷的 1 一律是「錯誤」，不計成拒絕，整體結束碼為 3。`run_probe.sh` 的 `rule_diag()` 用同一個判定式，計數與 `parse_results.py` 一致（有測試比對兩邊對同一批真實訊息的判斷）。每次呼叫核心加 `timeout`（預設 120 秒）。新增測試用環境變數 `CORE_BIN`、`PROBE_SCENES_DIR`、`PYTHON`、`CORE_TIMEOUT`、`TMPDIR`，平常不用設。
- `parse_results.py` 產出 `results.json` 與 `RESULTS.md`。整場失敗又沒有逐支前綴時，沒被點名的列是「同場未提交」。**依審查新增：**
  - 「錯誤」狀態（上一項）。
  - 「幾何不符」狀態：結束碼 0 還不夠。**接受列必須同時拿得到 `L=`、`角材原點：`、A0 接觸面 `vertex[i] =` 三項，缺任何一項都是「幾何不符（缺欄）」**，不是接受（ChatGPT 複審：先前只在欄位非空時才比，缺欄會被靜默接受）。三項齊全且有 oracle 矩形時：L 必須等於矩形長邊、原點必須是矩形的一個角、頂點外框必須等於矩形，對不上同樣標「幾何不符」，整體結束碼為 3。手寫探針場景沒有 oracle 矩形，欄位仍要齊全，但沒有東西可比（`geometry_checked` 為空）。
  - 每列記探測方式（原場景／省略後探測），`RESULTS.md` 開頭統計把「拒絕（容量）」與「拒絕（規則）」分開、原場景與省略後探測分開。
- `fixtures/`：#240 的四個探針場景（p3、p4、p8、p9）從 PR 留言複製成檔，解析測試改讀這裡，不再指向使用者的暫存區。內容只有輪廓座標與角色宣告，沒有路徑、帳號或其他資訊。
- `.gitattributes`：`scenes/*.scene`、`fixtures/*.scene`、`index.json` 固定 LF。這樣逐位元比對在 Windows `core.autocrlf=true` 的 checkout 也成立。
- `test_gen_scenes.py`：`python geometry-core/framing-template/core-probe/test_gen_scenes.py`，Ran 59 tests，OK（其中 10 項用 bash 假核心端到端跑 `run_probe.sh`，在負載下約 60 秒；沒有 bash 或設 `PROBE_SKIP_FAKE_CORE=1` 就跳過那 10 項，約 8 秒）。沒有編譯、沒有跑原生核心、沒有跑 oracle selftest、沒有用 WSL。假核心是一支 bash 腳本，回 139／2／逾時／1（規則診斷、容量、語法錯、讀檔失敗、無 stderr）／0（三項齊全、L 錯、缺欄）。
- `mutation_check.py`：`python geometry-core/framing-template/core-probe/mutation_check.py`。在暫存複本套一個突變、跑測試，確認每個突變都轉紅。見下面「突變檢查」。

## 實跑結果摘要

### 目前的 head `94eae4a3`（新 golden，2957 支）的實跑

來源：`94eae4a3068ec3a1df75c7a0122beeb03ed1e26a` 在 WSL 排他實跑，輸出在 `D:/geometry-axiom-work/core-probe-94eae4a3/run/`（`summary.txt`、`RESULTS.md`、`results.json`），核心建置 rc=0，`parse_rc=0`，`total_core_errors=0`。

| 狀態 | 支數 | 探測方式 |
|---|---|---|
| 接受 | 2639 | 原場景 2639 |
| 拒絕（容量） | 318 | 原場景 8、省略後探測 310 |
| 拒絕（規則） | 0 | — |
| 錯誤 | 0 | — |
| 幾何不符 | 0 | — |
| 合計 | 2957 | 64 個排法 |

- 56 個排法整場接受；有拒絕的是 F1 客廳的 8 個排法，訊息全是「角材的數量超過上限」。每個排法被擋的支數是 95−64=31、97−64=33、96−64=32、98−64=34、108−64=44、116−64=52、109−64=45、111−64=47（f1-00 到 f1-07），合計 318。容量拒絕不是放置規則，是核心一個世界只收 64 支。「原場景 8」是每個排法第一支超出的那一支，其餘 310 支是逐支前綴裡的探測。
- **這次實測與上一輪的推算完全相符**（830 − 8×64 = 318）。
- 24 支舊的 I19 規則拒絕消失，規則拒絕歸零。**但要老實講範圍：** 改宣告 custom 4 的 63 支裡，F1 的 53 支全部被容量擋在第 65 支之後，核心根本沒評估它們；真正被核心評估並接受的 custom 4 只有 F2 的 10 支。所以「custom 4 頂 custom 3 被核心接受」目前只有 F2 這 10 支的證據，F1 的 53 支要等容量放大後才知道。
- 接受的 2639 支都有 L、角材原點、A0 接觸面頂點三項輸出，三項都和 oracle 矩形對上（`geometry_checked` 全是 `L／足跡／原點`），沒有一支「幾何不符」。這是工具本身的等值檢查第一次對真實輸出跑，stdout 格式與假設相符。
- 孔邊上暫寫 secondary 的 32 支全部接受；沿牆料 custom 3 的 24 支全部接受。
- 這次跑的是**修正 1、2 之前**的 `parse_results.py`／`run_probe.sh`：當時 rc=1 一律算拒絕，缺欄位的接受列不擋。這次實跑沒有任何語法／讀檔錯誤、也沒有缺欄，所以結果不受影響，但**修完之後會再重跑一次，以新分類為準**（rc=1 要 stderr 帶規則診斷才算拒絕；接受列必須同時有 L、原點、A0 頂點）。
- 外層腳本呼叫 `parse_results.py` 時漏給 `--run-dir`（`launcher.log` 末尾的 usage 訊息）不影響結果：`run_probe.sh` 自己已經彙整過，`parse_rc=0`。

### 歷史：舊 golden 的實跑（`c2d218c2`）

來源：頭版本 `c2d218c2` 在 WSL 排他實跑（`wsl_locked3`，核心建置 rc=0）。**這次實跑在改宣告 custom 4、結束碼分類、幾何等值檢查與換 golden 之前**，所以下面的數字描述的是舊場景（舊 golden，3093 支），且當時的 `parse_results.py` 沒有分「原場景」與「省略後探測」。

- 舊 golden：64 個排法、3093 支角材。接受 2707 支，拒絕 386 支。**這 386 支是兩種不同的原因，不能合計：**
  - **容量拒絕 362 支。** 訊息全是「角材的數量超過上限」（`WORLD_MAX_TIMBERS` = 64）。F1 客廳每個排法 108–116 支，核心一個世界只裝得下 64 支，第 65 支起一律被拒。這是在讀到 `timber` 宣告那一行就擋下，根本沒進放置規則。被擋的 362 支全是副支。
  - **規則拒絕 24 支，全是 I19。** 副支（核心優先級 3）的端面頂到 `rc_parallel:custom`（探針暫定優先級 3）的側面，3 對 3 被拒。F1 14 支、F2 10 支。
- **容量遮住了約 40 支本來會因 I19 被拒的副支（推算，不是實測）。** 依產生器自己的擋面推算，副支頂到 custom 側面在 F1 八個排法都有，共 54 支，實跑只看到其中 14 支，其餘約 40 支被容量遮住（在看得到結果的 24 支上，推算 24/24 命中）。F2 實見 10 支。合計 I19 拒絕至少約 64 支，不是 24 支；「只出現在 F1 左下、右下兩個排法」是截斷造成的假象。舊 golden 上產生器的實際擋面判定也數到 64 支（F1 54、F2 10），與推算吻合。容量放大後要實跑確認。
- 50 個排法全數接受；有拒絕的是 F1 客廳 8 個排法和 F2 主臥 6 個排法。
- **依 opus 審查更正：孔邊 `rc_parallel` 32 支全部接受。** 原先預期長度伸出孔邊會被 I22 拒絕，那是錯讀：核心的延伸段只看外輪廓邊，D16 也一樣（延伸段是超出外輪廓 FIXED 邊端點的部分）。
- opus 審查手動核過接受的 2707 支：足跡與長度都和 golden 逐值相同，場景轉換是忠實的。那是當時的一次性人工核對；工具本身的等值檢查在 `94eae4a3` 那次實跑才第一次對真實輸出跑（見上）。
- 舊的 362 是 376 − 14：F1 八個排法合計 888 支，每個排法收 64 支得 376，當時有 14 支先被 I19 拒絕，騰出 14 個名額。

## 跳過了什麼

64/64 可施工，`conflict_codes` 都是空的，跳過清單是空的。程式仍會跳過 `buildable` 為假，或 `conflict_codes` 非空的排法。合成小 golden 的測試蓋到這兩種，證明跳過不是死碼。

F1 客廳八個排法的支數是 95、97、96、98、108、116、109、111（舊 golden 是 108、116、109、111、108、116、109、111），全部寫出，沒有為了 64 支上限抽料；八個都超過 64，場景標了 `# probe-capacity`。F2 主臥最多 62 支。讀 `current_geometry.c` 的 `WORLD_MAX_TIMBERS`（64）與錯誤字串「角材的數量超過上限」，並已由實跑證實（見上）。

孔邊上、golden 種類仍是 `boundary` 的 32 支（整條 24、被主支截短 8；舊 golden 是 40 支，整條 24、截短 16，少的 8 支是極短料）暫寫 `secondary`，`pending` 為 `hole-perpendicular`。

## 待裁定

見 `mapping.md` 的「待 Claude 裁定」。這裡不重做選擇。

1. 孔邊上種類仍是 `boundary` 的料：`secondary`（I21 孔邊可為 secondary、D17 垂直主支軸、R18 孔邊不算 onBoundary；oracle 建構註解稱柱面料為 secondary）對 `custom`（D15 沒有軸向義務）。`boundary` 與 `primary` 兩種已由 I20、I21 排除，不是待選項。
2. **（依 opus 審查更正，且已於 2026-10-18 拍板）** 原先寫成「`rc_parallel:custom` 的 priority 寫 3，沒有條文說只能是 3」，問錯了問題。取 3、4、5 都一樣被拒：副支（優先級 3）的端面頂 custom 側面，I19 要擋面優先級嚴格小於 3，custom 取 3、4、5 都不成立；而 custom 自己的端面要頂延伸段（按優先級 2 計）則要 N ≥ 3。整數無解的前提是副支必須是 secondary（優先級 3）。拍板結果是改宣告頂它的副支為 custom 4，沿牆料維持 3，條文不改。

## 最不確定的 3 件事

1. 孔邊垂直料的角色。場景暫用 secondary，沒有另做一份 custom 場景，所以這次探針量不到 custom 方案。若裁定是 custom，要重出這 32 支再跑。
2. 核心接受只表示這支 `place` 過了當下的不變量。D7 不寫長度，錨點是引用，所以長度與足跡要靠 `parse_results.py` 把核心輸出的 `L=`、原點、A0 頂點和 oracle 矩形逐支比對。它在 `94eae4a3` 的實跑上對 2639 支接受列跑過，全部相符，stdout 格式的假設（`角材原點：(x, y, z)`、`角材 N 的 A0（接觸面）：` 後四個 `vertex[i]`）成立；另假設承載面原點在 (0,0)、u = +x、v = +y（本探針所有場景如此）。F1 的 318 支被容量擋住，沒有核心輸出可比，所以這個檢查對那 318 支沒有證據。
3. B=33 與承載面 `origin 0 0 2500` 不在 golden。沿用既有天花場景。golden 沒有第三維，場景也沒有寫 `column`。

另外：golden 每換一次，要重新產生一次 `scenes/` 與 `index.json`（`python gen_scenes.py`），測試會逐位元比對，沒重產就會紅。現在的 64 個場景依 oracle `60785906` 的 golden 產生（已極短料、主支貼住相鄰料）。golden 的 `:custom4` 標籤若與實際擋面不一致，`gen_scenes.py` 會拒絕產生。

## 突變檢查

`python mutation_check.py` 把 core-probe 與 oracle-golden.json 複製到暫存目錄，每次套一個突變、跑 `test_gen_scenes.py`。對照組（不突變）綠燈，每個突變都轉紅。

| 突變 | 轉紅的主要測試 |
|---|---|
| m1 custom priority 3→4 | `test_declared_roles_and_priorities_follow_mapping_md`、`test_committed_artifacts_are_bit_identical_to_regeneration` |
| m2 格線中線 +1 mm | `test_member_rects_match_oracle`、`test_place_matches_comment_rect` 等 |
| m3 孔邊料改成 primary | `test_declared_roles_and_priorities_follow_mapping_md`、逐位元比對 |
| m4 拓撲排序 min→max | `test_placement_follows_tier_then_oracle_order`、逐位元比對 |
| m5a 刪 `scenes/f1-00.scene` | 逐位元比對、`test_committed_scenes_cover_every_buildable_layout`、`test_footprints_recomputed_from_scene_text_match_golden` |
| m5b 改動 `scenes/f2-00.scene` 一個字元 | 逐位元比對 |
| m5c `index.json` 過期 | 逐位元比對 |
| m5d `scenes/` 多出一個檔 | 逐位元比對、`test_committed_scenes_cover_every_buildable_layout` |
| m6 跨距一律退成 `through`（舊測試看不到） | 足跡重算、擋面、順序等多項 |
| m7 擋面角材指錯一支 | `setUpClass`（場景文字推不出足跡）、`test_member_rects_match_oracle` 等 |
| m8 任何非 0 結束碼都算拒絕 | 結束碼分類、`test_rc1_with_a_rule_diagnostic_is_a_rejection` 等 31 項失敗 |
| m9 不比對核心 L 與 oracle 長邊 | `test_legal_but_wrong_length_is_not_accepted` 等 |
| m10 `run_probe.sh` 把任何非 0 計成拒絕 | `test_segfault_139_is_an_error_and_the_run_fails`、`test_rc1_with_a_parse_error_is_an_error_not_a_rejection`（假核心） |
| m11 `parse_results.main` 有錯誤列也回 0 | 結束碼測試 |
| m12 產生器忽略 golden 的 `:custom4` 標籤 | 角色測試、`test_generator_cross_check_reports_no_disagreement`、逐位元比對等 7 項 |
| m13 所有副支都升格 custom 4 | 角色測試、交叉核對、逐位元比對等 6 項 |
| m14 關掉標籤與實際擋面的交叉核對 | `test_missing_custom4_label_is_detected`、`test_custom4_label_without_a_custom_stop_face_is_detected`、`test_cli_refuses_to_write_scenes_when_labels_disagree` |
| m15 升格後優先級寫 5 | 角色測試、順序測試、逐位元比對 |
| m16 golden 少標一個 `:custom4` | `test_golden_custom4_labels_agree_with_actual_stop_faces`、`test_generator_cross_check_reports_no_disagreement`、逐位元比對等 |
| m17 golden 多標一個 `:custom4`（該支沒有頂到 custom） | 同 m16 |
| m18 結束碼 1 一律算規則拒絕，不看 stderr | `test_rc1_with_a_parse_or_usage_error_is_an_error_not_a_rejection`、`test_whole_scene_rc1_parse_error_without_prefix_is_error`、`test_parse_run_exit_code_is_nonzero_for_core_errors`（11 項失敗） |
| m19 接受列缺 L／原點／A0 頂點也靜默接受 | `test_accepted_rows_must_have_length_origin_and_footprint`（只有 L、缺原點、缺 A0 三種各一） |
| m20 沒有 oracle 矩形的接受列缺欄也接受 | `test_missing_fields_are_also_rejected_without_an_oracle_rect` |
| m21 `run_probe.sh` 把結束碼 1 一律計成拒絕 | `test_rc1_with_a_parse_error_is_an_error_not_a_rejection`（假核心，`rejected=0 errors=1` 對不上） |
| m22 `run_probe.sh` 的判定式漏掉 D 編號 | `test_shell_and_python_rule_predicates_agree` |
| m23 `parse_results` 的判定式漏掉 D 編號 | `test_rc1_with_a_rule_diagnostic_is_a_rejection` |

**這一輪（rc=1 分類、缺欄）新增或改寫的 m8、m10、m18 到 m23 都在最後一版程式上重跑過，全部轉紅；對照組 59 個測試全綠。** m1 到 m7、m9、m11 到 m17 最後一次完整跑是在上一個 head（`94eae4a3`，20 個突變全紅）。使用者要開遊戲，協調者通知停跑多行程測試，所以這些沒有在最後一版再跑一次；它們的目標程式碼這一輪沒有動，只有 m9 與 m11 的測試輸入改成三項齊全的核心輸出，保險起見等通知後再整組重跑。

一個要老實講的地方：m4（拓撲排序取 min→max）**不會**被「每支料的擋面都先放」這一條抓到，因為取 max 仍然是合法的拓撲序，擋面還是都在前面。抓到它的是「每一步放下的那支，必須是擋面都已放置的未放角材裡 (階, golden 序號) 最小的」這一條。兩條都在測試裡。

## 1 mm 突變

`build(delta=1)` 把第一個可施工排法的第 0 支 x0、x1 都加 1。測試用 `assertRaises` 接住，所以套件仍是綠的。不接住時，因為第 0 支的端面不再與邊或相鄰料對齊，產生器改用 `through`，場景文字推不出長度，檢查器列出 `長度無法由場景文字推出` 與 `oracle [0, 0, 5000, 27] … 場景文字沒有算出這個矩形`，共 188 筆不符（第 0 支、所有以它為擋面而退成 through 的料，以及對不上的 golden 矩形）。提交版的 `delta` 預設是不偏移。

## 實跑前該知道的限制

- 逐支前綴會拿掉先前被拒的料。後面的擋面因此和整場一次放不同。`results.json` 的 `omitted` 記下那些被拿掉的編號，每列的 `mode` 標「原場景」或「省略後探測」，`RESULTS.md` 開頭的統計分開寫。
- 32 支孔邊 `rc_parallel` 的長度伸出孔邊，仍用 `at-face`，沒有改成 `at-line`，也沒有縮短。**依 opus 審查更正：** 原先寫「預期觸發 I22（V_EXTENSION）」，實跑 32 支全部接受，核心的延伸段只看外輪廓邊。
- 4 支 `rc_parallel:custom`（F1 右上／右下板長沿 Y，以及左下／右下板長沿 X，golden 編號 14）與凹角牆線共線，但和該邊沒有正長度交集，整段落在另一肢。R6(c) 的 at-face 要求與引用邊重疊，所以這 4 支用 `at-line`。矩形沒有改。其餘 20 支 custom 貼外輪廓，用 `at-face`。
- `git check-ignore -v` 對 `gen_scenes.py`、`scene_reader.py`、`scenes/f1-00.scene`、`fixtures/*.scene`、`index.json`、`run_probe.sh`、`mapping.md`、`parse_results.py`、`test_gen_scenes.py`、`mutation_check.py`、`.gitattributes` 沒有輸出，這些路徑沒有被忽略。沒有改 `.gitignore`。
- 原生核心在本次修正前實跑過一次（見「實跑結果摘要」），本次修正後尚未重跑。`run_probe.sh` 沒有在 WSL 上執行過新版；新版只用 bash 假核心在 Git Bash 驗過分類與結束碼。
