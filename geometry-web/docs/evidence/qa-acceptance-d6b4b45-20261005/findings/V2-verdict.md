# V2 複驗 T4-01:共享房間來源(#roomSourceCreate)保存後底圖顯示設定遺失

- 被測:main d6b4b450d741fcbbfd75c51631915d3082926990,worktree D:/geometry-axiom-qa;服務埠 8837(每次重起 probe fresh:true,版本 e2f2ee7b…,`probe_8837*.txt`);Chrome 偵錯埠 9337;profile V2-A(建檔)、V2-B(重開共享)、V2-C(重開對照),皆全新。1440x900。合成圖 synthetic_floorplan_A3_landscape.pdf,未驗真實案場。保存測的是下載備援分支(fsAccess:none),File System Access 原生分支未測。390px 未跑(本題是保存語意,非響應式)。
- 結束:daemon/Chrome 自行關閉;8837 只用 stop_server 停 run 記錄 PID(先核對命令列為 `serve.py 8837`);`git -C D:/geometry-axiom-qa status --short` 為空。

## 結論:T4-01 成立(而且比原描述更廣),屬「資料錯誤或遺失(顯示/對位偏好,非幾何)」;新發現,未被 #77 五道 gate 明列。信度:高(實測兩輪檔案一致 + 讀碼確認因果)。

## 1. 唯讀解壓 T4 兩檔
- t4-ulset-save4:format /10、faces=[]、全檔 0 個 opacity/locked/crop 欄;底圖基準只存在 featureAttachments.source-rooms/2 的 planes[].alignment {x:120,y:0,mmPerPx:17.64…,rotation:90} 與 calibration。
- ctrl-plain-import-op-lock:format /1、faces[0].pages[0] 含 opacity 0.84、locked true、crop。說法屬實。

## 2. 獨立重現(正式 UI)
共享路徑:新專案→匯入→校準 5000→確認 ROOM_A→不透明度 0.70→#roomSourceCreate(ROOM_A)→#roomNew 建 ROOM_L(6000x5000 L,boundary 2)→L 設 0.30+鎖定→面 1 設 0.75→旋轉 90→0.75→X=120→0.75→鎖定→保存→停服務重起→V2-B 開檔。
對照組:同前到確認 ROOM_A,不按 #roomSourceCreate;0.75→旋轉 90→X=120→鎖定→保存→重起→V2-C 開檔。

| 項目 | 共享來源路徑(存檔 → 重開) | 對照組 |
|---|---|---|
| 不透明度 | **遺失**:0.75 → 0.5 | 保留 0.75 |
| 鎖定 | **遺失**:已鎖 → 未鎖 | 保留 true |
| 旋轉 / X / Y | 保留 90 / 120 / 0(plane.alignment) | 保留 |
| mmPerPx、校準點/距離/單位 | 保留(plane.calibration、alignment.mmPerPx) | 保留 |
| crop(取景) | **不存**:plane 無 crop 欄,materialize 一律整頁(讀碼已確認;本次 crop 為整頁,未實測非整頁) | 存 |
| reviewRequired/核對 | 改由 rooms[].reviewState 表示,保留 needs-review(重開顯示「基準或邊界變更·需複核」) | reviewRequired true 保留 |
| 頁碼 / sourceId / pageSize | 保留(plane.page=1) | 保留 |
| 來源紀錄 records | 原頁 records 與核對收據移入 legacyHistory(唯讀歷史),共享頁 records 恆為 [] | 存於 page.records |
| ROOM_L | 同樣受影響(0.30+鎖 → 0.5/未鎖);房間↔邊界對應保留(ROOM_A=邊界1、ROOM_L=邊界2,同 plane/collection) | — |

**比 T4 描述更廣的三點(皆實測)**:
a. 不必保存就會丟:按 #roomSourceCreate 當下 0.70 → 0.5(s05-after-adopt.png;此刻 SVG 仍顯示 0.7,控制項與畫面不一致)。
b. 任何共享基準變更(旋轉/X)會把不透明度/鎖定重置:0.75→旋轉 90→0.5;0.75→X=120→0.5(s10)。另一間 ROOM_L 的 0.30+鎖定也被 A 的基準變更重置為 0.5/未鎖(s13)。
c. 只改不透明度/鎖定不標髒:重開後(「已保存」)改 0.8+鎖定,狀態仍「已保存」(r04);對照組同操作變「有未保存的變更」(c05)。使用者沒有任何提示會丟失。

## 4. 原因(讀碼)
- 已確認 source-plane.js:25 plane 白名單只有 id/sourceId/page/coordinateSpace/pageSize/calibration/alignment/basisRevision;:164-168 fromPage 丟掉 crop/opacity/locked;:170-177 materialize 硬寫 crop=整頁、opacity .5、locked false、records [](註解明說 derived renderer data 不序列化)。
- 已確認 reference-workspace.js:440-480 adoptRoomSource 把原頁自 g.pages 移除(:480 groups.delete),所以 g.pages 為空;:1093-1098 manifestData 只序列化 g.pages → faces=[]。T4 推論的 :1093-1098 是「現象點」,根因是共享 plane 契約沒有顯示欄位。
- 已確認 顯示值存在哪:room-collection-workspace.js:115-127 sourcePage 的 per-context/per-bid 快取物件(oc.underlays[bid]);app.js:4717-4726 feChangeUnderlay 對 opacity/locked 只 Object.assign 到該快取,再呼叫 reference-workspace.js:833-835 changed()→RoomCollectionWorkspace.changeBasis(值未變);room-collection.js:154-157 change() 遇 no-op 不寫 metadata → 不標髒、不入 history。基準真的改變時 :123 以 materialize 覆寫快取 → b 項重置。
- 開檔還原:planes 經 materialize 重建,顯示值必為預設(推論自上述,實測吻合)。
- 預期依據:docs/REFERENCE-PROJECT.md:9(對位、旋轉、透明度與鎖定同屬「對位與顯示」)、:28(圖頁含 crop/opacity/locked)。公理層 I36/I39/I41 規範工程/參數/組構保存,不涵蓋底圖顯示;#77 公理層無條號 → 這是 #77 契約(issue #77 首則留言明列 plane 欄位)與 REFERENCE-PROJECT 的規格缺口,不是 SSOT 違反。

## 5. 已知與否
- issue #77 五 gates(registry ZIP 往返/未知 envelope/source closure/attachment undo-redo/late-context)都不談顯示設定;且 registry 往返在 d6b4b45 已實際可用(plane/calibration/alignment 往返正確)。→ **新發現**(與 #77 範圍相鄰,建議掛 #77)。
- PR #134:改 app.js 多處,但不碰 feChangeUnderlay(4717)/底圖面板(6800-6870)/source-plane/room-collection/manifestData → 不涉及。
- PR #137(draft):改 reference-workspace.js:1101-1107 manifestData(加 scenarioCatalog)與 project-store.js(format /14 SCENARIO_FORMAT、keys 驗證),**沒有改 faces/g.pages 邏輯、source-plane、room-collection、app.js** → 未修 T4-01,不會改變行為;但與修正點同一函式/同一驗證器,有文字衝突風險。#135/#136 只動文件與 tests/binaries.py,無關。

## 6. 影響
資料遺失(次要):遺失的是使用者的底圖顯示/鎖定偏好與(若曾裁切)取景範圍;幾何、校準、對位、房間關聯不受影響。鎖定遺失會讓「已鎖定對位」在重開後可被誤拖動 → 間接風險改到共享基準(並把所有同來源房間標需複核)。信度高。

## 7. 建議修正範圍(未動手)
- 最小點:在共享 plane 外另存「每房間或每 plane 的顯示設定」(opacity/locked,及 crop 是否要保留需產品決定),走 source-rooms 附件新欄位(schema 升版 + capability,舊 reader 拒)或獨立 view 欄;feChangeUnderlay 對共享房間的 opacity/locked 改走 metadata change(標髒、可 undo);materialize 以 view 帶入既有顯示值,基準變更不得重置;adopt 時沿用原頁 opacity/locked(crop 若不支援,adopt 前應拒絕或提示)。需先拍板:顯示設定是「每 plane 共用」還是「每房間」。
- 回歸測試:共享路徑 保存→fresh context 開檔 斷言 opacity/locked(兩房各自)、adopt 前後值不變、旋轉/X 後值不變、只改不透明度會標髒且一步 undo;突變測試:拿掉新欄位序列化須紅。
- 排序:**排在 #137 之後**(同 manifestData 與 project-store format/keys 驗證,且 #137 佔用 /14);與 #134 無檔案級衝突。

證據(QA/evidence/V2/):s01–s15(建檔)、r01–r04(重開共享)、c01–c05/cr01(對照)、downloads/v2-shared-save1.gcanvas、v2-ctrl-save1.gcanvas、issue77.txt、pr134.diff、pr137*.diff、tools/。console/pageerror 全程 0。
