# L3 gates 封包準備；尚未執行

固定來源為 `6589248c9a94bdf0460d8f84dd1610e51048188b`，來源根目錄為本輪 `gates/`，預定輸出為本輪 `gates-publish-clean/`，最終副本為 `/workspace/geo261-evidence/final-bundle/gates-L3-formal/`。copy proof 另放 sibling `gates-L3-formal-appendix/`。現在只有外部腳本與待填 manifest；未讀取正在變動的 phase raw，未執行封包或產品，未碰 global／binary。

`curate-gates-l3.py` 沿用已凍結 L 封包的 copy2→原件映射→artifact-index→逐 bytes bundle copy 流程。原方法 SHA256 為 `091c26cdd312fa73980f2864186e8ddce35a77ba7a9afe75933efcbb22a8b753`。新增的是本輪完成條件、兩層接受器真碼與產物綁定、排除清單，以及明確保留更正與程序取樣限制；不修改正式工具或判準。

必須先等父代理確認四 phase 全部完成及還原，並明確放行封包。屆時另存一份完成 manifest，不能直接執行目前的 `gates-curation-completion.template.json`。模板保持 `readyForCuration=false`，所有尚待凍結的原件 hash 都是 null；工具觀察 pointer 只填父代理已指定的固定schema路徑，沒有填任何未出結果。未完成的模板會被拒絕，沒有任何接受結果。

完成 manifest 的來源、phase順序、jobs1與必需原件集合固定，不能刪 phase、改來源、換路徑、改數量或跳過某層。`pins` 的31個鍵必須完整相同，每個值填當次已完成原件的實際 SHA256；腳本重新讀取核對。native verification 另釘原 `ee80438dce224cf9d473184c4ffe97a4c690d401d98eecdbcbd5e458449df93b`，instance 另釘 `ad0e74a3798fedf240d7a02af82ee7849496981276418335c38b9f36715ac1f3`，接受器準備收據另釘 `fa46830092cfcf222f459b6c48e27b9d60b1f0db569ebcfa7b834913b17d8ad4`。

四 phase 各自必須有主 `verification/PHASE.json` 與詳細 `acceptance-review/PHASE.json` 的同 L3 accepted 結果、原分類與原數量，以及 `acceptance-execution/PHASE-{primary,detailed}-{command,receipt}.json` 和兩份 stdout／stderr。真正執行收據的 sourceSha／phase／cwd／argv／toolSha256／exitCode、未最佳化環境、command原件hash、executor原碼hash及 `producedReport{path,bytes,sha256}` 都會核對。接受器真正cwd是本輪BASE，正式gate的cwd才是工作樹，兩者分別核對。收據結構已只讀對照本輪完成的 Q38 兩份 receipt；這是schema參考，不將尚未完成的其餘phase冒稱通過。

腳本亦核原父 launcher 真子碼與父碼、持久化退出碼、16 MiB stack、CC／PYTHONOPTIMIZE缺省、phase前後 source clean／原bytes還原。Q38開始時間不得早於native完成；每個主接受器須在phase完成後執行，詳細接受器須在主接受器完成後執行，下一phase須在前一詳細接受器完成後開始。工作樹 HEAD及具名來源 bytes在封包前後再次核對；不由manifest自填true代替實際資料。

Q38仍是42案、41 killed＋原SPM24 equivalent，39 compiled與3 Python-only分開。controls仍是12案、9 survived＋3 unlabelled，raw1與expected0分開。card仍是53案及原3個tests target暫改還原；axiom仍是5案。所有病因、來源樹與red／restore的完整詳細判準由已固定原碼接受器先真跑0，封包程式不改判準或將blocked／crashed算通過。

`toolObservationPointers` 固定使用父代理已指定的最終schema：`phaseObject=/phases/PHASE`、`exitCode=/finalToolResult/exit_code`、`launcherReceiptSha256=/launcherReceipt/sha256`，腳本拒絕其他pointer。四個phase一個也不能少，正式工具與acceptance executor的實際工具退出碼皆必須整數0，session/chunk必須存在且父收據path/bytes/hash須真匹配。這些pointer只是原件位置，不是宣稱結果的值。工具觀察仍明示為事後逐欄轉錄，不能改稱transport自動日誌。

原目錄結構保留為 `q38-run/q38`、`controls`、`card-run/card`、`axiom-run/axiom`，並完整納入四launcher、dispatch、acceptance-execution、verification、acceptance-review、進度、command、receipt及其他正式文字檔。固定必收 `q38-progress-interpretation-correction.json` 及 `q38-readonly-process-samples.jsonl`：尚無model marker不能推定正在model baseline；stat/cmdline可讀而task/children出現FileNotFoundError，不能當作退出、全子樹清理或環境原因的證明。

封包前逐件重核既有 `primary.artifacts` 與 `detailed.rawFileIndex` 所釘的 bytes/hash，缺檔或驗收後變更立即阻擋；每phase實際要copy的正式raw集合必須與原接受清單完全相同，所有主接受器引用原件也必須在映射中。不能只列現存檔重新算hash就宣稱完整。

`tmp`、`bin`、`__pycache__`、`.pytest_cache`整個子目錄不遍歷，不讀binary；來源碼／binary副檔名與可執行非文字檔也明列為排除。Q38／axiom兩份私有model-base fingerprint是明示文字例外，保留原bytes與來源映射。未知副檔名或帶execute bit的正式文字檔會阻擋，不能靜默丟掉原始證據。`curation-exclusions.json`列實際排除的目錄／檔案及原因；沒有遍歷的暫存樹不虛構檔數或hash。

共享 bridge 從同L3 native final index經四phase前後索引逐段核來源、原件hash與mtime；保存現有launcher sidecar文字，不讀global或binary。來源原碼收據只在 `external-code-receipts/*.txt`，標明是外部調度／接受／封裝程式原文，並非新增正式產品工具。正式工具仍在來源commit的既有註冊位置。

完成後的實際命令形式為：

```text
env -u PYTHONOPTIMIZE python3 -B /workspace/geo261-evidence/revalidation-l3-6589248c9a94-20261021/preparation/curate-gates-l3.py --completion-manifest /workspace/geo261-evidence/revalidation-l3-6589248c9a94-20261021/preparation/gates-curation-completion.json
```

上面的完成 manifest 尚未建立，命令未執行。屆時父程序需直存stdout／stderr與真正exit收據，工具實際回應另作明示事後轉錄；放在appendix，不回改主子包。主 `artifact-index.json`排除自己，完整copy proof包含它，copy前後原bytes／mtime一致。若任何原件變動、缺檔或條件不符就停止並保留結果，不修criteria。

原子發布使用固定 sibling `/workspace/geo261-evidence/final-bundle/gates-L3-formal.staging`。staging與正式BUNDLE都必須預先不存在；先copy到staging，逐件bytes／mtime及完整檔案集合核對成功後，以同一父目錄的 `os.replace(STAGING,BUNDLE)` 一次發布。此前正式路徑不會暴露半成品；發布後程式不再寫入主子包，copy proof與後續執行收據只放包外appendix。若copy或核對失敗，保留staging與OUT供檢查，不冒稱完成、不重抽覆寫。

最大未確定處是其餘phase結果與最後工具觀察尚未全部凍結；目前只做AST／讀碼核對，沒有證明新封包腳本對尚未產生的原件能實際完成。正式全四phase原件到齊後，仍需按上述固定契約實跑封包並保真退出碼。

未執行草稿的只讀同行審曾指出cwd假定錯誤與缺少原raw索引重核，已在封包前修正。舊稿原bytes保留在 `gates-curation-draft-before-review.txt`（SHA256 `2f4195805f6d89db12f7c230edd197df98b451010e565217fb9359215545fdc9`）；這不是任何正式gate／接受器失敗，沒有改驗收原件或判準。

原子發布修改前的已審、未執行稿另保存在 `gates-curation-draft-before-atomic-publish.txt`（SHA256 `53a8a6ec2bec74949f3fb4052a4dddcf1183a119533c01ce2f76bd14d57b19ef`）。修改只限staging預檢、複製目的地、逐件核對位置與一次rename發布，不變更來源、正式判準或接受條件；原準備收據與索引也保存為 `.before-atomic.json` 歷史原件。
