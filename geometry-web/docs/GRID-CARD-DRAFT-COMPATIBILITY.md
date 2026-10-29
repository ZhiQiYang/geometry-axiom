# 整卡原始草稿相容契約（PR #353 R353-07／09）

本片的編輯器能力為 `grid-card-draft/1`。它描述未提交的整卡原始輸入，不宣告 native 已建立整卡來源。正式整卡仍沿 R60 使用 `parameters/1` 與 `grid-card-reference/1`。

## 資料與能力矩陣

| 內容 | 完整專案格式 | 必要能力與保存行為 |
| --- | --- | --- |
| 舊單份直接值／逐欄 raw `/1` | `/10`，若有其他較新內容則沿較新格式 | 原能力；不新增整卡欄位，不合成整卡，不改 raw 或 pins |
| 舊來源子規則 raw `/2` | `/13`，若有其他較新內容則沿較新格式 | `grid-editor-draft/2`；原 `ruleDraft`、字串與 pins |
| 草稿集合 | `/17`，若有正式整卡則 `/18` | `grid-editor-drafts/1` 及各草稿實際能力；舊、新 raw 可共存 |
| committed 整卡，沒有整卡 raw | `/18` | `parameters/1`、`grid-card-reference/1`；不因正式來源而宣告 raw 能力 |
| raw-only 整卡 | 原 `/10`、`/13` 或 `/17` | 原草稿能力加 `grid-card-draft/1`；raw 本身不要求 native 整卡能力 |
| committed 與整卡 raw 並存 | `/18` | 正式來源能力與 `grid-card-draft/1` 同時保留 |
| 只有 scenario snapshot 內含整卡 raw | 根依原內容選格式 | 含 raw 的 snapshot 與根都宣告 `grid-card-draft/1`；不把 raw 提升為正式來源 |

`rawForm` 只要帶 `igCard`、`igCardU`、`igCardV` 就屬此能力，包括三個空字串、未知 ID、未完成映射。三欄仍須全有或全無；檔案讀取只驗有限原始資料形狀，合法性留給正式預覽。剝除必要能力、未知能力或無對應 raw 的偽宣告都拒絕。

既有 `grid-editor-draft/1`／`/2` 不因整卡 raw 改號：它們同時決定既有 source pin 的 legacy／rule-aware 表示。新增能力不改 `baseRef`、`inputRefs`、fingerprint、lost、orphan 或原始字串。保存／重開不重新讀目前 catalog 來補釘；缺 pin 的 raw 可以保存，但不能藉重開取得發布資格。明示重新取得仍依 R54 的確認流程。

## 舊 reader 與原子拒絕

相容測試固定使用主線 `405f8c5e1a637a16cbe47470faf5ae1fa02b8676` 的真實 `project-store.js`、`feature-attachments.js` 及完整七檔 CommonJS 閉包。`tests/pr353_legacy_reader.js` 逐檔驗 Git blob，缺檔或不符即報前置條件失敗，不以目前版本或簡化 reader 代替。

固定舊 reader 的 manifest 有限能力清單與 raw 欄位白名單會拒絕新 raw。測試以真 ZIP 核對舊 writer→新 reader；舊 reader 拒絕則接到既有 `ReferenceWorkspace` 的 staging handler，驗在上傳／原生命令及 context、dirty、raw、history 寫入之前失敗。該 staging 測試使用 Node VM 的最小 DOM，**不是舊版 App／Chrome／native 驗收**。正式 App Save/Open 與現版缺能力拒絕另由 P353 的具名 CDP 案核對。

## 執行與突變

有完整 Git 歷史時，可直接執行：

```sh
node --test-reporter=tap tests/test_pr353_compatibility.js
python3 tests/run_pr353_compat_mutations.py --out /tmp/pr353-compat-mutations
```

輸出目錄須不存在或為空。runner 先驗正常基線，再為每個具名突變驗「同名控制綠→具名斷言紅→還原綠」，最後重跑完整正常基線。逾時、環境例外、缺固定 reader、少跑案例或還原失敗都不計 killed。

在 mutation runner 的無 Git 複本或淺層 checkout 執行 CDP 前，先在有固定 commit 的 repo 匯出原件：

```sh
compat_legacy=$(mktemp -d)
node tests/pr353_legacy_reader.js --materialize "$compat_legacy"
export GEOMETRY_PR353_LEGACY_ROOT="$compat_legacy"
```

此目錄只含測試固定原件；每次載入仍驗原始 Git blob。CLI 回報每檔 byte 數、SHA-256 與 Git blob，不宣告原生或瀏覽器已通過。

## GEO-219 減項

移除定義圖下原有獨立 `.ig-def-hint` 常駐說明段落，把尺寸／卡片標題的定位說明併入既有 `#igViewNote`。保留原操作與資訊，減少一個常駐區塊；`BACKLOG.md` 僅記入 GEO-262 對應條目。Node 只驗來源接線，CDP 案驗實際 DOM。完整七項驗收狀態以後續同版本實跑回報為準。

## 本片驗收邊界

固定的舊 reader 已支援正式 D64 `/18`，所以 committed-only 保持可讀；拒絕的是含本次新增整卡 raw 的 raw-only／mixed。不可把這個測試寫成「所有 `/18` 都被舊 reader 拒絕」。

來源子規則的瀏覽器相容夾具先建立 `/2` 編輯草稿，再選整卡映射；本片不修復現存 `/1` 編輯草稿轉 `/2` 時兩種 `baseRef` 指紋表示不同而被守門拒絕的流程，也不以自動重算歷史 pins 繞過該守門。原有 27 個 P353 案例與斷言保持；本片新增七個具名瀏覽器案例與七組撤修，全部 34 案及 21 組的最終 WSL 收據由後續回報綁定新 head。
