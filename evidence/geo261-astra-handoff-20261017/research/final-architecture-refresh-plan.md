# GEO-261 最終架構收據刷新準備

> 2026-10-17 的唯讀準備；**尚未刷新 manifest、執行 scanner／測試、套用 coverage patch 或合併來源**。本文件不是新架構證明，也不證明 Python default／native coverage 已通過執行驗收。只擁有本外部新檔；不改 repository 或既有 seals。

## 釘選來源

| 項目 | 精確識別 |
|---|---|
| 已讀 integration HEAD | `12260aeb667f86a773d37e24d026dc844e6afc2f` |
| Integration checkout | `D:/geometry-axiom-work/geo261-integration` |
| 待合入 Python default HEAD | `8f36f1a0dd7e1244c92aca926c0a80079451e7f0` |
| Integration／Python merge-base | `9de9cd4f67417b7918842ce05ef11044f8a08b68` |
| 尚未套用的 coverage patch | `D:/geometry-axiom-work/geo261-research/coverage-activation.patch` |
| Patch bytes／raw 與 LF SHA-256 | 8,817 bytes；`dd3bfd8252ee2f3e5431ee1fa07ab915d7a3dcd5ca0e08a67a9c27627172d69c` |
| 前次刷新 driver，僅作為保留的參考 | `D:/geometry-axiom-work/geo261-research/refresh_product_architecture_47d.py` |
| Driver bytes／raw SHA-256 | 26,718 bytes；`cc8ac5a0216db55def6d06f983a80a8c43cc39c84cccaf0a891bd9065f27c6bf` |

兩個 checkout 在本次檢查時均乾淨。Python 變更依共同祖先到 `8f36f1a0…` 的增量確認，不用兩個 HEAD 的整棵樹直接相減，避免把對方缺少的歷史證據誤當刪除。

## 目前缺項與過期狀態

讀取 manifest 的五個 `sourceRoots`、三個 `sourceFiles`，另以 `os.walk` 與前次 driver 的完整 executable suffix 集合獨立盤點；沒有匯入 scanner 或呼叫其 inventory／scan：

- Manifest：**332 sources + 244 exclusions = 576** 已登記 executable files。
- 實際檔案：**581**；恰有下列五個未登記歷史 Python helper。
- Missing registered paths：**0**。
- Stale exclusion hashes：**0**；vendor raw hashes／iframe driver-router LF hashes 過期：**0**。
- 相對現有 receipt 的 576 筆已封存來源，LF hash 改變：**0**。
- Scanner 與兩支 architecture test 檔的 LF hash 均仍等於原收據。

目前不需要更新任何既有 exclusion digest。以下五筆只能逐檔新增 exclusion，不可排除整個 evidence 目錄或任何 glob。

### 五筆精確 exclusion map

所有路徑的基底均為 `geometry-core/domain-decoupling/evidence/native-p1-closeouts-20261017/`；表中為完整 repository-relative 路徑。五檔在此快照均為 LF，raw 與 LF SHA-256 相同。最終仍須從凍結 checkout 重新讀 bytes 並與其 Git blob 比對。

| 精確 path | 逐檔 reason | LF SHA-256 |
|---|---|---|
| `geometry-core/domain-decoupling/evidence/native-p1-closeouts-20261017/extract_evidence.py` | Historical fourth-package extraction helper: recovers catalog-selected retained evidence bytes without executing them. Not a product-loaded module or current product entry point; final architecture audit reads/hashes this exact file only. | `ac626b84cc3cc6d029ecb95cceb2d3098b3a8cf084e8f8b69a3e98bd9d7e90f7` |
| `geometry-core/domain-decoupling/evidence/native-p1-closeouts-20261017/finalize_publication.py` | Historical fourth-package sealing helper: writes the package SHA-256 seal after original-byte verification. Not a product-loaded module or current product entry point; final architecture audit does not invoke it or replace the old package seal. | `13fe9eb20dd2827859866cf61a83d2badd6236f53eb322b8b79a37dafa865e87` |
| `geometry-core/domain-decoupling/evidence/native-p1-closeouts-20261017/prepare_publication.py` | Historical fourth-package publication helper for the frozen 370-file closed-receipt allowlist. Not a product-loaded module or current product entry point; final architecture audit does not republish or execute retained evidence. | `37cb07dbc7af6f453c056b7ccec2e777fe3dd991fda531def42112d16aa2a695` |
| `geometry-core/domain-decoupling/evidence/native-p1-closeouts-20261017/readable/watchdog-envelope-v1/recovered-selftest-source-868c0864cbf91da304ca37e7ebee140cfe68542fccc3d6f764f0d27a7f8dd9ac.py` | Historical recovered synthetic watchdog self-test source retained by its content hash. It imports a sibling watchdog and creates synthetic run output when executed; it is evidence, not a product module. Final architecture audit reads/hashes it and never imports or runs it. | `868c0864cbf91da304ca37e7ebee140cfe68542fccc3d6f764f0d27a7f8dd9ac` |
| `geometry-core/domain-decoupling/evidence/native-p1-closeouts-20261017/verify_publication.py` | Historical fourth-package byte/catalog verification helper. Not a product-loaded module or current product entry point; its original verification and seal remain historical records, and final architecture audit only hashes this exact source. | `79ff75e1ab60dba1e9c0008fc806b517159f952f677864da461b1dc9eec3406c` |

Use `hashMode: "lf"` for each new entry. Current Git blobs, in the same order: `3ba9a76b6285974af6d274c18cd12f406e7515ce`, `dff0d160abbf07e5adfa08c03917df8038587a3b`, `c42f36885a5472284fcb770e51abde82f5765bc9`, `828d36e5c3630dccda55404752af212bb9cb4d62`, `b30daec04dd243c96a858b756fff6d9753aac4a3`. Record final source HEAD, Git blob id, raw/LF digests and bytes as exclusion provenance; do not reuse these pins without verifying final bytes.

## 待合來源的最小 ownership map

| Exact path | 來源 | 現行歸屬／最終處理 |
|---|---|---|
| `geometry-app/geometry_app/model_native.py` | Python `8f36f1a0…` | 已有 **H / python**；只更新 receipt 的來源 hash，不新增 source／exclusion。 |
| `geometry-core/modeling/base.py` | Python `8f36f1a0…` | 已有 **H / python** compatibility facade；新增 `load_candidate` 仍屬同一檔案與歸屬。 |
| `geometry-core/modeling/engine.py` | Python `8f36f1a0…` | 已有 **H / python** compatibility facade；default 走 `load_candidate`／`source_graph=True`，只更新 receipt hash。 |
| `geometry-app/native/model_sources.inc` | Coverage patch | 已有 **H / c**；只更新 receipt hash。文字中的 `coverage.complete=true` 不構成 runtime 完整性的證明。 |

這兩個已知增量合計改 **4 個既有產品來源**，新增產品 source **0**，新增 executable evidence **0**。不要給非 vendor `sources` entry 加 `sha256` 欄位；來源雜湊在 receipt 的 `inputs`，manifest 的欄位名是 `sources`，不是 `modules`。

其他已確認路徑的處理：

- `geometry-app/native/MODEL-SOURCES.md`：coverage patch 修改的說明，非 executable，不進來源閉包。
- `tests/test_geo261_model_sources.py`：coverage patch 修改的測試，不在五個 product roots／三個 standalone inputs 內，不加 exclusion。
- `tests/test_geo261_default_native.py`：Python default 新測試，也在同一 inventory 範圍外，不加 exclusion。
- Python delta 的 `geometry-core/domain-decoupling/evidence/default-sources-f3c71065/` 只有 `.md`、`.json`、`.log`、`.gitattributes`；不需 executable exclusion。
- Python 分支的 registry `206 / 4449` 與八個 actual-default 測試屬其各自驗證／登記範圍；不得混成 architecture suite 的數量，也不得用 AST 發現數推論執行通過。

若凍結來源只有上述預定變更，刷新後 inventory 應為 **332 sources + 249 exclusions = 581**；layers 維持 `H=190, K=69, W=67, vendor=6`，languages 維持 `c=189, python=75, javascript=64, html=4`。後續若 P1 修正或新證據出版新增 executable，須先逐檔重新審查；不要把這個預測數硬塞進新收據。

## 保持不變與舊封存鏈

Scanner **不修改**。五個 source roots：`geometry-core`、`geometry-app`、`geometry-templates`、`geometry-web`、`geometry-guide`；standalone：`current_geometry.c`、`tests/__init__.py`、`tests/binaries.py`。保留 search roots、HTML／JS routes、vendor bundle、iframe driver／router pin、所有既有 exact exclusions 與 layer 歸屬，不新增廣域排除或放寬政策。

現有 **916 forbidden identifiers / 55 forbidden strings** 全保留。預定四個變動來源全屬 H；W 來源 bytes 若仍與既有 seal 相同，沒有新增 W guard 的理由，也不需要重做前次三個 accessor 的 supplemental probes。

前次封存來源基底為 `47d3bb4bcccddeeb034dd5899a7aa15c9cab0768`。它證明當時的 **576 inputs / 332 sources / 244 exclusions / 796 edges / 0 diagnostics**；這些是歷史結果，不是最終來源的新結果。

| 舊 pin | SHA-256（LF，除另註） |
|---|---|
| Manifest | `119e153590b9ecf5ea23d4a54fb6845528a302291f819c979a803d79712b3b33` |
| Scan JSON | `900894fedb455683ed9276157dd7db772b03363afc6c9f5c48a717637eb24bf2` |
| Report | `b43dd0bd2d3d76a9b679d1df3e99c37a5eb1f6a319d4de99702240b11e7211d9` |
| Receipt 本身 | `a4166fd433cb9477e87756f635b5491d5dfe457035974b10b03d6b33ddc676e7` |
| 舊 input closure | `401670b9f56655b29e367706e6602b70ee3344518c8cc4210ef45f7ef4b32dc2` |
| `tests/architecture_contract.py` | `bbd54265d0df88497228e1c362c904a495ed7ea986a3568adbeeb753e19d8f5e` |
| `tests/test_architecture_contract.py` | `17ffb47f6f18db4967087459bb6d563e4d7487b0e30b23101b38fe5d36a7f9e3` |
| `tests/test_product_architecture.py` | `12e83386323afbffda89babcaea46eaa337ade1383f85cf63ec17e114238713e` |

在最終刷新工作目錄建立 `previous/`，保存舊四個 audit outputs 的**原始 bytes**與 raw／LF hashes。原有 `manifest-refresh-47d3bb4`、driver、P1 packages、`PACKAGE-SHA256.json` 與任何 PASS／FAIL／UNRUN 收據均不覆寫。新版 receipt 連到舊 receipt digest／createdUtc／sourceBaseHead；不要把舊執行時間或來源 SHA 改成最終 HEAD。

## 前次 driver 的有限改寫清單

前次 `refresh_product_architecture_47d.py` 固定了舊 HEAD、三筆新增排除、兩筆 stale 排除、三個新 guard 與舊數字；**不可原樣執行，也不可只改 HEAD**。來源真正凍結後，使用檔案寫入工具建立新的外部 `refresh_product_architecture_final.py`，保留舊 driver，僅作以下有限調整：

1. `ROOT` 維持 integration checkout；`HEAD` 從必填 `GEOMETRY_ARCH_AUDIT_HEAD` 取得完整凍結 SHA，`WORK` 從必填 `GEOMETRY_ARCH_AUDIT_WORK` 取得全新外部 run 目錄。保留 `head()`、clean checkout、raw／LF inventory 與 tool hashes 的每階段 frozen gate。拒絕已存在的 `state.json` 或舊輸出目錄。
2. `NEW_EXCLUDED` 精確替換成上表五個 path／reason，`UPDATED_EXCLUDED = {}`。`before()` 預期 581 inputs、五個 unregistered、沒有 missing 或 stale digests；先保存舊四檔 raw bytes，再做 actual CLI prior-manifest check。若 scanner 仍採首錯即停，預期 `SOURCE_UNREGISTERED` 指向五者之一；實際命令、exit code、diagnostic 均如實保存。
3. 記錄 `changedPreviouslySealedInputs` 的實際差異。若最終只有已知 Python＋coverage 變更，應恰為上表四個 H sources；出現別的路徑就回到逐檔核對，不自動分類／豁免。核對新 executable 檔的 committed blob 與工作區 raw／LF bytes。
4. 不呼叫前次寫死「913→916、新增三 guard」的 `policy()`。在確認全部 W-owned sources 的 LF hashes 與舊 receipt 相同後，建立明確的 policy-reuse metadata：916／55 維持、`addedIdentifiers=[]`、`addedStrings=[]`，連到前次 policy／probe 證據。沒有新 guard 時不執行 `guards()`，新版 supplemental 欄位標明沒有新 probes，不把舊三次 probe 宣稱為本次執行。
5. `refresh()` 只 append 五筆 exclusion；原有 sources、routes、policy、vendor 與 244 個 exclusions 必須逐筆相同。把固定 `[:-3]` 改為依本次新增數量的精確比較；條件性總數更新為 332／249／581。SCANNER CLI 必須真跑，edges／diagnostics 從實際 JSON 讀，不硬編舊 796。
6. `product_tests()` 仍跑實際 `python -B tests/test_product_architecture.py`。若其 LF hash 仍等於上表，現行套件為 **18 methods**；保留實際命令、原始 stdout／stderr、時間與 exit code，不從其他 registry 推論數量。Generic scanner suite 若 scanner／generic-test LF hashes 仍完全相同，沿用舊 **205 total = 204 pass + 1 Windows symlink skip**，清楚寫「本次未重跑」。skip 不能算 pass；若工具檔變動，先重新界定驗證範圍，不冒用舊結果。
7. Report 保留前次 `47d3bb4…` 區段為歷史。新增最終區段，更新最上方當前 inventory 與最後一段的實際 scan／test／closure 結果。前次「#289 未合入」改為明確屬於當時來源的敘述；最終區段僅在驗證 ancestry 後說 default 來源已納入靜態閉包，runtime 仍引用獨立收據，不由本 audit 認證。不要改寫舊執行結果。
8. `seal()` 使用實際 final HEAD、五筆 exclusion provenance、真實 changed inputs、scan／product test 記錄及 generic reuse chain。移除「必須三個新 probes」斷言，改驗本次確為零新 guard／未執行 probes；保留 `notClaimed` 六項原文與 nativeAcceptance 的範圍界線。在同一最終 checkout 內比對 raw／LF closure 前後相同；跨 worktree raw bytes 可能只是 CRLF/LF 差異，不能拿它們互判來源不一致。
9. 最後只允許以下四個 repo outputs 改變：`geometry-core/domain-decoupling/product-architecture.json`、`product-architecture-scan.json`、`product-architecture-receipt.json`、`PRODUCT-ARCHITECTURE.md`。Receipt 自身不放進 product input closure；四份 audit outputs 仍依原 schema 分別 pin／排除自我遞迴。新版收據應回讀驗證，再逐項對照輸出 hashes。

## 凍結後命令順序（本次全部未執行）

前提：主工作者已完成所需來源整合及獨立驗證、明確凍結 checkout，並已按上節建立新的有限 driver。以下只執行靜態架構刷新；不會合併 Python branch 或套用 patch。檔案內容生成仍用檔案工具，不用 shell heredoc。

```powershell
$taskRoot = 'D:/geometry-axiom-work/geo261-integration'
$taskResearch = 'D:/geometry-axiom-work/geo261-research'
$taskDriver = Join-Path $taskResearch 'refresh_product_architecture_final.py'
$taskHead = (git -C $taskRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot read frozen HEAD' }
$taskStatus = git -C $taskRoot status --porcelain
if ($LASTEXITCODE -ne 0 -or $taskStatus) { throw 'Final checkout must be frozen and clean' }
if (-not (Test-Path -LiteralPath $taskDriver)) { throw 'Prepare the bounded successor driver first' }
$taskStamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$env:GEOMETRY_ARCH_AUDIT_HEAD = $taskHead
$env:GEOMETRY_ARCH_AUDIT_WORK = Join-Path $taskResearch ('manifest-refresh-final-' + $taskHead.Substring(0,12) + '-' + $taskStamp)
if (Test-Path -LiteralPath $env:GEOMETRY_ARCH_AUDIT_WORK) { throw 'Never reuse an older audit run directory' }
Set-Location -LiteralPath $taskRoot
python -B $taskDriver before
if ($LASTEXITCODE -ne 0) { throw 'Frozen-source preflight failed' }
python -B $taskDriver refresh
if ($LASTEXITCODE -ne 0) { throw 'Manifest update or actual CLI scan failed' }
python -B $taskDriver product_tests
if ($LASTEXITCODE -ne 0) { throw 'Current product architecture checks failed' }
python -B $taskDriver report
if ($LASTEXITCODE -ne 0) { throw 'Report update failed' }
python -B $taskDriver seal
if ($LASTEXITCODE -ne 0) { throw 'Final independent closure or seal verification failed' }
git diff --stat -- geometry-core/domain-decoupling/product-architecture.json geometry-core/domain-decoupling/product-architecture-scan.json geometry-core/domain-decoupling/product-architecture-receipt.json geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md
```

新版 driver 的 `before()` 必須完成第 4 點的 unchanged-W／policy-reuse 記錄，才能直接接 `refresh`。上列命令故意沒有舊 `policy`／`guards` 階段；不可把既有 driver 的函式未改就套用此順序。

Driver 內應保留的兩個實際驗證命令為：

```powershell
python -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json
python -B tests/test_product_architecture.py
```

它們由 driver 擷取原始輸出與 exit code，不另行重跑以免製造來源／時間不一致的收據。若失敗，停止刷新並保留該 run 的原始失敗；不得更新預期數、擴大 exclusions 或修改 scanner 讓結果變綠。

## 本次準備的界線

本次只讀現有 JSON、來源／patch 文字、Git ancestry／diff／blob 與 byte hashes，並新增此文件。沒有執行前次 driver、scanner、測試、C/native、WSL、瀏覽器或任何 Git mutation。五筆新增排除與四筆預定 H source hash 更新已精確定位；最終成功結果仍須等待來源凍結後的 actual CLI scan、product suite 與獨立 closure 核對。
