# R11 空間平面圖與三視圖：驗收矩陣

規格依據：[issue #116 的完整設計](https://github.com/ZhiQiYang/geometry-axiom/issues/116#issuecomment-6436046251)，第 3.3.1–3.3.3 節及 K4-SP-EDIT／CREATE、K4-V3-PICK／VIEW／HIDE。

本文件描述可重跑的測試，**不是已取得的瀏覽器驗收收據**。原生測試、VM 狀態測試與瀏覽器事件測試各有自己的證據層級，不能相互替代。

## 瀏覽器測試入口

使用獨立服務、獨立 profile 與 TEMP 內的 feedback 目錄。服務由既有 `start_local.py` 以目前來源建置，不得對使用者的服務送 fixture reset。

```bash
GEOMETRY_FEEDBACK_DIR=/tmp/geometry-tests/r11-feedback \
python3 geometry-web/start_local.py --port 18841 \
  --binary-dir /tmp/geometry-tests/r11-bin
```

另一個能存取該服務的執行環境中：

```bash
GEOMETRY_TEST_URL=http://127.0.0.1:18841/ \
GEOMETRY_FEEDBACK_DIR=/tmp/geometry-tests/r11-feedback \
GEOMETRY_CHROME=/usr/bin/chromium \
GEOMETRY_CDP_PORT=19441 \
GEOMETRY_WORKSPACE_CONTEXT_MENU_ONLY=1 \
node geometry-web/cdp_test.js
```

`GEOMETRY_WORKSPACE_CONTEXT_MENU_CASES=W01,W07` 可選具名案例；它必須與 `ONLY=1` 一起使用，空字串、重複 ID、未知 ID 及與其他 ONLY 混用都拒絕。未提供 CASES 時依序跑 W01–W12。完整 `cdp_test.js` 第二片也會執行本段，編號為 **P1161**，避免與既有 P116 角材重用段落撞名；原來最後的 P359 保存／重載測試仍最後執行。

`GEOMETRY_WORKSPACE_CONTEXT_MENU_SCREENSHOTS` 可指定額外截圖目錄。截圖名稱涵蓋空間柱選單、全域三視圖空白選單、空間 projection 選單、俯視柱，以及 390px 選單／尺寸表單。

## 真事件與獨立觀察

建立 fixture 可以呼叫既有原生 API；每個產品操作從 CDP 的真正滑鼠、右鍵、鍵盤或 touch 事件進入。測試不直接呼叫選單 resolver、command builder 或 adapter action 冒充使用者流程。

觀察器只記錄實際 `/api`、`/view/read`、`/view/pick` request 與 clone 後的 response，不替換原生回覆。唯 W11 具名 fault 暫停一個真實已完成的 pick 回覆，跨過一次真 wheel 事件後再交回。W06／W11 另具名保留舊 DOM node 點擊，用於模擬排隊中的過期 action；這部分不冒稱 trusted 輸入。

只讀與取消均比較原生 `dump`、既有 history identity oracle、project／dirty 狀態，並確認沒有 `line`、`newid`、reset／load／undo／redo mutation command。成功改尺寸、建立、重複、刪除則檢查一筆 history 及原生幾何，並以實際 workspace 的 Undo／Redo 按鈕驗回復。

| 案例 | 入口與主要斷言 | 規格對照 |
|---|---|---|
| W01 | 真右鍵 column 71 與空白；typed 標題；選單項目精確集合；開選單零寫入 | K4-SP-EDIT／CREATE |
| W02 | 柱 W/D 帶原值；取消、no-op 零寫入；合法改尺寸同 ID 且其餘原定義逐字不變；單一 history 與 Undo／Redo | K4-SP-EDIT |
| W03 | 樑保留 axis、from/to、center、top，只改寬深；負值拒絕；刪除送 typed native command，只刪指定樑；Undo | K4-SP-EDIT |
| W04 | 重複不先取 ID／寫入；Escape 與真第二指取消；明確新位置後才建立，原物件不變 | K4-SP-CREATE |
| W05 | 放柱／拖樑取消；選單開啟後改 viewport，動作時用最新 SVG CTM；右鍵 pointerup 不當樑終點；精確建立幾何 | K4-SP-CREATE |
| W06 | 原尺寸節點移到同一按需表單；typed 焦點 ContextMenu 鍵；native revision 後舊 action 無效；檢視 submenu 與 projection 導覽只讀 | K4-SP-CREATE、共用殼 |
| W07 | 全域三視圖空白入口；無 open；space projection 真 right → native typed pick → 相同 menu adapter | K4-V3-PICK |
| W08 | boundary／column 同數字 71 不混型；游離 RC 沒有假 D3；屬性同 renderer 唯讀無表單輸入；真 boundary ID 開面 | K4-V3-PICK |
| W09 | 子選單精確四方向＋恢復；前／側／俯／仰原生軸；非對稱柱在 top／bottom 的實際幾何及 pick；全程只讀 | K4-V3-VIEW |
| W10 | 單隱 column 71 的全部 ops 與拾取，其餘 column 83／boundary 71 保留；逐項還原；分類 rc 關閉時全部還原仍不勾回 | K4-V3-HIDE |
| W11 | 舊 opening node 不作用於新 target；一次只開一個共用殼；刪除後同 ID 重建不繼承 mask；晚到真 pick 不跨新畫面重開 | K4-V3-HIDE、世代守門 |
| W12 | 390px 選單與尺寸表單不溢出、確認可達；三視圖 ContextMenu 鍵與 Escape；取消與檢視零寫入 | 鍵盤／小螢幕 |

fixture 使用 surface 71／72、space 9、column 71／83、beam 91。面與柱刻意同數字 ID，且 ID 不等於 scene index。孔、凹輪廓、角材面、原生畫家順序與 root 依賴獨立性由 `tests/test_workspace_view.py` 的真 native fixture 補強；不能據此聲稱對應瀏覽器流程已測。

## P64 的 UI 契約更新

既有 P64 S1 原本斷言尺寸列常駐工具旁。#116 第 3.3.1 節明定把原節點收進同一按需表單，因此同一個既有斷言改驗：點放柱後表單可見、原 `spaceSizeTools` 與五個原尺寸 ID 各只有一份、位於 `rcDialog` 而非工具列。原 P64 的斷言數量不變。這項新斷言必須在基底先紅，在新 UI 綠；沒有真瀏覽器收據就仍是未驗，不得用改 golden 掩蓋。

## 瀏覽器具名突變計畫（尚未執行）

以下是預定的實際產品源碼突變，不是已被殺死的結果。本版未提供可宣稱完成的 browser mutation receipt；應在 W01–W12 正常版真正全綠後，以獨立 checkout 逐項撤修、跑對應 W、保存具名失敗／退出碼／stderr，再還原跑綠。

| 突變名 | 撤修點 | 必須紅的案例／斷言 |
|---|---|---|
| SP_CONTEXT_ENTRY | 拔 `space-context-menu.js` 的 contextmenu 入口 | W01 `MENU_VISIBLE` |
| SP_FINAL_CTM | 建立動作改用開單時的 room 座標，略過動作時 CTM | W05 `CREATE_USES_FINAL_CTM_AT_ACTION` |
| SP_SECOND_POINTER | 拔重複／建立草稿的第二指取消 | W04 `SECOND_POINTER_CANCELS_DUPLICATE_DRAFT` |
| SP_DUPLICATE_SIZE_UI | 複製原尺寸節點形成第二組同 ID 控件 | W06 `P64_S1_SINGLE_ON_DEMAND_DIMENSIONS` |
| V3_CONTEXT_ENTRY | 拔 `view-context-menu.js` 兩個 host 的 contextmenu 入口 | W07 `MENU_VISIBLE` |
| V3_TYPED_TARGET | 將 native target 的 kind／boundaryId 改成猜測值 | W08 `NATIVE_ROOT_EXACT_TYPE_AND_ID`／`OPEN_CORRECT_D3` |
| V3_TOP_NATIVE_SIGN | 俯視繪圖保留、拾取改用仰視符號 | W09 `RIGHT_CLICK_USES_NATIVE_TYPED_PICK`／`NATIVE_ROOT_EXACT_TYPE_AND_ID` |
| V3_MASK_PICK | 繪圖有 mask，pick 忽略單物件 mask | W10 `HIDDEN_ROOT_UNPICKABLE` |
| V3_OPENING_LEASE | 拔共用殼對 retained node 的 opening ownership 檢查 | W11 `OLD_OPENING_NODE_CANNOT_HIDE_NEW_TARGET` |

上述預期只說明 oracle 目的。若撤修後未紅，必須回報測試缺口，不能直接記 killed。除瀏覽器事件之外，`workspace_view_state_mutations.js` 另提供七個已可獨立執行的 VM 狀態突變；其 receipt 明列 `VM state only`。

## 補充狀態與真 native wire 檢查

```bash
node --test geometry-web/workspace_view_state_test.js
node geometry-web/workspace_view_state_mutations.js --out /tmp/geometry-tests/r11-state-mutants
node geometry-web/workspace_view_state_test.js --native-wire /path/to/native-recordings
```

預設狀態 suite 自足，不依賴暫存 evidence 路徑。15 個測試以明列的 mock transport 隔離 adapter 狀態，涵蓋 closed capability／wire、typed root、不同工作區、revision／session／project/load 失效、pan/zoom、舊 read/pick、exact frame、no-op、只讀與 closed metadata。U15 另執行從實際 `app.js` 讀出的 hover scheduler／pickAt 路徑，驗 scheduler 的 ownership guard 確實傳入原生拾取，取消後的晚到 hover 不能覆寫右鍵的精確 typed target，也不再進舊 guide index mapping。

`--native-wire` 是獨立模式，讀取 C bridge 原始輸出的 `native-view-capability.json`、`native-view-read.json`、`native-view-pick-boundary.json`、`native-view-pick-column.json`、`native-view-pick-timber.json`。它回報每檔 bytes／SHA-256，驗 actual READY／HIT 可穿過 UI adapter，含 boundary 71 → placement 19 與同號柱／角材；它不宣稱重新執行了這些 native 命中或瀏覽器操作。

## 尚需取得的證據

真瀏覽器基底紅、新版 W01–W12 綠、原完整 CDP 兩片及 space_model gate、瀏覽器具名突變、原 ZIP 同 viewport 像素比對，都必須另有收據。只有當真跑得出新 P1161 段落的完整計數後，才能依既有機制追加新段到 golden／分片計畫；不得估算數量或改掉原段落。

本批自動化仍不涵蓋實體中文 IME、iOS Safari／Pencil、Android／TalkBack、實機觸控板與雙指效能。390px 的 CDP mouse viewport 不等於實體觸控裝置驗收。
