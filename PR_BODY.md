容量 512 的真實放置路徑仍在正式驗收；維持 Draft、未達合併條件。本輪修 H 的局部 anchor／host 讀取、W 的重複排序及 plane 查詢、K 的重複 edge 查找；不刪依賴邊、不改幾何判準、不改 I33 CAPACITY、不改公理層。原 600 秒逾時保留。

| Current state（唯一當前矩陣） | 身分與真實結果 |
|---|---|
| 完整 PR head／evidence E | `2de39d384ed21ea092b9396787899bb39d86cbea` |
| 修前基底 B | `9a8584f57be7935604c3bad4c2481945a6ec3d9f` |
| Product／formal source F | `ac1d8017038ee9563f0cbd8596ea61c8b2577b19`；正式兩方法在獨立 clean checkout，E 僅追加證據 |
| 目前直接 base（#347） | `8bb0359331365c6f3a96872620427cf7847fcb50`，`codex/issue128-empty-panel-rows-20261024` |
| 相對 base | 原審查的「相對目前 base **behind 2**」以 `2e8a6ed20325aa4842dcd0f89eacd598662be598` 計；目前 base 已另加一個 evidence 提交，對現 base **behind 3／ahead 16、diverged**，未隱藏差異 |
| 阻擋 1：上游鏈 | #343→#346→#347 尚未閉合。修鏈後才一般 merge 精確 #347 head，逐 leaf 重審並重跑受影響驗收；本次未合入未閉合來源 |
| 阻擋 2：原 B 512 load | 新重現 timeout 600.013934 秒、exit -9、wait4 RSS279492 KiB；原兩份歷史 timeout 都在 initial load，沒有冒稱 replay/history 已各自執行逾時 |
| F 正式兩個 H7 placed 方法 | 20:08:28 UTC 首輪的64 load＋兩次canonical replay均exit0；512輸出遭正文Git補抓引發的ENOSPC打斷，原外層exit1，產品終態未完整回收，第二方法未真正啟動。保留原錯誤，恢復空間後同F重跑；**尚無512通過聲明**。原每batch600秒、16MiB stack、分離K/W/H -O0 |
| H scope／host借用控制 | `3420931a4a512f08e3f4d7584958cc8630e190c3`：6 tests、0 fail/error/skip、exit0；六項具名撤回各0/1/0 |
| W contact控制 | `a22d17c52f97115448160c4c13bfb72e62fd1686`：14 tests、0 fail/error/skip、exit0；41原控制保留，加兩項排序／plane撤回0/1/0 |
| K source-index控制 | F：21 tests、0 fail/error/skip、exit0；8原控制保留，加3項miss-slot／consumer hint／failed append撤回0/1/0 |
| Profile | B N12814.914535秒；F N12811.654085秒，兩者exit0且stdout逐byte相同。皆原O0加-pg診斷，**不能替代正式512**；-pg外部mcount成本不能直接稱memcpy成本 |
| ordered graph／五guards | 對照工具與基底build已備；完整比較尚未實跑通過 |
| 阻擋 3：完整整合 | 新來源的完整native、六browser、專項、#297 probe、全帳本及架構尚未完成；未報全綠 |
| 允許 skip | 無；未跑一律列未完成 |
| 狀態 | 非 READY-TO-MERGE，不合併、不force push |

實際執行命令（observer只保留原方法原斷言與完整stdout/stderr/returncode，沒有修改timeout）：

```sh
python3 -B /tmp/pr348-runs/run_formal.py --root /tmp/pr348-work --out /tmp/pr348-runs/domain-memo-tests tests.test_geo300_validation_memo
# exit0，6 tests
python3 -B /tmp/pr348-runs/run_formal.py --root /tmp/pr348-work --out /tmp/pr348-runs/contact-controls tests.test_geo261_wood_contact_world
# exit0，14 tests
python3 -B /tmp/pr348-runs/run_formal.py --root /tmp/pr348-work --out /tmp/pr348-runs/source-controls tests.test_geo261_source_index
# exit0，21 tests
python3 -B /tmp/pr348-runs/run_formal.py --root /dev/shm/pr348-formal --out /tmp/pr348-runs/formal-placed-ac1d8017 tests.test_geo261_timber_capacity_host.TimberCapacityHost.test_real_placed_64_and_512_load_dump_and_canonical_replay tests.test_geo261_timber_capacity_host.TimberCapacityHost.test_real_placed_512_sequential_replay_and_safe_513_history
# 首輪exit1（ENOSPC，產品終態未回收）；恢復空間後改新OUT重跑，不能填exit0
```

[原逾時與初步profile／H反證完整原件](https://github.com/ZhiQiYang/geometry-axiom/tree/2de39d384ed21ea092b9396787899bb39d86cbea/evidence/geo300-capacity512-20261024/timeout-diagnosis-20261028)；[W/K控制與修後profile完整原件](https://github.com/ZhiQiYang/geometry-axiom/tree/2de39d384ed21ea092b9396787899bb39d86cbea/evidence/geo300-capacity512-20261024/index-fix-20261028)。兩包各有逐檔hash／bytes manifest及tar回讀核對；F0f／F73原歷史收據保持原execution SHA，不能當成新F整合通過。`DIAGNOSTIC_LIMITS.json`明列初次環境啟動失敗、profile RSS包含compiler的限制；正式512使用wait4的產品child峰值。

效能與記憶體仍有未驗風險：K每node新增consumer metadata，W在512容量下新增巢狀stack約53,248bytes；須由正式結果確認，不以靜審代替。所有新改動已另交代理對抗靜審，原 assertions／golden／timeout 未放寬。CI尚無本修補head已執行通過的收據。
