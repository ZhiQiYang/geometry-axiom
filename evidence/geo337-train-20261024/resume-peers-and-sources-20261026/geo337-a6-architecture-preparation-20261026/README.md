# a6 架構實際來源與四檔準備

狀態：只備工具；未 materialize、未跑裁判、未組裝、未採入產物。必須另經獨立靜審及 root 新容量／排程准入。三項真正執行均由 root 用正式 require_escalated 和原 c387 recorder 包裝。

固定 source：`a6f4013364e21bcb7239b5dcc25caac0f6d61f77`。

1. `python3 -B prepare_source.py --execute-root-approved`
   - 以 S10 已封存 SOURCE_MANIFEST 的全部 3763 selected leaves 為集合，從 Git a6 逐檔取得原 bytes。保留完整 docs／prototype、604 宣告來源和五份 fixtures；不做縮減版 architecture scan。
   - 普通 local `git clone --shared --no-hardlinks --no-checkout`，只在新 `a6-architecture-source-20261026` 建 private Git 及 sparse checkout；不讀取或修改歷史 F10-pool／seed 的產品檔，不改其 nlink。
   - 新 private Git 的唯一 alternate 指向既有 publisher-source/.git/objects。這是持續依賴；root 不得在新 checkout 尚使用時移除 publisher objects。
   - 固定 selected inventory 與 S10 的差異只能是決策佇列；完整非 evidence diff 也只能有該檔。其新 raw hash 必須為 `e6f2aee291850d9aaf8cc0026994f6c86894bb2a7849798ddd11cd63c5558740`。這是來源識別，不是批准其中任何新語意。
   - 新來源、索引、raw capture、metadata、目錄與 64 MiB 餘裕合併檢查原兩 OWN 的 2 GiB 規劃上限及實際輸出掛載；不足就拒絕，未降低數字。沒有額外 mutation seed。

2. 新 source 實際 peer 必須提供 `exit_code:0`、`blocking_findings:[]`、`source_sha:a6完整SHA`、`source_result_sha256:實際RESULT雜湊`。Root 綁 `ROOT_GATE_REQUEST.template.json`（預設 lease=false），然後以原 16 MiB stack 執行：

   `python3 -B run_original_gates.py --request <bound.json> --request-sha256 <hash> --execute-root-approved`

   真跑 `architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json`、`test_architecture_contract.py`、`test_product_architecture.py` 三條，原 argv／無新 timeout／所有 exit、stdout、stderr、環境與 SHA 完整 capture。某條紅仍收齊三條；紅則工具 exit1。來源原 index 保全，Git identity 使用 out/private-index；604 closure 與完整狀態前後比對。

3. 新 gate peer 提供 `exit_code:0`、`blocking_findings:[]`、`source_sha:a6完整SHA`、`gate_result_sha256:真三條RESULT雜湊`。Root 綁 `ROOT_ASSEMBLY_BINDINGS.template.json`，以原 16 MiB stack 執行：

   `python3 -B assemble_a6.py --root /dev/shm/geometry-axiom-geo337-20261025/a6-architecture-source-20261026 --sha a6f4013364e21bcb7239b5dcc25caac0f6d61f77 --out /dev/shm/geometry-axiom-geo337-20261025/a6-architecture-four-original-20261026 --root-execution-lease --bindings <bound.json> --bindings-sha256 <hash>`

   由已審 S10 assembler 最小差分產生，完整差分見 ASSEMBLER_DIFF.txt；原 validate_gate／validate_inputs／snapshot／index checker 語意保留。只接受新 a6 三條真正收據（batch 只有三條0；沒有捏造 tracked-ledger row）。manifest／scan 保持原 bytes，604 closure 保持原值；report／receipt 改為 a6 原裁判與當次決策快照。

歷史 M6e50 九組反證／兩 neutral 原樣保留原來源，不稱 a6 重跑。全帳本仍引 S10 真重產原件，是否於 a6 有效另由 tracked `mutate.py --check` 判定；此工具不跑也不改帳本。產物採入、完整原件封包、原始退出碼與遠端交付均為後續獨立步驟。

`check_binding.py` 只有合成收據，驗證舊 S10 SHA 及 204/205 數量不能冒作 a6 完整三裁判；不是產品驗收。
