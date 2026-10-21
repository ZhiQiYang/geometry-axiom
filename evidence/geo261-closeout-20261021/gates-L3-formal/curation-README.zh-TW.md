來源 6589248c9a94bdf0460d8f84dd1610e51048188b 的四個完整 gate 文字證據。此摘要只在同來源 native、四 phase 主／詳細接受器及真退出碼全部核對後產生。

各 phase 的原始目錄結構完整保留；每份原件映射在 curation-source-mapping.json。正式 run-receipt、launcher/dispatch、acceptance-execution、verification、acceptance-review、全部進度與工具觀察一併保存。

Q38是42全案：41 killed與原SPM24 equivalent；39 compiled mutant與3個Python-only分開。controls是原12案9 survived/3 unlabelled；raw gate1與expected checker0保持。card53包含3個既有tests target，依原表暫改並逐byte還原；baseline43、restore按原case。axiom5 baseline與每次restore44。

本輪jobs1；CC與PYTHONOPTIMIZE未設定，python -B且未帶-O，stack16MiB。正式原argv、各子命令與環境均以run-receipt和launcher原件為準；以下是原launcher真正呼叫：

q38：{"killed": 41, "equivalent": 1}；外層秒數 870.8577103520001
["/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3", "-B", "/workspace/geo261-gates-l3-6589248c9a94-20261021/geometry-core/domain-decoupling/closeout-tools/run_gates.py", "q38", "--root", "/workspace/geo261-gates-l3-6589248c9a94-20261021", "--out", "/workspace/geo261-evidence/revalidation-l3-6589248c9a94-20261021/gates/q38-run/q38", "--jobs", "1"]

controls：{"survived": 9, "unlabelled": 3}；外層秒數 217.00801556200167
["/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3", "-B", "/workspace/geo261-gates-l3-6589248c9a94-20261021/geometry-core/domain-decoupling/closeout-tools/run_controls.py", "--root", "/workspace/geo261-gates-l3-6589248c9a94-20261021", "--out", "/workspace/geo261-evidence/revalidation-l3-6589248c9a94-20261021/gates/controls", "--model-base", "/workspace/geo261-evidence/revalidation-l3-6589248c9a94-20261021/gates/q38-run/bin/model-base", "--controls", "/workspace/geo261-gates-l3-6589248c9a94-20261021/geometry-core/domain-decoupling/closeout-tools/q38_controls.py", "--jobs", "1"]

card：{"killed": 53}；外層秒數 438.3904237300012
["/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3", "-B", "/workspace/geo261-gates-l3-6589248c9a94-20261021/geometry-core/domain-decoupling/closeout-tools/run_gates.py", "card", "--root", "/workspace/geo261-gates-l3-6589248c9a94-20261021", "--out", "/workspace/geo261-evidence/revalidation-l3-6589248c9a94-20261021/gates/card-run/card", "--jobs", "1"]

axiom：{"killed": 5}；外層秒數 89.26209334300074
["/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3", "-B", "/workspace/geo261-gates-l3-6589248c9a94-20261021/geometry-core/domain-decoupling/closeout-tools/run_gates.py", "axiom", "--root", "/workspace/geo261-gates-l3-6589248c9a94-20261021", "--out", "/workspace/geo261-evidence/revalidation-l3-6589248c9a94-20261021/gates/axiom-run/axiom", "--jobs", "1"]

Q38階段判讀更正保留原件：尚無model marker不能推定當時正在model baseline。只讀程序取樣的stat/cmdline與task/children讀取限制也完整保留，不用PID不可見或FileNotFoundError證明退出或環境原因。
共享bridge依同L3 native final→四phase before/after串接bytes/hash/mtime；本次封包只讀已保存文字與sidecar，不讀global或binary。初終取樣相同不代表期間從未暫寫。
curation-exclusions.json明列未納入的tmp source copies、private bin與程式碼。q38/axiom兩份private model fingerprint是有意保存的文字例外。external-code-receipts/*.txt是實際外部程序原bytes收據，不是新增正式工具；正式工具仍在來源commit的既有註冊位置。
未驗界線：本包不替代native、browser、P189或遠端CI各自的實跑收據。最大不確定仍是原fixture與突變表對未列輸入的涵蓋度；既有equivalent不等於證明所有輸入都語意等價。請使用者在 PR #288 按本包同L3實際結果更新Q38與§7，其他矩陣項引用各自收據；此包不提出合併請求。
