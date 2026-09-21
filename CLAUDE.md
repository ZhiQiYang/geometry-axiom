# CLAUDE.md

本專案給 agent 的規則**全部寫在 `AGENTS.md`**,請先讀那一份再開工。

重點提要(細節與理由見 `AGENTS.md`):

- 🔴 **公理層閱讀器只准有一份**:正典 `geometry-guide/公理層-閱讀器.html`(批註版)。
  它已經是零外部引用的單一自足檔,**不需要也不准再做「離線版」**。
  正典由 `geometry-guide/sync_axiom_reader.py` 原位同步,改它之前務必先讀
  `AGENTS.md` 裡那五道完整性 assert——任一道失敗會連桌面版面一起失效。
- 🔴 **`公理層.md` 是 SSOT**,不得擅改;發現矛盾只回報。條文未定案前不得實作。
- `geometry-guide/axiom-reader-design/`(第 3 版設計原型)與 `閱讀器-設計規格.md` 已於 2026-09-20
  一併作廢/移除;閱讀器的判準改為 `BACKLOG.md` 的 GEO-120(🔒)與第 11 流(GEO-139～149)。
- `make_axiom_reader.py` 已依 Q7 的退役條件移除(GEO-165);追溯診斷使用 `axiom_matrix.py`。
- 地雷:`current_geometry.c` 是**統一 CRLF**,要掃它一律用 Python 以二進位模式讀;
  root `.gitignore` 是允許清單制且全域忽略 `*.svg`。
