# #123 C2/C4 最小CSS修復與後續真browser驗收

候選 `458779f003e1f57fdc0f4420564a0b295227843e`。補丁 `issue123-c2-c4-css.patch`，只改 `geometry-web/app.css`，尚未套入repo。SHA256 `b2ee8fe6f69487311001faa142f9d6a48d5e8558cf99898fee2706e791fd019e`；apply --check exit0，工作樹仍clean。root指定最終單writer套用，本worker只準備private patch。

## 明確既定來源

GitHub #123 的現有私有讀取原件 `/workspace/closure-evidence/inventory/issue-123.json`：S1要求「accent/文字/框線/柱樑/網格顏色」共用tokens、「SVG使用computed styles」；S4要求「常駐空槽入口」。條文另明定保留DOM ID、C核心/公理/交易語義不變；此補丁沒有改markup、ID、handler或任何交易。

目前app.css:23已有 `--beam:#486987`、`--beam-soft:#edf3f8`；:2043清單icon已使用此color/background，而:887平面正式樑仍固定另一套藍。補丁讓正式樑fill/stroke接同一對現有token。只收斂C2/X7的樑切片，不宣稱所有柱/格網/預覽都完成。

目前app.js:3530已在每個空槽button內提供「未放置」及「＋放置」兩個span，aria-label為「放置{槽名}」，data-slot-preset與現有click handler接真放置入口。app.css:1561–1563只在hover/focus-visible顯示action。补丁令既有action常顯、idle隱藏；mobile原本已有常顯override，沒有另建入口。這是明定S4，無須創造設計規則或取得原ZIP才開始。

## 所有權與不衝突證據

- root最新指示授此private單檔patch，repo保持freeze，root負責同批接#173後套用；本worker不占用/改app.js、space-workspace.js或canonical browser檔。
- 最新#173交付 `ce74dc949168b597e33ec00110ce57f26ae51ff8` 更動app.js、edge_draft_redraw_test.js與證據，不含app.css，原git show/stat在latest-173-owner-delivery.json。
- app.css在9a→458逐bytes相同，hash `7a91aa9eb8b30599c1263546e37c71b6051ad12d93341101181a76a3448b4569`，工作樹無dirty。#175 owner表現有活躍產品責任限app.js/space-workspace.js及列名測試；沒有新的app.css writer交接。
- 這能證明本補丁不覆寫目前候選或新#173交付；不能證明看不到的本機未提交CSS不存在。舊#123交接曾將app.css歸共享writer，最終套用前由root維持一檔一writer即可，不把所有UI泛稱被#173阻塞。

## 尚未執行的browser最小方案

兩寬1400×1000、390×844；使用新整合候選、fresh/runtime/bridge綁定與唯一slot。synthetic fixture可沿既有P12/P19命令透過apiRequest建立（明示API setup），等待每命令ok及render完成。進空間從 `.ocard[data-kind="space"][data-id="1"]` 真dblclick；手機以 `#workspaceToggleLeft`/`#workspaceToggleRight` 真點擊打開所需清單/檢視器。讀DOM作oracle可evaluate，操作不得DOM.click、force、移除遮罩或sleep當完成。

C2：沿cdp_test.js P12現有六面4000×3000×2500房間、column1及beam1合法fixture（source :2226–2246）。只有一支樑避免錯配；beam1清單文字與native id先核對。讀 `#spacePlanSvg .space-plan-beam` 的computed stroke/fill，對 `#spaceRcList .type-icon.beam` 的computed color/backgroundColor：應分別全等，現token預期 rgb(72,105,135)／rgb(237,243,248)。截圖核樑仍可辨識，普通點擊其清單/已用入口、進出後保持同色；完整native dump/refs不得被CSS或導航改動。基線可先用同oracle記錄不一致，再於新候選補驗；不要改oracle配結果。

C4：沿P19既有兩面開放space1＋未放置boundary3 fixture（:2877–2888），有4個空槽；不需新增幾何或採納行為。進space後游標離开檢視器且焦點不在slot，逐個記 `.slot-empty`、`.slot-idle`、`.slot-action` 的computed display、rect及aria-label，要求可見「＋放置」、非hover/focus也可發現、無文字交疊。390先正常開rightdrawer，這是既有responsive入口。

分別正常click與真Tab鍵輪巡（有界上限並記焦點序列）到一個具名槽，按Enter；等待focus轉到真正未放置面3、#placeU/#placeV等於該槽既有PLACE_PRESETS，status命名同一槽。沒有提交placement，前後dump/refs全等；返回原space再測另一路。不得用程式focus冒稱Tab路徑。既有handler選清單首個游離面，不改其選取政策。

本草擬尚無browser收據；不得將apply-check或來源符合寫成C2/C4已驗。原ZIP只阻原稿像素/文字比較，這兩個已定案交互和computed-style條件可正常執行。
