# 候選採用工具最小真 Git 反證（僅準備）

沒有執行此套件、沒有採用產品來源、沒有寫任何真分支。root 必須先核當下容量並綁定 REQUEST，再以正式 require_escalated 執行。所有合成 Git objects、worktree、bare remote、TMP、capture原流只放同一個新 OWN 直接子目錄；準備目錄僅放腳本與小metadata。

採用工具本體不修改。subject固定 SHA256 `71b0b4eb9ddde59f6b8e9ab90eb2492f8e403d1469a645d81864585a631fefba`。沿用原 mature `build_tree` 真實函數；`publisher_state`、`clean` 與唯一 candidate `update-ref` call 用 AST 從同一已審 subject 抽出，在**只屬合成fixture**的 namespace執行。這只測所列 primitives；不呼叫正式main，也不替換/跳過validate_originals假稱正式schema通過。

每個phase先建立全新的tiny Git worktree和本地bare remote，原train branch被checkout、index真存在，candidate另有ref。正例以原build_tree改恰3葉，執原candidate CAS、普通push本地候選ref，核原HEAD bytes/index hash/train ref/status完全不變、其他樹葉不變且remote train仍原base。沒有網路GitHub命令。

三組各有 fixed／withdrawn／restored：

- **cas**：preflight通過後在合成candidate製造另一個並行child，再用已過期的expected parent執原CAS。fixed/restored必收到Git原nonzero與其expected/actual OID原錯誤、candidate保持race。withdrawn只從抽出的update-ref call拿掉expected-old參數，應錯誤覆蓋race，harness精確失敗 `CAS_EXPECTED_PARENT_NOT_ENFORCED`。
- **scope**：原三葉外加入一個已存在的第四產品葉，原build_tree必拒絕。withdrawn只在私有Python process把CHANGED policy集合加該第四葉（與原tiny proof相同方式），harness精確失敗 `FOURTH_PRODUCT_PATH_NOT_REFUSED`。
- **preservation**：在合成fixture依序合法地改HEAD指向、修改index、移原train ref，每次驗原clean必拒絕，再保全原bytes恢復。withdrawn只拿掉抽出clean的第一個歷史publisher state比較，三種破壞會被錯放，harness精確失敗 `HISTORICAL_PUBLISHER_CHANGE_NOT_DETECTED`。candidate ref檢查仍保留。

runner要求每組退出碼恰0/1/0、withdrawn的真AssertionError與具名文字完全吻合，不能把timeout、setup失敗、Git基準錯誤當kill。完整原request/stdin/stdout/stderr/result由不變c387錄製；phase JSON另記真Synthetic身份，不使用S10/A/F冒執行來源。

保守新增規畫 **16MiB**，不是降低任何正式native/源碼門檻。root先在共享2GiB規畫中保留此量；runner另查真out掛載free≥16MiB並在每phase後計allocated最大觀測≤16MiB。若超出，保留所有原件並真報紅，不清掉原流重試。不連續取樣、不稱真峰值。此套件不證真正source/index/fixtures/ledger schema、遠端GitHub bytes、64/128MiB或正式root租約；這些仍由正式adopter/transition/checks負責。

root入口（REQUEST現在全false/out null，不能照跑）：

```
python3 -B run_candidate_tiny.py --execute --request <root-bound-request> --request-sha256 <exact-hash>
```

正式採用不在本runner中；root執行後另交第二代理查actual原件，才可把本工具primitive反證記為通過。
