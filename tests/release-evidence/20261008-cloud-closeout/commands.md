# 重新執行與歷史命令

這是公開證據的重建說明，沒有在本次文件審查中重新執行測試。各 `command.json`／`receipt.json` 內的絕對路徑是歷史執行身分，不表示原私人工作目錄隨此包交付。新輪必須保存自己的 SHA、dirty diff、版本、runtime、stdout／stderr 和退出碼；預期失敗不能改成通過。

## 隔離環境與來源

以下命令針對 Linux，使用環境已准許的 Python、Node、Playwright 與 `/usr/bin/chromium`，保留 Chromium sandbox。`browser_probe.py`、`bhit_probe.py`、`edge_transition_probe.py` 固定讀 `/workspace/geometry-axiom`。因此請在**新的隔離環境**將 repo 放在此路徑；該路徑若已有工作樹就停止，不覆盖、reset 或清理它。瀏覽器、原生大型測試與 build 串行，先取得該環境唯一執行責任。

先把整份公開證據包放在 repo 外的可寫目錄；在該包根目錄執行：

```bash
EVIDENCE_DIR="$PWD"
test ! -e /workspace/geometry-axiom || exit 1
git clone --no-checkout https://github.com/ZhiQiYang/geometry-axiom.git /workspace/geometry-axiom || exit 1
git -C /workspace/geometry-axiom checkout --detach 5174a8dafd8c48329d7166abbd3d104e3c28c0c4 || exit 1
REPLAY_DIR="$(mktemp -d /tmp/geometry-closeout-replay.XXXXXX)"
cd /workspace/geometry-axiom
pwd
git status --short
git rev-parse HEAD
python3 --version
node --version
/usr/bin/chromium --version
python3 -m pip show playwright
```

`5174a8d…` 是本報告最後產品候選；`async-new-head` 的原輪在 `458779f003e1f57fdc0f4420564a0b295227843e`，contracts 的原輪也請依自己的 receipt 選擇 SHA。重播歷史版本須另建隔離環境，不能把新版本的新結果冒充舊輪。後續純文件交付不改變原輪 SHA。Node `playwright`／`playwright-core` 必須在環境既有、獲准的模組解析路徑可讀；缺件時依環境安裝規範處理，不改 sandbox 或建立公開隧道。

先依 repo 最新 AGENTS 檢查必要項目，再建立並核 freshness：

```bash
python3 tests/binaries.py build
python3 tests/binaries.py status
export GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge
export GEOMETRY_BRIDGE=/tmp/geometry-tests/bridge
export GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base
export GEOMETRY_CHROME=/usr/bin/chromium
export GEOMETRY_TEST_URL=http://127.0.0.1:18971/
export GEOMETRY_FEEDBACK_DIR="$REPLAY_DIR/feedback"
export GEOMETRY_REQUIRE_CLEAN=1
export GEOMETRY_VERIFY_ROOT=/workspace/geometry-axiom
export PYTHONPATH="$EVIDENCE_DIR/gates/edge-transition-ce74/sources/launch-adapters${PYTHONPATH:+:$PYTHONPATH}"
export NODE_OPTIONS="--require=$EVIDENCE_DIR/gates/edge-transition-ce74/sources/launch-adapters/sandbox-launch.cjs${NODE_OPTIONS:+ $NODE_OPTIONS}"
ulimit -s 16384
```

保留 build/status 原始輸出與 sidecar；兩者非零時停止後續依賴工作。不能指向他人的舊 binary 或在占用中的 `/tmp/geometry-tests` 重建。原 Linux 整套驗收使用 16 MiB stack；上列 `ulimit` 只在既有 hard limit 允許時執行，失敗就停止，不變更系統安全設定。這兩個 launch-only adapter 已在 probe 前設定：它們只保留 sandbox 並剔除停用 sandbox 的啟動參數，不改 fixture、操作或 oracle。

在另一個使用相同環境變數與 repo 路徑的終端，先確認 18971 未被使用，再用下列前景命令開啟**自己這輪**服務並另存輸出：

```bash
python3 geometry-web/serve.py 18971
```

等待實際 `/runtime` 回應，核 `fresh=true`、`root=/workspace/geometry-axiom`、來源 version 與待測 checkout 相符；保存 `/runtime` 原文。HTTP 可回應本身不是產品驗收。`tests/release_gate.py` 會核 clean checkout／runtime／配置的 fresh native binary，但 `/runtime` 本身不證明正在執行的 native 子程序；需要此證明的 probe 會另保存 live-child `/proc/PID/exe` hash。只關閉自己啟動的服務。

## 公開脚本的檔名與必要依賴

請複製**整個對應子目錄**到新的 repo 外目錄後執行，不在原證據包內產生新結果。這會保留原 bytes 與相對依賴。

| 公開目錄 | 必須同目錄存在的原名 |
| --- | --- |
| `async-new-head` | `browser_probe.py`, `browser_instrumentation.js`, `run_browser.py`; `bhit_probe.py`, `bhit_instrumentation.js`, `run_bhit_probe.py` |
| `async-edge-ce74` | `browser_probe.py`, `browser_instrumentation.js`, `run_browser.py` |
| `async-transition-ce74` | `edge_transition_probe.py`, `edge_transition_instrumentation.js`, `run_edge_transition_probe.py`, `source-plan.md` |

`gates/edge-transition-ce74/artifacts/executed-*` 是執行時原件，前綴不是依賴檔名。優先使用 `async-transition-ce74` 的完整原名組；若從 artifacts 重建，須將三個 `executed-*.py/js` 複製成上表的原名，再從完整包複製 `source-plan.md`，逐項對照 `copy-provenance.json` hash，不能修改腳本內容。

```bash
cp -a "$EVIDENCE_DIR/async-new-head" "$REPLAY_DIR/async-new-head"
cp -a "$EVIDENCE_DIR/async-edge-ce74" "$REPLAY_DIR/async-edge-ce74"
cp -a "$EVIDENCE_DIR/async-transition-ce74" "$REPLAY_DIR/async-transition-ce74"

python3 tests/release_gate.py --url "$GEOMETRY_TEST_URL" --output "$REPLAY_DIR/gate-held-proj" --timeout 900 -- python3 "$REPLAY_DIR/async-new-head/run_browser.py" rerun-held-proj --only handles --url "$GEOMETRY_TEST_URL"
python3 tests/release_gate.py --url "$GEOMETRY_TEST_URL" --output "$REPLAY_DIR/gate-held-bhit" --timeout 900 -- python3 "$REPLAY_DIR/async-new-head/run_bhit_probe.py" rerun-held-bhit --url "$GEOMETRY_TEST_URL"
python3 tests/release_gate.py --url "$GEOMETRY_TEST_URL" --output "$REPLAY_DIR/gate-edge16" --timeout 900 -- python3 "$REPLAY_DIR/async-edge-ce74/run_browser.py" rerun-edge16 --only edges --url "$GEOMETRY_TEST_URL"
python3 tests/release_gate.py --url "$GEOMETRY_TEST_URL" --output "$REPLAY_DIR/gate-edge-transition" --timeout 900 -- python3 "$REPLAY_DIR/async-transition-ce74/run_edge_transition_probe.py" rerun-edge-transition --url "$GEOMETRY_TEST_URL"
```

逐條執行並記錄各自退出碼；不要使用 `&&` 把已知失敗之後的獨立回歸跳掉。原輪 held-proj 通過；held-bhit、edge16 的 replacement-rejected-value、edge-transition 的 ownership-token oracle 失敗，wrapper exit 1 已保留。重跑輸出資料夾名稱必須全新。兩種原 wrapper 可能覆蓋相同 label 的 stdout，所以不能重用 label。

## 原生及真產品保存重開

原生 probe 已在 candidate repo：

```bash
python3 tests/integration/grid_rule_reopen_probe.py --root /workspace/geometry-axiom --bridge /tmp/geometry-tests/bridge --out "$REPLAY_DIR/native-grid"
python3 tests/integration/assembly_ownership_probe.py --root /workspace/geometry-axiom --bridge /tmp/geometry-tests/bridge --out "$REPLAY_DIR/native-assembly"
```

公開的既有合法 fixture 可直接供瀏覽器 probe 使用；`script.py` 的預設相對 fixture 路徑在公開布局下不成立，所以兩個參數不可省略：

```bash
python3 tests/release_gate.py --url "$GEOMETRY_TEST_URL" --output "$REPLAY_DIR/gate-save-reopen" --timeout 900 -- python3 "$EVIDENCE_DIR/contracts/browser/browser-run-02/script.py" --root /workspace/geometry-axiom --url "$GEOMETRY_TEST_URL" --bridge /tmp/geometry-tests/bridge --chrome /usr/bin/chromium --out "$REPLAY_DIR/browser-save-reopen" --grid-scene "$EVIDENCE_DIR/contracts/grid-final/grid-rule-timber.scene" --assembly-scene "$EVIDENCE_DIR/contracts/assembly-final/reopened-owned.scene"
```

預設是兩種 fixture × 1400／390；fixture 以 API 建立，後續 `.scene` 匯出／New／原生完整確空／真 file chooser 重开與 `.gcanvas` Save／New／Open 才是此 probe 的產品路徑。這不宣稱 UI 從零繪製。

## 完整 native 與完整 CDP

完成上述 clean／fresh／16 MiB stack／adapter 前置後，逐條串行執行：

```bash
python3 tests/release_gate.py --url "$GEOMETRY_TEST_URL" --output "$REPLAY_DIR/gate-native-full" --timeout 3600 -- python3 tests/run_all.py
python3 tests/release_gate.py --url "$GEOMETRY_TEST_URL" --output "$REPLAY_DIR/gate-cdp-full" --timeout 7200 -- node geometry-web/cdp_test.js
```

全 native 不加 `--only`、`--allow-skip` 或 `--update-expected`。全 CDP 必須從沒有 `GEOMETRY_*_ONLY`、`GEOMETRY_CDP_FROM_P31` 或 engineering modifier 的新 shell 執行，確認原始 `CDP_SCOPE` 是 `full` 且 filters／modifiers 為空；不能把 partial 結果稱為 full。不要傳 `--no-sandbox` 等關閉安全隔離的旗標；本環境不採用舊命令文件中該類範例。CDP 還須檢查 structured completion／section floor，不能只看程序曾啟動或通過計數。保留每輪失敗 log 與原生 suite 原始輸出。

## CSS slice 與其餘 gate

```bash
python3 tests/release_gate.py --url "$GEOMETRY_TEST_URL" --output "$REPLAY_DIR/gate-css-inspector" --timeout 900 -- python3 "$EVIDENCE_DIR/css-c2-c4/runs/r4/script.py" --root /workspace/geometry-axiom --url "$GEOMETRY_TEST_URL" --out "$REPLAY_DIR/css-slots390-inspector" --bridge /tmp/geometry-tests/bridge --chrome /usr/bin/chromium --width 390 --only slots --entry inspector
```

此 `script.py` SHA-256 為 `4db7be7eadd9ccfec9ea72ec648a1c53ea4e20c7aaeaa72608c9367421aba881`；同目錄不依賴私人 helper，使用 `--root/tests` 的既有 `binaries`。這條命令只重跑已通過的 390／slots／inspector 補驗。其預設 `--entry dblclick` 仍保留已知失敗：要重現該路徑，另用全新的 output 目錄並明傳 `--entry dblclick`，不能把 inspector 通過當作 double-click 修復。其他三個 CSS slice 通過來自包內明列的各輪腳本／收據，不合併成「一支最終腳本全範圍通過」。`gates/css-c2-c4-r2` 是更早的 observer 失敗原件，已保留，不作最新完成 recipe。

其餘 canonical 命令從該 gate 的 `receipt.json.command` 讀取，沿用 repo 最新 AGENTS／`tests/INTEGRATION-GATES.md` 的順序與必要前置；每個 gate 用新的 `--output`，前述 sandbox adapters 保持設定。若環境政策拒絕瀏覽器，保存錯誤並停止該動作。Q38 service-restart 的公開 wrapper 有自身 producer gate／結果綁定，須按其 `--help` 所列明確傳入**同輪** producer；不能借用歷史私人 producer 路徑或拿一般 exit 0 代替 canonical completion。

## 解開原始證據

重跑上述 probe 不需要解壓歷史 raw log。需要查看原始 HTTP/native log 時，先對照包內 member manifest，再解至新目錄：

```bash
mkdir "$REPLAY_DIR/contracts-raw" "$REPLAY_DIR/native-raw" "$REPLAY_DIR/new-native-raw"
tar -xzf "$EVIDENCE_DIR/contracts/browser/raw-evidence.tar.gz" -C "$REPLAY_DIR/contracts-raw"
tar -xzf "$EVIDENCE_DIR/native/native-suite-raw-logs.tar.gz" -C "$REPLAY_DIR/native-raw"
tar -xzf "$EVIDENCE_DIR/native/new-owner-native-suite-raw-logs.tar.gz" -C "$REPLAY_DIR/new-native-raw"
```

公開 archive 已獨審為相對、安全的一般檔案；下載後仍應核 archive/member hash。私人完整 trace、舊工作管理 DB、Windows full raw log 或原附件若只列 hash，不表示已隨包提供，也不作可重跑命令的依賴。

## 綜合非空專案與 Q38 同輪服務重啟

沿用前述隔離服務、fresh binaries、clean `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`、16 MiB stack、sandbox adapters 與 repo 外全新 `REPLAY_DIR`。歷史 compound 命令的私人預設 fixture 路徑在這裡明確改由公開原件提供；原 probe bytes 不變：

```bash
python3 tests/release_gate.py --url "$GEOMETRY_TEST_URL" --output "$REPLAY_DIR/gate-compound" --timeout 1200 -- python3 -B "$EVIDENCE_DIR/gates/compound-project/sources/compound_project_probe.py" --root /workspace/geometry-axiom --url "$GEOMETRY_TEST_URL" --head 5174a8dafd8c48329d7166abbd3d104e3c28c0c4 --out "$REPLAY_DIR/compound" --assembly-scene "$EVIDENCE_DIR/contracts/assembly-final/reopened-owned.scene" --bridge /tmp/geometry-tests/bridge --model-base /tmp/geometry-tests/model-base --chrome /usr/bin/chromium
```

compound 的 model fixture 是該 checkout 已提交的 `tests/release-evidence/20261008-phase3-formal/projects/model-save.gcanvas`，probe 會核固定 hash。這是已授權、合成模型來源，不依賴外部私人圖紙。

Q38 restart 使用同一輪完整 18-check producer；先產生新的 producer 與 canonical receipt：

```bash
export GEOMETRY_Q38_SAVE_OUT="$REPLAY_DIR/q38-producer"
python3 tests/release_gate.py --url "$GEOMETRY_TEST_URL" --output "$REPLAY_DIR/gate-q38-producer" --timeout 1200 -- python3 tests/integration/q38_save_roundtrip.py
```

只有 producer 的 `completed=true`、18／0、command／gate exit 0、前後 clean SHA／runtime 一致時才執行下一條。public `run_q38_restart.py` 與同目錄 `q38_restart_probe.py` 必須保留原名；wrapper 會重新核 producer 的原始 log hash、完整 `.gcanvas` 與模型 baseline。先確認 18973 未被占用；wrapper 只重啟自己建立的 18973 服務，不停止共用 18971。

```bash
python3 tests/release_gate.py --url "$GEOMETRY_TEST_URL" --output "$REPLAY_DIR/gate-q38-restart" --timeout 1500 -- python3 -B "$EVIDENCE_DIR/gates/q38-service-restart/sources/run_q38_restart.py" --head 5174a8dafd8c48329d7166abbd3d104e3c28c0c4 --producer-dir "$REPLAY_DIR/q38-producer" --producer-gate "$REPLAY_DIR/gate-q38-producer/receipt.json" --out "$REPLAY_DIR/q38-restart" --port 18973
```

上述是依公開 CLI／檔案布局核對的重建 recipe，未在本次文件審查中執行。每輪使用新的輸出目錄；不使用封存 receipt 中指向舊雲端 TEMP 的 producer 路徑，不把先前輪的 18-check 結果改綁新服務。


## 最後條文核對的限定補測

SR15參數／anchor、SR18角色拒因、SR16／SR23真UI雙面更新與保存重開，以及新ASan／UBSan和#62五類故障注入，實際綁定clean `d8642b2e684038cbb8e24aba057c44e7aac1b231`。這個head只比5174多四份#173收據文件。公開腳本布局、完整CLI與隔離前置見[限定補測重現命令](contract-gap-probes/REPRODUCE.md)；原命令和各輪失敗保留於[附錄](contract-gap-probes/verification-addendum.md)。這些是最後發現的具名條文缺口，不要求重跑不變的完整suite。

故障注入driver的原始exit 1與分類器漏掉preview拒絕分支的結果不得改綠；逐項語義判定另附独立審查，重建命令不包含修改產品oracle或覆蓋原結果。歷史sanitizer缺件仍是unknown，新隔離執行不冒充找回舊log。
