# 下一輪架構收據工具：937 → 937

唯一正式候選 `refresh_architecture_zero_delta.py` 是原 `refresh_geo337_final_architecture_20261024.py`（SHA256 `61aa806e619baa5f0b141d2a5026fe8146691e12406b112cb4b7f765e9db37b0`）的外部副本；原檔不改。原 schema、三條原裁判、604 項 Git/blob/raw/LF 完整盤點、205/18 測試與 798 edges/0 diagnostics、原 c387 指令/完整流收據均保留。

新工具只接受以下已核定範圍：

- 執行來源與上一份 manifest 逐 bytes 相同，固定937 identifiers/55 strings；政策、分類、exclusions、trust 皆不可變。
- `--prior-source` 必須等於前份 receipt 的真 `sourceBaseHead`，不是產物提交。採用的 R=a22df116c7e9f6b7d074451f1c8052d59e7e4f3e 內前份執行來源是 b9c9fb818f031828530994a4d66f1976da0d8138。
- 完整604 inputs 比前份 receipt 僅 `geometry-templates/woodworking/native/contact_world.c` 的 LF hash 可變，且必須真的變。其他任何輸入差異會在三裁判前拒絕。
- 九組 guard 都由新執行來源的原 scanner 重新做0/1/0。撤回 manifest 獨立取自歷史 Git `ca7838e0f4950452b9befcf40899d606db9b81fa`，原 SHA256 `80f44b8c870e097413e395d30ba029199ba66b7302985c0f325d4f446d0ce525`、928/55，且與937版只差指定九 identifier；不是上一份937版。其 Git 命令、SHA、proof variant 與每 phase manifest/source 欄都另存，不移標舊判決。`--guard-baseline-source` 只能指定確有同一固定歷史 bytes 且為新來源祖先的40字元 SHA。
- `newIdentifiers=0`、`guardIdentifiersRetested=9`；新執行來源、UTC、三裁判/guard結果、完整輸入、原命令與環境均新產生。僅沿用原 schema 靜態描述欄，沒有繼承 scanPassed/validation/CLI 等判決。

執行範例（由 root 在產品穩定、source乾淨且 guard 審核完成後執行；以下佔位非實跑紀錄）：

```bash
ulimit -s 16384
python3 -B /workspace/geo337-architecture-zero-delta-tool-20261024/refresh_architecture_zero_delta.py --root <new-clean-source> --sha <full-product-sha> --out <fresh-external-out> --prior-source b9c9fb818f031828530994a4d66f1976da0d8138
```

本輪只做工具 AST/15 個 Python 契約自驗和原舊 delta assertion 的合成撤回/恢復0/1/0，未跑架構三裁判、guard正式反證、C、帳本、或 source 物化。原 selftest 流在 `*.stdout.bin`/`*.stderr.bin`；這些不是產品 gate。正式輸出四檔仍寫在來源外，採用與正常推送由 root 另做。
