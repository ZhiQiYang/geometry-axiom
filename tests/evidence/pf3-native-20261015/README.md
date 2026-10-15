# 任務 22／PF-3 雲端交付與範圍外阻擋

**雲端 native,非正式 WSL 收據。保持 draft；完整 native 有 1 個失敗，不宣告驗收通過。**

## 來源與結論

- base：PF-H #227 `4be9ff3453202984433c9256dff9dd60d5c8437a`，已一般 merge，無 rebase／force push。
- 產品實作：`f22aa8ba58bd484e4a6d6c4a111a85f5f4248df9`。
- 最終測試及完整 native execution：`77ef94bedd3fe3c0a834ca0194067d82bff0ee2e`。
  其後只提交證據與交接，不修改產品／測試／expected／帳本。
- 完整 native：**90 suites，2876 pass／1 fail／1 既有允許略過，actual exit 1，533.619 秒**。
  所有 90 項都執行；沒有降低 expected 或新增 skip。允許略過是 Linux 沒有 Windows GDI harness。
- PF-1 22／22、PF-H 32／32、PF-2 17／17、PF-3 20／20、reader 41／41，均無 fail／skip。
  這些分項綠燈不能改寫完整 native 的 exit 1。

## 必須回報的範圍外失敗（依派工指示停手）

`tests/test_scenario_verify.py:403–421` 的
`ScenarioNativeAcceptance.test_model_timeout_stops_its_base_child_before_it_can_finish_late`
失敗，訊息為 `A model timeout left its native base child running`。
該 suite 為 37 題、36 pass／1 fail。完整 traceback 在
[native/logs.tar.gz](native/logs.tar.gz) 的 `py_test_scenario_verify.log`；機械結果同 archive 的 `.json`。

這是場景驗證的模型逾時／子行程清理測試，超出 PF-3 切片。該測試及 scenario／modeling
相關程式與 #227 base 無差異。本輪未修、未改斷言、未加 skip、未重跑成綠，也不將原因
預先判為環境或 flaky。依使用者「發現範圍外問題，停手並在 PR 留言」的要求停止實作，
交由 Claude 核對；完整 native 與正式七項的通過收據目前都未取得。

## PF-3 實際驗收

詳見 [實作契約](../../../geometry-core/panel-fill/PF3-NATIVE.md) 與
`tests/test_panel_fill_support.py`（固定 execution head）。

| 項目 | 實際執行及原件 |
| --- | --- |
| PF04／D43 | 孔、缺角、障礙單側不成縫；兩軸、奇數 gap、負 band、交丁 T 點；native suite 全綠 |
| PF05 | 純 evaluator 的 8／8、7／9、局部斷承接；另以真正 D7 boundary＋primary 實跑 8／8、7／9，X9 重算及不足仍可保存重開；[62 條原命令與回覆](pf05/native-d7-pf05.json.gz)、[退出碼](pf05/receipt.json) |
| PF06 | 精確有理數與極值分母、改名／排序後仍指原欄位；刪除／型別／非正值整筆拒絕；native suite 全綠 |
| PF07／PF11 原生部分 | 候選不提交、取消、Undo／Redo、清空後重開，只存定義；非 browser／完整專案收據 |
| PF13 本片容量 | evaluator N=32768 完整輸出、N+1 拒絕並清空；沒有宣稱已以完整 D7 World 耗盡所有容量 |
| PF23 原 E1 | 依 P-103 為純演算法輸入，三段 10／20、10／5、10／20；X5 全綠仍三段，不冒稱合法 D7 |
| PF23 E1-legal | 依 P-116 真宿主 primary，五段；[完整 state、D7 足跡及冷重開](witness/E1.json) |
| PF24 E2／E3 | 原 oracle 一段，真宿主各三段；[E2](witness/E2.json)、[E3](witness/E3.json)；同一組足跡與純 evaluator 全等 |
| R43 身分／映射 | 無宿主、普通共面宿主、不同真宿主均不冒算；零 id 的未放角材不計；反向結構側及垂直框架；native suite 全綠 |

`witness/summary.json` 是沿用 PF-H 擷取工具的原輸出，其中「PF-3 pending」是舊工具的
scope 字串，不能當本輪產品狀態。新增的 [PF-3 audit](witness/pf3-audit.json) 已逐段
直接比較 raw state 裡的 runtime support 與獨立 oracle，並核對冷重開全等；舊字串未手改。

## 突變與誠實性

- 最終新版控制：[mutations-v2-summary.json](mutations-v2-summary.json)。原版 20／20、
  19 個撤除實作全部具名 assertion 轉紅、還原 20／20；actual exit 分別 0／1／0，無 errors／skip。
  覆蓋雙側有效縫、極大段合併、板分片與足跡切點、開區間、聯集連續性、宿主身分、未放角材、
  s 映射、門檻引用／有理數／溢位、奇數縫、band、容量完整輸出。
- [原始命令、來源、binary／sidecar 與日誌](mutations-v2-originals.tar.gz)，
  [逐成員 SHA](mutations-v2-originals.tar.gz.inventory.json)，[實際產物核對](mutations-v2-artifact-audit.json)。
- 官方帳本 50 筆重產於產品 head：42 killed／1 crashed／4 equivalent／3 retired，
  [check actual exit 0](official-summary.json)。M20 crash 與 assertion kill 分列。
  [實際執行原件](official-originals.tar.gz)、[逐成員 SHA](official-originals.tar.gz.inventory.json)、
  [47 個實際 binary 與 baseline 核對](pf3-artifact-audit.json)。正式 native 再用空 MUTATE_CACHE 查核。
- 第一輪 18 題時有兩個 survivor（溢位例未觸發乘法溢位、band 只驗合法段存在）及一個
  已轉紅但未帶所需病因標記的案例，保留 [原結果](first-attempt-summary.json) 與
  [原日誌](first-attempt-logs.tar.gz)。補的是反例與病因標記，未改期望數字或放寬斷言。
- `mutations-summary.json`／`mutations-originals.tar.gz` 是產品 head 上第二輪全綠控制；
  `mutations-v2-*` 是補完 PF05 真 D7 測試後的最終控制，兩輪原件分存。

## 完整原件與未驗界線

- [完整 native receipt](native/receipt.json)、[stdout](native/stdout)、[stderr](native/stderr)。
- [207 份當次日誌](native/logs.tar.gz) 與 [逐成員 SHA](native/log-manifest.json)；
  [實際 binary／sidecar](native/binaries.tar.gz)、[身份索引](native/binary-final.json)。
- 15096 個 tracked 一般檔案，前後 SHA 全等、零排除，head 不變、結束工作樹乾淨。
  [前](native/tracked-before.json)／[後](native/tracked-after.json)。
- [交付稽核](delivery-audit.json)：產品／測試與 execution commit 一致，SSOT、白話、正典、
  決策佇列、BACKLOG 與 #227 逐 byte 相同；既有 expected 套件全不變，只增 PF-3 20 題。
  舊 `pf3-dependency-20261013` null／exit1 原件不變。
- 首次全量 `f4db6e66` 為補 PF05 真 D7 見證而主動中止，actual exit130；
  [中止收據](interrupted-native/receipt.json) 分存，不是完整成功收據。
- 正式 WSL 七項未跑／未排，browser／完整專案未驗。PF-4／PF-5／PF-6 未實作；
  API 保持 `complete:false`，無新可見入口（GEO-219）。

全目錄逐檔身份見 [manifest.json](manifest.json)。
