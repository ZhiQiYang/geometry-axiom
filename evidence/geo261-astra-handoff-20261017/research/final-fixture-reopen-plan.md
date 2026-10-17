# GEO-261 最終舊檔重開執行清單

2026-10-17，只讀準備；**本文件沒有執行任何產品、C/native、WSL、Node、browser 或完整測試**。整合來源為 `b53147a538b56c90487dfc88793b7081010dd8d0`（本機 ref 只讀核對）；若 root 隨後指定新 SHA，全部最終執行必須改用該完整 SHA，舊收據不自動沿用。

這份清單沿用既有 `geo261-evidence/p1/fixture-reopen/`，不新增比較器、不重製歷史資料。P1 只在原有 `wsl_locked3.sh` 共用鎖與隔離 namespace 下執行。每次使用新輸出目錄，保留第一次失敗；不要覆蓋既有 catalog、producer、紅燈收據或正在使用的服務。

## 1. 先分清楚要交付的三種結果

| 層級 | 既有入口與精確範圍 | 可宣稱的結果 |
|---|---|---|
| 原始場景與原生定義 | `run_native_pair.py`：354 組唯一 input bytes，2,189 個 owner rows | baseline/candidate 真 bridge load、read-back、成功後第二支 fresh bridge 重開；原 143 場景裁判照原定義跑。不是完整專案開檔 |
| 原始 ZIP／模型包 | `run_format_pair.py`：260 組唯一 archive／270 owner rows；115 組唯一 package／614 owner rows；共 375 比較列 | 真 `project-store.js` unpack/pack 與公開 `verify_package`、完整來源資產及包內容保全。不是 browser chooser/cold reopen |
| 完整應用重開 | 下方具名 browser gates，加上尚未接線的歷史專案清單 | 只能逐具名輸入記錄實際 browser import／chooser、draft、asset、model、owner、fresh service 結果，不能把前兩層全綠寫成 149 個 archive 都已 browser 驗過 |

固定舊來源：`a898ad6e12707104568679591fe1b21804bfc3df`。

既有 v2 catalog 的 **1,595 列**是 1,261 個 tracked `.scene`、270 個 archive（149 `.gcanvas`＋121 `.zip`）、52 個 saved-model JSON、1 個含包 schedule JSON、11 個其他 fixture/provenance 資產。分類為 accept 64、reject 86、not-product-input 121、unclassified 1,324；這些是盤點數，**不是已通過數**。舊 `FIXTURE-COMPATIBILITY.md` 的 1,246 scene／229 hashes 是更早盤點，不得拿來覆寫 v2。

原始來源與入口：

- `D:/geometry-axiom-work/geo261-evidence/p1/fixture-reopen/PROTOCOL.md`
- `baseline-a898-coverage-v2/coverage-manifest.json` SHA-256 `166bdb20a1bfb2fa4d8984b9ee294248330c360a831b36478528779162cddaad`
- `baseline-a898-formats-v2/format-inputs.json` SHA-256 `44f988cb9a8d6bc0a66a27f924356bde8ecc17af54306c79f98bb2ece5a65aa5`
- 同目錄 `REVIEW.md`：既有 referee 審查；11 synthetic self-check 通過只證明比較器，不是產品重開。
- `documentary-a898-v1/summary.json`：既有 5 個來源文件／歷史 blob 身份核對；保留為 documentary，不列產品通過。

## 2. P1 可直接啟動的既有雙版本重開入口

在 PowerShell 執行下列命令；這是**待執行指令**。label 必須尚不存在，如已用過就用 `v2`，不得刪除舊結果重跑同名。

```powershell
wsl.exe -d Ubuntu-24.04 -- bash /mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/wsl_locked3.sh run 'bash /mnt/d/geometry-axiom-work/geo261-evidence/p1/fixture-reopen/reopen-namespace.sh --candidate-sha b53147a538b56c90487dfc88793b7081010dd8d0 --label final-fixture-b53147a5-v1'
```

原 launcher 會自行建立獨立 ext4 candidate checkout、保留 shared-lock fd 7、開 private mount/net namespace、loopback、16 MiB stack 與各版本自己的 `/tmp`；用兩版各自 registry 建 `core`、`bridge`、`model-base`。既有 baseline `/var/tmp/geo261-baseline-a898ad6e` 必須仍是 clean 固定舊來源。不要另開第二個 heavy runner，也不要把命令改成直接執行 pair script 繞過鎖與來源檢查。

輸出：`D:/geometry-axiom-work/geo261-evidence/p1/final-fixture-b53147a5-v1/`。

驗收清單：

1. `stage-exit-codes.json` 恰有 `baseline-build`、`candidate-build`、`native-pair`、`format-pair`，四者均 0；根 summary `exit=0`、`runnersUnchanged=true`。建置或啟動失敗不是輸入拒絕。
2. `native/summary.json`：`uniqueNativeInputs=354`、`ownerRows=2189`、`matched=354`、`failed=0`；兩版所有 registry state 均 fresh，來源／manifest／runner 前後未變。每個成功 load 的 canonical dump 進第二支 fresh bridge；每個拒絕 load 的五項完整 reads 與事前非空世界相同。未分類輸入只報觀察到的差分一致，不替它創造 SSOT 判決。
3. `formats/summary.json`：`executed=375`、`matched=375`、`failed=0`；counts 為 260/270 archives、115/614 packages，`inventoryProblems=[]`（manifest 計數為 0），兩版 model-base fresh、來源／manifest／runners 不變。原 archive 所有附件 bytes 及 manifest、scene 保留；package 二次 verify 穩定；只有 verifier 真正升到自身目前 axiom pair 的兩個欄位可作具名 promotion，不能忽略整份 manifest。
4. 保留各 input 的 raw stdout/stderr、exit、完整 reads、比較 JSON paths、owner rows；不得把同 bytes 的不同 owner／容器出處刪去。
5. launcher 與 format summary 的 `fullFixtureAcceptance:false`、`browserExecuted:false` 是正確邊界，**不要改成 true**。

## 3. 目前整合來源的既有 frozen regression suites

這些已登記在 `tests/run_all.py`／`tests/run_all.expected.json`；若最終全量 aggregate 已對同 SHA 成功執行，就引用其逐 suite 收據，不為本清單無理由再跑一次。若 P1 需要先做可定位的 focused 重開，在已受鎖、已固定來源、已 registry 建置的 candidate checkout 執行：

```sh
export GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base
export GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge
export GEOMETRY_MODEL_UPDATE_BRIDGE=/tmp/geometry-tests/bridge
python3 -u -m unittest -v tests.test_domain_decoupling_compatibility tests.test_engineering_model_compatibility tests.test_section_profile_modeling
```

精確預期 **65 tests = 14＋31＋20，0 failures/errors/skips**；此數由 b53147a5 expected registry 與 AST 方法數只讀交叉核對。`test_engineering_model_compatibility` 包含明示 mocked protocol／合成錯誤版本探針，不能把 31 全說成 31 個歷史原生檔。

| suite | 既有真讀取／frozen baseline | 精確範圍與應保留內容 |
|---|---|---|
| `test_domain_decoupling_compatibility`，14 tests | `tests/fixtures/domain-decoupling-main-a898ad6e/` 的 producer receipt、原包與 inputs | 真舊 producer 的 profile、finite-grid、infinite-grid、stagger、parameter **5 成功包**；subdivision **1 既有拒絕 input**。profile volumes 2,138,400×3＋84,960,000；finite/infinite 1,171,200,000；stagger/parameter 1,746,360；原 bytes 不變。subdivision 保持 `UNSUPPORTED/CAPABILITY/I32`。其他 tests 是版本／能力／偽造內容守門，非額外舊成功檔 |
| `test_engineering_model_compatibility`，31 tests | `model-package-main-a393a0f0.json`、`model-package-main-d1db88ae-profile.json`、`model-package-main-839063b9-profile.json`，各自 provenance；另工程範例 archive | 原保存包不變；公開 verify 重推導，只准已明訂的新包 axiom pair promotion；混搭／未知版本、重算 hash 的假 geometry 仍拒絕。工程 archive 的模型 inputs 可重建不代表整包 browser cold reopen |
| `test_section_profile_modeling`，20 tests | `q38-legacy-space-model.json` 與配對 `.gcanvas`，真 producer `6a8c2fac3f220ea4e76139da7c232a658dfebf16` | 真讀 `/16` ZIP，manifest models、world.scene 對照 fixture；verify **5 個原包**：run package＋saved model 的 space/volume/clearance/walls；保留六行 section-profile 定義、54,000,000,000 mm³ saved space 結果。這裡沒有 browser 開整包 |

不要在最終候選重新執行 `producer.py` 覆寫上述歷史輸出；14-test suite 會檢查 receipt SHA `4660414637141df3cfa8da3c392bb17ae33b7c96ff1c35eb8b86827d0eb707e1`、script hash 及各 fixture 原 bytes。

另有已登記的具名 coverage，若 aggregate 未跑可按需執行同環境：

```sh
python3 -u -m unittest -v tests.test_space_modeling tests.test_model_update tests.test_panel_fill_finish_surface
```

精確預期 **88 tests = 40＋26＋22，0 failures/errors/skips**。前兩者讀 `issue119-legacy-missing-walls.gcanvas` 的舊 saved model 語意，區分歷史 replay 可接受與同 input 新 preview 應拒絕；PF1 suite 讀 `pf1-legacy-dumps.json`，對真 producer `444a871c87d78f8a12fd40f8cd79c3e6621ff393` 的 5 組 canonical dumps 逐字重開（ceiling-a、room_full、D31、D28、R08）。這 88 個 tests 包括其他行為，不能充當 88 個歷史檔案數。

單一原始模型 JSON 的現成診斷入口（輸出到新檔，勿覆蓋 input）：

```sh
python3 -u geometry-core/modeling_cli.py verify tests/fixtures/model-package-main-839063b9-profile.json --base-executable "$GEOMETRY_MODEL_BASE" --output "$OUT/839063b9-rebuilt.json"
```

此命令只接受真正 model package。`geometry-space-preview/1`、schedule／provenance JSON 不是頂層 package；其內嵌包由既有 `format-inputs.json` 的 exact JSON pointer 交 `exercise_model_package.py`，不要整份誤餵 CLI。

## 4. 完整 browser 重開：現成入口與具體邊界

所有命令在 shared-lock 的獨立 candidate checkout／namespace 內執行，沿用正式 CI 的依賴與 browser 安裝，不在現用服務上 reset。使用 `start_local.py` 建立該 checkout 的完整服務，server 與測試傳同一個 TEMP feedback；每個新服務都先 `runtime_version.py --probe`，要求 root、version、fresh 與 binary receipt 對應目前 SHA。

下面是 P1 內部 shell 的可執行準備；`OUT` 必須是本次新建的 `/tmp/...`，`pwd` 必須是固定 b53147a5 candidate。結束只停止本段 PID 與其專屬子 bridge，保留 logs，不停止其他服務。

```sh
set -e
export PATH=/opt/node/bin:$PATH
export OUT=/tmp/geo261-final-browser-b53147a5-v1
mkdir "$OUT"
export GEOMETRY_FEEDBACK_DIR="$OUT/feedback"
mkdir "$GEOMETRY_FEEDBACK_DIR"
npm run build
python3 -u geometry-web/start_local.py --port 18849 >"$OUT/service-18849.log" 2>&1 &
SERVICE_PID=$!
export GEOMETRY_TEST_URL=http://127.0.0.1:18849/
# 保留各次 probe 輸出；未 ready 時有限重試，不以網址能連線代替版本檢查。
runtime_ready=0
for attempt in $(seq 1 120); do
  if python3 geometry-web/runtime_version.py --probe 18849; then runtime_ready=1; break; fi
  sleep 1
done
test "$runtime_ready" = 1
```

| 現成命令 | 既有真正入口／預期數 | 仍不能宣稱的部分 |
|---|---|---|
| `GEOMETRY_SAVE_REOPEN_ONLY=1 GEOMETRY_CDP_PORT=9347 node geometry-web/space_model_test.js` | 實際 controls 建 synthetic grid/rule/timber，真 Save／Open 與來源身份核對；由 `save_reopen_synthetic_test.js` 載入 | 當版自產 archive；不是固定舊 archive 全集、也不是第二獨立服務歷史 reopen。保留本次輸出 census，不拿 full-space 數充 focused 數 |
| `GEOMETRY_SECTION_EVIDENCE="$OUT/section" node tests/test_section_profile_browser.js` | **68 個具名 checks**＝33×1440/390 兩寬度＋runtime／console 2 checks；真 download＋chooser Open、section full World／模型體積重算 | archive 是本次產生的 `/16`；不是 `q38-legacy-space-model.gcanvas` 原 bytes cold-open receipt；同服務的 New/Open 不能冒稱 fresh second service |
| `GEOMETRY_RULE_READER_OUT="$OUT/rule-reader" GEOMETRY_REQUIRE_CLEAN=1 node tests/test_grid_rule_reader_browser.js` | 讀歷史 `issue48.../archives/1280-full.gcanvas`，保留 sources，再 authored 衍生 `/13` 原生／raw／evidence archive 進真 chooser；實際 native prepare＋Save | 進 chooser 的是衍生包，不能稱原 `1280-full.gcanvas` unchanged bytes 已完整重開；runner 無預登記固定 census，記實際 `passed/checks`，不可虛構精確數 |
| `GEOMETRY_ROOM_ACCEPTANCE_DIR="$OUT/rooms" node tests/room_outline_acceptance_browser.js` | 實際來源／PDF room workflow、Save 與 fresh browser context Open；預設全部 scenarios＋negative cases，不設縮減 env | workflow 所造 archive，不是149原始archives；fresh browser context 仍非第二個 fresh service |

K2A 另有**現成兩服務 cold-open gate**，須增加同 SHA 的獨立第二個服務並成功 probe：

```sh
python3 -u geometry-web/start_local.py --port 18850 >"$OUT/service-18850.log" 2>&1 &
FRESH_SERVICE_PID=$!
runtime_ready=0
for attempt in $(seq 1 120); do
  if python3 geometry-web/runtime_version.py --probe 18850; then runtime_ready=1; break; fi
  sleep 1
done
test "$runtime_ready" = 1
export GEOMETRY_FRESH_TEST_URL=http://127.0.0.1:18850/
export GEOMETRY_ISOLATED_SERVICE=1
export GEOMETRY_EXPECTED_SHA=b53147a538b56c90487dfc88793b7081010dd8d0
export GEOMETRY_BROWSER_RECEIPT="$OUT/k2a-zip"
node tests/k2a_zip_browser.cjs
```

它必須驗兩服務 session 不同，live bridge fresh、前後 source/binary/runtime 身份不變。實際讀到的舊檔為 `tests/evidence/k2a-boundary-review-20261012/legacy/base49-capacity.gcanvas`（131,071-byte 舊 envelope），另有本次 generated draft/lost/capacity/collection 包。它核對原 rawForm/ruleDraft、orphan/lost、重開 dump 與升存 `/17`；不是 `tests/fixtures/k2a-legacy-live-ref-9e136db.gcanvas` 的既有獨立 cold-open 接線。**Save File Picker writer 是明示 stub**，真 browser/native/importBytes 仍成立，但不能叫作原生 OS chooser Save 驗證。以兩份 `gate.finish()` receipt 的實際 assertions 記數；該 gate 沒有固定 expected registry，無法預先誠實填一個靜態總數。

## 5. 必須在最後報告保留的具體缺口

1. **149 `.gcanvas` 尚無通用逐原始 bytes 的真 browser chooser/cold-reopen runner。** 現成 native/store/package launcher 明確不做 browser；不要以 260 archive format rows 的成功替代。最終 owner 表必須保留每個歷史 archive 的原路徑、SHA、格式、reader、cold/fresh-service 狀態。
2. `issue119-legacy-missing-walls.gcanvas`：Python saved-result/replay 路徑有；本輪未找到其原 bytes 真 browser cold-open 現成入口。`q38-legacy-space-model.gcanvas`：ZIP＋五原包有；現成 section browser 測的是新生成 archive。兩者都不能只抽 world.scene 完成交付。
3. `wp60-a-main4bea-near-capacity.gcanvas`：現成 store／PDF bytes coverage；原包 cold browser、接近容量時全部 source/drafts/model owner 恢復仍需具名執行。`k2a-legacy-live-ref-9e136db.gcanvas`：既有 `test_reference_workspace_races.js` VM/lifecycle owner 與 documentary provenance；不能用另一個 `base49-capacity.gcanvas` 的兩服務 receipt 抵充。
4. `geometry-web/examples/{space-model-v1,engineering-spec-v1,assembly-rules-v1,assembly-generation-v1,source-subdivision-v11,source-subdivision-rooms-v11}.gcanvas` 有 native/store/model 或具名 workflow consumers；本清單沒有找到能讓同一 runner 直接傳任意原 archive 路徑並 cold-open 全六包的介面。尤其 rooms 的原 source、draft、collection/history 不能用場景重載證明。
5. 121 `.zip` 包含 evidence bundles；先依 catalog 的 kind/owner 和既有 consumer 分類，不強迫全部當 project。1324 個 unclassified owner rows 的 baseline/candidate 相同只能記 observed parity，不能自行貼 accept。
6. `model_snapshot_schedule.json` 使用既有 `tests/test_model_snapshot_navigation.js`、`tests/test_model_snapshot_schedule.js`；其內嵌 model package 的 format gate 不替代 schedule/navigation UI 邏輯。PDF、source helper、capability/vector JSON、provenance 各沿 catalog 具名 owner，不要硬算為 reopened project。

交付結果採三欄獨立狀態：`native-differential`、`format/package`、`browser-owner/cold-reopen`。每個 owner 只能標實際 executed、documentary 或 unresolved＋具體原因。上列命令全部成功，最多證明其列出的邊界；缺口未完成時整體仍不得宣稱「全部舊檔已重開」。

## 6. 十個原始 `.gcanvas` 的最小 cold-reopen 接線提案（只讀設計，尚未實作）

本段是 root 追加的有限方案：只補 **4 個 tests/fixtures 原件＋6 個 examples 原件**；不把149個 archive 的全量 browser 批次引入本次工作。354 native／375 format 比較列照前文獨立交付。

### 唯一允許的原件清單

每列從既有 `baseline-a898-coverage-v2/coverage-manifest.json` 以**完整 path 精確選取**，沿用該列 `blob` 的原始 bytes 與 hash。不要用 basename 搜尋：catalog 另有 evidence 內同名副本，會錯擴成14列。Driver 啟動時要求恰好10個不同 owner path，且完整原始檔 hash 全符；候選 checkout 同名檔不能替代 frozen blob。

| 完整 path | 最少必觀察的實際資料 |
|---|---|
| `tests/fixtures/issue119-legacy-missing-walls.gcanvas` | PDF 原 bytes、2 個原 saved models、歷史缺 walls 的既有 replay 語意；不要觸發新 preview 來替代原 stored-model 開檔 |
| `tests/fixtures/q38-legacy-space-model.gcanvas` | 原 `/16` scene、section sources、1 個 saved space model 及其嵌入包；原 model object 保留、model library 可讀 |
| `tests/fixtures/wp60-a-main4bea-near-capacity.gcanvas` | PDF bytes、近容量 manifest、全部 engineering drafts／room attachments；不能只比 count 或只保留前幾筆 |
| `tests/fixtures/k2a-legacy-live-ref-9e136db.gcanvas` | 原 `/17` raw draft、baseRef/inputRefs、live grid 1/2 身份與 owner；完整 rawForm/ruleDraft，非重新建立相似 draft |
| `geometry-web/examples/space-model-v1.gcanvas` | 原3個 models、saved result/source/input 與 face projections |
| `geometry-web/examples/engineering-spec-v1.gcanvas` | 原工程來源、固定 material/method version、saved model、engineering drafts |
| `geometry-web/examples/assembly-rules-v1.gcanvas` | rule definitions、parameter/engineering source、assembly drafts 與固定版本引用 |
| `geometry-web/examples/assembly-generation-v1.gcanvas` | generation instances、source/member mapping、owned object identity、原 draft/model 資料 |
| `geometry-web/examples/source-subdivision-v11.gcanvas` | 原已提交子規則、ruleKey/nextRuleKey、binding/vertex identities；不以重新產生規則代替 |
| `geometry-web/examples/source-subdivision-rooms-v11.gcanvas` | 原 source bytes、grid drafts、source-room collection/history、attachment owner closure |

### 最少新增一個外部 driver，不改產品或現有測試

建議日後僅新增 `D:/geometry-axiom-work/geo261-evidence/p1/fixture-reopen/exercise_ten_projects_browser.cjs`。這是**待實作檔名，本次未建立**。它只做 Playwright 導航、真實 Open/Save 操作、公開 API read-back、結果封存與比較；不注入模型結果、不 patch fetch、parser、native 或 exporter。

建議介面為 `--root <固定checkout> --source-sha <完整SHA> --side baseline|candidate --url <第一服務> --fresh-url <第二服務> --coverage-manifest <原v2清冊> --out <新TEMP目錄>`。這是待實作介面，不應當現有可執行命令。使用同一 driver 分別跑兩版；服務仍由既有 shared-lock／P1 launcher 建立，每版兩支不同 session 的 fresh service，可按版本先後跑，不需同時四支。第一個 browser context 每件重新建立；第二服務每件首次接收保存包前亦需恢復可證明的乾淨隔離狀態。若只能 reset bridge 而未證明 browser／project recovery 清空，不得稱該件是 fresh cold reopen。

可直接參照／重用的既有接線：

- `tests/room_outline_acceptance_browser.js::freshOpen`：`browser.newContext({acceptDownloads:true})`、關閉 OS Save Picker 能力以走**真正 download fallback**，`#fileMenuBtn` → `#btnOpenProject` → `page.waitForEvent('filechooser')` → `setFiles(originalPath)`。`tests/test_section_profile_browser.js` 另用真 `#projectFile.setInputFiles` 進同一產品事件路徑。
- `geometry-web/reference-workspace.js:1806` 的 `importBytes` → `openProject` → `importProjectData` → `readProjectContext` 是已有的完整 document controller；成功時仍經 `uploadScene` 的 prepare／commit 交易及實際 context 切換，沒有直接塞 world。`readProjectContext` 會先逐一驗 stored models、rule-case/evidence closure、source pages、scenario children，再提交整個 context。需要取得可 await 的拒絕錯誤時可沿用 `importBytes`，但該 case 要標明 controller import，不能寫成 chooser case。現行 `ReferenceWorkspace` **未公開名為 `importFile` 的方法**；真檔案入口是 `reference-workspace.js:2086` 的 `#projectFile.onchange`，讀取 `File.arrayBuffer()` 後同樣呼叫 `openProject`。若 driver 自取 helper 名 `importFile`，必須說明它使用真 chooser 或這個既有 input，不能假定產品有同名 API。
- `tests/k2a_browser_receipt.cjs::begin/finish` 已有預期 SHA、live bridge fresh、runtime/session、前後 binary 身份與實際 assertions 計數；兩服務同 session 必須拒絕。其舊 `snapshot()` 清單未包含目前全部 `geometry-app`／`geometry-templates` 來源，故 P1 另沿用 fixture pair 的 `source_manifest` 完整 tracked 前後 manifest；不能只靠這個舊 helper 宣稱新來源閉包全部凍結。
- 真 Save 用 `[data-project-action="save"]`＋`page.waitForEvent('download')`＋`download.saveAs(newPath)`，照 section/room browser；不得用 stub writer。再以各版自己的 `GeometryProject.unpack` 讀下載包，並從第二個 fresh service/context 的真 chooser 開該包。`ReferenceWorkspace.exportBytes()` 是既有完整 export/controller，但不能替代這次要求的使用者 Save 路徑。

`reference-workspace.js:1362` 的 `exportSnapshot`／`:1378` 的 `exportBytes` **包含完整專案**：native dump、`manifestData` 的 sources/pages/faces、models、assembly/engineering drafts、feature attachments（含 source-room collections/history）、scenario catalog，以及 `context.sources` 全部原 binary bytes（含 PDF／圖像／attachment 資產），最後交 `P.pack`。`manifest()` 單獨只有 metadata，沒有原 binary bytes；dump 單獨更不含這些資料。不過 export 會先呼叫 `AssemblyWorkspace.flush()` 與 `InfiniteGridWorkspace.flush()`，因此不是無副作用 getter，**拒絕前後的只讀 snapshot 不要呼叫 exportBytes**；改取下表完整 metadata＋sources bytes＋history，再將真 Save 的下載包另作 roundtrip 比較。

### 完整 owner snapshot 的既有 API

用 `page.evaluate` **只讀**下列內容。保存全部值為 JSON／binary 檔，不只摘要或 screenshots；大附件在頁內 WebCrypto 算 hash並保留原 bytes的外部檔，避免用龐大的 `Array.from` 一次塞滿 CDP。

| 目的 | 現成讀取路徑與比較方式 |
|---|---|
| World／typed references | `apiRequest('dump')`、`apiRequest('objects')`、`apiRequest('references')`、`apiRequest('engineering-read')`，保存完整 response；固定版本／生成 ownership 在 native definitions/references 中比完整內容 |
| 專案持久資料全集 | `await ReferenceWorkspace.manifest()`：projectId/name、sources、faces/pages/activePage、faceProjections、reconstructionReviews、models、assemblyDrafts、engineeringDrafts、featureAttachments、scenarioCatalog；保持所有欄位，不自行白名單刪掉不認識的 owner |
| 原 source 資產 | `ReferenceWorkspace.context().sources` 的每個 `{meta,bytes}`；逐 source id／hash／name／type／size 與完整 bytes，比 catalog archive 的 `sources/<hash>`。不要 JSON.stringify Map 後把空 `{}` 當成保存成功 |
| Saved model／草稿讀取 | `getSpaceModels()`、`getAssemblyDrafts()`、`getEngineeringDrafts()`、`readGridDrafts()`；與 manifest 對應 records 全等。`readGridDrafts()` 的 orphans、lost、baseRef/inputRefs、rawForm/ruleDraft 亦在比較內 |
| room/evidence/scenario owner | manifest 的完整 `featureAttachments`／`scenarioCatalog`，再用 `readFeatureAttachment(kind,getProjectState().contextToken)`／`readScenarioCatalog()` 作有資料家族的實際讀取；保留 source-room collection/history 與所有 attachment owner IDs。不要硬造未知 kind，從原 manifest 提取 |
| 當次交易／拒絕原子性 | `getProjectState()`、`getModelOperationState()`、`context().dirty`、`history.undo`／`redo`／`group` 的可序列化資料及 `history.frame.ids` Map；同一 context 的拒絕前後比較完整值（包括 contextToken、revision），比既有 source_navigation snapshot 更完整 |
| 保存再讀 | 真下載 bytes → `GeometryProject.unpack(bytes,fflate)` 的 `{manifest,scene,sources}` → 第二 fresh service chooser → 再取上述同一 snapshot；原 input bytes 必須始終不變 |

`contextToken`、model operation 的 opaque context/frame/undo identity、runtime session、openedAt/download time 等是每次執行的身份，**跨版本不要求隨機字串一樣**；原值仍完整封存，且各自有前後穩定／成功換 context 的斷言。跨版比較 projectId／所有持久引用／保存內容及每項身份關係；只能列出這些已知 session 欄位的逐項對照，不得籠統忽略 whole project state／provenance／manifest。原件到 canonical reopen 若有升版或自動排版差異，保留實際 diff與兩版結果；沒有現成允許規則的差異不得自動變成 pass。

### 有限計數、成功條件與失敗原子性

1. 固定 **10 個原件 × 2 版 = 20 個首次冷啟動 Open attempts**，逐件原 bytes相同。兩版每件先從獨立乾淨 context 讀 runtime/source pin；用同一個非空 sentinel project 作原子性前狀態，sentinel 由既有正常 controller 建立並保存，不能改全域 state 冒充。
2. 每個接受的 attempt 都必須完整 snapshot、真 Save、第二 fresh service/context chooser reopen 及完整再讀；若20次均接受，就恰有 **20 次追加 saved-copy cold reopen，共40次開檔**。若有拒絕，追加數等於實際接受數，不能把未到達 roundtrip 的 case 補成 passed。這是流程數，不預造 assertions 總數。
3. baseline 與 candidate 同件 verdict 必須相同。任何一邊出現 crash、timeout、transport／model adapter infrastructure code、console unexpected exception、runtime/source漂移，都記 execution failure，不算 domain reject。未分類歷史原件兩邊都拒絕，最多是 observed rejection parity，不自動算「此檔合法性已驗證」。
4. 正常原件若被拒絕，driver 必須等產品 finally 清除 busy，再把 sentinel 的 World reads、完整 manifest、每個 source bytes、models/drafts/attachments、project state、歷史/frame identities 與失敗前逐項相比；只有錯誤/status 呈現可改。保留 UI status/dialog、controller exception與 native API response 的原文及 code/clause（有才記，不猜）。同版原子性先判；兩版錯誤再比，不能只看都 `ok:false`。
5. 若10個原件均接受，拒絕原子性仍需要一個真正被執行的對照。最小只取 **q38 原件的1個 detached 壞 `sceneHash` control × 2版 = 2個負向 attempts**：原件另存後只改 manifest.sceneHash 為明確不同的合法64位hex，用 zip helper重封，**不經 product pack 修正 hash**。在原 q38 已完整打開的非空專案上，沿真 chooser/controller進既有 unpack hash guard；原件SHA未變。兩列獨立標 `derived-negative-control`，不是新增歷史原件，也不取代正常10件讀取；不擴成每原件的全面負向測試。
6. q38 正向若尚未通過，該 control 不得用較早拒絕當成功，記具體前置失敗。每次拒絕比較都保存該 side/context 新的完整 before snapshot；不得用 candidate 的 before 去替 baseline 比。

最小交付檔：一個 driver、其自身 hash、10-row fixture selection receipt（引用既有 blob／owner，不另生 baseline）、兩版20件 original outcomes、成功保存包與對應 fresh reopen outcomes、2件獨立 negative-control outcomes、逐owner snapshot/diff、前後完整 source/binary/runtime receipts。是否全接受及其真正 assertion census由執行結果決定；方案本身不新增任何 PASS 聲明。
