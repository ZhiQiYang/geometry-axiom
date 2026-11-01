# H 初始化修正：既有原件對抗審查

產品來源：`2c4635577a8fcb11e88b346547f7bb1c7b739fb7`；基底：`6df0264f75e84f03adb70746b6ac3db07a9910fc`。

審查結論：未發現阻擋此局部修正的缺陷。唯讀檢查 1777 項，exit 0；這是收據與程式審查的檢查數，不是新增正式測試數。

- 四個變更檔案符合預期。產品只將 `ReferenceEval` 的完整零初始化移到 fallback 分支；持續狀態分支先取得有效 ctx，失敗仍原樣返回 false，沒有讀取未初始化 local。
- 原本 13 個測試方法及其他原方法逐位元組保持不變；新增 1 項，registry 只由 13 改 14，沒有放寬斷言或時限。
- 原 runner 確實跑完 14/14，0 失敗、0 skip、0 import error；原程式、外層及 reaper 均 exit 0。
- 219 個 source manifest 檔案皆與公開 Git SHA 和實際來源相符；169 個子命令完整 stdout/stderr 及 89 筆 native 執行紀錄交叉核對；52 個 compiler snapshot 的 189 份不同原件逐一核 hash。
- 每個 phase 的 fallback 校準都實際攔截一次 127,584-byte 清零。fixed/withdrawn/restored 工作量 exit 為 0/1/0；清零 calls 為 0/2/0、bytes 為 0/255168/0。撤回版精確失敗：`ASSERT:persistent-reference-local-zero-work line=166 expr=local_zero_calls==0&&local_zero_bytes==0`。
- 三個 phase 的 persistent、fallback、allocation-failure、ordered-graph 均 exit 0；撤回版的失敗被限制在多餘工作量，而非破壞語意。

限制：本 focused 測試使用原 `-O0`，不是 `-O2` 正式 N16/R8 效能收據，不能據此宣稱效能紅燈消失。Windows 未跑；其 portable 分支只觀察初始化路徑。原 native ELF 為 hash-only（payload_retained=false），未宣稱留存執行檔 payload。完整 native、6 browser、帳本與架構重產仍需在主線最終 SHA 完成。

執行指令：`python3 -B /tmp/geo337-h-init-resume-actual-peer-20261025/audit.py`；exit 0。

`REVIEW.json` SHA-256：`6fde0efefd97340bf49c0529062e40b42663207cf8fe5c5d8ec4f7dd351c11c8`。
