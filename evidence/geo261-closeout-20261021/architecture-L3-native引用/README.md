# L3 native 的架構具名結果引用

本附件補齊 `../architecture-L3/` 在 05:42 實跑 CLI 後尚待到齊的兩套 native 結果。原凍結收據、四 metadata 與 stdout 完全未改；此處沒有重跑產品、架構 CLI 或兩套測試。

本輪實際來源 L3 為 `6589248c9a94bdf0460d8f84dd1610e51048188b`，正式 native 工作樹為 `/workspace/geo261-native-l3-6589248c9a94-20261021`，來源分支是 `codex/geo261-closeout-20261021`，native 以同 SHA 的獨立 checkout 執行。命令 `timeout 2100 python3 tests/run_all.py --build` 自 2026-10-21 05:49:55.452245+00:00 執行至 06:20:25.133869+00:00，耗時 1,829.6815555930007 秒，main／wrapper／launcher 真結束碼皆 0；前後 HEAD 同 L3 且乾淨。

| 具名套件 | 通過 | 失敗 | skip | 原始 JSON／unittest 時間 |
| --- | ---: | ---: | ---: | --- |
| `py:test_architecture_contract` | 205 | 0 | 0 | 0.52／0.331 秒 |
| `py:test_product_architecture` | 18 | 0 | 0 | 11.68／11.524 秒 |

各 `.json`、`.log`、`.unittest.log` 完整原 bytes 均保存在 `native/suite-logs/`。兩份普通 `.log` 是當時真空檔，不是遺漏；unittest 分別明列 `Ran 205 tests`／`Ran 18 tests` 與 `OK`。JSON 的測試檔身份、通過數、失敗／skip／blocked／import／extra-error 欄均核對，run.log 的各唯一具名表列亦相符。

來源綁定核對同時鎖定 verification SHA256 `ee80438dce224cf9d473184c4ffe97a4c690d401d98eecdbcbd5e458449df93b`，具名結果→來源索引→六份原件、原件 mtime 落於本輪執行區間、command 的 cwd／開始時間、wrapper 原碼與 argv、launcher 對實際 receipt hash 及真 wait 碼的引用。原 packager SHA256 `609f59b2d0f9b067ac100d7ee99e3f7e685a594e75f2e9fb72df39179135b4bb` 與實際原碼相符，只以 `.txt` 保存，沒有在本程序執行。完整 23 份引用原件與來源 path／bytes／hash 清單在 `binding.json`。

本附件獨立核的是兩套具名結果與上述引用鏈；完整 224 suites／188 Python JSON／600 raw 的驗收，引用已鎖 hash 的正式 verification，不重新解析全表或掃描 600 份日誌。該正式驗收總數為 5,188＝5,187 pass＋0 fail＋唯一允許的 Windows GDI skip 1；兩套架構測試自身 skip 都是 0。不能寫成 5,188 個斷言全部通過。

相鄰 `../source-binding-L3/` 的新快照 SHA256 `3420121fdc8a24cdff5335762ffdd07db82a531c5efea7ca32aedd3f7f50bd43`、expected 原 bytes 與 CLI receipt 皆已交叉引用。四 metadata 的原 sourceBaseHead 仍 S2 `cabe824128be31d0039dc6c94fa3f04cfb722a6b`，未宣稱在 L3 重產。

引用接受器命令為 `python3 -B bind-L3-native-architecture.py --out /workspace/geo261-evidence/architecture-L3-native-reference-run01`，實跑原碼、完整 argv、stdout／stderr、父 wait 收據均收錄。真結束碼 0，父程序等待 0.050214569993840996 秒；binding SHA256 `41c8216749dad563dc1b2d5529490524955dd6975abd4bc742fcb3833f1cac1d`。本輪沒有新增突變控制或性能量測；其他關卡與 PR 複審仍依其各自正式收據判定。
