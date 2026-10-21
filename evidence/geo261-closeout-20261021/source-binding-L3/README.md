# L3 來源綁定

本包記錄分支 `codex/geo261-closeout-20261021` 的正式 L3 `6589248c9a94bdf0460d8f84dd1610e51048188b`。直接父提交 S3 是 `19401ca5448e162ee6140fed37b64b83b31ddec8`；兩者唯一差異為 `tests/mutants_results.json`。

原版 `snapshot_bindings.py` 的 6,622 bytes 沒有修改，SHA256 為 `0640270f504fc0f12398cf15dda289f45dda188b9fa42cf3e32b862ee76a9a48`。本輪以新 Python 程序、全新快取與暫存目錄，取消 CC／PYTHONOPTIMIZE、堆疊 16 MiB，實際執行 `timeout 120 python3 -B snapshot_bindings.py --root /workspace/geometry-axiom --expected-head 6589248c9a94bdf0460d8f84dd1610e51048188b`；原始完整 argv、環境、stdout、stderr、wait status 及時間在 `來源綁定/`。快照真結束碼 0，0.8910366969939787 秒；外層來源／CLI runner 父程序真 wait 0，6.172822811997321 秒。

新快照 SHA256 為 `3420121fdc8a24cdff5335762ffdd07db82a531c5efea7ca32aedd3f7f50bd43`。本次重新枚舉 1,010 檔聯集：C include closure、tests 根層 Python、根層與 core 場景、611 架構 inputs、四份 metadata、帳本。這不是全 repository 或所有執行期 binary 清單。S3→L3 中 1,009 檔 bytes 相同，帳本有變；前後 HEAD 一致且 tracked clean，未聲稱所有 untracked 為空。

帳本原 bytes 為 5,170,289，SHA256 `52aa08ac9e0c88f96b81d35f985b7fadfbb746086ec8b99d7ae10fd3043d3178`。78 筆記錄 checksum 重算一致；75 筆 execution 全為 S3，逐筆 source／closure／oracle／mutant／tool 與 L3 新快照相符。70 killed、1 crashed、4 equivalent、3 retired；並未把 execution 改寫成 L3，也沒有在此程序重跑突變、正式 `--check` 或個別等價證明。帳本方法與限制另見 `../ledger-S3-cc/` 及其獨立審查附錄。

`tests/run_all.expected.json` 在快照聯集以外，因此另收 S3 與 L3 的完整 Git raw bytes，兩者 SHA256 同為 `f08443be7de507ea4550790bfdf3d51ce4c35fc74e2055286691ec511082bec0`，總 expected 為 5,188。

四 metadata 及 611 架構 inputs 與原收據相符；收據 sourceBaseHead 仍是 S2 `cabe824128be31d0039dc6c94fa3f04cfb722a6b`，本輪沒有重生四檔。S3 唯一修正的 `tests/test_geo261_host_authority.py` 不在該 611 inputs 中；完整突變帳本仍在 S3 真重產。

`L3帳本發布/` 保留 root 原始 default-check／一般 push／remote exact 收據；其歷史欄名 `sourceA2` 的值實際是 S3，`ledgerL2` 的值實際是 L3。`source-S3-ledger-L3-binding.json` 明列別名，不修改原收據。S3 自身公開／主分支正常快轉的原件已在相鄰凍結 `source-S3-binding/`、`source-S3-adoption/` 與 `source-S3-外層工具補充/`，此處不重複包裝。

本包沒有宣稱完整 L3 native、canvas、Q38、§7 已完成，也沒有建立或驗證 E3。最大限制是這是指定來源聯集與裁判雜湊的綁定，不可取代各正式驗收的真實執行。原始機器絕對路徑保留供稽核；移機重現應把 `--root` 指向同 SHA 的實際 checkout，另用新輸出目錄。
