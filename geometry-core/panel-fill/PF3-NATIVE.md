# PF-3 有效板縫與承接比對

任務 22 沿用 #226，依 P-098 一般 merge PF-H #227 的
`4be9ff3453202984433c9256dff9dd60d5c8437a`，未改寫歷史。
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
