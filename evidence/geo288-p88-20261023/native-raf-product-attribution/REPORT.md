# P88：產品／測試歸因獨立審查

受驗來源 `3d681636902371ecc528b20f51eea33e272581c9`。先以原工具 fresh fetch handoff至 `acd1289228d490c68a139cf17e02fdc1f3cb247c`，讀 head `ee28481` 審查。此輪只讀產品、既有工具及已完成fixed trace；沒有修改來源、開Chrome、編譯、重測或新增門檻。

結論：現有證據足以支持「舊helper取得未穩定DOM的座標，原callback完成後該座標已過期；修正於唯一真click前重測而有效」。它不能證明原F13自然紅就是此query，也不能證明所有真人點擊交錯安全。fixed中未觀察到表單pointerdown/up期間的query／restore位移；目前沒有新增已確立的產品缺陷，不建議只憑假設改產品。

## 原fixed證據能證什麼

原 trace `/tmp/g288p88r/fixed/trace.json`，89,601,264 bytes，SHA256 `7804288498ee8556082f59849ba989656c1eebdfe4e900b9e38938b8c3fd42bf`。本目錄 `FIXED_TRACE_PROJECTION.json` 是有明列截斷的派生摘錄，不能取代原trace。fixed原stdout為143斷言／0失敗／無新增例外、partial不比golden；本報告沒有重跑，也不把它冒完整grid/canvas。

| 原事件serial | performance.now ms | 觀測 |
|---|---:|---|
| 7525 renderer95 enter | 163528.9 | 原query→paintQuery→renderFaceInspector；parent.scroll25，舊mode中心602.5 |
| 7529 renderer return | 163545.8 | 重建新節點token5737，parent.scroll0；mode中心627.5 |
| 7533/7534 native入口／單次原量測 | 163550.3/163550.5 | 同新節點，舊helper原p=(293.75,627.5)，hit=mode |
| 7535 原native callback return | 163550.5 | 原scroll guard通過，恢復25；mode中心602.5，舊點627.5命中真ratio label |
| 7538 pointerdown | 163733.5 | trusted、(293.75,602.5)、target=mode、token5737、scroll25 |
| 7543 pointerup | 163752.3 | trusted、同座標／token／rect／scroll／target |
| 7546 click | 163752.4 | target仍mode，沒有錯點後第二次mousePressed補救 |

callback確為app.js:8758登錄、native request id1648、真native dispatcher一次、原this/window與原timestamp args、callback原文字hash相符。其前後改變由原callback執行，不是工具手寫scroll。新helper保留原精確focus predicate、共同25秒截止與12次輸入前探測，新增settle及同node/rect跨兩frame檢查都在唯一mousePressed之前。

另對fixed已錄的1004對trusted pointerdown→next pointerup作純資料掃描：無nested/orphan/unclosed pair；4對包含render，但全部stack是canvas規則線 `hit.onpointerdown→select` 的預期選取重畫，不是query重畫表單。目標native restore不在表單按下區間內。本工具未錄pointercancel，故這只描述已錄配對，不能外推未測輸入與瀏覽器原生popup。

## 產品已有的保全與功能理由

`app.js:348–400` 的 inspectorState/restoreInspectorState只保存同bid的呈現上下文：draft值／select標籤、details open、active id、兩層scroll，以及placement/reference-page/grid identity等；身份改變時不錯套舊draft。最終visibility完成後reapplyInspectorFocus，且pane中已有不同active control時不奪回焦點。`captureDirtyInputs/restoreDirtyInputs:435–462`另保邊長draft、model、revision/submission及owner，避免重畫觸發錯誤提交。

`grid-rule-lines.js:59–68,85–107` 以context/edit/focus/stamp/viewport/request/revision/fingerprint驗query所有權，回應只更新唯讀rows/messages/graph與rule-selection呈現；`:80–84` 的paintQuery才決定重畫面板。無rule的普通面不重畫引用表單。這是有功能理由的唯讀刷新，不是無條件重新載入World。

`renderFaceInspector:8563`仍整份換innerHTML；之後還會恢復draft、切advanced/source欄位、bind grid／section、再恢復最終焦點。`:8751–8763`原註解說明details toggle在下一frame前完成，同步恢復會被中間較短form截短，因此保留原rAF再恢復scroll是產品補救。seq/bid/兩層scroll guard避免舊次重畫或後續使用者捲動被蓋掉。P88既有「超高表單重畫保留點擊位置／焦點／World」及「不蓋新scroll」也保留，不能隨意刪rAF或其guard。

上述保全不是pressed DOM node identity或pointer gesture保全；本次讀到的helper也未保存input selectionStart/End。但「沒這個欄位」只是未覆蓋範圍，不能直接宣告已出現caret或點擊缺陷。

## 目前不能證什麼

native診斷把原量測安排在原callback入口前，**callback完成後才resolve measure**。所以它直接涵蓋「measure→restore→click」，沒有涵蓋「pointerdown→query/render/restore→pointerup」。此次fixed恰好也觀察到restore比pointerdown早約183ms，不能把這份成功次序當作所有人類輸入的保證。

沒有Paint/compositor frame/screencast證據，無法證明627.5的中間DOM曾畫成使用者看到的像素；單憑rAF名稱也不能補此證據。原F13自然1/0/0失敗沒有pointer原trace，不能倒填某個query／callback就是其唯一自然根因。自然紅原件、舊query診斷不成立收據均應保留。

因此本報告接受這是一項有真stale-coordinate反證的測試定位修補，但不寫成「產品對真人無影響」或「產品已確立有互動bug」。P88 source撤回0/1/0由原proof及其他獨立裁判審，本報告的獨立產品結論主要綁上述fixed原資料。

## 可選最小真輸入反例設計（未實作／未執行）

等root收齊列定gates後才決定是否需要；這不是本報告新增的正式gate。使用同F、原P88合法390表單與原本可成功建立引用線的既有有效輸入，優先選普通button `#refGuideCreate`，避免native select popup本身的點擊規則混淆。

1. 以真既有query捕捉**原有**最後source-inspect回傳物件，保同context/stamp/revision與原parsed JSON；只延後resolve，不改回應內容、不新造query、不寫scroll/style/DOM，不延長原既有診斷預算。
2. query仍held時，待原正常UI穩定，對Create量一次可見命中座標。發唯一真CDP `mousePressed`；由trusted pointerdown/mousedown記錄原node token、buttons、rect、scroll、active，確認沒有先送mouseReleased。
3. 釋放上述原query；讓原query→paintQuery→renderFaceInspector與原native scroll-restore callback照常跑。只等待觀測到匹配的真native callback終態，禁止手動invoke、另造rAF或改guard。若query因所有權變動合法失效、callback取消或未出現、反例前提不成立，分類未證／工具紅，不能改當產品紅。
4. 以原來完全相同的x/y發唯一真CDP `mouseReleased`，不重新量測來救click、不replay／dispatchEvent。保存整段原target／old node isConnected、new node token、scroll/rect、active、click與API寫入序列。
5. 重用原P88單次合法建立的既有結果predicate／World差分；若同座標pressed node被換後單次click遺失、點錯或多寫，且所有原callback/transport/owner前提成立，才是有效產品交互反例。只觀察DOM移動而既有動作仍正確，不能單憑移動標紅。

兩個相鄰控制保同合法表單、回應與一次down/up：query先完成再開始click，以及click完成後才釋放query（後者可能依原ownership正確丟棄舊回應，須原樣記錄）。兩控制用來分清互動交錯與表單本來無效；不為反例調新mm/ms閾值。若最終必須針對原mode select，再獨立列native popup範圍，不能拿button結果冒mode結果。

若此真反例確立，最小候選產品修法是只延後**唯讀query造成的inspector整份重建**：active pane pointer gesture及其原click dispatch完成前保留原node，暫存最新呈現dirty狀態，之後按原owner/stamp重新確認再重畫，保留原scroll-rAF與draft/focus守門。不改核心/公理/數值，不自動重播使用者click，不只取消scroll restore（後者會留下已截短scroll）。是否採此方向仍須反例確立與原反證，不因本靜態風險直接實作。
