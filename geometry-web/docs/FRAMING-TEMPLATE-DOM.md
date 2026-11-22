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

## 第二片：政策 A 固定治具的矩形範圍

第一片 `flat-ceiling/1` 的政策指紋、預設建立行為、read/1 請求和 P205 的 25 個斷言保留。第二片新增不可變 `flat-ceiling/2`，政策指紋為 `3641dec4060cfcf062e2f1d55f341ecb5ae5023da4a4d8a3aba2c3c4110b6d58`；沿用已核定 oracle 的固定 M 治具與末兩步重疊處理，但仍限矩形、無孔、World 無柱樑、水平 +N、RC 邊界、無 FT02 退縫與 R-butt 主支移位。所有候選仍須完整原生合法性與逐側承接；不保證每個矩形皆可生成。

沒有新增頂層入口或常駐說明卡。「面內工作」原 select 增加 `value="framing-fixed"` 的「平釘天花骨架（政策 A 固定治具）」選項，取代同位置的第一片範圍說明；`value="framing"` 仍明選第一片。副支欄位在 v2 顯示「固定治具步距 M（mm）」，保存欄位名稱仍為 `maxSecondarySpacing`，不猜測或換算另一份預設。原值 367 保留。

切換模式會重新讀取所選版本並清空本次來源選取；已有同版本配方可明選，沒有就顯示新配方草稿。直接選另一版本的已保存配方，也會先重新讀取該精確版本，再要求明選來源。這兩個動作均是明示選擇，不把 v1 配方改為 v2。未知 generator 版本仍原樣唯讀；不可複製成可用版本來無聲移轉。

### 版本、來源與候選協定

| 契約 | 第一片 | 第二片 |
| --- | --- | --- |
| 來源請求 | `framing-template-read/1`，只有 schema、boundaryId | `framing-template-read/2`，另必填精確 template 三欄：id、version、policyFingerprint |
| 來源回覆 | `framing-template-read-result/1`、`rectangle-common-policy` | `framing-template-read-result/2`、`rectangle-fixed-jig-no-retreat` |
| 生成請求 | `framing-template-generate/1`，固定 v1 | 同一協定，明選固定 v2；schema 不代替版本選取 |
| 候選回覆 | 原 `framing-template-preview/1` 不變 | 同一協定，另含精確 `template` 與候選封存後的 `definitionFingerprint` |
| 確認 | 本次 token ＋ ownerKey | 同一交易，不重新搜尋或重新生成；確認後定義指紋須等於預覽封存候選 |
| 保存 | `framing-template-recipes/1` | 同一附件 schema，保存 v2 版本與指紋；不新增任何結果、token、搜索或正式物件擁有權欄位 |

Host 遇版本／政策不符的 read 回覆直接拒絕；預覽版本不符、缺少候選指紋或缺少原有合法性證據時取消精確 token/owner，不能顯示可確認候選。舊配方和目前來源讀取版本不同時，以 `FT_VERSION_SOURCE` 拒絕生成。未知服務回執仍沿原紀律處理，不重送確認。

### T→P、撤回與瀏覽器交接

`tests/test_framing_template_session.js` 保留原 12 個案例，新增 10 個政策 A 案例，正常計數為 22；原 `test_framing_recipe_project_store.js` 的 9 個案例不變。新案例驗兩版本固定指紋、精確來源讀取、預覽版本守門、拒絕零寫入、確認同 token 不重搜、真 ZIP 保存與冷還原。具名撤回 `R03A_HOST_COLD_OPEN_SEARCH` 在 v2 真 ZIP 冷還原路徑插入生成請求，必須由 `R03A_HOST_COLD_OPEN_NO_SEARCH` 斷言殺死，並保留原兩個 host 撤回。這是 Node host 證據，不是瀏覽器或原生幾何證據。

新 `framing_template_jig_workflow_test.js` 為 P2052，共 28 個具名斷言；原 P205 不增加或減少斷言。主正例是 F4 走道、板長沿 u、預覽圖左上，28 支逐支對照原 frozen oracle，另比對 seams 與固定治具 marks。它實際走原面入口、保存 v1／v2 兩份意圖、預覽／取消零寫入、單筆精確候選確認、復原／重做、390 px 與 1400 px、FT02 拒絕零寫入、真 `.gcanvas` 下載、另一 native service/session 與新 Chrome process/profile 冷開。冷開要求原 World 與兩版本配方逐值一致、沒有 framing endpoint 請求，且新程序 `generatorInvocations=0`。錯 v2 指紋檔案整案拒絕，未知版本原樣唯讀。

瀏覽器程式尚須雲端 Claude 實跑。依既有隔離服務、來源與 binary sidecar 新鮮度紀律準備後：

```sh
GEOMETRY_FRAMING_JIG_ONLY=1 node geometry-web/cdp_test.js
node geometry-web/generate_framing_jig_golden.js --run
```

第一條只是 P2052 定位；第二條必須完整 CDP、零失敗、舊段計數不變，才接受原產生器實際觀察到的 P2052。28 是待驗收契約數，不是實跑收據。`GEOMETRY_FRAMING_JIG_ARTIFACT_DIR` 可指定新下載檔與獨立冷開原件的保存目錄；不要指到既有證據目錄。完整兩片 canvas 與 coverage 仍須正式 CI，原時限不變。

### L4 一般 App 操作路徑

用一般 App「建立物件」或既有畫房間入口建立 1680 × 3880 mm 的封閉矩形面與水平向上框架。從工程規格材料頁明示發布 915 × 1830、厚 6 mm 的板材；由既有參數入口明示建立 X=8 mm dimension 欄位。這些準備也要留 UI 操作原件，不能用 P2052 的 API 夾具冒充一般入口。

雙擊封閉面 → 屬性 → 面設定 → 完成面／骨架 → 面內工作選「政策 A 固定治具」→ 保存新配方（起鋪預覽圖左上、板長沿 u、M=367）→ 明選框架、板材版本、X 與 RC／literal → 預覽 28 支 → 取消並核對 World、附件、修訂、歷史與 id 高水位不變 → 再明選來源預覽 → 確認一次 → 復原／重做 → 另存 `.gcanvas` → 新 native 程序與新瀏覽器冷開。另走 3700 × 2000 退縫拒絕案例與第一片 v1 配方保留。L4 只據實際走通且留原件的範圍登錄；原生／Node／撰寫完成的瀏覽器碼不提升到 L4，雲端操作也不等於使用者驗收 L5。
