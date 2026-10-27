# 原生角材完成尺寸料單（#47 F4a 首批）

進入已放置的面，左側「面內物件 → 角材料單」沿用原有角材清單。
每支角材顯示原生完成 L、截面 A/B、方向與法線厚度側；點列會選取並定位畫布。
在畫布點角材也會反向高亮同一列。手機先開左欄；尺寸來源與端面資訊按需展開。

範圍預設是此承載面的所有正式已放置角材，可以先選取角材，再把範圍切成「所選角材集合」。
集合固定為當次明選的 ID；後續點選、相機裁切、排序不會靜默改變範圍。
集合中的構件被刪除或換面後會拒絕導出並提示重新選定，不把消失構件改成長度 0。
mm/cm 只格式化顯示，CSV 一律保存精確 mm。

CSV 匯出逐件相同資料，包含 typed timber/surface 身分、方向、定位與跨距選擇器、
工程尺寸來源、兩端世界座標、來源 SHA-256 指紋及未知資訊標記。
全部欄位包引號並處理換行與引號；公式樣式欄位以文字前綴保護。
匯出前再核對原生來源指紋；若來源已變，先更新料單並要求核對後再次匯出。
選取、顯示與匯出不改 World、專案 dirty 或復原歷史。

## 資料與能力邊界

K1-a（D49／I59(d)）在原生工程來源與 assembly slot 的有效 A/B 最後增加唯讀 `terminal`：
材料末端包含 `(id, version, fingerprint)`，其餘末端為 literal／spec／parameter，無法求值為 null。
它由核心既有 D28／R31 查找鏈提供；前端不可解析 path 或重做查找。做法 gap 的直接值仍標為 literal，
不區分做法與物件直接整數。既有欄位、World dump、定義指紋與歷史不變；K1-b 另由專案功能附件宣告 `cutting-plan/1`。

- `references.sourceFingerprint` 由原生 `eng_definition_hash` 對正式定義計算，排除畫布擺位。
  目前讀取整個 World 定義指紋，無關來源變動也會保守要求重新核對。
- 只計原生 placed Timber，每個 `timber:id` 一次。兩個同截面／同長的實際構件各自保留，Timber 0 亦是有效身分。
  獨立 placement 0 亦合法，和保留的 boundary 0 是不同型別；null 不是 0。
  不計未生成規則／Binding，不混入空間模型的已保存 mesh 快照，不估算影像或外接盒長度。
- A/B/L 及方向讀原生資料；兩端世界座標只是以原生長度與軸展開供核對，不是另算料長。
- 已與 PR53 的 format8／生成來源整合。生成的 owned Timber 仍逐件一次；原生 references
  重用 assembly-read 的型別來源，保留 instance/member、binding、固定 rule version/fingerprint 及 A/B 來源。
  binding 有效尺寸須與正式 Timber 核對相等，資料不足時拒絕，不把生成來源展平成「直接尺寸」。
  CSV 同時保存完整 typed dimension source definitions 與生成身分／來源指紋。
- 直接尺寸沒有材料名稱，保持「材料未設定」。工程來源保留 typed source、固定版本、path、override。
  自動推導跨距的確切支撐構件／局部面 selector 尚未由現有 bridge 提供，明示「支撐身分未提供」。
  這是 #47 的剩餘追溯適配項，不能將端點座標當成支撐關係已完整辨識。
- 料單為現場導出視圖，不增專案附件或修改保存格式；保存正式專案後可重開並重新導出。
- F4b 加工餘量、鋸縫、毛料、原材、餘料、採購及庫存均不在本批。

K1-b 由既有「排序」控制合併的「料單檢視」入口接上 F4b，範圍與料單仍共用原生正式角材；詳見 [CUTTING-PLAN.md](CUTTING-PLAN.md)。`derive` 的錯誤新增型別 `code`，原文字保持；owned slot 的來源帶入原生 `terminal`。F4a 與保存快照的 CSV 共用序列化時剔除 `terminal`，保持原有位元組。

## 驗證

`tests/test_timber_schedule.js` 驗精確範圍、同尺寸不同身分、失效拒絕、單位／排序與 CSV 安全。
`tests/test_reference_contract.py` 驗原生指紋只讀、排除畫布擺位、來源變動與 undo/redo。
`geometry-web/timber_schedule_test.js` 是完整 `cdp_test.js` 的 P80 外掛，使用真原生服務與真 Chrome。P79 保留給 #54 房間候選；整合時兩段均須保留。
實際命令、計數與尚未驗項在 PR 與 BACKLOG 回填；測試存在本身不代表通過。
獨立審查追加合法零號與延遲預驗負例：資料刷新、原生提交後尚未刷新、範圍／context改變，
或錯誤讀回都拒絕導出；同時核對没有新增 CSV Blob，不只看提示與快取是否更新。
