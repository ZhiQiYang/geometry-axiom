# A2→L2 新來源綁定

分支 `codex/geo261-closeout-20261021`，實際 checkout 為 L2 `249571fe2477845d5330f6190dad965bf327f43b`，直接 parent 為 A2 `cbefb39b47fb0edcfaf003d2c1101929fea244c8`。總 Git diff 唯一修改 `tests/mutants_results.json`；前後 tracked 工作樹乾淨。這一輪新跑原 snapshot 工具，沒有改寫舊 L 快照或只替換 SHA。

實際命令（父程序提供取消 CC／PYTHONOPTIMIZE、全新 TMPDIR／PYTHONPYCACHEPREFIX、禁寫 bytecode 與 16 MiB stack）：

```text
timeout 120 python3 -B /workspace/geo261-evidence/source-binding-preparation/snapshot_bindings.py --root /workspace/geometry-axiom --expected-head 249571fe2477845d5330f6190dad965bf327f43b
```

原工具 bytes 不變，SHA-256 `0640270f504fc0f12398cf15dda289f45dda188b9fa42cf3e32b862ee76a9a48`。2026-10-21 04:14:10.688375Z 至 04:14:11.679882Z，耗時 0.991518403 秒；真 `waitpid` raw status 與結束碼皆 **0**，stderr 空。原 stdout 就是 `snapshot-L2.json`，487108 bytes，SHA-256 **`6f5840a1c9247617a67af1c03a7a63fb1dc7b61adf01e381f6322361f684e48b`**。

本次重新枚舉聯集為 **1010 檔**：include closure、flat `tests/*.py`、所用場景、611 架構 inputs、四 metadata 與 ledger。每件 raw bytes 與 L2 Git blob 核對，並重算 LF hashes；這是指定聯集，不是全 repo 或 binary 清單。A2→L2 總差異只有 ledger，因此聯集其他 **1009 檔** Git bytes 與 A2 相同，不能誤稱 1010 檔全同。

新 ledger 為 5170289 bytes，SHA-256 **`6bda315331050bd3478ed65211a8263508cb1a1f6f67cee3f35df377506e7f0b`**；工作檔、L2 Git blob、A2 當輪重產原件逐 bytes 相同。78 記錄 checksum 全正確；75 execution 全保留真實 A2 head，逐筆 source／include closure／oracle／mutant／tool hashes 與新快照吻合。結果為 70 killed、4 equivalent、1 crashed、3 retired；沒有把 A2 execution 回填成 L2。

`tests/run_all.expected.json` 不在上述聯集，已另做 A2／L2 Git blob 與工作原 bytes 核對：24624 bytes，SHA-256 `f08443be7de507ea4550790bfdf3d51ce4c35fc74e2055286691ec511082bec0`，expected count 總和 5188。這是契約數量，不能當作完整 native 已通過。

正式 hash 新值：

| 項目 | SHA-256 |
|---|---|
| core＋bridge include closure | `dff8a902e49aa2ed96c1981870e2739163c5f18076a3e9e3fed121d79103292f` |
| core oracle | `f8222a4ac7ae76339cfb7536634f98e572ecd2bb0d649ce3395d6d452e2fa306` |
| mutation tool | `24c391b89880b8abc36cf4b7431afd1bb5486982cb9d41a6a0d975ac7c3c6387` |
| 611 架構 inputs 的 LF closure | `2c665544b106ed8b2542425ae3d752843e9cd281b340ab349fe8a3734bc36076` |

包內另保存 root 的 S2 採用、A2 公開、L2 匯入／default-check／公開原件與 S2→A2 metadata 綁定。L2 default `--check`、一般 push、remote exact 均引用 root 的真原件，本程序沒有重跑或再次查遠端。importer 頂層 wait 另有工具回覆事後轉錄，明示不是原始 transport 檔或重新 wait；`publication.json` 本身不被當成頂層 wait。

架構四 metadata 保持 S2 產生、A2 提交的原 bytes，receipt.sourceBaseHead 仍為 `cabe824128be31d0039dc6c94fa3f04cfb722a6b`。L2 另實跑正式 CLI，原件在新的 `architecture-L2` 包；本次沒有重產四檔，也不冒稱 205／18 項測試已在本程序重跑。完整 native 與其餘整合驗收由 root 另行安排。

本輪沒有新增負控制。快照是來源綁定而非測試成功，不能代替 mutant --check、完整產品行為或性能驗收；最大未定項仍是所有 L2 整合驗收的最後完整原件。舊 L1／L／A 歷史包保持不動。
