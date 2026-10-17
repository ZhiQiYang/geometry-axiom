# GEO-261 下一包實跑證據的出版準備

2026-10-17 唯讀核對，讀取 integration HEAD `43305271770760a690e360ce18ce11cc07f35ea2`。這份筆記沒有取得、掃描或封存仍 active 的 `4aec` 工作資料，也沒有執行任何封存 helper、native／WSL／browser／測試。最終實跑結果仍未取得；以下是沿用既有工具的準備，不是驗收結果。

結論：**可沿用現有的 portable evidence 格式與封存／驗證流程；extractor 可以直接指定新包重用，但既有 publisher、verifier、finalizer 是各包專用，不能原樣拿來出版最終包。** 將新包放在 repository 根目錄 `evidence/geo261-final-validation-<實際凍結識別>/`，不會使 product architecture inventory 增加 helper exclusions；目前 Git 放行規則仍需對那個確定的新目錄增加一條精確例外。

## 既有四包與可重用入口

四包均位於 `geometry-core/domain-decoupling/evidence/`，catalog 都使用 `geometry-p1-portable-evidence/1`。original／followup 的 seal schema 是 `geometry-p1-package-files/1`；authority／closeouts 則是 `geometry-p1-publication-package/1`：

| 既有套件 | 已封存 logical files | 套件檔案數，含 seal | 入口 |
|---|---:|---:|---|
| `native-p1-20261016` | 868 | 203 | `prepare_publication.py`、`verify_publication.py`、`extract_evidence.py`、`finalize_publication.py` |
| `native-p1-followup-20261016` | 459 | 75 | 同上，另有 `verify_followup.py` 與 `PREDECESSOR.json` |
| `native-p1-authority-20261017` | 536 | 115 | 同上，使用 `PREDECESSORS.json` |
| `native-p1-closeouts-20261017` | 370 | 68 | 同上，使用 `PREDECESSORS.json` |

這些是檔案數，不是測試數。最新第四包只到 `fa5deb70`，其 README 與 verifier 明文排除 `599`；新包需另收已結束的 `599` 及其後真實執行紀錄，不覆寫四包或改標其原始結果。

現有流程已具備所需構件：

1. **prepare**：從凍結的逐檔選取 catalog 讀原始 bytes，依 SHA-256 去重為 `blobs/<sha256>`，寫 `raw-evidence.tar.xz`；保留原始 logical path、bytes、source／target digest 與選定的 byte-identical `readable/` 副本。來源 commit object、Git tree／selected manifest、原始 runner claim 另存 provenance。它不是對工作目錄做無界限 glob。
2. **verify**：核對 archive／blob／catalog／readable bytes、source 與 runner provenance；帶 `--originals` 時對照保留的原始檔案；可核對未變的 predecessor 包。`--unsealed --report <新報告>` 供封存前比對，封存後再核對 seal。成功只代表證據一致。
3. **finalize**：先要求原始 bytes 比對成功，才建立 `PACKAGE-SHA256.json`；拒絕覆寫既有 seal。seal 涵蓋套件其餘所有檔案，包括 README、helper 與 `VERIFICATION.json`，不包含自己。
4. **extract**：依 catalog 選定 logical path，驗 archive 及目標 bytes/hash，再取回到包外的新目的地；不執行封存 runner、不重建 source checkout。第四包的 `extract_evidence.py` 沒有固定來源 SHA／370 檔數限制，可直接對相同 schema 的新包使用。

以下僅是未來命令介面，本次未執行：

```powershell
# 既有第四包，仍在原本相鄰的前包路徑；只驗封存資料。
python -B geometry-core/domain-decoupling/evidence/native-p1-closeouts-20261017/verify_publication.py geometry-core/domain-decoupling/evidence/native-p1-closeouts-20261017 --predecessors

# 新包完成後，可直接沿用既有 extractor，不需要為它新增另一份產品來源。
python -B geometry-core/domain-decoupling/evidence/native-p1-closeouts-20261017/extract_evidence.py evidence/geo261-final-validation-<實際凍結識別> --path <catalog中的原始log或receipt路徑> --out <包外全新目錄>
```

出版入口的既有參數是 `prepare_publication.py --plan <catalog> --evidence <originals> --repo <repo> --out <package>`；驗證有 `verify_publication.py <package> --originals <originals> --predecessors --unsealed --report <new-report>`，封存有 `finalize_publication.py <package>`。**這些參數並不表示舊程式已支援新包。**

## 唯一主要程式限制：publication 工具鎖定原包設定

最新 `prepare_publication.py:55` 後明確鎖住輸出 parent/name、plan SHA、原五組 source、三個前包與 370 檔；`verify_publication.py:43` 起鎖住相同檔數、bytes、outcomes，並拒絕 `599`；`finalize_publication.py:18` 要求 `originalFilesByteCompared == 370`。此外 `verify_publication.py:313` 用 `root.parent / name` 找前包，新包移到 root `evidence/` 後，不能原樣找到仍在 `geometry-core/domain-decoupling/evidence/` 的舊包。其他三包也不是不帶包級條件的通用 publisher／verifier。

因此後續只需在**新包的有限設定**中帶入已封閉 catalog／實際結果與明確的 repository-relative predecessor 路徑，沿用同一封存及驗證機制；不要改舊包中的 helper 或 seals，也不要把舊 370／295／599 排除直接換成推測值。這是既有工具的包級適配，不需要另建 framework；本次沒有製作或修改該適配。

## root evidence 路徑與版本控制

`product-architecture.json` 的五個 `sourceRoots` 是 `geometry-core`、`geometry-app`、`geometry-templates`、`geometry-web`、`geometry-guide`；三個 `sourceFiles` 是 `current_geometry.c`、`tests/__init__.py`、`tests/binaries.py`。根目錄 `evidence/` 均不在其中。把僅供證據出版／核對的 helper 和 raw logs 放到新 root evidence 包，維持現有 inventory 規則即可，不需新增 exclusion、不需改 scanner 或擴大 source roots。

目前 `.gitignore:24–26` 為：

```gitignore
!/evidence/
/evidence/*
!/evidence/architecture-gate-99455b9f/
```

唯讀 `git check-ignore -v --no-index` 已確認 hypothetical 新包的 README、archive、verifier 都被 `/evidence/*` 忽略。因此現在**尚未允許**新包正常加入版本控制。確定實際名稱後，最小規則變更是緊接其後增加一條精確目錄例外：

```gitignore
!/evidence/geo261-final-validation-<實際凍結識別>/
```

沿用每個現有 P1 包的 local `.gitattributes`：`* -text`，保住原始 CRLF／LF／UTF-16 bytes；不用放寬 root 全部 evidence。現有 root `.gitattributes` 只對舊 `architecture-gate-99455b9f/**` 放 `-text`，不會自動涵蓋新包。全域 `*.exe`／`*.obj`／`*.svg` ignore 仍保留；既有出版格式也明列不收 compiled binaries 或 source checkout。這次未修改任何 ignore／attributes。

## 哪些 pins 現在可沿用，哪些必須等待

**四個 immutable predecessor 的 catalog／seal digests 已可讀取，無須等最後來源 SHA。** 下表只是在此輪讀取兩個 JSON 檔案的 raw SHA-256，並非重跑整包 verifier：

| 包 | CONTENT-MANIFEST SHA-256 | PACKAGE-SHA256 自身 SHA-256 |
|---|---|---|
| original | `3d185f46be22a99e9556e73f23ba5e7adf312f2253ef40bfa3cc2c055a1cc025` | `e828215b3d6c250bf2d088c1dd4be78247b47b4e70769f580ba525968759efc9` |
| followup | `eb0022ad651d55d9d7740b4f3e2351dca36757782230ea32128287d420c0fbb7` | `4de418b8942b01a85c6ce0705b715363f30f43e95a066e4e9e3cbf7f63a7d801` |
| authority | `0da17c9277a71d658aff15c6fbfab42c8bf66d9a2de953f0f1c8fa1511986168` | `34fdbc368708b6633ca6891f2a9af9203ee4dcedfd461b3ae46bffb2a01233e2` |
| closeouts | `71a12f1140f43e56994b19184d59d49af81ed855a7378839dc8c7f348a0d1941` | `d500b347e5e66fce69e3ad016c188e9d5cf38dcd91cea6db8ec590ed9e51e0e8` |

其餘分三個時點，不能都先填成目前 integration HEAD：

| 時點 | 屆時取自真實資料的 pins |
|---|---|
| 實際來源凍結 | 每個 run 的完整 source SHA／tree；source commit object bytes/hash；full Git object manifest 與 selected paths 的 mode/blob/bytes/digest；最終 architecture receipt 的 `sourceBaseHead`／closure。較早已關閉的 `599` run 保留自己的來源，不改成後來 final SHA。 |
| 各 run 關閉、收件清單凍結 | source-before／after receipt hashes；runner／launcher 在執行時真正留下的 before／after claims；所有 raw stdout/stderr/log/exit/receipt hashes、bytes；原始 PASS／FAIL／UNRUN；逐檔 selection catalog SHA 與檔數／byte sums；保留但不打包的 source tar archive hash/bytes。缺少的執行當下 claim 應維持缺口，不能以出版時讀檔補稱。 |
| 新包 bytes 全部生成並核對完成 | `raw-evidence.tar.xz` 實際 raw SHA-256／bytes、唯一 blob 數；各 `readable/` 的 byte-identical hash；新 provenance 與 `VERIFICATION.json` hashes；最後 `PACKAGE-SHA256.json`。archive hash 由產物算出，並非把舊 archive hash 常數替換掉。 |

`publicationBaseHead` 是出版當時 checkout 的基底，與各 receipt 的實跑來源分開記；之後只提交 audit／證據的 commit 不應回寫成原始 run source。新包各欄位須等真實 closeout 與最後來源確定後填入；目前沒有為它們設定假定 SHA、檔數、archive digest 或成功結果。

## 交給 PR reviewer 的最小內容

沿用現有 README＋CONTENT-MANIFEST＋provenance＋`readable/`＋raw archive＋seal。README 逐個來源列出真實結果及明確缺口，讓 Claude 從 PR 讀可讀副本，再按 catalog path/hash 抽出原始 bytes 核對；封存成功不等於產品驗收。原始失敗與修正後成功並列，不跨 SHA 加總成一次全綠。

本輪只核對四包已封存文件／工具、Git ignore／attributes 與現行 inventory 設定；僅新增這份外部筆記。沒有改 repo／Git／舊收據，沒有建立新 driver/framework，也沒有接觸 active `4aec` 工作目錄。
