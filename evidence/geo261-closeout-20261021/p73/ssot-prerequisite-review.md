# P73 空空間失敗：規格、前置與排程的獨立只讀審查

審查者：`/root/p52_review`。受測分支 `codex/geo261-closeout-20261021`，來源 `366ef501b78105d1f7242dc1f4f4752cac9086b5`。本審查只讀取SSOT、產品／測試原碼、原完整canvas紀錄與另一代理產出的探針證據；沒有修改repo、啟動瀏覽器或跑編譯／native。另存的Git blob比較為 `ssot-prerequisite-source-comparison.json`。

結論：**零成員且沒有實體幾何的空間不應出現有限房間範圍，期望有SSOT支持。已證實的產品缺陷是空態仍產生格線標註與可見的零範圍metrics；不能把隱藏SVG內的裝飾rect說成畫面真的出現假房間。** 原P73條件不宜直接放寬或改成更久sleep。最小方向是修正空態的標註守門與metrics清理，保留原69題與golden。

## 規格與原斷言

- `公理層.md:130–142` 的D5：空集合不產生有限範圍或封閉證明；零成員空間是合法空容器，無界、恆非封閉。`geometry-guide/PRODUCT-VISION.md`明說願景不是新規格或擴大授權，本判斷沒有據願景新增行為。
- `geometry-web/docs/DOM-CONTRACT.md:151`：零成員空間顯示空容器說明與加入成員入口，不渲染有尺寸房間矩形。
- `geometry-web/uiux_review_test.js:213–221`：宣告`space 990`，等待renderObjects與enterFocus，明確點plan分頁。218先核對空態可見與dump不變，219才核對成員文字`0`、SVG沒有polygon/rect/path、空態節點存在、文字含加入／成員。

219的selector包括所有裝飾節點，語義比「沒有可見房間邊界」更強。它可以抓到空態renderer重新生成不該存在的標註，但僅有此條false不能單獨證明畫面出現有面積房間。修正應針對已證實的錯誤狀態，不以改selector把錯誤藏掉。

零成員也不能被泛化成「永遠不能有任何平面圖」：D11的柱／樑不是成員，若其他合法流程明示配置了實體，其足跡仍可顯示。這次990的成員、所屬columns、beams都為空，候選應使用renderer的`noGeometry`與hidden／viewBox狀態，不能只用`members.length===0`一律封鎖。

## 前置是否被P72B污染

`uiux_review_test.js:90`前後自行關dialog、`resetSceneFocus()`、`setView3(false)`、`closePanels()`、native reset並建立新fixture。`app.js:1846`的resetSceneFocus遞增navigationSequence、清除焦點／面快取並隱藏工作區。P73後續另正式開啟工程範例，沒有沿用P72B的grid-system世界。

`app.js:2716–2759`的enterFocus會等待openSpaceWorkspace；`3294–3318`進空間時重新renderObjects並等待renderSpaceWorkspace；`3320–3353`同步成員數，等待投影後才renderSpacePlan。原完整失敗log中，plan點擊已發生，218「空態可見且保留世界」也通過。因此沒有證據把這次失敗歸為未await世界讀取或前一模組原生資料殘留。

FATAL_UI仍顯示「成員面清單」是`app.js:3318`的固定status文字；分頁handler`3380–3387`只改active／pane與工具提示，不改該status，不能據此宣稱沒有切plan。2026-09-28紀錄曾有前序留下分頁的測試假設，但現行217已明確點plan，本輪218也已通過，不能直接套用舊原因。

另一代理在原18839服務唯讀擷取的`original-world-objects.json`確認空間990為`members:[]`、`closed:false`，沒有屬於990的columns／beams；`original-world-capture.json`保存擷取時間與命令。這支持原生fixture正確，但沒有補回原失敗瞬間的四個DOM子條件值。

## 已核對的ResizeObserver路徑

`app.js:3482–3529`的renderSpacePlan先清空SVG；noGeometry時顯示empty、設SVG hidden attribute、移除viewBox後return。`3637–3650`的syncSpacePlanAnnotations卻只檢查`svg.hidden`，然後依`viewBox.baseVal`建立defs/path與格線rect，並寫SVG外的`#spacePlanMetrics`。`10656–10658`建立metrics節點及ResizeObserver；這個observer可以在前述清空／隱藏之後再執行。

CSS `app.css:71`有全域`[hidden]{display:none!important}`，所以hiddenSVG仍不會被`883`的display:block顯示出來；然而SVG外的metrics沒有跟著隱藏。

我已直接讀取另一代理的`minimal-original.log`與receipt，確認自然enterFocus完成時及兩個rAF之後，尚未手動呼叫sync的快照都記錄：

- memberCount為`0`、空態存在且可見、加入成員文字正確，columns／beams均空。
- `svg.hidden`型別為undefined，但hidden attribute為true、computed display為none。
- viewBox attribute不存在，getScreenCTM仍返回identity，viewBox.baseVal為0範圍。
- SVG已被加回defs、格線path與0×0 rect，原合取false。
- SVG外metrics實際可見，內容為「x 0…0 · y 0…0 mm · 格距 10 mm」。

因此並非只有主動手動呼叫才能誘發；自然observer即可破壞空態DOM，手動sync階段只是另行確認該原函式會維持錯誤狀態。探針由`/root/p52_candidate_review`執行，我未自行跑browser。minimal模式是DOM機制診斷，沒有69個斷言，不能拿其exit0當P73完整通過。

同一原來源獨立完整P73執行`full-original.log`通過69/69、0例外、exit0。這表示原完整canvas的失敗具有排程／版面相關性，不是每個新context都必然失敗；不能用這次單跑成功抹去原1689通過／1失敗的完整canvas紀錄。

## 候選範圍的審查意見

另一代理提出的兩處修正方向可接受：

1. 在renderSpacePlan的noGeometry狀態隱藏metrics並清空文字；回到有實體幾何時恢復顯示。
2. syncSpacePlanAnnotations以`hasAttribute('hidden')`檢查SVG。建議同一守門一併拒絕缺少viewBox：初始SVG的祖先可能隱藏，但自身尚無hidden，CTM仍可能identity；沒有renderer建立的有限viewBox時不應生成0範圍標註。matrix讀取放在這兩個守門之後即可，不需擴張到任意祖先、任意非同步或新幾何規則。

正常非空分支一定先設定含正pad的viewBox，再呼叫sync，因此此守門保留正常成員與RC-only足跡。必要控制應包括非空→空→非空，確認格線／metrics正常恢復、空態確實清除、World不因標註同步改變；完整原69題與精確撤回負控制仍須由執行者完成。不能只把原predicate改成true或移除polygon/rect/path條件。

## 來源比較與未驗界線

輕量Python讀Git blob比較，結束碼0；main `adbaebf9c73ea6801d7b4d5214e4b846b132923b`與R2的`uiux_review_test.js`整檔、`app.css`整檔、空間開啟／渲染區塊、renderSpacePlan／syncSpacePlanAnnotations區塊皆逐bytes相同。`app.js`其他部分有GEO-261相關委派差異，但本次空態與observer程式不是R2新加入。

我也只讀審查`p73_probe.cjs`初版：full分支直接require原uiux_review_test.js並檢查69總數與P73地板；minimal自然觀測、兩rAF與明示手動sync分段，沒有用控制結果冒充原斷言。本篇撰寫時候選與正式修正後完整canvas尚未由我驗到，不能宣稱修正已收尾。

最不確定的是原完整canvas失敗瞬間的DOM子條件與逐次observer排程沒有直接保存；目前的相同來源自然最小重現已證實一條會產生同樣predicate false的產品路徑，並確認有實際可見的錯誤metrics，但不能據此捏造原次每個callback的時間線。
