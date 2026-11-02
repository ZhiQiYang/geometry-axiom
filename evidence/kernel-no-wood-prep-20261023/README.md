# 不帶木工模板：專有準備與驗收

目前只有 repo 外候選，沒有修改整合分支、產品、決策佇列、公理層或全域突變帳本，也尚未執行編譯／測試。

權威程式底本為 `13d02c1db7022145a52ee063286a558e595eb212`。既有 `tests/test_rectangular_template.py` 已安裝真實的七個 K 檔、矩形格網兩檔及兩個測試檔，獨立編譯 exact／geometry／grid、第二模板與 harness；沒有沿用現成產品 binary。現有 11 個測項包含 1000×600 的 15 格、精確來源、型別／容量／拒絕回滾、實際 K 整除守門突變與缺 K object 的連結控制。

最小候選只改同一個既有測試檔：

- 原匯入 blocker 補入實際套件根名 `geometry_woodworking`，保留 `geometry_app`、`modeling` 及原 `woodworking*` 拒絕；用可正常取得的 sentinel 套件驗證確實由 blocker 拒絕，不能把 module 不存在當成成功。
- 原已安裝 source closure 的 quoted local include 檢查，對 K 額外要求目標仍在 K。W 矩形格網可以 include K，K 不能反向 include 此 W。一般 C 前處理的完備性仍屬產品架構原裁判，不把此小型檢查冒稱為通用 C parser。
- 在隔離的真 K `grid.c` 加唯一一行 `#include "../../geometry-templates/rectangular-grid/rectangular_grid.h"`。此 header 在 installation 中真實存在且 manifest 屬 W；先證明 mutant 可編譯、連結並執行 exact-cells 為 0，再對同一隔離裁判取得 0／1／0。編譯錯誤、缺 header 與 crash 都不能代替這個 source-layer control。

候選保留原 11 個測項，新增兩個後共 13 個。`tests/run_all.expected.json` 是共享檔，依 root 指定的 #323→#314→combined→#318→本任務順序交接後才更新。全域帳本由 root 在最終 SHA 整份產一次，本代理不產。

`candidate/` 保存原件、候選、精確 patch、讀取命令與 hash。`run_proof.py` 只從固定 Git tree 安裝 11 個來源，外部候選覆寫只供明列的 preflight。正式收據須使用已提交的測試 bytes，不能把 preflight 標為最終 SHA。

待 root 發布編譯槽位、正式分支建好後執行：

```sh
python3 -B /workspace/kernel-no-wood-prep/run_proof.py \
  --git-dir /workspace/kernel-no-wood-prep/metadata.git \
  --sha <完整的受驗 commit SHA> \
  --out /tmp/kernel-no-wood-final-<sha8> \
  --heavy-lock /tmp/g261r3/heavy.lock
```

只有事先明列的候選 preflight 可加：

```sh
--test-override /workspace/kernel-no-wood-prep/candidate/test_rectangular_template.py
```

五個 phase 為完整 baseline、撤回 woodworking blocker、恢復 blocker、撤回 K→W guard、恢復 guard，真退出應為 `0／1／0／1／0`。兩個撤回只改相應守門，所有測試斷言保持原 bytes。正向 phase 另驗內部 K include control 的 `0／1／0` 與 mutant 功能執行 `0`。所有原 argv、stdout／stderr、環境、SHA、source／variant hash、compiler 子指令及真退出保存；watchdog、compile failure 或 crash 不算有效反證。

本代理已做 #318 條文候選的獨立對抗審查，見 `REVIEW318_CANDIDATE.md`／`.json`，它不等於 #318 核心或 oracle 已通過。#288 space 原收據只證自身 full-space-suite，明列不含 timber 兩個群組；沒有重跑該綠項。
