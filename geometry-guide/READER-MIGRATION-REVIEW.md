# 閱讀器歷史遷移逐項評估（#82）

基線 `e5d168e5d263a43fce844f77c876cf930c8b8a86`；在記憶體中包裝其原本的
`force()` 並實際重建 canonical，以下 46 次呼叫皆未改動輸入。這是本輪獨立量測，
不是沿用 PROJECT-REVIEW 的結果。行號指該基線的 sync 腳本；20 次色碼遷移共用第 166 行。

PR92 先修 #81／#83 與重複見證事件；本後續只退出已完成的色碼遷移對現行 CSS
完整字串的強制依賴。沒有把 46 次 no-op 全刪，也沒有另造閱讀器。

「色碼相容」表示：已知 OLD 仍存在時，以原本具唯一性保護的 `force()` 遷移並登記；
現行 CSS 不再要求逐字等於歷史 NEW。`COLOR_CONTRACTS` 逐項核對目前 selector 的相關宣告，
容許宣告空白、順序及無關版面属性改動。仍拒絕 token／效果遺失、錯誤宣告、退役深色 override 回來，
及既有 `hardcoded_colors()` 找到的寫死色碼。格式已改的 OLD 不會被猜測性重寫；明示拒絕。

獨立審查修正：歷史 OLD／NEW 使用獨立的最小 stylesheet fixture，不從現行 canonical
尋找完整 NEW 字串再倒改。現行格式測試按 selector 處理當前宣告；調整字級後仍須通過整組測試。
宣告守衛只支持列出的精確 selector 的無條件普通宣告，不充當完整 CSS cascade 引擎。
它保持巢狀 at-rule 的 scope，拒絕受管 property 的條件式／style modifier 宣告及任何
`!important`；不以 print-only 定義補足螢幕契約，也不猜测優先權／條件是否會作用。
一般 scope 中的無關版面宣告仍可演化；未知巢狀 selector／不平衡結構保守拒絕。

| 次序 | 基線行 | 用途 | 決定與理由／相容範圍 |
|---|---:|---|---|
|1|899|見證圖面板腳本|保留 live SVG 接線；PR92 只刪精確已知死 img 函式與重複 listener，未知歷史改動拒絕。|
|2|902|切分頁前保留草稿|保留；依賴 flushDraft、active tab 與 docked 狀態，不能只憑 no-op 退出批註保全接線。|
|3|908|見證圖初始化|保留 marker 遷移；初始化與事件更新分工不同，#81 現在兩種成功分支均登記。|
|4|851|halfQuery 宣告|保留；960–1279px 的已採納半高 sheet 契約。|
|5|858|底部半高 sheet|保留；show／showModal 分支及正文讓位是現行行為。|
|6|867|關閉 sheet 收回 padding|保留；只在所有 dialog 已關閉才收回讓位。|
|7|842|過期批註就地動作|保留；重新綁定／跳段／復原入口尚為現行批註契約。|
|8|843|重新綁定前後對照|保留；不能恢復舊 confirm 或跳過明示確認／anchorHistory。|
|9|844|重新綁定 action 分派|保留；與上一項共用狀態及復原責任。|
|10|937|activeFacet 宣告|保留；搜尋與分類疊加的現行狀態。|
|11|940|facetMatch helper|保留；讀取資料屬性，不恢復條號白名單。|
|12|943|facet 條件疊加|保留；搜尋、分類、chip 必須合取。|
|13|947|chip 選取態|保留；選取態反映 activeFacet。|
|14|953|chip 點擊|保留；切換篩選並重新計算結果。|
|15|959|resetSearch 清 chip|保留 marker 相容；另一搜尋遷移會修改同一函式，不改成脆弱 NEW 判定。|
|16|1081|HTML 預設深色|保留；GEO-120 已拍板預設，仍接受已知舊模板。|
|17|1088|mode／theme 初值|保留；單頁長捲與預設深色不能退出。|
|18|1095|還原已存主題|保留；保持使用者選擇與系統設定的既有順序。|
|19|166|focus-visible outline|色碼相容；守各 focus selector 的 accent outline 與 offset，不綁完整 rule 拼法。|
|20|166|未存批註色|色碼相容；守 `.review-save-state.dirty` 的 note-strong。|
|21|166|過期批註色|色碼相容；守 `.stale-note` 的 note-strong；字級可正常演化。|
|22|166|有批註段落左線|色碼相容；守 `.review-block.has-comments>.review-target` 的 note 邊線。|
|23|166|段落定位外框|色碼相容；守 `.review-block.target-flash` 的 note outline。|
|24|166|inline-note 左線|色碼相容；改以 `.inline-note` 宣告核對，不綁 border-radius 與相鄰次序。|
|25|166|批註恢復橫幅|色碼相容；守 `.recovery-banner` 的 note border，不綁 padding。|
|26|166|批註錯誤色|色碼相容；守 `.review-error` 的 danger。|
|27|166|提案原文邊線|色碼相容；守 `.proposal-before` 的 proposal border。|
|28|166|歷史例圖底色|色碼相容；守 `.ex figure img` 的 figure-bg；不重跑歷史圖。|
|29|166|歷史 img 見證樣式|色碼相容；保留 img 相容樣式的 figure-bg；不恢復已退役 img handler／第二份圖。|
|30|166|圖片檢視底色|色碼相容；守 `.image-viewport` 的 figure-bg，不綁 flex／padding。|
|31|166|拒絕 badge|色碼相容；守 reject-bg 與 reject-ink。|
|32|166|拒絕預期輸出底色|色碼相容；守 `.ex.no .expect` 的 reject-bg。|
|33|166|歷史實錄 badge|色碼相容；守 transcript-bg 與 transcript-ink，不把歷史實錄當本輪驗收。|
|34|166|DSL 命中行|色碼相容；守 hit-bg 與 hit-line。|
|35|166|條文參照底線|色碼相容；守 `.copy .reference-link` 的 link-underline。|
|36|166|深色拒絕 override 刪除|色碼相容；OLD 精確出現時刪，宣告守衛拒絕該退役 selector 重現。|
|37|166|深色 DSL override 刪除|色碼相容；同上，保留集中 token 的單一色彩責任。|
|38|166|深色全文參照字色|色碼相容；守 full-ref 的 sheet-ref-ink。|
|39|1008|搜尋狀態列|保留；第 n／m 筆是現行鍵盤導航反馈，不憑 no-op 退出。|
|40|1014|resetSearch／渲染|保留 marker 相容；與 facet reset 共用函式，保留後續變換相容。|
|41|1024|navigate 保留查詢|保留；GEO-142 明示跳轉不可清查詢。|
|42|1030|方向鍵第 n 筆|保留；與 visibleResults／keyboardIndex 狀態相關。|
|43|1036|Enter 下一筆|保留；不能因已有回歸便當成死接線。|
|44|1049|Esc 先清查詢|保留；與現行 panel 關閉順序相關。|
|45|998|觸控長按|保留；段落工具觸控可達性，未以桌機 click 替代實體觸控驗收。|
|46|970|hover 預覽|保留；GEO-120 指定與固定參照欄並存，不新增第二套參照來源。|

新增測試逐项回放 20 個 OLD 相容輸入、20 個錯誤宣告／退役 selector 故障；
另一個 fixture 同時格式化全部現行 NEW 的宣告，並調整無關字級，實際 `rebuild()`／`validate()`
仍須通過且保留原 bytes。這些案例只在記憶體中處理，不改公理／白話／圖／原始批註。
26 個 JS 遷移保留完整 drift 保護，不聲稱所有互動任意格式改動都已解除限制。
審查補強另釘住已改字級的 canonical 仍能跑歷史／格式測試、print／supports／style media
不可充當普通宣告、以及錯誤 important 值先於普通 expected 值等覆蓋情境。
受管屬性的重疊 shorthand／longhand／vendor alias 及 `all` 重設保守拒絕：
background family、outline 線條、border 的寬／型／色與邏輯邊、text-decoration-color
的 shorthand。跨 rule、反向順序、print scope 與 important 均拒絕，不推算完整 cascade。
現行模板已有的 border／text-decoration 基底 shorthand，只有在同一普通 rule 內
先於正確的受管 longhand 時可接受；不綁該基底的歷史字串。其他 alias 與 `all` 無此例外。
字級、padding、border-radius、非受管邊線與非受管 selector 的正常修改另有正例，
不因歷史色码相容而重新鎖住完整 CSS rule。

## 重跑

```sh
python geometry-guide/sync_axiom_reader.py
python geometry-guide/sync_axiom_reader.py --check
python tests/test_axiom_reader.py
ulimit -s 65536
python tests/run_all.py --build
```

真瀏覽器仍以唯一 canonical HTML 驗證一次事件一次 SVG clone、空見證狀態、導覽、主題與批註保全。
實體 iOS、原生另存視窗及雲端政策阻擋的 file:// 開啟另列未驗。本文不宣稱效能加速、部署或合併。
