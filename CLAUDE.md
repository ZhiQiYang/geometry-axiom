# CLAUDE.md

本專案給 agent 的規則**全部寫在 `AGENTS.md`**,請先讀那一份再開工。

重點提要(細節與理由見 `AGENTS.md`):

- 🔴 **公理層閱讀器只准有一份**:正典 `geometry-guide/公理層-閱讀器.html`,
  唯一產生方式 `python geometry-guide/make_axiom_reader.py`。
  它已經是零外部引用的單一自足檔,**不需要也不准再做「離線版」**。
  要改閱讀器 = 改生成器模板整份重產,不准另存一份再改。
- 🔴 **`公理層.md` 是 SSOT**,不得擅改;發現矛盾只回報。條文未定案前不得實作。
- `geometry-guide/axiom-reader-design/` 是設計參考,不是閱讀器來源。
- 地雷:`current_geometry.c` 含 NUL byte(grep 會靜默截斷);
  root `.gitignore` 是允許清單制且全域忽略 `*.svg`。
