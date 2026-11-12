# #348 全帳本規則靜態核對

本件只讀來源與已存在 JSON；未匯入／執行 `mutate.py`、未跑測試、未編譯、未修改來源或 Git。

固定來源：`7a0e6dd81c54066995981393925fa46a815de2f8`，工作樹 `/dev/shm/pr348-final-source-7a0e6dd8`。讀取 Git HEAD 命令 exit 0。原始檔案 SHA256：

| 檔案 | bytes | SHA256 |
|---|---:|---|
| `tests/mutate.py` | 139592 | `bd2d0c768439a93e7f848ff0299a5b164aabe1d80a0f4e9a5bcb7ab83eb4b315` |
| `tests/mutation_bridge.py` | 33469 | `7febe80ba29a3c0e7821277f47102a57a0c9ab0610a02e8981bb0eb2a79b3c58` |
| `AGENTS.md` | 19140 | `d3fcb30f0e711a4130f032a2ae8edab70c0cd69897c37ae504cd5f3416d3cbca` |

## 覆蓋範圍與退出碼

以 Python `ast.parse` 只讀解析模組頂層 `MUTANTS = [...]` 和全部 `MUTANTS += [...]`，逐筆 `dict(id=...)` 常值讀取：123 筆、123 個唯一 ID；core 70、bridge 53。這是靜態表大小，不冒充執行結果。另讀既有 `/dev/shm/pr348-ledger-7a0e6dd8/ledger.json`：ID 集合與該表全等，無漏、無額外 ID，記錄為 114 killed、1 crashed、5 equivalent、3 retired。

`mutate.py:1361–1376` 對所有已登記 ID 逐筆核對，缺紀錄為 unrun，孤兒紀錄為 stale；`1392–1399` 的原退出碼規則是 blocked 優先 exit 2，否則 survived／invalid／stale，以及 strict 的 unrun 任一存在則 exit 1，其餘 exit 0。完整 `run_pass` 在 `1636–1664` 重合 core 與 bridge 後再次核全表；`check_pass` 在 `1667–1687` 使用 `require_execution=True` 與 `strict=True`。因此 123 並非「123 個 killed」，也不等於產品 native 全驗收。

## 三種非 killed 判決

- **crashed**：`RUN_RETRIES=3`（`mutate.py:94`）；`815–842` 要求基準已過、三次同一組非空存取違規夾具，並與 killed 分開計。單次死亡、非相同夾具、啟動失敗、逾時或其他異常不能當偵測成功。`execution_problems`（`1212–1267`）重新由已存完整結構化 oracle 結果判決，核 `crashed_on`；基準必須 survived。AGENTS `218–225` 與此相符。本次只有 M20，`crashed_on=["_test_lshape.scene"]`，已存 3 attempts；原 why 明列三次 `-11`，不是斷言殺死。原件逐次核對由上層核收負責。
- **equivalent**：M09、M23、M56、M36、M110，定義在 `mutate.py:148,222,285,318,583`；錨點須恰一次（`1062–1095`），理由文字、變異定義及來源閉包須一致。完整執行預設 `audit_equivalents=True`（`1439,1451,1636`），仍實際編譯與跑 oracle，只有 survived 才轉 equivalent，若產生其他非 blocked 判決則 invalid（`1595–1599`、bridge `535–538`）。**頂端舊說明「equivalent 不受 oracle 約束」不可單獨引用**：正式 check 的 `require_execution=True` 在 `1344–1347` 明確核等價 audit 的 oracle，並驗完整 execution receipt。本次應保留「5 equivalent」，不可改稱 killed 或免跑。
- **retired**：M51、M55、M35，定義在 `277,299,313`。`1087–1090` 要求舊錨點完全不存在；再出現即 invalid。保留逐字退役依據與 mutant/record checksum（`1283–1302,1320–1327`），不帶來源／oracle 閉包、不編譯；這是已明示的退役規則，不能算 3 次真執行或新增豁免。

## 來源、裁判與 binary/cache 身分

- `Sources`（`mutate.py:855–886`）：core 與 bridge quoted-include 聯集，以原 bytes 讀取後 CRLF→LF，按相對路徑／檔案 hash 排序產生 closure。此正規化僅來源行尾；不是對測試輸出正規化。
- core oracle（`889–905`）：`run_tests.py` 原文與 `TESTS` 引用的各 scene 原文（LF）共同 hash。bridge oracle（`mutation_bridge.py:102–114`）：具名 methods、RESTORED、全部 `tests/*.py`、`tests/*.c`、`tests/fixtures/**/*.scene` 與 root scene；排除 JSON 帳本避免自指。
- 定義／紀錄完整性（`mutate.py:1182–1189,1305–1357`）：record checksum、description／equivalence或retired理由、mutant hash、目標來源與全 closure／oracle hash均核；不符為 stale。純來源恢復可還原原判決，但不可移標 execution SHA。`execution.head` 以原 full 40 hex保存，原程式使用 closure 判有效，未要求把歷史 execution 改成目前 adoption commit。
- core cache（`938–977`）：mutant、closure、實際生成注入來源、編譯命令四指紋全等；sidecar 必須有實際 ELF hash且bytes匹配。`adopted:` 舊推導 sidecar 一律 stale；只有 hit 可沿用。原 baseline 亦核 closure與編譯命令。`1255–1265`：cache artifact 若存在必須與原 execution 相符；乾淨機器缺 ELF不會由此自動使已具完整收據的結果失效。
- bridge（`mutation_bridge.py:402–461`）：baseline 與 restored 必須跑完全部 RESTORED；mutant methods必須來自原RESTORED (`mutate.py:1071–1085`)；重試只允許原存取違規規則，最多3次，原檔名序列及 stdout hash不得重用同一輸出冒三次；三組 build exit 0、sidecar source closure、各 ELF身分、原流hash、命令末尾methods一致。POSIX baseline/restored ELF須逐byte hash同；`byte_restored`及原oracle一致。若現存 mutant ELF不同亦invalid receipt。
- 真執行入口（bridge `467–542`）要求 committed SHA、scratch同HEAD/closure、變異錨點一次，逐筆原位撤回並重編／跑RESTORED；所有上述規則為原程式要求，本輪未新增或放寬。

## 本件範圍與交付限制

已完成靜態規則、AST ID全集與既有 ledger 的集合／判決分類核對，命令皆 exit 0。未另跑 `--check` 或任何產品測試，未獨立重判每個內層 raw；正式退出碼、各 raw hash、binary 及來源前後保存，仍以本輪上層對原 receipt 的核收為準。不能將本報告當新測試輪次，也不把 114/1/5/3 變成 123 assertions killed。
