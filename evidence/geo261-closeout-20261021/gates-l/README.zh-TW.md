本包是同一最終產品來源 L 的實際 Q38／§7 複測，不是從舊帳本外推。來源完整 SHA：43f85313c32410ac01406ab585846bbacafea278；隔離工作樹：/workspace/geo261-gates-l，detached HEAD。未建立分支、commit 或 push。交接來源為 59796b1af9259eb23d30134c2ce5a56317a06091；交接分支未合併。

四個 phase 依序執行，原始裁判、表格與預期值均沿用 L 的正式工具。每次開始及結束均 L clean、檢查的來源 bytes/hash 相同。card 與 axiom 只依既有表格暫改具名 target，逐 byte 還原；沒有額外改裁判或放寬 expected。

| 項目 | 實際結果 | 正式原始入口碼 | expectation runner／launcher／工具 session 碼 | 外層秒數 |
|---|---|---:|---|---:|
| Q38 全 42 | 41 killed、SPM24 既有 declared equivalent；native baseline 27、model baseline 20 | 0 | 0／0／0 | 455.842849766 |
| Q38 controls 全 12 | 9 survived／exit 0、3 unlabelled／exit 1，逐案符合原 EXPECTED | 1 | 0／0／0 | 121.983123108 |
| §7 card 全 53 | 53 killed、baseline 43；每案原具名 restore 綠 | 0 | 0／0／0 | 433.745350973 |
| §7 axiom V01–V05 | 5 killed、baseline 44；每案完整 44 restore 綠 | 0 | 0／0／0 | 90.290380795 |

Controls 原始入口 exit 1 是預期負控制，不是把它改成成功碼。run_controls 的獨立 expected 核對真 exit 0。9 案是 XC36、XC39、XC40B、XC28L1、XC28L12、XC28L13、XC29L1、XC29L12、XC29L13；3 個缺少終端原因標籤的案例 XC40A、XC03L1、XC04L1 維持 unlabelled／exit 1。沒有把 unlabelled、crashed 或 blocked 算成 killed。

Q38 完整跑 SPM01–SPM42，沒有 only/group/explore 篩選。39 組實際編譯的 mutant 來源樹與二進位均可由原件核對，39 個 binary hash 與 baseline 不同；Python-only 的 SPM37、SPM38、SPM40 沿用此次 fresh adapter。39 個 AssertionError 與 SPM38／SPM40 的具名 ModelError 是原裁判規定的 kill；SPM24 的 equivalent 是既有表格分類，並非本次證明所有輸入都語意等價。Controls 另用 --only 明列原始 EXPECTED 的全部 12 案，並非縮減 Q38 42 案。

Card 原 53 案包括 P146-error-fields、P154-identity-boundary、P154-identity-one-message 三個既有裁判自證，正式 target 是 tests/test_grid_card_reference.py。因此本包不宣稱「tests 完全未被暫改」。精確範圍是原表具名 targets 的暫時突變與完整還原；未額外改正式表、runner、expected 或持續修改測試。53 個 red 都是具名 assertion failure，errors／skips／compile_failures／infrastructure_failures 均 0；每案 restore 為原 runner 指定的具名案例，不是每案重跑全 43 baseline。

Axiom V01-remove-gate、V02-ignore-manifest、V03-ignore-source、V04-exempt-latest-pre-adoption、V05-card-adoption-treated-as-pre 全 killed。唯一 target 為 geometry-core/modeling/__init__.py；每次 red 具名失敗、exit 1，還原後在新程序重跑完整 44，exit 0。報告與 verification 保存每個 mutated hash、red 和 restore 計數。

實際父環境透過 env -u CC -u PYTHONOPTIMIZE 啟動，使用 python3 -B、未帶 -O；stack 為 16,777,216 bytes。這能證明本次沒有最佳化執行，但外層僅 assert PYTHONOPTIMIZE 不存在，並未實作對任意 python -O 的完整防護。CC 未指定，依正式工具預設 compiler 契約。

每個 phase 的完整外層呼叫與實際工具 session 回傳在 tool-observations.json；它是事後轉錄，不冒稱工具傳輸層自動紀錄。launcher/<phase>/command.json、receipt.json、.exit-code、.launcher-exit-code 保存真正 Popen/wait 的子碼與父碼。正式工具與 build／裁判 argv、環境、起訖、耗時另見各 phase 的 run-receipt.json 與 command 原件。下列為本次實際正式 runner argv，cwd 均 /workspace/geo261-gates-l；重跑必須另選不存在的新輸出目錄。


q38：

~~~text
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B /workspace/geo261-gates-l/geometry-core/domain-decoupling/closeout-tools/run_gates.py q38 --root /workspace/geo261-gates-l --out /workspace/geo261-evidence/gates-l/q38-run/q38 --jobs 2
~~~

controls：

~~~text
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B /workspace/geo261-gates-l/geometry-core/domain-decoupling/closeout-tools/run_controls.py --root /workspace/geo261-gates-l --out /workspace/geo261-evidence/gates-l/controls --model-base /workspace/geo261-evidence/gates-l/q38-run/bin/model-base --controls /workspace/geo261-gates-l/geometry-core/domain-decoupling/closeout-tools/q38_controls.py --jobs 2
~~~

card：

~~~text
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B /workspace/geo261-gates-l/geometry-core/domain-decoupling/closeout-tools/run_gates.py card --root /workspace/geo261-gates-l --out /workspace/geo261-evidence/gates-l/card-run/card --jobs 2
~~~

axiom：

~~~text
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B /workspace/geo261-gates-l/geometry-core/domain-decoupling/closeout-tools/run_gates.py axiom --root /workspace/geo261-gates-l --out /workspace/geo261-evidence/gates-l/axiom-run/axiom --jobs 2
~~~

Q38 與 axiom 各自從同一 L fresh build 私有 model-base，build 原命令與 exit 0 在對應 run-receipt.json。Q38 的 GEOMETRY_MODEL_BASE=/workspace/geo261-evidence/gates-l/q38-run/bin/model-base；controls 沿用此 fresh binary。Axiom 使用 /workspace/geo261-evidence/gates-l/axiom-run/bin/model-base。兩份 fingerprint 原文收於 private-model-fingerprints；binary 留外部保存，不放可提交 evidence。Card runner 雖設同型 GEOMETRY_MODEL_BASE 路徑，本入口未聲稱另外建置私有 model-base。

下列為內層正式裁判實際 argv；環境除父 CC／PYTHONOPTIMIZE 未設定外，含各 run-receipt 的專屬 TMPDIR、LANG=C.UTF-8、LC_ALL=C.UTF-8、PYTHONIOENCODING=utf-8、PYTHONDONTWRITEBYTECODE=1 與上述 GEOMETRY_MODEL_BASE。


q38：

~~~text
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B -u tests/section_profile_mutation_check.py --jobs 2 --receipt /workspace/geo261-evidence/gates-l/q38-run/q38/receipt.json --logs /workspace/geo261-evidence/gates-l/q38-run/q38/logs
~~~

controls：

~~~text
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B -u /workspace/geo261-gates-l/geometry-core/domain-decoupling/closeout-tools/q38_controls.py --jobs 2 --receipt /workspace/geo261-evidence/gates-l/controls/receipt.json --logs /workspace/geo261-evidence/gates-l/controls/logs --only XC36 --only XC39 --only XC40A --only XC40B --only XC28L1 --only XC28L12 --only XC28L13 --only XC29L1 --only XC29L12 --only XC29L13 --only XC03L1 --only XC04L1
~~~

card：

~~~text
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B -u geometry-core/card-reference/run_mutations.py --output /workspace/geo261-evidence/gates-l/card-run/card/raw
~~~

axiom：

~~~text
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B -u geometry-core/card-reference/run_axiom_mutations.py --output /workspace/geo261-evidence/gates-l/axiom-run/axiom/raw
~~~

Q38／controls 仍依賴 /tmp/geometry-tests/bridge，因此正式排程在 native 全部結束後才執行 gates。首個 bridge-before 逐 byte、hash 與 mtime 接上同 L native-final/final-build-binary-index.json；之後每個入口 before 接上前個入口 after，全部保持相同。bridge SHA-256 為 1dde99f08755c785223bceb3a733ad999311749d8eb5e0be16e1fc7daeb5ed0b，sidecar 為 91a510bf879ff7e3c57e44c44f830a3fd947cfca80faddf07a3d0801bea772d5。每次原 binary 與 fingerprint 都先存到外部 preservation 目錄；本包包含原 fingerprint、before／after index 及原始 mtime，沒有把共享 binary 說成私有或無全域相依。

final-source-process-check.json 在 2026-10-21T00:40:57.301435Z 只讀確認 L clean、8 個已知 launcher／直接子 PID 全部不存在，所有可讀 /proc cmdline 的具名 gate 程序與 gate 工作／輸出目錄存活程序匹配皆空，沒有 cmdline 權限漏項。這是收尾當時的程序快照，並非整段執行期間的完整 descendant 追蹤。

可提交目錄保留完整裁判文字原件、收據與索引。raw-source-index.json 明列每個原始絕對路徑 → 本包平坦化路徑、bytes、SHA-256；artifact-index.json 覆蓋本包全部檔案但排除索引自身。q38-run/q38 映至 q38、card-run/card 映至 card、axiom-run/axiom 映至 axiom，controls 不變。排除 tmp source copies、compiler/binary、.py/.js/.exe/.so 等工具；外部 launcher-code.txt 只保存實跑收據原文。正式可重現工具仍在 L 的 geometry-core/domain-decoupling/closeout-tools。

正式工具 hash：run_gates.py 8dc2e7372da70a22e7f28506270a9709e2f0c3e53419a5043165c2cfe4afcfb3；run_controls.py b7e7430e53d157f6a82050417be7a9f8d77bd50c1fb5f2f3a34a1ba44de8363f；q38_controls.py 64a76303d825d931736f10bef43b23e56e751a79433bd4aeed895c352b740fe2。provenance.json 另核對具名來源及 card 全部 15 targets 的工作 bytes 與 Git L 原 blob 完全相同。

未驗範圍：本包只涵蓋 Q38、其 12 個控制與 §7 card／axiom；同 L native、六 browser、replay、architecture 與 P-189 的結論應引用各自實跑收據。本包不替代那些入口，也沒有重跑 Windows／WSL／遠端 CI，沒有對 #323、#300 或第 7 節使用者待決事項下決定。最大不確定仍是既有 fixture 與突變清單對所有合法輸入的涵蓋度；全部具名案例達標不等於對清單之外的全域正確性證明。
