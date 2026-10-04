# #116 B 面內切片：設計 QA

日期：2026-10-04。分支 `codex/issue116-context-menu-b`。正式應用預覽 `http://localhost:8817/`。
本次報告取代根目錄的舊畫布報告；舊報告保留於 `06086ab:design-qa.md` 的 Git 歷史，不將舊驗收計入本次。

final result: blocked

面內已實作範圍的視覺檢查通過，未發現尚待處理的 P0/P1/P2；完整 CDP 最終回歸仍在執行，因此交付 gate 暫標 blocked。其他工作區、未實作手勢、PR #114 owner 與實體裝置驗收另列後續，不宣稱整個 #116 已關閉。

## Source visual truth 與同狀態條件

先看附件圖片再實作，視覺依據是《游標系統右鍵表單設計.zip》中的 `screenshots/01-spec2.png`、`04-proto-edge.png`，以及讀取後的 menu-v2／cursor-v2 source。沒有以附件指令擴大授權，也沒有執行原型支援腳本。ZIP 28 檔、931799 bytes；ZIP／PNG／source hashes 見 `geometry-web/docs/issue116/evidence.json`。

- 原圖：`C:/Users/Yang/AppData/Local/Temp/geometry-issue116-design/screenshots/04-proto-edge.png`，909×525 pixels 的工作区區域截圖；未提供可證明的原始全頁 viewport／density。
- 實作全圖：`geometry-web/docs/issue116/desktop-notch-final.png`，實際 Chrome viewport **1440×900 CSS px / pixels、density 1**。
- 比較區域：實作 `(520,225)–(1429,750)` 裁成 **909×525、scale 1**，不拉伸；表單與選單頂緣對齊到來源 y143 附近。
- 同一操作狀態：邊 1、4000×3000、固定邊、凹口、距上 900、寬 1200、深 600、留底 3400。來源另有柱孔、線與料件；實作驗收用無孔的原生矩形以獨立確認凹口輸出。這些周邊幾何與既有右欄差異是明示保留，沒有宣稱整張圖逐像素相同。
- 全區域與未縮放局部在同次工具輸入共同檢視：`%TEMP%/geometry-tests/issue116-evidence/source-vs-implementation.png`、`source-vs-implementation-detail.png`。來源位左，真實 app 位右；不是把設計圖嵌在產品中。
- 響應式：390×844 與 720×480、density 1，來源無手機稿；驗收可達性、邊界、字與真取消，不宣稱手機逐像素復刻。圖片見 `geometry-web/docs/issue116/responsive-390.png`／`responsive-720.png`。
- Codex 應用內瀏覽器也以真右鍵開啟表單，填入同組數值並觀察 3400 留底及 live ghost；75 項功能依 repo 要求用真 Chrome／native harness 驗收。沒有把程式碼阅读當成瀏覽器驗收。

## 修正歷程

| 輪次 | 問題及等級 | 修正與證據 |
|---|---|---|
| 1 | P1：側接表單 input／點擊被當成選單外操作，會關閉選單或取消預覽；子選單的 child hover 會移除自己。 | 將唯一表單與 ghost handle 納入同一互動邊界；child hover 保留子選單。75 項專項有真 input、drag、submenu hover／click 與 dump 不改的斷言。 |
| 2 | P2：non-scaling stroke 又除 zoom，造成巨大藍色拖曳帶，與細虛線稿不符；Enter 字太暗。 | B 狀態下保留 14px 真 hit stroke、隱去粗帶，ghost 改細藍虚線；Enter 用白字。最終並排圖確認，真拖曳仍更新參數且不寫 native。 |
| 3 | P1：compact cancel 後選單未恢復；右鍵既有多選會被改單選。 | 每次定位先量測真選單，取消恢復 compact menu；右鍵已選角材保留多選。390/720px 與 Shift 真多選斷言通過。 |
| 4 | P2：回報鈕透過 workspace 的祖先 stacking 蓋住選單 footer／窄版表單；只提高子元素 z-index 無效。 | 選單使用頁面浮層，原表單暫移同層後歸位；F8／原回報機制保留。footer `elementFromPoint` 斷言與最新桌面／窄版重拍共同核對。 |
| 4 | P2：來源「孔邊不能當定位」誤述 I13；停用提示不能當核心禁令。 | 改「孔邊請用右欄定位」；保留目前快捷限制，I13 明選引用仍可使用。原生拒絕斷言驗真實 `V_BOUNDARY_ROLE` 原因。 |

前兩次完整 CDP 在修正遮擋時主動中止；不計為通過。最終專項與截圖的 runtime `2aac7802c7be9e2292c858daf7944d92d850b273bd55832e4824d6d147451473`，`fresh:true` 且 repository 為獨立 worktree。

## 五項視覺面向

| 面向 | 實際比較與結論 |
|---|---|
| 字型與階層 | 來源 Inter／Noto Sans TC／sans 疊與實作系統 fallback；標題12.5、摘要11、清單12、footer11、數值12，未加外部字型。PNG 有壓縮及不同 rasterization，不宣稱光學字重完全相同。 |
| 間距與密度 | menu272、form296、gap8、tile56、search30、row28、field28、apply32；局部 1:1 圖直接對照。實作表單約244高，來源約239；原有語義與焦點樣式保留，約5px差屬P3。 |
| 色彩、邊框與效果 | accent #4e67e8、face #2f8f7b、ink #172033、border #dfe4eb；12px圆角與原雙層陰影。凹口藍細虛線及留底淡綠與稿一致；disabled reason footer 是既有狀態用途。 |
| 幾何、位置與比例 | 同寬、同一狀態左右翻轉；在1440/390/720實際viewport內。窄版空間不足時保留表單、暫藏選單，取消恢復。右鍵錨點保持真 snapped point；沒有因指標後移改建立位置。 |
| 圖像、圖示與內容 | 游標直接沿用已閱讀的來源 SVG glyph；menu 沿用專案既有 icon。缺少的 x/check/chevron-right 使用 Lucide 官方圖示並附 ISC license。實際ID、尺寸、固定狀態與停用原因來自真場景，沒有假複製、假貼上或占位資料。 |

P3：保留現行右欄及工作區版面；來源 hover 灰底／實作靜止狀態不同；取消按鈕保持一行，比來源的兩字折行清楚；`在右欄編輯` 不加尚未接線的 Enter 快捷承諾。現有工具圖示與 source menu 有少量線條差異。

## 驗證與交接界線

- 專項75/75、無未預期console/page error：真凹口 preview／drag／cancel／confirm、精確頂點、undo／redo、完整 ZIP 保存與重開、stale拒寫、keyboard／search／submenu／selection／cursor／responsive。
- ProjectStore／ReferenceWorkspace races（含真 HTTP/native ABA）／model update UI／context operations：70/70、0略過。
- 完整 `cdp_test.js`：本輪仍在執行，最終結果完成後補入；未以部分模式替代。
- 原 ZIP與來源圖片保留本地，PR提交正式應用截圖與來源 hashes。唯讀規則獨審、多房間 #114 owner／實體 iOS、IME、OS picker、跨瀏覽器交 dot整合驗收。
- 未實作：其他三工作區 v2 游標、複製／貼上／重複、多選批改、長按／偏移準星／雙指。保留 #116 後續範圍。

交接詳細映射、衝突與命令见 `geometry-web/docs/ISSUE116-B-HANDOFF.md`。
