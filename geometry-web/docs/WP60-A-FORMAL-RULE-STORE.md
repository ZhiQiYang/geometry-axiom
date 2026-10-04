# WP60-A：正式來源子規則保存與 reader

基底 main `861b65e9e2281192dd41a068fdd87866617b638d`（2026-10-04）。Refs #60、#58、#59；本切片不關閉 #60／#61／#62。採納依據是 [公理層 D19a/I25a/R32](../../公理層.md) 與 [已合併 PR107 的 native 契約](../../geometry-core/GRID-SUBDIVISION-NATIVE-CONTRACT.md)。舊 proposal 的 REPEAT_PANEL、巢狀、allocator 替代設計不是現行授權。

## 邊界與盤點

本分支修改 `project-store.js`、專屬測試／runner 登記及本文件；已正常合流 main `4bea91a`（PR124）、`417f4c0`（PR127）。PR125 的 app/index/contextmenu 不競寫，`model_update`、space producer 不改。依 root 後續明示授權，增加既有 load-prepare 的候選 canonical scene，並完成 reference 的 /11 能力守門與實際 dump 容量檢查窄接點。沒有公理、能力容量、其他 owner worktree、部署或使用者 PC 變更，沒有重做 PR107 native core。

PR107 已提供 source-local uint32 非零 ruleKey、`nextRuleKey` 高水位（0 表耗盡）、all-cells／單一 signed cell、decimal-string cell、guide `gridrule:` 與直接 `at-line rule`。dump 包含未套用來源、刪完 rules 的非預設高水位、依賴順序與 native 能力標記；load-prepare 在獨立 World 驗完整來源閉包，confirm 才原子替換。這些都是沿用的 native 能力。

舊正式 store 會直接拒絕新語法／能力。C `model_base` snapshot 能讀回新語法並保存正式定義（它既有規則會刪掉衍生 R18 註解及 presentation）；Python `modeling.base.load_base` 只支援 engineering/parameters，仍以 `UNSUPPORTED/CAPABILITY` 拒絕 rules。C 能 dump 不代表模型求值、依賴／hash 與完整模型 adapter 已支援。本分支不改 hash，不擴 model 能力。

## 最小格式與驗證路徑

新增 `geometry-canvas/11`，能力 `grid-subdivision-rules/1`。沿用同一 ZIP、`manifest.json`、`world.scene`、sources hash closure 與 streaming bounds；沒有第二套匯入系統或第二份 rules JSON。正式 rules、名稱、selector、等分數、key／高水位及 typed refs 只在 native scene。

有實際 rule／highwater／gridrule／at-line-rule 語法時，reader 獨立要求 scene 的 `requires grid-subdivision-rules/1`，包含 `next 1` 及 replay 後已不存在的物件。manifest 同時必須為 /11 並保留能力。未知能力／schema、manifest 降版、移除標記與 hash tampering 在解包時拒絕；幾何合法性、容量與來源閉包依真 native load-prepare 拒絕。服務能力經 reader 的有限集合過濾，再由既有 `assertProjectCapabilities` 守門；缺能力會取消候選，不 confirm。

/11 可共存原有工程／參數／組構、原始 sources bytes、圖頁、projection、reconstructionReviews、`featureAttachments` 的 grid-editor-draft/source-rooms/source-room-history。這些資料保持既有 schema 與驗證器。沒有 rules 的檔案仍依既有 /1…/10 選格式，不新增規則或預設細分。含 rules 的模型 input/package 明確拒絕；獨立且不含 rules 的合法歷史模型可與目前 rules scene 共存。

房間 metadata 的新 edit 在沒有 scene 讀取時預留五種 native 能力字串與既有 lifecycle 成長。舊檔讀取及 codec 保存沿用原四能力預留，再加實際宣告／使用能力，不能因未使用的未來能力縮小舊檔上限。`tests/fixtures/wp60-a-main4bea-near-capacity.gcanvas` 由原 main 的真 pack/unpack 產出，清單 8,388,493 bytes，含 PDF 與 history，僅重新壓縮 ZIP；原 `7bc8682` reader 拒絕已重現。修正後 reader／codec 完整 roundtrip 通過、真超限拒絕。新 edit 邊界亦真 pack/unpack 含 rules 與房間/history/raw附件，+1 byte 拒絕；8 MB 與所有既有容量不變。

## owner 接點與尚未交付

- #61 規則 editor 的 raw 未提交草稿目前沒有對應正式 schema／UI adapter。本切片只證明既有 source/binding raw grid 草稿共存，**不聲稱規則草稿已保存**。請由共用 owner 擴既有 finite attachment validator，沿用 context token、flush、共同保存與 ContextHistory；不保存 preview token／key reservation。
- 已完成 /11 candidate capability 核對。既有 native `cmd_load_prepare` 新增候選的 `final_scene`（同一次 parse 的 World dump，不另跑 solver）。序列化完整成功後才輸出 ok；open/write/read I/O fault injection 均回 IO error、失效候選、保留 World/revision。/11 明確要求此欄位並獨立核對它與 candidate.required_capabilities；輸入 lexical／manifest／service 檢查保持原狀。marker-bearing default-only allocator、稍後刪除 source 或 reset 合法匯入，最終能力可為空；canonical mismatch／缺欄候選則 cancel、零 confirm。舊 /5…/10 守門、/model/space-replay 與 #77 atomic hooks 保留。receipt consumers 盤點：formal reader、HTTP passthrough、scenario verifier/native CLI 均不鎖死 native receipt 頂層欄位；模型 package 嚴格 schema 未改。真 native import／scenario tests 46/46。
- 已完成舊近上限正式 browser 保存接點。`manifest(c, scene = null)` 將 scene 傳給容量檢查，`exportSnapshot` 將已有 `r.text` 傳入；所有新 metadata edit 仍省略 scene，保留五能力預留。真 Chromium 正式 open→共同保存按鈕下載→390px 新 context reopen 11 checks 通過，保留整份 non-scene metadata、PDF bytes 與保存 dump。原 fixture 沒有 canvas-pos，瀏覽器既有自動排版加入位置，因此 sceneHash 正常依實際保存 dump 重算；沒有改模型 hash 或刪除資料以繞容量。新 metadata edit 拒絕仍保留 World/context/history；該近上限資料加入 rules 的 codec 保存明確超限拒絕。
- `manifestData` 的格式列舉亦止於 /10。實際 exportSnapshot 將真 dump 交給 `P.pack`，由 store 選 /11／补齐模型與 projection containers，真 browser 保存已驗。owner 要在 metadata 顯示 /11 時使用 `P.SUBDIVISION_FORMAT`，不要另存一份 rules。
- #61 全流程空白 → 用 UI 建 rule／preview／confirm → 選子線、跨面來源改動，以及未失焦規則草稿、物理手機／OS 選檔仍未驗。完整 #60 依這些接點後續交付；fresh context 不載入舊 undo/redo stacks。

## 可重現驗收

先 red：最小 pack 測試於原基底以「尚未支援的工程能力」失敗；獨審 checkpoint `70d5e21` 的 canonical mismatch 仍 red，證據保留。補齊窄接點後 `tests/test_subdivision_project_store.js` 33/33 Node tests 通過、0 skip；新增 4 個真 formal replay、main 近上限完整 archive、同時降版／移除 manifest capability 並重算合法 hash、canonical mismatch 與缺 candidate scene 負例。降版負例不呼叫 prepare/confirm，replay 的輸入 service 能力不足仍取消候選。這不代表整項 #60／#61 完成。

```sh
ulimit -s 16384
python3 tests/binaries.py build
GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge \
GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base \
GEOMETRY_WP60_EVIDENCE_DIR=/tmp/wp60-evidence \
node --test tests/test_subdivision_project_store.js
python3 tests/run_all.py --build
```

非機密範例：`geometry-web/examples/source-subdivision-v11.gcanvas`。含兩個配置、實際大 signed cell、guide 與有合法支撐的直接 rule-line 材料、同號不同 source 的未套用 rule、耗盡 allocator 及刪完 rules 的非預設高水位。原生 dump 在新服務/專案上下文逐字往返；不靠同一 JSON stringify/parse。

完整範例 `geometry-web/examples/source-subdivision-rooms-v11.gcanvas` 是真 browser 共同保存按鈕下載的原 bytes，另含原 PDF、source-rooms/source-room-history 與既有 raw source-grid draft，以及實際保存的 canvas layout。它不是 #61 rule editor 產物；不把原生 scene 檔冒充完整 archive。

驗證記錄與實際 ZIP／browser 證據將在完成 gates 後列於同版交接；不能把進行中 gate 當通過。assert 數與 case／test 數分列。Browser plugin 不可用，agent-browser CLI 也不存在；依技能 fallback 用已有 Playwright＋Chromium，不安裝依賴。瀏覽器保存驗證選用真 download fallback（測試上下文無 showSaveFilePicker，沒有模擬 writable handle），不代表原生 OS 檔案對話框。

## 最終 exact-head 驗證

已凍結、root source review 通過、完整 gates 的 code head 是 `65e733c05aa1d5b3c8b080601ca31419398ced06`，main `417f4c0ee67235e5042b22f94318b7bca0c0baee` 位於 ancestry。後續提交只增加本交接、原始 evidence／截圖與上述實際下載範例，可執行 code/test blobs 保持相同；不為文件／證據重跑長測試。

| Gate | 實際終態／範圍 |
| --- | --- |
| `run_all.py --build` | 66 suites，exit 0。合計 2123 個各 suite 計數單位，2122 pass／0 fail／1 具名 Windows GDI 平台不適用；其中有 C checkpoints，不能稱 2123 test cases。Node aggregate 實際 491 tests 與 floor 相符。 |
| 專屬 formal/native suite | 33/33 Node tests，0 skip；另真 native import／scenario Python suites 10+36 tests 均於 strict runner 通過。 |
| full CDP | completed=true，1987 assertions／0 failure／0 skipped group；82 段逐段 golden matched，保留 main 的 P76=86／P79=87。exception count=1 是 P38 刻意注入且確認的 fb-auto-probe，沒有新增未預期例外。assertions 不是端到端案例數。 |
| full SPACE | completed=true，202 assertions／0 failure，browser health clean；原範圍明列 omitted timber-material／timber-source-guards。 |
| 完整 rules archive browser | 16 checks，1440×900／390×844，真 native、file input、共同保存下載、新 context 重開、PDF/history/raw draft/ref closure；console/page errors 0。 |
| 原 main 近上限 legacy browser | 11 checks，官方 open→save→390px 新 context reopen；保留 non-scene metadata、PDF bytes、saved dump；新 metadata edit 與新增 rules 超限仍拒絕。 |
| 原房間 browser gates | official owner API 的 browser／exit／recovery／remove 全部 exit 0，分別 37／61／111／46 checks；recovery 的預期 HTTP409 與真正 errors 分開記錄。 |
| Scenario GridDraft | real-owner validator/native 1/1 Node test，0 skip。 |
| I/O fault injection | open／write／read 三種模式皆回 IO、失效候選、不改 World/revision；Linux LD_PRELOAD 的實際故障，不代表 Windows 已驗。 |
| Evidence Links adapter browser | 67 checks 通過；attachment backend 是原 harness 的 injected-memory，**不是正式 ZIP evidence-links 整合**。 |

原始 logs、browser result JSON、desktop/mobile 截圖與 code blob pins 位於 `docs/evidence/wp60-a-20261004/final/`。最終 browser 私有服務 `/runtime` 皆 fresh=true；未使用使用者服務、圖紙、PC 或清理其儲存。

保留不適用／未驗：Windows GDI、physical Windows/iOS/OS file picker、#61 rule UI／未提交規則草稿，以及 SPACE 列出的兩個 omitted groups。獨立 `scenario_browser_check.cjs` 官方 harness 在原 main4bea 已缺 source-plane/feature-attachments scripts；只在 /tmp harness 補實際依賴後，1280／390 模組 ZIP browser 通過，nativeCalls=12／forbidden liveCalls=0／errors=0，不能聲稱未改官方入口通過。#77 owner-five 入口未配置 test adapter，實跑 exit 3／executed=0；其預設 pending_implementation 訊息不是本輪產品盤點，亦不把四個 browser gates 冒充該五項測試。
