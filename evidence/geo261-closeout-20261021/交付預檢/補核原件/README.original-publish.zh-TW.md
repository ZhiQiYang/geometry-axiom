# GEO-261：Q38 與 §7 最終來源複測

驗證來源為整合分支 `architecture/geo261-integration-20261016` 的完整 SHA `7dae5f21c7ca401e660450d437e60ba566218da8`。本次在獨立 detached 工作樹 `/workspace/geo261-gates` 執行；未改動產品、正式測試或公理，未提交或推送此工作樹。交接資料來源為 `59796b1af9259eb23d30134c2ce5a56317a06091`；交接分支未合併。

## 正式關卡

| 項目 | 原始入口結束碼 | 結果 | 耗時 |
|---|---:|---|---:|
| model-base 新編 | 0 | 獨立輸出與來源指紋 | 17.292 秒 |
| Q38 正式 gate | 0 | 42 案：41 killed、1 equivalent（SPM24）；crashed／blocked／invalid／survived 均為 0 | 472.701 秒 |
| §7 編譯突變 | 0 | 53/53 killed；每筆還原控制皆綠 | 442.911 秒 |
| §7 公理版本突變 | 0 | V01–V05 全 killed；每次還原完整相容 suite 皆綠 | 71.413 秒 |

Q38 原生基準 27 題、模型基準 20 題，全數成功且零 skip。41 個 killed 中，39 個由具名 `AssertionError` 偵測；SPM38、SPM40 由事先登記且訊息吻合的 `geometry_app.model_common.ModelError` 偵測，不能把這兩筆原始 ERROR 紀錄改稱 AssertionError 或 crash。SPM24 是既有明列 equivalent：有效進階 frame 已保證 `up=-V` 合法，撤除重複條件不改接受集合。

§7 編譯突變先跑 43 題完整基準。53 筆紅控制均為子程序 exit 1、至少一個斷言 failure，且 error、skip、編譯失敗及基礎設施失敗計數皆 0；每筆逐位元組還原後重編並重跑該案所選方法，均 exit 0、零 failure／error／skip。公理版控先跑 44 題完整基準；每個 V01–V05 撤防線後具名測試 exit 1、零 error／skip，恢復後完整 44 題均 exit 0。

## Q38 裁判控制

控制檔 `q38_controls.py` 逐位元組取自交接 commit 的 `handoff/scripts/q38_controls.py`，SHA-256 為 `64a76303d825d931736f10bef43b23e56e751a79433bd4aeed895c352b740fe2`。`run_controls.py` 在執行前已固定 12 案的預期，禁止將所有非零結束碼一律視為成功；實際逐項結果另列 `controls-results.md`。

正式 gate 的成功標準是故障確實被指定原因偵測。控制的成功標準則是：舊路徑或不完整撤防線不能冒充同一故障已被 killed，且其他原因的紅測試不能冒充指定原因。原始 gate 對這批控制預期 exit 1；外層控制核對只有在兩組基準全綠、12 案身分／verdict／子程序結束碼精確吻合，且工作樹乾淨時才 exit 0。兩種結束碼分別保存在 `controls/run-receipt.json`。

## 實際執行及重現

每組 `run-receipt.json` 保留完整來源 SHA、cwd、環境、stack limit、命令、起迄時間、實際結束碼及工作樹前後狀態。Q38 的逐案原始終端例外、編譯命令與二進位雜湊在 `q38/logs/`；§7 的逐案編譯 stdout／stderr、命令、紅控制及恢復控制在各組 `raw/`。UTC 時戳為原始程序收據。

下列命令從待驗 repo 根目錄執行。`--root` 必須指向乾淨工作樹；各 `--out` 必須是不存在的新目錄，避免覆蓋前次證據。工具本身將 stack 設為 16 MiB，Q38 設兩個 worker；這只調整並行度，不更改測項、斷言、判準或 timeout。`run_gates.py` 在 `--out` 的上一層建立獨立 `bin/`，不與其他工作樹的 `/tmp/geometry-tests` 共用產物。

```sh
python3 -B geometry-core/domain-decoupling/closeout-tools/run_gates.py q38 --root "$PWD" --out /tmp/geo261-gates-retest/q38 --jobs 2
python3 -B geometry-core/domain-decoupling/closeout-tools/run_gates.py card --root "$PWD" --out /tmp/geo261-gates-retest/card
python3 -B geometry-core/domain-decoupling/closeout-tools/run_gates.py axiom --root "$PWD" --out /tmp/geo261-gates-retest/axiom
python3 -B geometry-core/domain-decoupling/closeout-tools/run_controls.py --root "$PWD" --out /tmp/geo261-gates-retest/controls --model-base /tmp/geo261-gates-retest/bin/model-base --controls geometry-core/domain-decoupling/closeout-tools/q38_controls.py --jobs 2
```

調度器對應交接的 `q38_gate.sh`／`card_ref_mutations.sh`，將 Windows／WSL 固定路徑改成 CLI 路徑，使用既有隔離工作樹並檢查乾淨狀態，不執行 checkout 或 clean。正式裁判直接來自待驗工作樹，不複製或修改正式裁判邏輯。重現不依賴使用者電腦上的其他交接腳本；只需已登記的三個工具、Python、GCC 及待驗 repo。

## 範圍與不確定性

- 這批收據只涵蓋 Q38／§7。未據此宣告 canvas、七項整合測試或 P-189 通過；它們由各自收據驗收。
- Q38 裁判按現行定義排除 `test_source_index_typed_closure_and_display_identity`，因該方法要求正式 binaries.py 收據，而拋棄式突變 binary 不具該身分。這項排除原已存在，本次未新增。
- Q38 的 42 案是現有逐條故障注入，不宣稱與提案 AC16 的全部 AC 一對一對應；現有裁判檔頭已明示這個範圍。
- 本次未重產 `tests/mutants_results.json`。§7 的暫時修改均已逐位元組恢復，正式來源與 `tests/*.py` 最終無 diff；完整帳本是否適用其他變更仍須由該變更的來源指紋檢查決定。
- 本次與其他隔離工作樹的建置／瀏覽器工作曾並行，因此執行耗時只記錄本輪成本，不能作 P-189 效能證據。
- 最大不確定性是這些既有有限故障集合以外的覆蓋缺口；通過此 gate 不表示任意未列出的故障都會被偵測。
- 沒有改動第 7 節使用者待決事項，也沒有執行任何 GitHub PR 操作。

`provenance.json` 保存正式裁判、夾具及來源工具的雜湊。原始文字證據完整保留；二進位與暫存來源拷貝不納入提交，二進位身分由原始收據的 SHA-256 保存。
