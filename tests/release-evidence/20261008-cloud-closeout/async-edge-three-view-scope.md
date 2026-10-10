# #173「成功套用及三視圖」覆蓋補充

結論：**新 edge probes 未驗 #173 的三視圖 UI，也未驗 edge 請求等待期間切換三視圖再釋放晚回覆。** `main／face × 1400／390` 只表示物件畫布檢查器和面內檢查器兩種 UI，不能用數量代替三視圖路徑。#174 的 handle probes 確實進三視圖，但没有編輯 #173 的邊長 input，不能借用它結案 #173。

這次只做來源／既有證據唯讀核對，未啟動瀏覽器。實跑版本仍是 `bdd1bf7812ba6126aab9ddffced43cd200ac977e`。本次靜態工作區為 `9a4136da264249f76ba08258a7f14be926f96a95`；另直接用 `git show bdd1bf78:...` 核對下列來源，不把新 head 寫成已受測。app.js bytes 與原受測 `86c82675d0b7eb0dc76659705186273112f6d17c2712426f7a681e5fa48497d8` 相同。

## 新探針實際到達哪裡

`browser_probe.py::fixture` 一開始 `await setView3(false)`，再 reset、建合成面、renderObjects。`edge_test` 選 `.object-row[data-kind="boundary"]`；`scope='main'` 直接操作 `#mainEdgeLength0/1`，`scope='face'` 再正常點 `#inspEnter`，進 `oc.edit.bid===731` 的面內工作區操作 `#edgeLength0/1`。整個 `edge_test` 沒有點 `#btnObj`、沒有驗 `view3===true`、沒有操作 `#cv` 的三視圖手把或選取。

`handle_test` 才點 `#btnObj`、驗 `view3===true`，操作 `#workSurf` 和 `[data-v3-tool]`。它扣 `proj`，場景是面 711／712；沒有送 `commitEdgeLength`，沒有 #173 input draft 或拒絕重繪。

面 731 的 scene 有 placement（`origin 0 0 2500 u +x v +y`），只證明具備可投影資料，不能證明 UI 曾開三視圖。主畫布 success-sibling 的完整 scene 是：

- before：外環 `0,0 4000,0 4000,3000 0,3000`，另有孔；
- after：外環 `0,0 4200,0 4200,4242 0,4242`，孔／placement／canvas-pos 留在原資料；
- gate 中第一個真正 native 回覆是 `ok:true`、原命令只改寬到4200；其後又出現另一筆 trusted change 和 native 命令，把未送出的鄰邊也改成4242。

因此「成功的 native apply 路徑有實際到達」成立；「成功套用後保全另一個未送出邊長的驗收完成」不成立。兩 pane／兩尺寸都有同一個未通過條件。這不是單純因沒成功回覆而未驗，也不是成功回覆就全通過。

## 真正三視圖入口與來源分歧

在受測 bdd1bf78：

- `geometry-web/index.html:52–53`：`#btnCanvasView` 是物件畫布，`#btnObj` 明確是三視圖。
- `app.js:10403–10442`：`setView3(true)` 會設 `view3=true`、`oc.on=false`，清選取／關抽屜，顯示 `#cv`、viewToolbar、v3PickPanel，隱藏 inspectorContent 和 objectWorkspace，再 await render／refreshSurfaces；按 `#btnCanvasView` 才回物件畫布。
- `index.html:312` 的 v3PickPanel 只含選取結果和游標位置。`app.css:1441` 也在 v3-mode 隱藏右欄其他內容。三視圖没有 #173 的 mainEdgeLength 欄位；不能為了測試而硬顯示它。
- 真三視圖編輯是 `[data-v3-tool="edit"]` → enterEdit／drawEditHandles，以及 `#cv` pointerdown／move／up → canvasDown／canvasMove／canvasUp。`canvasUp`（app.js:1424起）會走 emitBoundary，再 enterEdit／drawEditHandles。
- `emitLine`（app.js:1181起）在原生回覆後看**當時的** `oc.on`：true 走 renderObjects，false 走 render＋refreshSurfaces。新 edge probes 一直留在 oc.on 路徑，所以沒有覆蓋原生回覆後進入三視圖分支的晚回覆影響。

這些是來源事實與覆蓋界線，不是尚未執行的三視圖產品失敗聲明。

## 精確未驗路徑與可行下一步

| 待驗路徑 | 既有入口與前置 | 判定界線 |
| --- | --- | --- |
| #173 主／面內的 edge 提交等待中離開並切三視圖，再釋放真正 success 或 rejection 回覆 | 從合法可放置面、無角材引用的合成 fixture 起；正常輸入／Tab 送出後扣原 native reply；main 直接點 #btnObj，face 先正常點 #workspaceBackButton 返回，再點 #btnObj；等待 setView3 的 render／surfaces 完成。 | 驗最新 mode、選取／工作面、B 的顯示與已完成工作不被舊 A 搶回；原生成功造成的合法 A 變動與拒絕不變分開比對。當前 probes沒有這條。 |
| 三視圖內直接拖邊／頂點成功與拒絕後的顯示一致性 | 正常選 #workSurf、edit，依實際 view 對合法面上的可見手把 pointer 操作；成功採保持孔在外環內的改動，拒絕採孔會跑出外環的改動；扣實際 bhit／line 回覆並等待完整操作 settled。 | 對照完整 boundary／dump 與實際三視圖手把；若切B或view，舊操作不能重建A編輯／清B。這是與#174同歸屬根因相關但尚未在新edge probe驗的三視圖操作，不是假造三視圖邊長欄位。 |
| 回物件畫布／面內後的模型顯示 | 正常 #btnCanvasView → 選原面／#inspEnter，再等真正 inspector 完成。 | 欄位 defaultValue／幾何與完整 native 模型一致；是否保留主動離開前未送出草稿要依既定行為／原probe釐清，不擅自創造「跨所有離開永遠保留」政策。 |

原 #173 私有 probe 不可得，無法知道其未完成「三視圖晚回覆」究竟準備走哪個細分情境。可沿上述既有入口先做有限回歸；不能宣稱重現原探針。若 `.reference-impact` modal 開著，先依產品正常取消／確認並等待關閉，不能強制點 #btnObj。本文建議的無引用 fixture 可避免把 modal 遮挡誤作邊長缺陷。

交付狀態應写：「main／face 的 native success 已到達，但 draft 保全驗收失敗；#173 三視圖及跨 view 晚回覆尚未驗。#174 的三視圖 A→B handle 缺陷已另有真證據。」

private staging 的 README／REVIEW／binding 已補這條界線；原始結果、scene、圖和各輪脚本全部保持原 bytes。
