# #173 replacement 拒絕殘值：第一批交付

原生拒絕較早的邊長提交後，Inspector 已重繪產生的新欄位現在回復模型值；較新的输入和其他邊的未提交草稿保持原值。修復以提交身分追蹤目前欄位，不再只尋找已斷開的舊 DOM。

| 執行 | 完整受測 SHA | dirty | 原 16 案 | exit |
|---|---|---|---|---|
| 改前 | `9029a8f6bc00a9ff8de1d2b0deb844f331e032e3` | false | 12 pass / 4 fail | 1 |
| 改後 | `bd6294ea2ea5bfe77c1611c479becbdff80c3372` | false | 16 pass / 0 fail | 0 |

兩輪在 Linux Chromium、1400px 與 390px，重播 #176 的原 16 案。拒絕案例要求 World 逐字不變、殘值回復 `4000`；控制組要求新輸入 `5151`、兄弟邊草稿 `4242` 及成功提交 `4200` 保持正確。明示的產品 redraw fault injection 保留，沒有以強制點擊、重試或放寬斷言取得通過。

## 正式 EDGE 回歸：保留三輪失敗與最終通過

| 正式輪次／完整受測 SHA | 檢查數 | pass / fail | completed | exit |
|---|---|---|---|---|
| `9029a8f6bc00a9ff8de1d2b0deb844f331e032e3` | 26 | 24 / 2 | false | 1 |
| `bd6294ea2ea5bfe77c1611c479becbdff80c3372` | 38 | 34 / 4 | false | 1 |
| `c15f14b288389a60483993980bab5012e40b9539` | 38 | 36 / 2 | false | 1 |
| `992e1f788ea6f8f88f8de2cad49dc4c2df5c98e7` | 38 | 38 / 0 | true | 0 |

四輪受測工作樹都乾淨。基底原正式 harness 有 26 個檢查，第一個修復另外加入 12 個拒絕替換欄位檢查，後三輪使用相同 38 檢查 harness；不同版本／輪次的通過數沒有相加。正式原結果、原 assertion 行、完整 log 的路徑投影及原 log／receipt 雜湊各自保留：[基底 24/2](formal/baseline-9029/receipt.public.json)、[首修 34/4](formal/after-bd6294e/receipt.public.json)、[修正 face 後 36/2](formal/after-c15f14b/receipt.public.json)、[最終 38/0](formal/after-992e1f7/receipt.public.json)。

基底兩個失敗是三視圖往返時 blur 把未提交 `777` 寫入模型。首修 `bd6294e` 又引入兩個 face 成功回覆遺失 pending 身分的回歸，實際欄位及模型成為 `500`；原 16 案當時已通過，但正式 34/4 不被宣稱為整體通過。`c15f14b` 修正 face pending 身分，仍保留原兩個三視圖失敗。`992e1f7` 讓導覽保留草稿且不提交，正式 38/0 才完整通過此限定 harness。

正式 harness 自行建立與停止隔離服務。收據中的 caller URL 是 orchestration label；`actualFormalNativeBindings` 列出實際服務 runtime 與其直屬 bridge 程序／binary SHA-256，沒有用外面的 19176 服務冒充正式測試服務。26／38 檢查的已提交 JS 原件也按 byte 保留在 `formal/`，雜湊見 manifest。

正式完整 raw log 含私人 feedback／機器根目錄，原件留雲端且雜湊／大小列在每輪公開投影；公开 `log.public.log` 只替換那些路徑。`assertions.raw.log` 保留原 PASS／FAIL／EDGE_RESULT 行，`result.raw.json` 是原 result 全檔的逐 byte 副本。沒有刪掉失敗、改 completed 或修改原件。

這是合成 fixture 的限定瀏覽器驗證；fixture 由既有 API 建立，重繪由既有 renderer 注入，並未宣稱 UI 建立 fixture、Windows、完整 CDP、完整 Space 或 golden 核收。完整 CDP 整合驗證另列，不把這 16 案相加成完整模式。

原始命令輸出及結果逐 byte 保留於 [baseline/raw.log](baseline/raw.log)、[baseline/results.json](baseline/results.json)、[after/raw.log](after/raw.log)、[after/results.json](after/results.json)。每輪公開收據列出完整 SHA、前後 dirty、來源/runtime/native 身分、命令、退出碼、原始 log/result 雜湊：[改前](baseline/receipt.public.json)、[改後](after/receipt.public.json)。

公開收據明示刪除了機器與隔離 feedback 路徑；原件未修改，仍保留在本次雲端 scratch，原件大小與 SHA-256 見 [manifest.json](manifest.json)。這些公開投影不冒充原收據。私人 feedback、圖片、trace/profile、native binary/sidecar 及工作管理器資料沒有收入 Git。

## 腳本來源與重播

[probe/provenance.public.json](probe/provenance.public.json) 記錄 #176 中的原始 repository 路徑、完整 SHA 與原始／實際執行腳本 SHA-256。實際執行 portable probe 僅改 hardcoded repository 根目錄；函式與 oracle AST 不變，JS instrumentation 與原件逐 byte 相同。

此公開可重播副本又將根目錄改為必填環境變數 `GEOMETRY_EVIDENCE_REPO`，公開 wrapper 的預設根目錄改為目前目錄；**公開副本沒有冒充已執行的檔案**，兩者實際執行與公開雜湊分列。函式與 oracle AST 全等仍經核對。使用現有乾淨 checkout、自有 fresh service、同版本 bridge/model-base、隔離 feedback，並為每次執行選全新輸出目錄：

```sh
GEOMETRY_EVIDENCE_REPO="$PWD" python3 tests/evidence/cloud-takeover-20261009/first-edge/probe/run_gate.py \
  --root "$PWD" --url "$GEOMETRY_TEST_URL" \
  --bridge "$GEOMETRY_TEST_BRIDGE" --model-base "$GEOMETRY_MODEL_BASE" \
  --feedback-dir "$GEOMETRY_FEEDBACK_DIR" \
  --output "$GEOMETRY_EVIDENCE_GATE_OUT" --artifact-dir "$GEOMETRY_EVIDENCE_ARTIFACT_OUT" \
  --expected-cases 16 -- \
  python3 tests/evidence/cloud-takeover-20261009/first-edge/probe/browser_probe.py \
  --url "$GEOMETRY_TEST_URL" --out "$GEOMETRY_EVIDENCE_ARTIFACT_OUT" --only edges
```

## 歷史收據與範圍

既有完整 CDP `2207/0/0` 的受測乾淨版本仍是 `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；`9029a8f6bc00a9ff8de1d2b0deb844f331e032e3` 是後續文件／證據提交，不改綁。#173 完整 Windows 模式仍為 `1692 pass / 2 fail`、exit `1`、`completed:false`。P74/P75 局部通過不相加；本雲端未讀到 Windows 原件，明示尚未核收，也不宣稱這輪比對過 golden。

## 接續工作

Cross-B、held-bhit、新手勢保護、390px 卡片雙擊、完整安全 Resume、#123 已採納 UI、#54 單房操作成本及兩處過期整合閘門文件仍各有下一步，由 root 接續修復。held-proj 既有修復只保留回歸，沒有重新修同一件事。

GitHub 的依賴仍是 #169 → #176 → 本工作分支；本批維持 draft，交維護者審閱。沒有合併、部署、改帳務／安全設定，或發出 #168/#169 審查留言。
