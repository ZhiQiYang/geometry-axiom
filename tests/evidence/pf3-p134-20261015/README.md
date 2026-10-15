# P-134：固定來源的 native 失敗對照

本輪只新增證據，產品、測試、skip、斷言、expected、官方突變帳本均不修改。
**雲端 native,非正式 WSL 收據。** 正式七項由本機列車另跑。

## 固定來源與對照方法

- base：`303fec02257d21cf719287045a718665c3283006`（#227）。
- PF-3：`4f8da467e81be91bc288c765971431aed1530a94`（#226 開工時最新 head）。
- `git merge-tree --write-tree base pf3` 與 PF-3 HEAD 的 tree 均為
  `aa73311333b874f3cc84975efa642d2451dd2623`；PF-3 已完整包含指定 base。
- 同一雲端機器、Python、16 MiB stack；每一階段使用同一份環境字典、相同 argv、
  相同 executable 路徑，交替 base／PF-3。執行前切換為各自來源實編的 binary／sidecar，
  不拿 PF-3 binary 冒充 base。兩邊 HEAD 與工作樹皆保持不變。
- 每次保存原始 stdout、stderr、退出碼、精確 SHA、環境 SHA、elapsed 及輸出 SHA；
  原測試未 monkeypatch，沒有新增 timeout、sleep、負載、skip 或放寬斷言。

具名指令（每次 argv 完全相同）：

```sh
python -m unittest tests.test_scenario_verify.ScenarioNativeAcceptance.test_model_timeout_stops_its_base_child_before_it_can_finish_late -v
```

## 實際觀察與歸因界線

| 階段 | base | PF-3 | 原件 |
| --- | --- | --- | --- |
| 預先固定 10 組交替單例 | 10 過／0 失敗／0 略過 | 10 過／0 失敗／0 略過 | [summary](standalone-10/summary.json)、[原輸出／編譯與 binary／sidecar](standalone-10.tar.gz) |
| 未重現後，另固定 50 組交替單例 | 50 過／0 失敗／0 略過 | 50 過／0 失敗／0 略過 | [summary](standalone-50/summary.json)、[原輸出](standalone-50.tar.gz) |
| 保留前置測試情境，官方 runner 完整 scenario 套件 3 組 | 每組 37／37、零略過 | 每組 37／37、零略過 | [summary](scenario-suite-3/summary.json)、[完整 run.log／JSON](scenario-suite-3.tar.gz) |

每階段所有樣本皆保留，沒有失敗重試或只挑成功結果。單例與完整 suite 的指令不同，
不能混稱同一組觀察；同一階段的兩邊則完全使用相同指令與環境。
另有一次延伸階段啟動前，跨 shell 的完整環境 SHA 守門拒絕執行，實際啟動 0 個測試，
保留於 `aborted-setup.stderr`。之後只要求同階段兩邊的完整環境相同，並確認公開的執行設定
與首階段一致；兩個階段環境 SHA 分列，不宣稱跨 shell 全部環境位元組相同。

**結論只到「本輪未重現」**：未觀察到 P-134 的「base 也紅」或「只有 PF-3 紅」分支。
不得將 60 次單例及 3 次完整 suite 的綠燈推成「原失敗已證實由環境造成」，
也不能只由檔案無 diff 判定原失敗與 PF-3 無關。
目前沒有足夠證據指名 #227 或環境，故不另開帶有無根據歸因的 issue、不修改 PF-3 程式。
原始 `77ef94b` 完整 native exit1 收據保持原樣，見
[前輪索引](../pf3-native-20261015/README.md)。

## 最終 SHA 的完整 native

本證據提交後，凍結同一個最終 HEAD 執行 `python -u tests/run_all.py --build`，
不加 skip、不放寬斷言、不降低 expected；完整執行後不再提交，確保交付 HEAD 與
實際 execution SHA 完全相同。最終結果、精確 SHA、原始 stdout、receipt 與原件的
壓縮分片將刊於 #226 的【Codex】P-134 收據留言，不以先前 SHA 的成功代替。

完整 native 若再次失敗，保留原紅，不將未重現或偶發綠燈宣告為原因排除。
正式 WSL 七項、本機列車與 browser 不在本輪雲端補跑。

機械對照見 [comparison.json](comparison.json)；各 archive 的 `.inventory.json`
列出逐成員 SHA，固定來源的檔案 SHA 包括測試、驗證器及 modeling/base.py。
