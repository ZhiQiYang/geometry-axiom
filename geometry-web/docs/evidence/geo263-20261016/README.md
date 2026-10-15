# GEO-263：精簡網格改名保留相位差

指定任務 31；issue #263。固定 base：`a898ad6e12707104568679591fe1b21804bfc3df`。
開工前已讀 #252 全串，未見任務 31 owner ACK；#263 無留言，263 分支搜尋為空。
領取紀錄：[#252 / 6201633030](https://github.com/ZhiQiYang/geometry-axiom/issues/252#issuecomment-6201633030)。

## 問題與修正

D29 是完整宣告；D10b／I24 明定省略 stagger 就沒有相位差；I37 要求逐欄來源先求值。
精簡檢視器原本只帶回 phase/step 或 panel/gap/anchor，漏掉 stagger 與其 ParameterRef。
修正將兩種排法的共用相位差尾段放在同一處：有引用時保留 `param:id:field`，
否則保留明示值；原本沒有相位差時仍省略。既有間距驗證與參數唯讀守門不變。
不改核心幫前端猜舊值，也不新增可見入口。

## 入口逐項檢查

以下行號固定於 base，不冒充修後行號。掃描了 geometry-web 56 個非測試／非 browser-check
產品或輔助 JS 檔；完整 `grid-system` 宣告建構位置只有下列前三列。

| 入口 | 來源 | 核對結果 |
|---|---|---|
| 精簡檢視器改名／改直接間距 | `grid-inspector.js:165–173` | 本次修正；保留兩軸的完整現值與所有 ParameterRef。 |
| 完整無限網格工作區：改名、主支方向、排法、欄位 | `grid-system-workspace.js:714–733,992–1003` | sourceDraft 讀回欄位、ParameterUI sourceRef；sourceCommand 已帶 stagger 與其引用，無須改。 |
| 舊有限 GridSystemEditor | `app.js:8261–8289,8420–8423` | 無限來源會轉交完整工作區；有限來源本就不支援相位差／逐欄參數 token（核心 read_axis 對有限排法用 literal parse），不能因此遺失合法 stagger。 |
| 明確移除相位差 | `grid-system-workspace.js:453–459,714–733,992–995` | 清引用、清 raw field，序列化省略 stagger；本次修正沒有加回它。 |
| 網格配置編輯 | `grid-inspector.js::saveBinding`；完整工作區 saveBinding | 只送 grid-binding，不重宣告來源軸。 |
| 來源子規則編輯 | `grid-system-workspace.js`／`grid-rule-lines.js` | 使用規則自己的交易，不另組軸宣告；帶相位差來源本就禁止規則。 |
| 參數卡改值 | `parameters.js` 與 engineering 交易 | 送參數操作，由原生候選重算使用者；不以數字重寫網格引用。 |
| 原始指令／專案載入 | 既有原始輸入、dump／load 路徑 | 是使用者明寫的完整宣告或完整場景，不是局部表單編輯，不偷偷補回被省略的欄位。 |

本 PR 不改 `grid-system-workspace.js`，不與 #260 競寫。

## 實測與原件

`grid_inspector_stagger_test.cjs` 載入完整產品 `grid-inspector.js`，以最小 DOM 替身
觸發 renderInspector 註冊的預覽事件，接真實編譯的 native bridge；不是重寫 saveSource。
確認對話框以受控確認替身提交同一 token，DOM/指標/HTTP 不在此探針驗證範圍。
明確移除對照使用現有 sourceCommand 原函式，原生獨立讀回與 dump／loadfile 驗結果。

| 執行 | 結果 | actual exit |
|---|---|---:|
| 修改產品前同一測試的首紅 | `GEO263_STAGGER_LOST`，第一次 u/repeat/literal 改名漏掉 -250 | 1 |
| 修後 | 11 pass／0 fail | 0 |
| 拿掉唯一共用 stagger 序列化尾段 | 同一具名 assertion 轉紅 | 1 |
| 還原 | 11 pass／0 fail | 0 |
| 突變驅動器（驗出口碼、具名紅燈、同測試 SHA、還原 bytes） | PASS | 0 |
| 三個 JS 檔的 node --check | 通過 | 0 |

11 項包含：u/v × REPEAT/REPEAT_PANEL × 直接/參數，共 8 種改名；每種都逐欄比對完整軸定義，
確認其他參數來源不變、dump 保留 token，實際保存 dump 後 loadfile 重開並再比對。
另外 3 項是參數 400→350 後相位差重算、直接間距 600→700 保留相位差，及明確移除仍省略。

原件：before.stdout/stderr/exit 是首紅；fixed／mutant／restored 的 stdout、stderr、
每筆 native 指令與回覆 jsonl，以及 mutation-receipt.json 是最終同裁判三輪。
before 使用當時尚未加 transcript／roundtrip 的測試版本；最終三輪同一 test SHA，
不冒稱首紅的測試 bytes 與後來擴充完全相同。

`compile_probe.py` 記實際 gcc argv、stdout、stderr、actual exit、時間及 binary SHA。
`source-identity.json` 的 50 份原生 include 閉包檔，每份 Git blob SHA 均與固定 base
逐 byte 相符；`current_geometry.c` 以 bytes 寫入／比對，保留 CRLF，沒有改產品核心。
編譯器既有 warnings 保存在 compile.stderr，未修改它們或當成測試失敗。

環境：Linux 6.18.44 x86_64、glibc 2.39、GCC 13.3.0、Node v24.19.0、Python 3.12.14，
測試前 `ulimit -s 16384`。**雲端定向 native，非正式 WSL 收據。**

重現：

```sh
ulimit -s 16384
python geometry-web/docs/evidence/geo263-20261016/compile_probe.py
GEOMETRY_TEST_BRIDGE=/tmp/geometry-task31-bridge node geometry-web/grid_inspector_stagger_test.cjs
GEOMETRY_TEST_BRIDGE=/tmp/geometry-task31-bridge python geometry-web/docs/evidence/geo263-20261016/verify.py
```

## 真瀏覽器回歸與未驗

`grid_system_test.js` 的 P70 新增四個真 CDP 檢查：精簡改名保留直接相位差、
改名保留參數引用、參數改值重算、完整工作區按「移除」後清除數值與引用。
測完恢復舊 fixture 的 400 與來源引用，讓既有保存／重開檢查沿用原前提。
既有斷言、等待、上限與 runner/expected 均未改；新獨立探針在 geometry-web 下，不假稱
已自動加入完整 native 註冊表。正式 grid job 會透過原 P70 入口執行新增四檢查。

本環境未找到 Chrome/Chromium，**新增 CDP 檢查尚未實跑**。最小 DOM 的原生探針不代替它。
完整 native、canvas／grid 真瀏覽器與正式同整合 SHA 七項亦未執行，不新增 skip 求綠。
初次撰寫探針曾先修正測試工具自己的 schema 名、fixture I8a 確認流程與證據工具路徑；
這些是測試工具準備錯誤，不算產品首紅或有效突變。
不改公理、白話、正典、決策佇列、tests/、官方帳本、expected、runner 或其他任務檔案。
交付維持 draft，請 Claude 核對。
