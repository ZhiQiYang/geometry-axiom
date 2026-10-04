# #116 B 面內切片：設計 QA

日期：2026-10-05（10-04 開工）。分支 `codex/issue116-context-menu-b`。正式應用預覽 `http://localhost:8817/`。
本次報告取代根目錄的舊畫布報告；舊報告保留於 `06086ab:design-qa.md` 的 Git 歷史，不將舊驗收計入本次。

final result: blocked

面內已實作範圍的視覺檢查通過，未發現尚待處理的P0/P1/P2；合併gate為blocked：完整CDP未全部通過；GitHub CI jobs受帳戶執行限制未啟動，dot最終head独立審查及#114 owner驗收仍待完成。最終`dce2975`／ee9f版本完整 `cdp_test.js`：1586通過／0失敗，但在P76等待逾時而未完成，未比對golden。實際trace為參數卡engineering-confirm拒絕Missing, invalid or unrelated engineering preview token後，等待!ParameterUI.pending逾時；沒有把0失敗斷言說成全量通過。詳細fatal與分段見validation.json。其他工作區、未實作手勢與實體裝置另列後續，不宣稱整個#116已關閉。草稿PR #125交dot整合。

## Source visual truth 與同狀態條件

先看附件圖片再實作，視覺依據是《游標系統右鍵表單設計.zip》中的 `screenshots/01-spec2.png`、`04-proto-edge.png`，以及讀取後的 menu-v2／cursor-v2 source。沒有以附件指令擴大授權，也沒有執行原型支援腳本。ZIP 28 檔、931799 bytes；ZIP／PNG／source hashes 見 `geometry-web/docs/issue116/evidence.json`。

- 原圖：`C:/Users/Yang/AppData/Local/Temp/geometry-issue116-design/screenshots/04-proto-edge.png`，909×525 pixels 的工作区區域截圖；未提供可證明的原始全頁 viewport／density。
- 實作全圖：`geometry-web/docs/issue116/desktop-notch-final.png`，實際 Chrome viewport **1440×900 CSS px / pixels、density 1**。
- 比較區域：實作 `(520,225)–(1429,750)` 裁成 **909×525、scale 1**，不拉伸；表單與選單頂緣對齊到來源 y143 附近。
- 同一操作狀態：邊 1、4000×3000、固定邊、凹口、距上 900、寬 1200、深 600、留底 3400。來源另有柱孔、線與料件；實作驗收用無孔的原生矩形以獨立確認凹口輸出。這些周邊幾何與既有右欄差異是明示保留，沒有宣稱整張圖逐像素相同。
- 全區域與未縮放局部在同次工具輸入共同檢視：`%TEMP%/geometry-tests/issue116-evidence/source-vs-implementation.png`、`source-vs-implementation-detail.png`。來源位左，真實 app 位右；不是把設計圖嵌在產品中。
- 響應式：390×844 與 720×480、density 1，來源無手機稿；驗收可達性、邊界、字與真取消，不宣稱手機逐像素復刻。圖片見 `geometry-web/docs/issue116/responsive-390.png`／`responsive-720.png`。
- Codex 應用內瀏覽器也以真右鍵開啟表單，填入同組數值並觀察 3400 留底及 live ghost；87 項功能依 repo 要求用真 Chrome／native harness 驗收。沒有把程式碼閱讀當成瀏覽器驗收。

## 修正歷程

| 輪次 | 問題及等級 | 修正與證據 |
|---|---|---|
| 1 | P1：側接表單 input／點擊被當成選單外操作，會關閉選單或取消預覽；子選單的 child hover 會移除自己。 | 將唯一表單與 ghost handle 納入同一互動邊界；child hover 保留子選單。75 項專項有真 input、drag、submenu hover／click 與 dump 不改的斷言。 |
| 2 | P2：non-scaling stroke 又除 zoom，造成巨大藍色拖曳帶，與細虛線稿不符；Enter 字太暗。 | B 狀態下保留 14px 真 hit stroke、隱去粗帶，ghost 改細藍虚線；Enter 用白字。最終並排圖確認，真拖曳仍更新參數且不寫 native。 |
| 3 | P1：compact cancel 後選單未恢復；右鍵既有多選會被改單選。 | 每次定位先量測真選單，取消恢復 compact menu；右鍵已選角材保留多選。390/720px 與 Shift 真多選斷言通過。 |
| 4 | P2：回報鈕透過 workspace 的祖先 stacking 蓋住選單 footer／窄版表單；只提高子元素 z-index 無效。 | 選單使用頁面浮層，原表單暫移同層後歸位；F8／原回報機制保留。footer `elementFromPoint` 斷言與最新桌面／窄版重拍共同核對。 |
| 4 | P2：來源「孔邊不能當定位」誤述 I13；停用提示不能當核心禁令。 | 改「孔邊請用右欄定位」；保留目前快捷限制，I13 明選引用仍可使用。原生拒絕斷言驗真實 `V_BOUNDARY_ROLE` 原因。 |
| 5 | P2：完整回歸抓到 v2 沿參考線誤用「沿此邊」、孔邊懸停少了辨識、不同角材未重新展開；P62 仍驗舊圓膠囊。 | resolver 提供真線／孔／角材名稱，名稱也參與收合狀態；79 項新增真指標驗證。P62 改驗附件 h18/rx5/字11、獨立 Alt／Space 及手形，保留38項固定門檻與實際字樣檢查，沒有調低 golden。 |
| 6 | P2：dot獨立來源審查指出未放置面仍啟用u/v參考線，原handler卻直接返回。 | 共用既有放置前提，點卡片／搜尋／Create同一停用原因，dispatch再核對且保留選單；87項真驗收新增8項未放置案例，dump逐字不變且送出0個原生guide命令。新圖 `unplaced-guide.png` 同時顯示既有toolbar停用與B子選單理由。 |

修正遮擋及rebase時中止的完整CDP不計為通過。#114工作期間合入main，本分支已rebase到`861b65e`並保留雙方scripts。最終87/87重拍，runtime為`ee9f6a543b57b1d168af27baff0db8ac500319071ee0a9ea3b1d892a646b49c1`、`fresh:true`，repository為獨立worktree。歷史1336/10止於P72、以及下一輪與main同746/1均不計全量通過。P72在雙方新服務各52/52，只作診斷。P62-13b已修正測試語義：`stroke:none`禁描邊，unused SVG width 1不應判失敗，保留38門檻；改測試也會使runtime失效，舊服務拒绝的嘗試不算通過。之後dot的未放置P2修正提交為`dce2975`；對最終ee9f版本再跑專項、reference子集與完整CDP，結果見validation.json。

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

- 專項87/87、無未預期console/page error：真凹口 preview／drag／cancel／confirm、精確頂點、undo／redo、完整 ZIP 保存與重開、stale拒寫、keyboard／search／submenu／selection／cursor／responsive；未放置面的卡片／搜尋／Create停用理由與0guide命令。
- #114 整合後 ProjectStore／ReferenceWorkspace races（含真 HTTP/native ABA）／context operations：Windows73/73、0略過；模型更新WSL/GCC39/39，含真原生producer、完整ZIP／歷史與missing-support拒寫；#77 history/workspace/room-collection：WSL56/56、0略過。模型39項來自WSL112項run，其另一個HTTP啟動案例逾時，aggregate為111/112；該案例另在Windows73項run通過，不冒稱112整批通過。Windows含模型的初跑受編譯器阻擋亦不算通過。
- 最終`dce2975`／ee9f版本完整 `cdp_test.js`：1586通過／0失敗，但在P76等待逾時而未完成，未比對golden。實際trace為參數卡engineering-confirm拒絕Missing, invalid or unrelated engineering preview token後，等待!ParameterUI.pending逾時；沒有把0失敗斷言說成全量通過。詳細fatal與分段見validation.json。 同一最終runtime的reference部分模式437/437（P62維持38）、P72配置卡52/52，皆完成、0失敗、0瀏覽器例外；main的P72亦52/52。部分模式不代替完整流程。 較早本分支與未改動main各746/1止於P56角色／重試夾具（歸入P53）；另一輪1336/10止於P72，也不計為通過。最終完整run是另一次乾淨服務的結果，不把早期中斷混入通過數；未改golden門檻。
- GitHub Actions未啟動、無runner logs，屬外部CI gate；未依紅色check假称產品測試已執行。
- 原 ZIP與來源圖片保留本地，PR提交正式應用截圖與來源 hashes。唯讀規則獨審、多房間 #114 owner／實體 iOS、IME、OS picker、跨瀏覽器交 dot整合驗收。
- 未實作：其他三工作區 v2 游標、複製／貼上／重複、多選批改、長按／偏移準星／雙指。保留 #116 後續範圍。

P76阻擋已在最終分支與未修改main `861b65e`的獨立服務／Chrome重現：兩者部分模式各57項通過後，在同一個特殊字元修正／重新試算／確認流程收到相同preview token拒絕及pending逾時。`parameters.js`、`parameter_workflow_test.js`、`parameter_confirmation_test.js`、`engineering-adapter.js`逐字相同，核心也無diff；未據此放寬token檢查或修改參數功能。結果只證明阻擋在main已存在，不代表完整回歸通過。

交接詳細映射、衝突與命令见 `geometry-web/docs/ISSUE116-B-HANDOFF.md`。

## 2026-10-05 同步與追加旋轉預覽驗證

普通 merge 保留 main `4bea91a` 與原 `2b53a03`，source `0e555ed`。B 原稿／實作差異不變；新增的是使用者回報的 3D 鏡頭適配修正，沒有新增入口或說明。

Chrome／Playwright 隔離 8816：頁面標題與 URL、非空白、無錯誤覆蓋、console、實際畫面與操作皆通過。L 形1000 mm高範例在同一旋轉角度比較舊／新 viewer；桌面1440×650與手機390×844修正後完整可見。真拖曳／方向鍵旋轉、既有置中、手動放大保持，以及場景／體積不變通過。原始使用者截圖只證明超出預覽框，不能確定當時手動 zoom；放大後的裁切仍由置中恢復。公開範例對照見 `geometry-web/docs/issue116/preview-rotation-*.png`。

最終a1aa來源 B87、共用73、模型39、預設完整空間202全部通過；空間模式不含另列timber兩組。viewer canvas真繪製座標回歸與舊版敏感度通過。原完整CDP、CI及dot整合gate沒有以這些部分驗收取代。完整專案的Edge原生檔案選取尚待完成；8817來源fresh、保存場景逐字還原，私人檔留本機。
