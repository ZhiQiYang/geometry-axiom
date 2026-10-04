# WP60-A：正式來源子規則保存與 reader

基底 main `861b65e9e2281192dd41a068fdd87866617b638d`（2026-10-04）。Refs #60、#58、#59；本切片不關閉 #60／#61／#62。採納依據是 [公理層 D19a/I25a/R32](../../公理層.md) 與 [已合併 PR107 的 native 契約](../../geometry-core/GRID-SUBDIVISION-NATIVE-CONTRACT.md)。舊 proposal 的 REPEAT_PANEL、巢狀、allocator 替代設計不是現行授權。

## 邊界與盤點

本分支只修改 `project-store.js`、專屬測試／runner 登記及本文件。PR124 sole owner 的 `reference-workspace.js`、`model_update`、space producer，以及 PR125 的 app/index/contextmenu 均不競寫。沒有 native、公理、能力容量、其他 worktree、部署或使用者 PC 變更。遠端 open PR 盤點只有 #124／#125，沒有重做 PR107 的 native core。

PR107 已提供 source-local uint32 非零 ruleKey、`nextRuleKey` 高水位（0 表耗盡）、all-cells／單一 signed cell、decimal-string cell、guide `gridrule:` 與直接 `at-line rule`。dump 包含未套用來源、刪完 rules 的非預設高水位、依賴順序與 native 能力標記；load-prepare 在獨立 World 驗完整來源閉包，confirm 才原子替換。這些都是沿用的 native 能力。

舊正式 store 會直接拒絕新語法／能力。C `model_base` snapshot 能讀回新語法並保存正式定義（它既有規則會刪掉衍生 R18 註解及 presentation）；Python `modeling.base.load_base` 只支援 engineering/parameters，仍以 `UNSUPPORTED/CAPABILITY` 拒絕 rules。C 能 dump 不代表模型求值、依賴／hash 與完整模型 adapter 已支援。本分支不改 hash，不擴 model 能力。

## 最小格式與驗證路徑

新增 `geometry-canvas/11`，能力 `grid-subdivision-rules/1`。沿用同一 ZIP、`manifest.json`、`world.scene`、sources hash closure 與 streaming bounds；沒有第二套匯入系統或第二份 rules JSON。正式 rules、名稱、selector、等分數、key／高水位及 typed refs 只在 native scene。

有實際 rule／highwater／gridrule／at-line-rule 語法時，reader 獨立要求 scene 的 `requires grid-subdivision-rules/1`，包含 `next 1` 及 replay 後已不存在的物件。manifest 同時必須為 /11 並保留能力。未知能力／schema、manifest 降版、移除標記與 hash tampering 在解包時拒絕；幾何合法性、容量與來源閉包依真 native load-prepare 拒絕。服務能力經 reader 的有限集合過濾，再由既有 `assertProjectCapabilities` 守門；缺能力會取消候選，不 confirm。

/11 可共存原有工程／參數／組構、原始 sources bytes、圖頁、projection、reconstructionReviews、`featureAttachments` 的 grid-editor-draft/source-rooms/source-room-history。這些資料保持既有 schema 與驗證器。沒有 rules 的檔案仍依既有 /1…/10 選格式，不新增規則或預設細分。含 rules 的模型 input/package 明確拒絕；獨立且不含 rules 的合法歷史模型可與目前 rules scene 共存。

## owner 接點與尚未交付

- #61 規則 editor 的 raw 未提交草稿目前沒有對應正式 schema／UI adapter。本切片只證明既有 source/binding raw grid 草稿共存，**不聲稱規則草稿已保存**。請由共用 owner 擴既有 finite attachment validator，沿用 context token、flush、共同保存與 ContextHistory；不保存 preview token／key reservation。
- `reference-workspace.prepareProjectScene` 的現有格式列舉在 /10；owner 下次接線應把 `P.SUBDIVISION_FORMAT` 納入「candidate required capabilities 等於 sceneCapabilities」分支。現有 native 候選、manifest/service 能力、最終 objects／pins 與 atomic confirm 已實跑 /11，不因這個列舉缺口跳過 native 校驗。
- `manifestData` 的格式列舉亦止於 /10。實際 exportSnapshot 將真 dump 交給 `P.pack`，由 store 選 /11／补齐模型與 projection containers，真 browser 保存已驗。owner 要在 metadata 顯示 /11 時使用 `P.SUBDIVISION_FORMAT`，不要另存一份 rules。
- #61 全流程空白 → 用 UI 建 rule／preview／confirm → 選子線、跨面來源改動，以及未失焦規則草稿、物理手機／OS 選檔仍未驗。完整 #60 依這些接點後續交付；fresh context 不載入舊 undo/redo stacks。

## 可重現驗收

先 red：最小 pack 測試於原基底以「尚未支援的工程能力」失敗。修改後正式 `tests/test_subdivision_project_store.js` 為 25 個 Node tests：10 codec／syntax／schema／legacy/model tests，fresh native/formal import、能力不足候選 cancel、8 個真 source-closure/native 負例、C/Python adapter 區別、房間/history/raw附件、import 一次 undo/redo、native 舊 scene。

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

驗證記錄與實際 ZIP／browser 證據將在完成 gates 後列於同版交接；不能把進行中 gate 當通過。assert 數與 case／test 數分列。Browser plugin 不可用，agent-browser CLI 也不存在；依技能 fallback 用已有 Playwright＋Chromium，不安裝依賴。瀏覽器保存驗證選用真 download fallback（測試上下文無 showSaveFilePicker，沒有模擬 writable handle），不代表原生 OS 檔案對話框。
