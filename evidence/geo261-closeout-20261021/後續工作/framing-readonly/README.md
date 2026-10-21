# framing 唯讀預審封裝

**本包來源是 framing 分支 `1126991c9dbd3de92d8cce6eab2419f8f7970e34`，不是 #288 的受驗來源。** 沒有產品修改、提交、合併、開 PR、原生編譯、完整 suite 或 browser 驗收。

先讀 [唯讀預審報告](framing-readonly-review.md)。該檔從外部報告逐位元組複製，來源／封裝 SHA-256 與相等核對在 `manifest.json`。

## 證據取得時間與界線

最初審查時的 stdout／stderr 只出現在工具回應，沒有落地成獨立原始檔。以下是收到封裝指示後，於同一固定來源**重新取得**的輕量核對；每組新的實際 UTC 時間、命令、cwd、來源、退出碼及輸出 hash 均在 `runs/*/receipt.json`。不把這次重取時間改成最初審查時間，也不補造原來那次 FileNotFoundError 的 raw 收據。

- `pure-counterexample/`：從實際來源 AST 只取 `CORE_CHECKS`、`core_limit_problems`、`verdict`，傳入兩個固定資料。stdout 顯示正確理由與錯誤 C8 理由在同一端面都被判 core_limited。exit 0 是微量程式成功結束，**不是「錯誤理由應接受」的驗收通過，更不是 killed**。
- `static-checks/`：六份變更 Python 只做 AST 解析；對 Git 基底及本 head 的 JSON 做靜態比較。確認 golden 只增加 64 個空 core_limits，step／step_mirror 的 528／1056 個排法集合搬移不變。沒有 import oracle 或執行其 suite。
- `runs/`：同時保存 Git 來源、乾淨狀態、提交歷史、變更範圍及遠端 ref 的實際輸出。
- 兩份小型取樣原碼只存為 `code.txt`，無執行權限；它們不是新產品工具或 oracle 副本。完整程式由指定 Git SHA 取得；受讀檔案的 Git blob／raw hash 索引見 `source-files.json`。

第 22 輪 `round22/`、`run10.py`、`source-mutants.txt` 及原 #251 第 3 阻擋／第 4 須改全文未在可讀交接與分支找到；本包沒有補造這些資料。詳細缺口與未執行驗收見報告。

原三阻擋一須改未自行解除；最大不確定性是缺少的原審查要求與完整歷史收據，以及更廣房型中的分類影響。#288 仍優先，framing 審查與程式均不帶入 #288。

