# 限定補測的公開重現入口

本文件是可攜命令與依賴說明，沒有因此重新執行產品測試。原執行 SHA、命令、stdout／stderr、退出碼與版本保存在各 `gate-receipts`、`*-driver` 或 `driver` 與 run 原件；原始絕對路徑是歷史身分，不是讀者必須取得的私人資料。所有輸出必須寫到新的 repo 外目錄，不覆蓋本包。

## 環境與完整來源

需要 Linux、Git、Python 3、GCC 相容 `cc`；瀏覽器專項另需環境已獲准的 Python Playwright 與 sandboxed Chromium。使用一個新的隔離環境，先取得唯一原生／瀏覽器執行責任。不要在有其他 owner 使用的 `/tmp/geometry-tests` 重建，也不要占用既有 HTTP 服務。政策拒絕瀏覽器時保存原始錯誤並停止該動作。

把完整公開證據包放在 repo 外；以下從包根目錄執行。`SR_REPO`、`SR_RUN`、`SR_URL` 請填新 checkout、全新父目錄及自己獨占的本機 port。`SR_RUN` 本身可以先建立，各 probe 子目錄不可預先存在。

```bash
SR_BUNDLE="$PWD"
SR_REPO=/absolute/path/to/new-clean-checkout
SR_RUN=/absolute/path/to/new-private-output-parent
SR_URL=http://127.0.0.1:18971/
SR_CHROME=/usr/bin/chromium
git clone --no-checkout https://github.com/ZhiQiYang/geometry-axiom.git "$SR_REPO"
git -C "$SR_REPO" checkout --detach d8642b2e684038cbb8e24aba057c44e7aac1b231
git -C "$SR_REPO" status --short
git -C "$SR_REPO" rev-parse HEAD
mkdir "$SR_RUN"
cd "$SR_REPO"
python3 --version
cc --version
python3 tests/binaries.py build bridge model-base
python3 tests/binaries.py status bridge model-base
export GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge
export GEOMETRY_BRIDGE=/tmp/geometry-tests/bridge
export GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base
ulimit -s 16384
```

逐條保存輸出並檢查退出碼；clone／checkout／build／freshness／stack 前置失敗時停止依賴命令。來源須 clean，`HEAD` 必須等於完整指定 SHA。bridge 的 sidecar 由原有 `tests/binaries.py` 產生並與實際 binary 同放；不能用只重命名或無來源指紋的舊 binary。這些 probe 會核 repo 與 binary 身分。若在後續純文件 head 重跑，需使用真正的新 SHA，保存來源同一性比較，不能把結果重標為 d864 原轮。

完整 checkout 提供 `tests/_bridge.py`、`tests/binaries.py`、`tests/test_grid_subdivision_oracle.py`、`tests/test_grid_system_contract.py`、`tests/test_parameters_core.py`、`tests/fixtures/grid_subdivision_vectors.json`、`tests/release_gate.py` 及其來源閉包。只複製一支 probe 不能替代 repo。SR15／SR18 的合法 fixture 在腳本及既有 test helper；SR16／SR23 的合成 boundary／真支撐 fixture 在其脚本內，不依賴私人圖紙。

## SR18 與 SR15 r2

```bash
python3 -B "$SR_BUNDLE/contract-gap-probes/sr18-probe/sr18_role_probe.py" --repo "$SR_REPO" --head d8642b2e684038cbb8e24aba057c44e7aac1b231 --out "$SR_RUN/sr18"
python3 -B "$SR_BUNDLE/contract-gap-probes/sr15-probe/r2/executed-probe.py" --repo "$SR_REPO" --head d8642b2e684038cbb8e24aba057c44e7aac1b231 --bridge "$GEOMETRY_TEST_BRIDGE" --out "$SR_RUN/sr15-r2"
```

二者串行並分別保存 shell 退出碼、stdout／stderr；原輪均退出 0。SR18 的負例只變 role，精確 `D17/I21 V_PRIMARY_AXIS`；SR15 r2 包括完整 snapshot、兩面參數與單一 anchor、兩次 Undo／Redo，以及 902 非整除與 4/3 anchor 的精確拒絕。SR15 r1 是未完成的歷史失敗，保留其原脚本、结果与 [r1→r2 判定修改 diff](sr15-probe/r2-preparation/r1-to-r2.patch)，不是 r2 可攜命令的依賴。

## SR16／SR23 真 UI

沿用完整包的 [共同啟動規範](../commands.md)，但 checkout 必須是本段的 d864。環境 adapter 原件位於 `gates/edge-transition-ce74/sources/launch-adapters/sitecustomize.py`，只剔除會停用 sandbox 的 launch 參數；本 probe 自身明確 `chromium_sandbox=True`。

```bash
export GEOMETRY_TEST_URL="$SR_URL"
export GEOMETRY_CHROME="$SR_CHROME"
export GEOMETRY_FEEDBACK_DIR="$SR_RUN/feedback"
export GEOMETRY_REQUIRE_CLEAN=1
export GEOMETRY_VERIFY_ROOT="$SR_REPO"
export PYTHONPATH="$SR_BUNDLE/gates/edge-transition-ce74/sources/launch-adapters${PYTHONPATH:+:$PYTHONPATH}"
python3 -m pip show playwright
"$SR_CHROME" --version
```

在另一終端用相同變數與 repo，確認 18971 由本輪獨占後以前景方式啟動 `python3 geometry-web/serve.py 18971`，另存服務輸出；若選其他 port，同步修改 `SR_URL` 與 serve 參數。等待真 `/runtime` 完成，保存原文並核 fresh、root、version；再從本終端執行：

```bash
python3 tests/release_gate.py --url "$SR_URL" --output "$SR_RUN/sr16-sr23-gate" --timeout 1200 -- python3 -B "$SR_BUNDLE/contract-gap-probes/sr16-sr23-browser/r1/executed-probe.py" --root "$SR_REPO" --url "$SR_URL" --head d8642b2e684038cbb8e24aba057c44e7aac1b231 --bridge "$GEOMETRY_TEST_BRIDGE" --model-base "$GEOMETRY_MODEL_BASE" --chrome "$SR_CHROME" --out "$SR_RUN/sr16-sr23"
```

不傳 `--width` 會串行跑 1400 與 390。原輪两種寬度各 75 具名檢查，是兩條工作流程，不是 150 個使用者情境。boundary／placement／真支撐以 API 種植，source／rule／binding／正式 guide／direct 及保存重開以 UI 操作。原兩檔實際是 `/11`，沒有執行脚本準備的 `/13` 分支；SR16 原拒絕是 `R6/I5/I6`。下載 fallback 不代表 OS 對話框驗收，390 不代表實體手機或 IME。

## #62 ASan／UBSan 與五項故障注入

這組使用自己的 sanitizer executable，無需占用前述普通 bridge 或 HTTP 服務。仍須串行執行，來源 clean，stack hard limit 允許 driver 子程序的 64 MiB，禁止 sanitizer suppression。只在新的私有準備目錄複製三支**未修改**原腳本，然後用原 `prepare.py --repo` 建立匹配新 checkout 路徑的 plan／54 份來源／五個 patch。不要直接拿歷史 `plan.json.repo` 指向不存在的 `/workspace`，也不要改寫封存的原 plan。

```bash
SR_SAN="$SR_RUN/sanitizer-preparation"
mkdir "$SR_SAN"
cp "$SR_BUNDLE/contract-gap-probes/sr62-sanitizer-mutations/preparation/prepare.py" "$SR_SAN/prepare.py"
cp "$SR_BUNDLE/contract-gap-probes/sr62-sanitizer-mutations/preparation/run.py" "$SR_SAN/run.py"
cp "$SR_BUNDLE/contract-gap-probes/sr62-sanitizer-mutations/preparation/oracle_runner.py" "$SR_SAN/oracle_runner.py"
python3 -B "$SR_SAN/prepare.py" --repo "$SR_REPO"
python3 -B "$SR_SAN/run.py" --execute --out "$SR_RUN/sanitizer-run"
```

prepare 僅讀來源、生成 plan 並核既存 archives，不編譯或執行產品。記錄新 plan hash 與原三腳本 hash；prepare 非零時停止。run 的六次編譯與十一個 oracle 子程序串行，每次上限 300 秒；若包外監督程序設 timeout，應至少 6000 秒，並允許 driver 回收自己的子程序。不要修改原測試、期望值、fault patch 或 compiler flags 迎合結果。

原 r1 的 [summary](sr62-sanitizer-mutations/r1/summary.json)為 `complete:true, passed:false`，driver／gate 退出 **1**：baseline 54 通過、五個 mutant 原測試均失敗、每次回復同一路徑至 pristine bytes 後原測試通過。M1／M3 的自動分類仍是 `OTHER_FAILURE_NOT_A_KILL`，因 plan 把 rejection helper pin 在 187 行，而原測試實際在同 helper 的 189 行拒絕判定失敗。獨立語義審查只追加結論，不修改原 verdict、不宣稱 runner 已綠，也不是新增一次測試通過。原测试／script／plan／準備失敗輪全部保留。新執行者須自行保存與審查實際結果，不能預填本輪結論。

這個新 54 方法範圍包含 41 subdivision 與 13 grid-system 方法，不是缺失的歷史 152 重現，也不是 54 個 native 子程序；五個 fault 只代表既定清單選中的整除、序列化、跨 source 身分、hole clipping 與 capability preflight 分支。完整原生 transport／stderr 和合成 scene 都公開；native executable、重複來源副本及瀏覽器完整 trace 不公開，只在 manifest 留 hash。原件不依賴私人工作管理 DB、憑證或原圖。
