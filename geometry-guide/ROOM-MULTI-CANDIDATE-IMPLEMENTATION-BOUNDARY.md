# #87：可直接推進的有界 session 多房候選

2026-10-08。基準：整合候選 `1eb6ccbbef58e4c94c2f3a377db95cfd2dd848e8`，不是宣稱已合入 main。本文完成實作邊界與驗收準備；本輪另由專用分支依此推進產品，實際完成範圍及收據在最終整合矩陣核收。

來源：[issue87](https://github.com/ZhiQiYang/geometry-axiom/issues/87)、[PR157 原提案](https://github.com/ZhiQiYang/geometry-axiom/blob/52d0c9e7942ff6d8a1b62d10e23f25a6bc0f6049/geometry-guide/ROOM-MULTI-CANDIDATE-PROPOSAL.md)、[Q37 精確採納](IMPLEMENTATION-QUEUE-20261004.md)。本輪重新讀取 issue87／PR157 正文，兩處均無後續評論。舊 PR 的 proposal-only 狀態不抹去原 A→B→C 工作授權，也不構成本次「全部收尾」後一般工程實作的額外許可門檻。

## 1. 可做的範圍與不需要新公理的證明

第一個可完成切片：**在已有且已校準的 #77 共享來源頁／collection，以一次本地分析取得有界候選，在既有工作區逐個明選、修正、核對，經 #77 新建交易逐一接受。** 未接受列表只存在目前分頁 session；保存已接受成果前可安全暫停，再於同一 session 恢復未接受修正。候選不是正式幾何、不预配 native id、不批量接受、不覆蓋原房 A。

| 待加行為 | 現行規格的充分約束 | 公理差異 |
| --- | --- | --- |
| 從原頁提出多個可核對區域 | 候選只是來源分析，正式輪廓才須符合 D1／D3／I2；沿用 #54 來源座標→整數 mm 核對 | 無；不新增幾何型別 |
| 逐個明選新房，不替換現房 | Q37：房間名稱／Boundary 獨立，新增不覆蓋，明選才編輯 | 無；沿既有 #77 intent |
| 接受與 undo／redo | I8／I8a，加既有 native＋metadata 同一步交易；取消和過期不提交 | 無；不能把兩次 commit 偽裝成一筆 |
| 共享來源／基準 | Q37：同 PDF 共用 basis；basis 變更舊房 needs-review，原生幾何不自動變形 | 無；不建 Space 父子或自動 transform |
| Session-only、來源改變即失效 | issue87 已明列；草稿不是 D9 正式定義，不進 World／保存能力 | 無；沒有新 persistent schema |
| 12 列、64 分量、期限與 Worker 排程 | 已授權工程選容量／效能預算；超限不得假報完整 | 無；以實測固定，不問使用者逐一選數字 |
| 安全暫停與恢復 | 不改正式定義、不繞 lease／save guard，仍保留未接受原字串及修正 | 無；屬受授權工作流的 owner 生命週期接線 |

**本切片對 `公理層.md` 的逐條 diff 為空。** 可以在既有授權內直接實作／驗收，不需要使用者先重答 Q37 或替這份文件「追認公理」。以下是可檢查的應用契約，不能拿來放寬 I2、猜造孔／牆或改正式世界。

## 2. 相對現行單房與 PR157 的逐項差異

| ID | 原行為／提案 | 本次可實作的差異與反例 |
| --- | --- | --- |
| MR01 | #54 的單種子外環意圖可替換 host | 多房從同一次 obstacle/grid 解析枚舉分量；接受只轉接 #77 `beginNew`，永不回落 host 替換 |
| MR02 | 單房只有一份 `fe.draft` | 仍只一份 active editor；其他列僅保存 bounded plain session data，舊 DOM/input 不得寫新列 |
| MR03 | PR157 的既有頁與零房新頁替代方案 | 本切片採既有校準共享頁；零房 staged source-collection 交易是後續增量，不偷偷建立占位房或第二 basis |
| MR04 | issue87 已指定 session-only | 不新增 manifest／IndexedDB／localStorage 欄位；只保存已接受的 native＋room＋原圖＋basis |
| MR05 | 直接 Save 遇草稿須拒絕 | 明選安全暫停後才回原 Save；不能臨時把 hasWork 改 false、保存後改回來 |
| MR06 | 來源或 context 變更退休舊操作 | 換頁／校準／來源／換案／undo／redo 令整個 session 失效；唯有可核實為本 session 成功新建一房的回執可延續剩餘列 |
| MR07 | Q37 basis 變更舊房不變形 | 候選全失效；已接受房只依既有契約 needs-review，不自動重建、改名或移動 |
| MR08 | PR157 文中 PR153／155 尚未整合的歷史 | `1eb6ccb` 已包含其候選修復；在本來源上保留 pan、受控 Enter、IME／repeat guards，不重開舊 owner 工作單 |

原 PR157 的分析、去重與安全暫停條件仍是具體工程輸入；本文件不把其歷史 A1–A13 寫成已通過。尤其不再把「採納優先方案／是否 session-only」列成開始上述切片前必問的問題：前者採最小增量，後者已由 issue87 明示且與本輪授權相容。

## 3. 唯一 session owner 的狀態契約

```text
idle → analyzing → ready → editing → previewing → confirming → ready
ready/editing → parking → parked → restoring → editing
任何狀態遇 source/context/service 失效 → stale
取消自己的分析 → idle 或保留仍新鮮的舊 ready 列表
```

每份 session 固定 `project/context/serviceSession/generation/planeId/collectionId/sourceFingerprint/requestFingerprint/runId`；每列有 `candidateId/draftRevision/sourcePoints/pointsMm/rawInputs/dimensions/reviewed/status`。這些是私有暫時資料，名稱不冒充已註冊 schema。

- source fingerprint 含原始來源 hash、頁碼、原座標系／頁尺寸、crop、calibration／alignment／basis revision；request 另含分析方法、參數、人工分隔與分析版本。相機 pan／zoom 不在其中。
- Candidate ID 使用 run identity＋完整 canonical component key；不要預測 Boundary ID、拿 ordinal 或名稱當跨 run 身分。
- 選列先把當前未套用原字串／修正回存原列，再取得唯一 editor；任一幾何修正清 reviewed。reviewed 綁同一列與 draft revision。
- Worker request／reply、PDF operator-list／decode 完成、進編輯及接受之前都驗 owner；只 terminate 自己 Worker，late message／finally 不清新 session／新 editor。未知 native reply 走同 request receipt recovery，不重送建立。
- 接受成功須同一次交易提交 native Boundary＋room metadata；以回執核對新增 pin、source/basis、既有房完整不變後才更新 session context，剩餘列全部清 reviewed。核對不出唯一成功就失效，不能按「context 大概相同」解鎖。
- Park 前先取得完整 bounded snapshot；有 native preview／confirm、room intent、lease、history group 或未知回覆時拒絕。退休自己的 Worker/consumer/drag/draft owner 後才標 parked，再呼叫正式 save gates；其他工具的 blocker 不動。
- 保存成功、取消或寫入失敗均保留 parked snapshot；恢復時重验來源及正式資料身分，使用新 generation／新 editor，清 reviewed，不復活舊 token。保存狀態本身改變不等於幾何來源失效。
- 關閉／reload 不承諾保留 session；離開提示包含 parked 修正，不能只看 dirty=false。過期內容可顯示原因，不能接受。真正跨次續編需另有明確持久化契約，不能混入本切片。

## 4. 分量取得與拓撲的最低實作要求

沿 #54 的同一個 obstacle→compressed grid→component→ordered loops 路徑抽共用 helper；單房 API 仍用同一 helper 的單 seed。多候選一次遍歷 free cells，不以密集 seed 反覆解析，也不重渲每間房的 PDF。

1. 明示分析的原頁 crop；連到 crop 外緣者不假裝閉合，不輸出 bbox 房間。
2. 外环每一凹入轉角、完整 cyclic adjacency 都要保留。斜邊、退化、分岔、無法閉合明示，不自動修成矩形。
3. 巢狀障礙內環不擅當另一房；帶孔候選須保留內環警告，不能把外環面積冒充淨面積。真孔轉回既有人工孔流程。
4. 開門使兩區連通時顯示一個連通候選／警告；只有使用者既有人工分隔明確閉合後才重取兩區，不猜門弧或瓶頸。
5. exact 去重只做完整 ordered loops 的循環起點／方向正規化；同 bbox／area 不同凹口不能合併。近似重複標示，不直接刪除。
6. 排序固定為原座標 minY→minX→canonical key；pan／zoom／編輯不重編列。與已接受同來源同 basis 房間只在可證明完整相同時阻止重建；身份不明不猜。
7. 向量失敗可明示原因後整批影像 fallback；已取消或失效不 fallback。向量部分成功不自動混補另一批影像候選。

初始工程預算沿 PR157：1 Worker、30 秒消費者總期限、64 封閉分量、總 16,384 頂點、每列 256 頂點、顯示最多 12 列；解析 pixels／ops／cells 仍用現有上限。13–64 個完整分析結果可固定排序列前 12，但必標未完整呈現；超過分析容量則整批拒絕，不能先取 12 就省略其餘拓撲／包含檢查。工程量測可調整數值，須同步邊界測試及顯示文案，不改為無界或假完整。

## 5. 可逐項交付的驗收矩陣（未執行）

| Gate | 正例 | 必須打紅的負控制／拒絕例 | 觀察證據 |
| --- | --- | --- | --- |
| M01 拓撲 | 自製双房／三房含 L／凹口；vector、raster 分列 | 同 bbox/area 的錯凹口、crop 未閉合、孔內家具框假房 | 獨立完整 ordered loops 及 adjacency，不只面積 |
| M02 來源／座標 | PDF 原頁旋轉、四種 basis、crop、pan／zoom | 舊 basis、錯頁、換 bytes、錯誤 rounding | 來源坐標／mm 對照及偏差；不使用私人PDF |
| M03 排序／容量 | 12與13列、64與65分量、256與257頂點 | 提前截成12卻標complete、溢位／逾時、忽略後續衝突 | exact status／coverage／完整診斷；原案未變 |
| M04 所有權 | 列B未套用raw切C再返回；取消／重取 | B舊input改C、late Worker／decode／finally覆蓋新session | 逐列raw/draft/reviewed、owner frame、零native mutation |
| M05 新建原子性 | A既存，接受B，一次undo／redo，再接受C | host A被替換、metadata另添一步、重複confirm、繞reviewed | 完整World、typed room pins、history身分、transport次数 |
| M06 未知回覆 | native已提交而回覆丟失，原receipt恢復 | 重送create、未判定先解鎖、同號新案接受舊reply | 實際request/receipt與context；fault injection明標 |
| M07 暫停保存 | 已接受B＋未接受C修正/raw；park→真下載→同session恢復 | 臨時清hasWork、漏raw、保存取消/失敗丟稿、lease仍在卻save | 完整snapshot、保存狀態、native/history零額外變更 |
| M08 新profile重開 | 真 `.gcanvas` 正式選檔 | 未接受候選偷存、原圖重複／缺失、錯pin/unknowncap仍替案 | bytes、World、room/basis/附件完整roundtrip；候選不復活 |
| M09 源與歷史變化 | 正常接受回執受控延續 | 外來修改、undo／redo／basis變更卻仍可接受active/parked舊列 | 源stamp、history/frame、明示stale與原房保全 |
| M10 UI與負擔 | desktop/390px選列、核對、接受、pan、尺寸Enter | 焦點跨列、hidden按鈕強制click、repeat／composition繞守門 | 真指標／鍵盤、console、screens；不用emulation冒充IME |
| M11 既有回歸 | 原#54單房替換、#77人工新建、PR153/155行為 | 新候選adapter劫持舊意圖或改舊失敗語意 | 原入口結果及完整CDP；依AGENTS判斷Space是否受影響 |
| M12 實圖／裝置 | 後續可用環境才測真iOS、使用者既有私人圖 | 用390px／公開合成圖代替真裝置／實圖 | 分開保存範圍，不以缺裝置否定已驗Linux切片 |

M10 的操作／時間比較須包含首房與 shared source 設定、辨識等待、逐邊核對、修正、暫停／恢復及重核，與同一夾具的現有人工流程比較；未實測不得聲稱更快。每個新負控制證明對應 oracle 會拒絕，再跑正常正式入口；不能只把原作者數字抄成獨立驗收。

## 6. Writer、UI減項與停止條件

演算法 owner 只抽取共用 helper／Worker protocol；共享 app／source/history 由單一整合 owner 接線。候選 adapter 只使用正式 public APIs，不寫 private Context Map。主線檔案所有權不因這份提案而轉移。

新增 UI 的減項：把「新增房間」合併成一個方式控制（人工／同頁候選）；重用唯一尺寸／頂點／確認表單，列表不複製每房表單，不新建常駐工具列或第二來源工作區。實作時在 BACKLOG 記錄此具體減項，常駐操作說明≤3塊。

可完成的交付是上述既有校準頁首切片及 M01–M11 對應範圍，不把它說成「所有私人圖／實體手機／零房起步／跨次草稿全完成」。沒有新的待決公理；若實作發現必須新增保存欄位、改 basis 會自動移動舊房、批量確認或支援 I2 外輪廓，立即停在具體差異，不以本文件擴權。

零房初次建立 collection 的替代入口、未接受候選跨 reload 保存是可分開規劃的後续功能，**不是先做本切片必須等的決策**。不得因舊 PR157 列了二選一就把可直接做的工作重新丟回使用者。
