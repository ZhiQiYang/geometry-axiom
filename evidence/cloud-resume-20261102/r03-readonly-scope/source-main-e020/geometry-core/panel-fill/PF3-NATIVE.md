# PF-3 有效板縫與承接比對

任務 22 沿用 #226，依 P-098 一般 merge PF-H #227 的
`4be9ff3453202984433c9256dff9dd60d5c8437a`，未改寫歷史。
最後核對再一般 merge #227 最新 `303fec02257d21cf719287045a718665c3283006`；
該提交只增加任務 21 證據，不改產品／測試。原受測 SHA 與失敗收據不變。
行為基準是公理層 D43／D44、R42／R43；P-103／P-116 釐清原始演算法
oracle 與合法 D7 場景的分工。研究 R17／R15 不是規格。

## 計算與輸出

`geometry-core/panel_fill_support.inc` 直接消費 PF-2 `pf_build` 的
`PfLayout`（板分片、孔環、signed 縫線及交丁 band），不另算排板或縫位。
沿每條縫收集板分片及真足跡頂點，使用雙倍整數內點取截面；不使用 epsilon，
不把切點本身拿來判定。兩側板邊各自從整數縫中心扣除／加上相應半縫寬，
故 3 mm 縫的兩板邊不會被錯放到中心線上。

只有兩側均有相鄰板分片的區間列入 `effectiveSeams`。輪廓、孔、障礙造成的
單側區列入 `nonSeams`，`nonSeamReason=outer-edge-not-two-panels`，不產生
承接結論；兩側均無板的區間不列。各縫保留 fillId／axis／signed k／band
及完成面框架下的 `range`、兩側板邊 `edges`。不把衍生宿主的可見格線當有效板縫。

承接集合只取來源試排真 D4 宿主上的已放 D7 角材；透過既有
`timber_a0_footprint_uv` 讀足跡，再以 `(u,v_d)→(u,s·v_d)` 映回完成面。
尚無宿主時集合為空；其他共面宿主仍不計入。
截面先取足跡聯集，再從各側板邊量其與該分片的連續覆蓋；孔、板片邊及足跡間斷
均會截斷寬度。相鄰子段僅在左右兩側實值完全相同時合併，不按顏色合併，亦不跨
有效縫段／band 身分合併。

`support` 每筆含 `seam`（effectiveSeams 索引）、`range`、`left`、`right`、
`supported`、`status` 與 `colour`。兩側均達 D31 引用門檻才是 supported／green；
不足是 insufficient／red，但仍能保存合法試排。比較使用整數商與餘數，保留有理數，
避免 `寬度×分母` 溢位。API 不接受任意足跡；只有測試 executable
`pf3-algorithm` 可給定純演算法輸入，不能冒稱該輸入是合法 D7 場景。

## 交易、容量與切片界線

World 與 scene 仍只保存定義。讀取、候選預覽、確認後、Undo／Redo、重開均重新
推導；沒有板縫或承接結果 cache。候選經 D7 重建後先完整計算，超限在提交前
整筆拒絕，不等讀取時才截斷。每份試排最多 32768 條有效段、32768 條單側段、
32768 條承接子段、1048576 次開區間求值；板片、頂點、縫線及角材沿用上游限制。
這些是執行器資源界線，不是公理的幾何限制。

沿用原生 API 與 `complete:false`，沒有可見 UI 入口（GEO-219 無新增項），
不提前實作 PF-6 建議、PF-4 引用網格、PF-5 空間流程或 browser／完整專案交付。
`tests/test_panel_fill_host.py` 原 PF-H 獨立 oracle 斷言改為直接比對新 runtime
結果；保留原足跡及原期望數字，未放寬斷言。

## 驗收對照

- PF04／D43：缺角、孔、障礙的兩側相鄰性；雙軸奇數縫、負 band 與交丁 T 點。
- PF05：8／8、7／9、局部斷承接、X=9，以及不足結果可保存／重算。
- PF06：門檻改名、排序、正有理數換值、極值分數、刪除、型別及非正值拒絕。
- PF07／PF11 的原生部分：取消、候選不提交、Undo／Redo、清空後重開；只存定義。
- PF13 的本片容量：純 evaluator 的 N=32768 完整輸出、N+1 明確拒絕且清空結果。
- PF23／PF24：原 E1 三段與 X5、E2／E3 一段；合法 E1 五段與 E2／E3 三段；
  同一組足跡輸入的 runtime 與純 evaluator 全等；反向／垂直框架及逐側寬度。

測試命令（雲端 native 一律先 `ulimit -s 16384`）：

```sh
python tests/binaries.py build bridge pf3-algorithm
python tests/test_panel_fill_support.py
python tests/pf3_mutation_check.py --out /tmp/pf3-mutations
python tests/mutate.py
python tests/mutate.py --check
python tests/run_all.py --build
```

具體受測 head、退出碼與原始輸出由本輪 evidence 索引記錄。
**雲端 native,非正式 WSL 收據**；正式七項由本機列車於整合樹執行。

## GEO-261 之後的故障注入錨點（2026-10-20）

整合分支 `7e36543b` 上，`tests/test_mutation_anchors.py` 報出 `unplaced`、`host-identity` 兩個案例的錨點不存在：承接足跡的篩選從 `w->timbers[i]` 改成 `w->wood.timbers[i]`，原本的單一條件被拆成幾個敘述。另外 17 個案例的錨點沒動，實跑也全部仍被殺。

承接規則「只有放在本填板衍生宿主上的已放角材才算承接」在 GEO-261 有兩處把關。工具的案例本來就是補丁清單，`host-identity` 這次改成兩個補丁，`unplaced` 一個。

| 案例 | main `adbaebf9` 原本打的位置 | 整合分支改打的位置 | 層數與對照組 | 為什麼是同一條規則、同一種錯誤 |
|---|---|---|---|---|
| unplaced（R43） | `geometry-core/panel_fill_support.inc:30` `if(!w->timbers[i].placed||w->anchors[i].placement_id!=host->id)continue;` 拿掉 `!…placed||` | 同檔 `:23` `if(!w->wood.timbers[i].placed)continue;uint32_t placement=…;` 拿掉前半句，留下 `placement` 宣告 | 1 層，單層即被殺 | 規則是「沒有 D7 放置的角材沒有足跡，不算承接」，仍只靠這一句。測試場景的零 id 宿主與未放置角材 99（錨點的 `placement_id` 預設 0）剛好 id 相同，篩掉 `placed` 之後角材 99 進入足跡計算，得到 `R43: timber 99 footprint unavailable`。失敗在 `test_panel_fill_support.py:186` → `derived()` 的 `assertNotIn("error", …, "PF3_UNPLACED…")`（`:29`），與 main 完全相同。 |
| host-identity（R43） | `:30` 同一行拿掉 `||w->anchors[i].placement_id!=host->id` | 同檔 `:25` `if(placement!=host->id)continue;` 整行拿掉（`placement` 在來源圖路徑取自 `wood_definition_sources_placement`）；另一層 `geometry-app/native/reference_sources.inc:496` `reference_member_footprint` 內的 `anchor.placement_id!=placement_id||` | 2 層。只拿迴圈篩選（XP1）：候選被拒 `R43: timber 1 footprint unavailable`（`PANEL_FILL_INVALID`），測試在 `:168` 的 `apply` 失敗，到不了指名的 `PF3_HOST_FILTER` 斷言，工具判 not-killed。只拿足跡檢查（XP2）：存活，結束碼 0。兩層都拿掉才被殺 | 規則是「只有放在本填板衍生宿主 id 上的角材算承接，共面但不同宿主不算」。main 只有迴圈這一道；GEO-261 另在足跡計算裡再驗一次（角材放置 id 必須等於要投影的宿主），所以只拿掉迴圈，別的宿主的角材會變成「足跡不可用」的候選拒絕，而不是被悄悄算進去。兩層都拿掉後，別的宿主的角材被當成承接，`widths` 變成 `[[0,27,100,900,True],[27,273,10,20,True],[273,300,100,900,True]]`，期望是 `[[0,300,0,0,False]]`，失敗在 `:170` 的 `PF3_HOST_FILTER`，與 main 完全相同。 |

第二層所在的 `reference_member_footprint` 是共用函式，`references.inc` 的其他檢查與世界驗證（經 `app_reference_member_footprint`）也呼叫它。補丁只用在這個案例的暫存副本，案例的裁判只有指名的那一個測試；其他呼叫端受到的影響沒有逐一分析。

### WSL 實跑收據（2026-10-20）

受驗提交是 `bda11f1430a19c88e0b0474dfe5034d3cf35b9f5`，`git status` 乾淨。環境：WSL Ubuntu-24.04、GCC 13.3.0，ext4 clone `/var/tmp/anchor-drift-geo261/repo`，經 WSL 鎖。指令 `python3 tests/pf3_mutation_check.py --out … --jobs 3`，結束碼 0，587 秒。

- 基準線 pass：20 個測試，0 fail、0 error、0 skip。
- 19 個案例全部 killed：每個都是 1 個測試、1 個 failure、0 error、0 skip，stderr 含指定標記；沒有 identical-binary。
- 還原後 pass：20 個測試；原始碼逐位元組未變（`originalSourcesUnchanged: true`）。
- main 對照（`adbaebf9`，main 原本的 `unplaced`、`host-identity`）：都 killed，失敗位置與訊息和上表相同。
- 改錨前對照（`7e36543b`，工具未改）：基準線 pass 後，在 `unplaced` 的錨點斷言停下，工具結束碼 1。

收據在 `D:/geometry-axiom-work/anchor-drift-20261020/`，沒有提交進 repo：

| 目錄 | 內容 |
|---|---|
| `final-tools/out/pf3/` | 受驗提交；`summary.json` sha256 `38f480d99c5d22231c426f38a8e507f0a7e904cacaa972aac3a7c2e4b49a705d`，每個案例一個子目錄（結果、stderr、建置收據） |
| `controls/out/pf3/` | XP1、XP2；`summary.json` sha256 `5de279eeeeddc443ef888714968f7cc91c124a45cd9511f78e345b859445a659` |
| `main-compare/out/pf3/` | main 的原突變；`summary.json` sha256 `6f601c215104e42831e6bbf3e09fac6649debbb435313e915946afaded5a0aef` |
| `before-tools/` | 改錨前的失敗，`pf3.out` sha256 `7f0cdbe3787de304380531e7a00cdac95c7bb017757bfae81843805b6cbfed01` |
