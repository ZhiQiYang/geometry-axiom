# R03 平釘天花第一片：DOM 與驗收契約草案

本文件說明本次產品碼與待雲端 Claude 實跑的瀏覽器驗收碼。它不是瀏覽器通過收據，不表示實體觸控、輸入法或輔助科技已驗收。公理來源是 `公理層.md` 的 D／I／R⟨FT1⟩，本文件不另定條文。

## 唯一面內入口

在物件畫布雙擊封閉面，開啟「屬性 → 面設定 → 完成面／骨架…」。既有 `data-panel-fill-open` 保留，在原工作區內以 `data-face-product-mode` 切換「完成面與鋪排」或「平釘天花骨架（矩形第一片）」。沒有新增永久頂層工具、頁籤或第二套面入口。

骨架第一片明示只接受矩形、無孔柱、RC 邊界，以及既有 oracle 與本次規則共同相容的排法。原 3700 mm 需要退縫的案例回報 `POLICY_RULE_CONFLICT`，禁止確認；不自動改角、換方向、移縫或搜尋其他版本。

## 操作與 DOM

| 節點／動作 | 可見用途與契約 |
| --- | --- |
| `[data-ft-workspace="boundaryId"]` | 目前面的唯一骨架工作區；不代表 native object owner |
| `[data-face-product-mode]` | 既有面內工作的共用切換器；候選或未保存輸入期間停用 |
| `.ft-scope` | 持續可見的第一片範圍、裁切／主支／副支規則與 3700 mm 拒絕案例 |
| `[data-ft-field="recipe"]` | 明選專案配方；可新增、複製、更名保存或整張刪除 |
| `[data-ft-action="save"]` | 只保存配方意圖，單筆 local history；不呼叫 native 生成 |
| `defaults.panelWidth / panelLength / gap / timberWidth / timberDepth / maxSecondarySpacing` | 六個明設整數預設；length 是欄位語意，尺寸大小與正方形不會換軸 |
| `corner / lengthAlong` | 明選起鋪角與板長欄位軸向；不依矩形長邊推測。預覽圖以 u 向右、v 向下呈現：`min-min`＝預覽圖左上、`max-min`＝預覽圖右上、`min-max`＝預覽圖左下、`max-max`＝預覽圖右下；不代表世界上下方向 |
| `on / panel / threshold / materials` | 每次生成明選目前放置框架、固定板材版本、X 的 dimension 欄位與 RC／literal 語意；初始全部空白／未勾選 |
| `[data-ft-action="materials"]` | 前往既有工程規格的材料頁；回原面保留配方輸入，重新讀取且重新明選活來源 |
| `[data-ft-action="threshold"]` | 由既有 ParameterUI 提議 8 mm X；來源必須獨立預覽確認，不藏第二個 X 常數 |
| `[data-ft-action="preview"]` | 只準備完整原生候選；逐值核對 source、revision、context、固定 policy、definition chain 與 support 完整性 |
| `[data-ft-member] / [data-ft-member-row]` | 圖與表逐項呈現原生傳回的矩形位置、角色、長度與 A/B；host 不重算木工幾何 |
| `[data-ft-action="confirm"]` | 只有本次有效候選可用；送單一 requestId，單筆 native history，正式物件不受配方擁有 |
| `[data-ft-action="cancel"]` | 只取消本次 token＋owner；取消前後 World、附件、revision 與 history 不變 |
| `[data-ft-status]` | `idle / reading / ready / previewing / confirmable / confirming / cancelling / committed / rejected / stale / unknown`；未產生或被拒絕的候選不顯示成功 |

確認／取消回覆未明時禁止重送；只向既有 receipt 管線查原 requestId。未知預覽回執恢復後取消其精確 owner，不直接變成可確認候選。專案、歷史、面來源或服務世代變更會使候選失效。

## 保存語意

`framing-template-recipes/1` 是正式專案附件能力，不是 World capability。配方只有名稱、固定模板版本與 policy 指紋、字面預設、排法偏好、來源槽與非權威提示；不保存產物清單、長度快取、搜尋軌跡、候選 token 或 native 身分宣稱。

已知版本的指紋不符、未知附件 schema 或缺少／未知 capability 都整案拒絕。可讀 schema 下未知 generator 版本原樣保存、唯讀顯示，禁止生成或改成可用版本；使用者仍可明確刪除整張配方，既有普通物件不動。

保存配方與確認生成是兩個可獨立復原的交易。取消生成保留先前正式保存的配方與獨立建立的材料／X。冷開只讀保存的配方和普通 World 定義，不重新搜尋、不更新模板、不自動套用來源提示。

## 回歸與剩餘驗收

Node suite 實際執行出貨 Session、ReferenceWorkspace、ContextHistory 與 ZIP 解析；transport fixture 明確只證明 host 協定，不冒充 native 幾何或瀏覽器證據。兩個具名撤回為 `R03_HOST_CANCEL_WRITES`、`R03_HOST_COLD_OPEN_SEARCH`，各要求正常／撤回／恢復為 0／1／0，且中間必須命中指定 AssertionError。

`framing_template_workflow_test.js` 定義 P205 的 25 個固定具名斷言。它從真面入口操作，以 F4 走道 `min-min / lengthAlong=v` 的 25 支對既有 oracle 逐值比較；包含取消零寫入、確認單筆歷史、復原重做、390px 排版、Enter 不提交、3700 mm 衝突、真 `.gcanvas` 下載與獨立的新 native service／session、新 Chrome 程序／profile 開檔。未知 capability、錯 policy、未知 generator 的檔案變體各走真開檔入口。

25 是測試契約數，不是已通過的瀏覽器數。P205 重用既有 `cdp_bay_repeat_io.js` 啟動可核對 pid、session、版本及 binary sidecar 的獨立新 native service 與新 Chrome 程序／profile，再由真開檔入口載入原下載包。它要求完整 World 與配方原樣一致、沒有生成請求，且新程序的 generatorInvocations 為 0；這項聯合冷開尚待雲端實跑。

在雲端已啟動既有隔離服務與 Chrome 環境後執行：

```sh
GEOMETRY_FRAMING_TEMPLATE_ONLY=1 node geometry-web/cdp_test.js
node geometry-web/generate_framing_template_golden.js --run
node --test tests/test_canvas_shards.js tests/test_boundary_pair_browser_scope.js tests/test_framing_template_browser_scope.js
```

第二條會跑既有完整 CDP 模式，要求零失敗才產生 golden，且只准新增實際觀察到的 P205；任一舊段數值不同或未完成會恢復原 golden bytes。不得把部分模式計數手貼為正式 golden。之後仍須依既有 CI 跑兩個完整分片及其彙總；時限、原有段落、交接狀態與所有舊 golden 值維持不變。

`tests/mutants_results.json`、product architecture 收據／掃描／文件與正典閱讀器等衍生物由 CI 或 Claude 依正式產生器重產，本補丁不手寫。
