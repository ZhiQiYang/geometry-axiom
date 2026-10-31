# #314 v2 失敗／v3 專項反證完整收件準備

只收既有終態，不執行產品、不讀 live NATIVE，不變更分支。固定來源 F9 `4f8a794f4167c3562eb182045102e86e9e37cca9`；兩次皆為暫時套用已審測試修補及具名 K 探針，結束恢復 F9，不能當成新的已修 final SHA 或完整 native 通過。

- v2：204 regular、13,578,903 B，原 outer 1。保留精確 `original ROOT index bytes/inode/metadata untouched` 失敗與 `INDEX_AFTER_FAILURE.bin`，也完整收 staged-index、私有 objects、所有原 CLI/環境/全 stdout、stderr、Git 守門與恢復紀錄。
- v3：258 regular、20,191,163 B，原 outer 0。保留 ORIGINAL_INDEX、phase-index、staged-index、私有 objects、38 原命令的完整紀錄。349／0 獨審不會改寫 v2 原紅燈；正式 F9 native 仍為原 1。
- 另收 1,357 份固定準備、原工具、診斷及獨審檔，共 1,888,607 B；包括原反證工具 tiny fixture 的自有 Git objects/index，不排除、不把它們連到 live NATIVE。

既知原 payload 合計 35,658,673 B，加原 host FINAL、請求、封存工具、scope 與獨審小檔。保留原已審 collector 的九個 helper 與整段 16 MiB 分包、gzip level 1、4096 B/member tar header 上限、gzip 最壞界、8 MiB metadata 與 64 MiB reserve、逐 member 回讀及來源前中後 hash/stat/葉集合守門。封包不省略 index 或 objects，不猜壓縮率；原件不刪。初始盤點 SHM 可用 17,369,022,464 B，WS 只有 12,578,816 B，因此 archive 只寫既有任務 SHM，不複製原 raw 到 WS。正式每 part 仍重新量 fresh free，原守門不降低。

`SCOPE.json` 固定兩次原 RESULT、請求、executor 與 host pins；全部補充原檔逐葉 pin。靜態比較保存在 `PREPARATION.json`，沒有執行 collector。先由另一代理核對 collector／launcher 精確 pins，主代理再用正式 `require_escalated` 執行：

```sh
env -u PYTHONOPTIMIZE python3 -B /workspace/geo314-counterproof-terminal-preparation-20261025/launch_collection.py --peer <REVIEW.json> --peer-sha256 <peer-sha256> --terminal-pins /workspace/geo314-counterproof-terminal-preparation-20261025/TERMINAL_PINS.json --terminal-pins-sha256 5dd0744b2b7dd9ef84d7ea7316ed751ce6a0453984edc49eb9a6e9f70591fb0a --execute-root-approved
```

只有 root 可親執；launcher 綁定獨審的 `exit_code=0`、`collector_sha256`、`launcher_sha256`，並核兩份原 host pins。使用原 c387 保存收件命令、真 exit、完整流；精確新輸出為 SHM 下 `geo314-counterproof-terminal-collection-original-20261025` 與 `geo314-counterproof-terminal-package-20261025`，已存在即拒絕。

封存成功後再獨審封包，才準備出版。正常 push 與 GitHub raw blob 全長/hash/OID 核對以前，`delivered=false`。原 F9 native 1 與 v2 outer 1 保留；v3 只證專項修補反證及 index 隔離，歷史 index 寫入者仍未完全確立。
