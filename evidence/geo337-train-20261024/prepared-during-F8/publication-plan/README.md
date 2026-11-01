# F8 背景準備成果的候選出版清單

以 `MANIFEST.v2.json` 為目前清單：877 個 regular 檔名、5,825,898 bytes，低於 8 MiB。這只是選定來源檔案及 hash 的清單，尚未建立封包、複製來源、寫 Git 或推送。root 審查並核對來源未變後，才可在新 evidence prefix `prepared-during-F8/` 出版。當前預期父提交為 `ecdcc22c78d3fcbd44847674b7b38965a5edbfea`；正式來源仍為 F8 `75a1e93811a52b69385cbdaf6a09d773ed9052ad`。

五個工作包保留完整選定準備目錄、同儕報告及原合成命令輸出：

- F9 nonperf-v2、37 argv 計畫、真 tiny Git rename 0/1/0；F9 尚未綁定、37 argv 沒有被宣稱執行。
- F8 full123 terminal collector-v2 及真 metadata 0/1/0／五個壞 JSON 向量。沒有讀取、凍結或收件目前活動的 full123 job/cache/outer。
- F8 memo copy-v2、四處機械撤回保全及 copy/hardlink/copy 合成反證。正式 175 ABC、memo profile 尚未由這份準備執行。
- #341 cost-v2、完整 metadata/protocol 原流及解決 truncated FACE 缺陷的 current peer。尚未編譯或量測產品成本。
- #348 唯讀根因準備、Python 協定守門、原 first-only tiny C protocol 與 actual peer。原 first-only 61 checks／26 commands；產品 ELF、N512 與效能根因未實測。小 C `builds/` 是此包的合成 stub executables，不能當作產品二進位。首次缺事前環境／磁碟紀錄的限制原樣保留；未實跑 `r2/` 草稿排除。

另附 QUESTIONS 的文件 peer、真 first-attempt exit1 與 resume exit0 全原流。前者只在 Git add 留下警告及指定 tracked 葉的 staged bytes；後者核對原 HEAD／staged bytes 後正常 commit/push。兩份結果都保留，不能把 first1 重標0。

## 範圍與凍結方式

`source` 是原件絕對路徑，`path` 是候選出版相對路徑。每葉附 size、SHA256 及 device/inode/mode/nlink/mtime/ctime；讀取前後與清單結束時狀態一致。既有 PREPARATION/PINS/INVENTORY 原葉與已審 anchor 均核對。此處的 freeze 是 pin 與讀取穩定性，不是 chmod、鎖定或更動來源；真正出版前仍須按清單重新核 hash/state。

所有 `.git` 目錄、objects、Python cache、未列來源均排除；合成 rename fixture 的目前檔案、Git 命令原 stdout/stderr（包括 nested Git bytes 的 hex）完整保留，原 `.git` 在 `/tmp` 原處不刪。memo 合成 hardlink 反證的兩個檔名都列入且保真 nlink/inode；如日後建 tar，應每個選定檔名獨立保存 regular bytes，不產生指向外部的 hardlink/symlink 成員。

`MANIFEST.json`、`SUMMARY.json` 是追加 QUESTIONS 之前的原準備版本，保留不覆寫；current 為 `.v2.json`。不同 peer 的 initial/rejected 報告也保留歷史身分，以其明列 V2/actual current 報告為準。F9 與 memo 第一份 metadata proof 的原 argv 指向 v1，沒有移標為新 v2 實跑。這些是工具可靠度與準備的證據，不能解除 R8 exact 三差、B′/C 未核可、P-189 或 required CI 阻擋。
