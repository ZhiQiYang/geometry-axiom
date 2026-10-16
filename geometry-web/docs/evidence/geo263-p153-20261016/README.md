# P-153：#265 作者範圍 M1–M3 續修

父提交：`4b4f619f36779cfb01162b4a860019af06729b19`。
依 [P-153](https://github.com/ZhiQiYang/geometry-axiom/pull/265#issuecomment-6202205138)。
原 inspector 修法與 native 核心均未改；本輪只補測試接線、裁判與 fixture 隔離。

## M1：接進自動執行

將 `geometry-web/grid_inspector_stagger_test.cjs` 搬為
`tests/test_grid_inspector_stagger.cjs`，加入 `tests/run_all.py` 的 NODE_TEST_FILES。
它經原 `node:tests-js` suite 執行，沿用該 suite 的 bridge／model-base build 需求與
GEOMETRY_TEST_BRIDGE 環境傳遞。未另外假造 bridge 或新增 skip。

改為 node:test 父測試與 12 個具名子案例：原 11 項，加 main-along／來源規則案例。
Node 實報 **13 tests**（12 子案例＋父測試），不是 13 個獨立幾何案例。
`run_all.expected.json` 只改 `node:tests-js` **711→724（+13）**；既有其他數量不變。
13 來自本次定向實報，未宣稱完整 native census 已執行。

## M2：真正移除 → sourceDraft → serializer → native

測試先由 native 取得仍有相位差／ParameterRef 的來源，建立有值的欄位與 source select。
執行 workspace 原始 `[data-ig-remove-stagger]` callback body（非測試另寫的刪欄位邏輯），
讓其清 source select、dispatch change、清 input／rawOverrides；再執行產品原
`int` 與 `sourceDraft`，經原 sourceCommand 組完整宣告、原生預覽／確認與讀回。
測試沒有先手動 delete 待送物件的 stagger。

這仍是有受控 DOM／sourceRef 提供者的函式探針，沒有宣稱是真 UI 指標事件或完整
ParameterUI handler 驗收；P70 的實際按鈕驗收仍由 B1 負責。

新反證：只在隔離副本的 sourceDraft return 前補回 `s.source` 的舊 stagger。
同一測試以 **GEO263_SOURCE_DRAFT_MUST_NOT_RESTORE_REMOVED_STAGGER** 轉紅。
另一個既有反證移除 inspector 的 stagger 序列化尾段，仍以 GEO263_STAGGER_LOST 轉紅。
沒有變動產品 workspace；兩個突變只存在臨時副本。

## M3：共用 fixture 還原與引導提示

inlineRename 補上與既有 open 相同的 btnZoom／guidance-dismiss 處理。
新 CDP 區塊進入時保存完整 canonical dump 與兩個 grid-system 宣告，使用 try/finally：
取消未確認 impact、捨棄未發布草稿、將參數901還原400、重放兩份原始完整來源宣告
（包含原名稱與被移除的引用），重繪後逐字核對 dump 等於進入前。
清理不新增 check()，新增四個正式檢查的數量不變。

新增記錄案例：main-along u、無相位差來源，真正建立一條 all-cells divide 2×2 規則，
經精簡改名確認後，原生核對 mainAlong 與完整 rules 陣列不變。

## 本輪結果

| 驗證 | 結果 | actual exit |
|---|---|---:|
| 新 node:test 定向 | 13 pass／0 fail／0 cancelled／0 skip | 0 |
| 隔離刪除 inspector stagger 序列化 | 具名斷言紅 | 1 |
| 隔離 sourceDraft 補回已移除 stagger | 一個子案例斷言紅，父測試連帶紅；11 pass／2 fail／0 skip | 1 |
| 同一 oracle、還原原件 | 13 pass／0 fail／0 cancelled／0 skip | 0 |
| 驅動器完整核對 | PASS | 0 |
| P70 與新測試 node --check | 通過 | 0 |

四輪原始 stdout／stderr／native jsonl 與來源、測試 hash 在本目錄；receipt.json
保留各子程序的實際 exit／耗時。父測試與子測試的連帶失敗分列，不當成兩個獨立反例。
測試 SHA 四輪一致；原產品來源前後 bytes 相同。native bridge 沿用原固定 base
`a898ad6e` 的實編 binary；其 50 份 include 閉包與編譯收據見前輪 source-identity／compile-receipt。
本輪工具初次把建立規則寫成 new，被原生 RULE_SYNTAX 拒絕；改為正式 create 後才進行
上述四輪，不將這個工具錯字算成有效突變。

重現：

```sh
ulimit -s 16384
GEOMETRY_TEST_BRIDGE=/tmp/geometry-task31-bridge node --test --test-reporter=spec tests/test_grid_inspector_stagger.cjs
GEOMETRY_TEST_BRIDGE=/tmp/geometry-task31-bridge python geometry-web/docs/evidence/geo263-p153-20261016/verify.py
```

## B1 仍未解除

未動 `geometry-web/cdp_sections.golden.json`。依 P-153，作者修完後由本機工人在 WSL 鎖內
對新 head 跑 grid 與 canvas，確認新增四檢查及後續共用 fixture 斷言，再以
GEOMETRY_CDP_UPDATE_GOLDEN=1 取得 P70 真計數並提交；不能用本輪定向 Node 結果猜 golden。

本輪沒有 Chrome，**P70 新區塊及其 finally 清理尚未真瀏覽器實跑**；M3 是程式補件與
語法驗證，完整閉合仍取決 B1。完整 native／正式七項也未跑。
**雲端定向 native，非正式 WSL 收據。** PR 保持 draft，不宣告可合併。
