# 交回

> 依 opus 審查與 ChatGPT 審查對 #297 的意見更正（2026-10-18）。更正處標「依 opus 審查更正」。

## 做了什麼

在 `geometry-core/framing-template/core-probe/` 新增探針，沒有改 oracle、核心、公理層、閱讀器或測試列車。

- `gen_scenes.py` 讀 `oracle/oracle-golden.json`。8 個房間 × 8 種排法裡，64 個都可施工，各產一個 `.scene`（`scenes/` 與 `index.json`）。
- 每支角材一個 `place`。沒有為了讓核心接受而改座標、縮短延伸段或改角色（唯一的角色改寫是下面「使用者拍板」那一項，它是角色宣告，不動座標）。
- **依 opus 審查更正：「矩形逐支相同，測試鎖住」這句原本講過頭。** 舊測試比的是產生器內部抄自 golden 的 rect，等於自己比自己。現在的範圍是：`scene_reader.py`（不 import `gen_scenes`）只讀場景檔文字，從錨（`at-face`／`at-line`）、截面寬、`between` 擋面獨立算出每支的 `[x0,y0,x1,y1]`，寬向與長度方向都和 golden 逐支比對。這份 golden 的 3093 支全部是 `between`，沒有 `through`，所以長度每支都推得出來。測試**沒有**涵蓋的是核心實際推導出的 L 與足跡，那要實跑，由 `parse_results.py` 的幾何等值檢查負責（見下）。
- 貼到外輪廓或孔、而且與該邊有正長度交集的料用 `at-face`。沒有貼邊的用 `at-line`，中線 = 寬向 lo + ⌊w/2⌋。
- 放置順序不是把全部邊界材機械地放在主支前面。依端面的全寬角材擋面做拓撲排序：不延伸的外輪廓 boundary → primary → 有延伸的 boundary → custom priority 3 → secondary（含改宣告 custom 4 的副支）。同階用 golden 原序。同階 boundary 的轉角互頂不建依賴。這份 golden 的環數是 0，沒有 `# probe-cycle`。
- **使用者拍板（2026-10-18，🔒，`決策佇列.md`「凹角沿牆料的排序」，#301）：** 端面頂到沿牆料（`rc_parallel:custom`，含 F1 與凹角牆線共線的併料）的副支，改宣告 `custom priority 4`，條文不改；沿牆料本身維持 custom 3。判定依產生器的實際擋面（`timber_stops`），不看 kind 字串。現行 golden 共 64 支（F1 54、F2 10）。其餘副支仍是 secondary。
- `mapping.md` 是種類對角色的對照，每列有條號，測試直接讀這張表當依據。
- `run_probe.sh` 給之後在 WSL 執行：編譯原生核心一次；整場通過就整場記接受；否則逐支前綴，被拒的不留在後面的前綴裡；被拒的保留條號與 stderr 原文。輸出在呼叫者給的目錄（預設 `/var/tmp/framing-core-probe`），不覆蓋 repo 裡的 `scenes/`。**依審查更正：** 結束碼只有 1（`current_geometry.c` 的 `main()` 唯一的拒絕碼；它只回 0 或 1）算規則拒絕。其他非 0（139 崩潰、2、124 逾時…）一律是「錯誤」，不計成拒絕，整體結束碼為 3。每次呼叫核心加 `timeout`（預設 120 秒）。新增測試用環境變數 `CORE_BIN`、`PROBE_SCENES_DIR`、`PYTHON`、`CORE_TIMEOUT`、`TMPDIR`，平常不用設。
- `parse_results.py` 產出 `results.json` 與 `RESULTS.md`。整場失敗又沒有逐支前綴時，沒被點名的列是「同場未提交」。**依審查新增：**
  - 「錯誤」狀態（上一項）。
  - 「幾何不符」狀態：結束碼 0 還不夠，有 oracle 矩形的列，核心輸出的 `L=` 必須等於矩形長邊；stdout 有印 `角材原點：` 與 A0 接觸面 `vertex[i] =` 時，原點必須是矩形的一個角、頂點外框必須等於矩形。對不上不得標「接受」，整體結束碼為 3。
  - 每列記探測方式（原場景／省略後探測），`RESULTS.md` 開頭統計把「拒絕（容量）」與「拒絕（規則）」分開、原場景與省略後探測分開。
- `fixtures/`：#240 的四個探針場景（p3、p4、p8、p9）從 PR 留言複製成檔，解析測試改讀這裡，不再指向使用者的暫存區。內容只有輪廓座標與角色宣告，沒有路徑、帳號或其他資訊。
- `.gitattributes`：`scenes/*.scene`、`fixtures/*.scene`、`index.json` 固定 LF。這樣逐位元比對在 Windows `core.autocrlf=true` 的 checkout 也成立。
- `test_gen_scenes.py`：`python geometry-core/framing-template/core-probe/test_gen_scenes.py`，Ran 43 tests，OK，約 22 秒（其中 6 項用 bash 假核心端到端跑 `run_probe.sh`，約 14 秒；沒有 bash 或設 `PROBE_SKIP_FAKE_CORE=1` 就跳過）。沒有編譯、沒有跑原生核心、沒有跑 oracle selftest、沒有用 WSL。假核心是一支 bash 腳本，只回 139／2／逾時／1／0。
- `mutation_check.py`：`python geometry-core/framing-template/core-probe/mutation_check.py`。在暫存複本套一個突變、跑測試，確認每個突變都轉紅。見下面「突變檢查」。

## 實跑結果摘要

來源：頭版本 `c2d218c2` 在 WSL 排他實跑（`wsl_locked3`，核心建置 rc=0）。**這次實跑在本次修正（改宣告 custom 4、結束碼分類、幾何等值檢查）之前**，所以下面的數字描述的是舊場景，且當時的 `parse_results.py` 沒有分「原場景」與「省略後探測」。

- 64 個排法、3093 支角材。接受 2707 支，拒絕 386 支。**這 386 支是兩種不同的原因，不能合計：**
  - **容量拒絕 362 支。** 訊息全是「角材的數量超過上限」（`WORLD_MAX_TIMBERS` = 64）。F1 客廳每個排法 108–116 支，核心一個世界只裝得下 64 支，第 65 支起一律被拒。這是在讀到 `timber` 宣告那一行就擋下，根本沒進放置規則。被擋的 362 支全是副支。
  - **規則拒絕 24 支，全是 I19。** 副支（核心優先級 3）的端面頂到 `rc_parallel:custom`（探針暫定優先級 3）的側面，3 對 3 被拒。F1 14 支、F2 10 支。
- **容量遮住了約 40 支本來會因 I19 被拒的副支（推算，不是實測）。** 依產生器自己的擋面推算，副支頂到 custom 側面在 F1 八個排法都有，共 54 支，實跑只看到其中 14 支，其餘約 40 支被容量遮住（在看得到結果的 24 支上，推算 24/24 命中）。F2 實見 10 支。合計 I19 拒絕至少約 64 支，不是 24 支；「只出現在 F1 左下、右下兩個排法」是截斷造成的假象。本次產生器的實際擋面判定也數到 64 支（F1 54、F2 10），與推算吻合。容量放大後要實跑確認。
- 50 個排法全數接受；有拒絕的是 F1 客廳 8 個排法和 F2 主臥 6 個排法。
- **依 opus 審查更正：孔邊 `rc_parallel` 32 支全部接受。** 原先預期長度伸出孔邊會被 I22 拒絕，那是錯讀：核心的延伸段只看外輪廓邊，D16 也一樣（延伸段是超出外輪廓 FIXED 邊端點的部分）。
- opus 審查手動核過接受的 2707 支：足跡與長度都和 golden 逐值相同，場景轉換是忠實的。那是一次性的人工核對；工具本身的等值檢查是這次才加的，還沒對真實輸出跑過。
- 本次修正後預期：改宣告 custom 4 的 64 支副支不再因 I19 被拒（24 支規則拒絕消失）；容量拒絕不變（還是 362 支，需要核心放寬或換拆法才會變）。要實跑才算數。

## 跳過了什麼

64/64 可施工，`conflict_codes` 都是空的，跳過清單是空的。程式仍會跳過 `buildable` 為假，或 `conflict_codes` 非空的排法。合成小 golden 的測試蓋到這兩種，證明跳過不是死碼。

F1 客廳八個排法的支數是 108、116、109、111、108、116、109、111，全部寫出，沒有為了 64 支上限抽料。場景標了 `# probe-capacity`。讀 `current_geometry.c` 的 `WORLD_MAX_TIMBERS`（64）與錯誤字串「角材的數量超過上限」，並已由實跑證實（見上）。

孔邊上、golden 種類仍是 `boundary` 的 40 支（整條 24、被主支截短 16）暫寫 `secondary`，`pending` 為 `hole-perpendicular`。

## 待裁定

見 `mapping.md` 的「待 Claude 裁定」。這裡不重做選擇。

1. 孔邊上種類仍是 `boundary` 的料：`secondary`（I21 孔邊可為 secondary、D17 垂直主支軸、R18 孔邊不算 onBoundary；oracle 建構註解稱柱面料為 secondary）對 `custom`（D15 沒有軸向義務）。`boundary` 與 `primary` 兩種已由 I20、I21 排除，不是待選項。
2. **（依 opus 審查更正，且已於 2026-10-18 拍板）** 原先寫成「`rc_parallel:custom` 的 priority 寫 3，沒有條文說只能是 3」，問錯了問題。取 3、4、5 都一樣被拒：副支（優先級 3）的端面頂 custom 側面，I19 要擋面優先級嚴格小於 3，custom 取 3、4、5 都不成立；而 custom 自己的端面要頂延伸段（按優先級 2 計）則要 N ≥ 3。整數無解的前提是副支必須是 secondary（優先級 3）。拍板結果是改宣告頂它的副支為 custom 4，沿牆料維持 3，條文不改。

## 最不確定的 3 件事

1. 孔邊垂直料的角色。場景暫用 secondary，沒有另做一份 custom 場景，所以這次探針量不到 custom 方案。若裁定是 custom，要重出這 40 支再跑。
2. 核心接受只表示這支 `place` 過了當下的不變量。D7 不寫長度，錨點是引用，所以長度與足跡要靠 `parse_results.py` 把核心輸出的 `L=`、原點、A0 頂點和 oracle 矩形逐支比對，這是本次才加的，還沒對真實輸出跑過。它假設 stdout 的格式與 2026-10-17 實跑相同（`角材原點：(x, y, z)`、`角材 N 的 A0（接觸面）：` 後四個 `vertex[i]`），並假設承載面原點在 (0,0)、u = +x、v = +y（本探針所有場景如此）。
3. B=33 與承載面 `origin 0 0 2500` 不在 golden。沿用既有天花場景。golden 沒有第三維，場景也沒有寫 `column`。

另外：oracle 那邊正在修極短副支（1–23 mm 的副支會被拿掉、主支會貼住相鄰料），golden 之後會變。現在的 64 個場景依現行 golden 產生；golden 更新後要重新產生一次 `scenes/` 與 `index.json`（`python gen_scenes.py`），測試會逐位元比對，沒重產就會紅。

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
| m8 任何非 0 結束碼都算拒絕 | 結束碼分類四項 |
| m9 不比對核心 L 與 oracle 長邊 | `test_legal_but_wrong_length_is_not_accepted` 等 |
| m10 `run_probe.sh` 把任何非 0 計成拒絕 | `test_segfault_139_is_an_error_and_the_run_fails`（假核心） |
| m11 `parse_results.main` 有錯誤列也回 0 | 結束碼測試 |
| m12 不升格（副支仍寫 secondary） | 角色測試、逐位元比對 |
| m13 所有副支都升格 | 角色測試、逐位元比對 |
| m14 只看 kind 字串升格 | 角色測試、逐位元比對 |
| m15 升格後優先級寫 5 | 角色測試、逐位元比對 |

一個要老實講的地方：m4（拓撲排序取 min→max）**不會**被「每支料的擋面都先放」這一條抓到，因為取 max 仍然是合法的拓撲序，擋面還是都在前面。抓到它的是「每一步放下的那支，必須是擋面都已放置的未放角材裡 (階, golden 序號) 最小的」這一條。兩條都在測試裡。

## 1 mm 突變

`build(delta=1)` 把第一個可施工排法的第 0 支 x0、x1 都加 1。測試用 `assertRaises` 接住，所以套件仍是綠的。不接住時，因為第 0 支的端面不再與邊或相鄰料對齊，產生器改用 `through`，場景文字推不出長度，檢查器列出 `長度無法由場景文字推出` 與 `oracle [0, 0, 5000, 27] … 場景文字沒有算出這個矩形`，共 214 筆不符（第 0 支、所有以它為擋面而退成 through 的料，以及對不上的 golden 矩形）。提交版的 `delta` 預設是不偏移。

## 實跑前該知道的限制

- 逐支前綴會拿掉先前被拒的料。後面的擋面因此和整場一次放不同。`results.json` 的 `omitted` 記下那些被拿掉的編號，每列的 `mode` 標「原場景」或「省略後探測」，`RESULTS.md` 開頭的統計分開寫。
- 32 支孔邊 `rc_parallel` 的長度伸出孔邊，仍用 `at-face`，沒有改成 `at-line`，也沒有縮短。**依 opus 審查更正：** 原先寫「預期觸發 I22（V_EXTENSION）」，實跑 32 支全部接受，核心的延伸段只看外輪廓邊。
- 4 支 `rc_parallel:custom`（F1 右上／右下板長沿 Y，以及左下／右下板長沿 X，golden 編號 14）與凹角牆線共線，但和該邊沒有正長度交集，整段落在另一肢。R6(c) 的 at-face 要求與引用邊重疊，所以這 4 支用 `at-line`。矩形沒有改。其餘 20 支 custom 貼外輪廓，用 `at-face`。
- `git check-ignore -v` 對 `gen_scenes.py`、`scene_reader.py`、`scenes/f1-00.scene`、`fixtures/*.scene`、`index.json`、`run_probe.sh`、`mapping.md`、`parse_results.py`、`test_gen_scenes.py`、`mutation_check.py`、`.gitattributes` 沒有輸出，這些路徑沒有被忽略。沒有改 `.gitignore`。
- 原生核心在本次修正前實跑過一次（見「實跑結果摘要」），本次修正後尚未重跑。`run_probe.sh` 沒有在 WSL 上執行過新版；新版只用 bash 假核心在 Git Bash 驗過分類與結束碼。
