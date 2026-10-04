# WP60-A：正式來源子規則保存與 reader

基底 main `861b65e9e2281192dd41a068fdd87866617b638d`（2026-10-04）。Refs #60、#58、#59；本切片不關閉 #60／#61／#62。採納依據是 [公理層 D19a/I25a/R32](../../公理層.md) 與 [已合併 PR107 的 native 契約](../../geometry-core/GRID-SUBDIVISION-NATIVE-CONTRACT.md)。舊 proposal 的 REPEAT_PANEL、巢狀、allocator 替代設計不是現行授權。

## 邊界與盤點

本分支修改 `project-store.js`、專屬測試／runner 登記及本文件；已正常合流 main `4bea91a`（PR124）。PR125 的 app/index/contextmenu 不競寫，`model_update`、space producer 不改。root 已允許有界修正 reference 的 /11 capability 守門；獨審發現需要區分輸入與最終 World，目前列出 native/reference 最小接點交 root 協調，尚未套用。沒有公理、能力容量、其他 owner worktree、部署或使用者 PC 變更，沒有重做 PR107 native core。

PR107 已提供 source-local uint32 非零 ruleKey、`nextRuleKey` 高水位（0 表耗盡）、all-cells／單一 signed cell、decimal-string cell、guide `gridrule:` 與直接 `at-line rule`。dump 包含未套用來源、刪完 rules 的非預設高水位、依賴順序與 native 能力標記；load-prepare 在獨立 World 驗完整來源閉包，confirm 才原子替換。這些都是沿用的 native 能力。

舊正式 store 會直接拒絕新語法／能力。C `model_base` snapshot 能讀回新語法並保存正式定義（它既有規則會刪掉衍生 R18 註解及 presentation）；Python `modeling.base.load_base` 只支援 engineering/parameters，仍以 `UNSUPPORTED/CAPABILITY` 拒絕 rules。C 能 dump 不代表模型求值、依賴／hash 與完整模型 adapter 已支援。本分支不改 hash，不擴 model 能力。

## 最小格式與驗證路徑

新增 `geometry-canvas/11`，能力 `grid-subdivision-rules/1`。沿用同一 ZIP、`manifest.json`、`world.scene`、sources hash closure 與 streaming bounds；沒有第二套匯入系統或第二份 rules JSON。正式 rules、名稱、selector、等分數、key／高水位及 typed refs 只在 native scene。

有實際 rule／highwater／gridrule／at-line-rule 語法時，reader 獨立要求 scene 的 `requires grid-subdivision-rules/1`，包含 `next 1` 及 replay 後已不存在的物件。manifest 同時必須為 /11 並保留能力。未知能力／schema、manifest 降版、移除標記與 hash tampering 在解包時拒絕；幾何合法性、容量與來源閉包依真 native load-prepare 拒絕。服務能力經 reader 的有限集合過濾，再由既有 `assertProjectCapabilities` 守門；缺能力會取消候選，不 confirm。

/11 可共存原有工程／參數／組構、原始 sources bytes、圖頁、projection、reconstructionReviews、`featureAttachments` 的 grid-editor-draft/source-rooms/source-room-history。這些資料保持既有 schema 與驗證器。沒有 rules 的檔案仍依既有 /1…/10 選格式，不新增規則或預設細分。含 rules 的模型 input/package 明確拒絕；獨立且不含 rules 的合法歷史模型可與目前 rules scene 共存。

房間 metadata 的新 edit 在沒有 scene 讀取時預留五種 native 能力字串與既有 lifecycle 成長。舊檔讀取及 codec 保存沿用原四能力預留，再加實際宣告／使用能力，不能因未使用的未來能力縮小舊檔上限。`tests/fixtures/wp60-a-main4bea-near-capacity.gcanvas` 由原 main 的真 pack/unpack 產出，清單 8,388,493 bytes，含 PDF 與 history，僅重新壓縮 ZIP；原 `7bc8682` reader 拒絕已重現。修正後 reader／codec 完整 roundtrip 通過、真超限拒絕。新 edit 邊界亦真 pack/unpack 含 rules 與房間/history/raw附件，+1 byte 拒絕；8 MB 與所有既有容量不變。

## owner 接點與尚未交付

- #61 規則 editor 的 raw 未提交草稿目前沒有對應正式 schema／UI adapter。本切片只證明既有 source/binding raw grid 草稿共存，**不聲稱規則草稿已保存**。請由共用 owner 擴既有 finite attachment validator，沿用 context token、flush、共同保存與 ContextHistory；不保存 preview token／key reservation。
- **獨審 hold：/11 candidate capability 核對仍未完成。** 原候選只提供最終 World 的 required capabilities／typed objects，沒有其 canonical scene；輸入 scene 的 marker-bearing default-only allocator、稍後刪除 source 或 reset 均合法，但最終 required capabilities 是空陣列。不能直接以輸入 lexical capability 等值核對，也不能只改成 subset 而放過 canonical mismatch。建議在既有 native `cmd_load_prepare` 增加候選的 `final_scene`（同一次 parse 的 World dump，不另跑 solver），/11 明確要求此欄位並獨立核對它與 candidate.required_capabilities；输入 lexical／manifest／service 檢查保持原狀。舊 /5…/10 守門、/model/space-replay 與 #77 atomic hooks 保留。
- **獨審 hold：舊近上限正式 browser 保存接點。** 真 Chromium 已成功開啟上述 main 舊檔，但 `manifest()` 的無 scene metadata 預留仍會拒絕 export。最小接點是 `manifest(c, scene = null)` 將 scene 傳給容量檢查，`exportSnapshot` 將已有 `r.text` 傳入；所有新 metadata edit 仍省略 scene，保留五能力預留。此接點尚待 root 協調，不能聲稱正式 browser 舊近上限 roundtrip 通過。
- `manifestData` 的格式列舉亦止於 /10。實際 exportSnapshot 將真 dump 交給 `P.pack`，由 store 選 /11／补齐模型與 projection containers，真 browser 保存已驗。owner 要在 metadata 顯示 /11 時使用 `P.SUBDIVISION_FORMAT`，不要另存一份 rules。
- #61 全流程空白 → 用 UI 建 rule／preview／confirm → 選子線、跨面來源改動，以及未失焦規則草稿、物理手機／OS 選檔仍未驗。完整 #60 依這些接點後續交付；fresh context 不載入舊 undo/redo stacks。

## 可重現驗收

先 red：最小 pack 測試於原基底以「尚未支援的工程能力」失敗。獨審 checkpoint 的 `tests/test_subdivision_project_store.js` 為 32 個 Node tests：31 pass、1 fail、0 skip；唯一 red 是 /11 canonical candidate mismatch 尚未拒絕。新增 4 個真 formal replay、main 近上限完整 archive、同時降版／移除 manifest capability 並重算合法 hash 的負例；降版負例不呼叫 prepare/confirm，replay 的輸入 service 能力不足仍取消候選。不能把這個 checkpoint 稱為綠燈或完整 #60。

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
