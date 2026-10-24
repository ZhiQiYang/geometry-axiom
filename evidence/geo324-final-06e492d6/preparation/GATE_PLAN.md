# #324 替代線：原 gate 與待執行計畫

本檔是準備，不是測試收據。source 起點為 Grok `4e176e830b691269cc72d021ce7e1bc0b167d621`，PR-local base 為 `7dae5f21c7ca401e660450d437e60ba566218da8`。先將 main `eda91c8593f0795278f7f16ff8b93d147a4fdaa7` 一般 merge 到 `codex/geo324-faces-20261024`；root 再排入新 train。HEAD 尚未固定為受驗 final SHA，下面的 `FINAL_SHA`、`CHECKOUT`、`OUT` 都是待綁定值。沒有建立 checkout、編譯、Chrome 或產品測試執行。

最新 handoff `d193946b8e0fbda024d3b134c4851e9393a43d38` 的 324.md：最後審查為 06:41:43，17:01:09 原作者只更新正文並轉交雲端，沒有重跑。predicate 覆蓋已接受；剩下同 final SHA 的 aggregate／expected／importer／七 job／帳本 check。舊 Actions 零步驟 failure 屬環境，原 Windows 45 tests 不冒成本環境 final 驗收。

## 來源與衝突預判

正確 PR-local 只三檔、121+/2-。`model_sources.py` 與 `test_geometry_host_sources.py` 在目前 main 的 blob/mode 精確同 PR-local base，預期可直接合入這兩個 leaf。`run_all.expected.json` 的 #324 範圍只 `py:test_geometry_host_sources` 39→45；保留 main 的 contact13、definition9、hostfacts19、placement19。這是 Git 靜態比較，實際 merge 結果仍要保存三方父節點、衝突、各檔 bytes/mode；不能把舊 integration 歷史當 #324 新變更。公理層／決策佇列原字不修改。

## 原正式項（全部 UNRUN）

1. registry/discovery 清點：`python3 tests/run_all.py --list`。它拒絕未登錄檔；不執行 tests，也不檢查所有 discovered counts。不能以 list 0 代替 expected gate。
2. 完整 native／expected gate：`ulimit -s 16384; python3 tests/run_all.py --build`。無 `--only`、`--allow-skip`、`--update-expected`。原 workflow native 35 分鐘。完整 run 內的 `compare_expected(..., full=True)` 才驗全部 suite count／registry 收斂；實際同 SHA stdout、原 exit、完整每 suite log 一起保。
3. 六 browser 原 `.github/workflows/integration-tests.yml` job：canvas35、assembly15、documents10、grid15、space15、timber20 分鐘。逐 job 保 npm build、真必要 CJK 套件安裝狀態、原 shell／stack／runtime probe／cleanup／artifact 及原完整 stdout/stderr。每 job 獨立埠、TMPDIR／profile／feedback；Chrome 指向既有 `/workspace/geo261-environment/bin/google-chrome`。canvas 保 full golden；其它原 partial filter 及 golden scope 不擴稱 full。診斷 watchdog 不代替原 CI 時限。
4. 受影響 importer 原 suites：先以 `run_all.py --build --only py:test_geometry_host_sources --only py:test_geometry_source_runtime --only py:test_geo261_default_native --only py:test_geometry_kernel_runtime --only py:test_rectangular_python` 收直接 public default-provider/source-graph 路徑；另選 `py:test_geometry_host_native`、`py:test_geometry_host_world`、`py:test_geometry_kernel_compatibility`、`py:test_domain_source_pins` 收 transport/provider pin/import compatibility。這是明標 PARTIAL 的前置診斷，不替代完整 native，套件範圍在真合流 source 再核一次，不能只沿 direct import。
5. 原 mutation freshness：`python3 tests/mutate.py --check`，保存原退出／全部輸出。這裡不產完整帳本；過期如實交 root 依整體列車一次重產，不能把未跑寫成綠。
6. 這次 W owned Python/source 與 tests 變更，原架構三裁判要在正式 source 跑：`python3 -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json`、`python3 -B tests/test_architecture_contract.py`、`python3 -B tests/test_product_architecture.py`。四檔重產依原 PRODUCT-ARCHITECTURE/schema，不能削弱 source hashes 或 policy；由 root 排合流後刷新，未重產／未跑各自標記。

所有結果由 c387 原錄製器保 command、cwd、env、原 exit、timeout、stdout/stderr 原 bytes/hash 與完整 source SHA；outer／collector 0 不代原 gate。先收齊各項紅燈再分類，不更改原斷言或新增閾值。測試限 root 給的磁碟／時槽，最多兩項；canvas／perf 獨占。舊 global `/tmp/geometry-tests` 不由本計畫自動搬走，native 快取獨立方案在執行前與 root 協調。

## 三 predicate 補充反證（UNRUN）

`run_face_predicate_proofs.py` 只在 repo 外複製原四 packages 與原三 test modules，逐 predicate 各跑原 public 行為 method 的 baseline／只撤該 predicate／逐 bytes 還原。原 CLI 仍為 `python -I -B -c <原 unittest runner> <copied tree> tests.test_geometry_host_sources.NativeCandidateTransportTests.<原方法>`，每次 60 秒；沒有改 tests/assertions。要求實際 0/1/0、同一原 method、正常 unittest FAIL（不能 import/syntax/error／timeout）及 bytes 還原，三組完整原件分別封存。這不重開前輪已接受的覆蓋，也不捏造成原內建 helper 已逐案跑三次 restored。

待真 final SHA／clean checkout／slot 後的明確 argv：

```bash
env -u PYTHONOPTIMIZE -u PYTHONPATH -u PYTHONSTARTUP -u NODE_OPTIONS \
  python3 -B /tmp/geo324-owner-20261024/preparation/run_face_predicate_proofs.py \
  --repo CHECKOUT --expected-head FINAL_SHA --out /tmp/geo324-predicate-FINAL8
```

list predicate 對 null/object；dict predicate 對 nested list；feature predicate 對 int/list feature。feature=int 單獨會被後面的六面名集合檢查攔下，真正有牙齒的是同 method 的 unhashable list。原正例 `test_public_default_transport_preserves_unchanged_wire_in_one_invocation` 仍保，在完整45-method模組／native裡實跑，不以本3-method反證代替。

## 出版與正文

每次完成項目將原收據／全部輸出與 `PROGRESS.md` 正常推自己的 `evidence/geo324-final-<sha8>/`，不推 grok/claude、不寫 integration；唯一 current-state 矩陣分 source SHA／evidence head／原 gate exit／partial／skip／unknown，沒有結果用 null。正文 `PR_BODY.md` 正常推 `codex/geo324-faces-20261024-prbody`。root 依 handoff/pr-requests/README 送替代 draft PR request，本 owner 不合併。產物交 p88_priority 對抗審。
