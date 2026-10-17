# 交回

## 做了什麼

在 `geometry-core/framing-template/core-probe/` 新增探針，沒有改 oracle、核心、公理層、閱讀器或測試列車。

- `gen_scenes.py` 讀 `oracle/oracle-golden.json`。8 個房間 × 8 種排法裡，64 個都可施工，各產一個 `.scene`（`scenes/` 與 `index.json`）。
- 每支角材一個 `place`。矩形與 golden 逐支相同，測試鎖住。沒有為了讓核心接受而改座標、縮短延伸段或改角色。
- 貼到外輪廓或孔、而且與該邊有正長度交集的料用 `at-face`。沒有貼邊的用 `at-line`，中線 = 寬向 lo + ⌊w/2⌋。
- 放置順序不是把全部邊界材機械地放在主支前面。依端面的全寬角材擋面做拓撲排序：不延伸的外輪廓 boundary → primary → 有延伸的 boundary → custom priority 3 → secondary。同階用 golden 原序。同階 boundary 的轉角互頂不建依賴。這份 golden 的環數是 0，沒有 `# probe-cycle`。
- `mapping.md` 是種類對角色的對照，每列有條號。不確定的兩項列在「待 Claude 裁定」。
- `run_probe.sh` 給之後在 WSL 執行：編譯原生核心一次；整場通過就整場記接受；否則逐支前綴，被拒的不留在後面的前綴裡；被拒的保留條號與 stderr 原文。輸出在呼叫者給的目錄（預設 `/var/tmp/framing-core-probe`），不覆蓋 repo 裡的 `scenes/`。
- `parse_results.py` 產出 `results.json` 與 `RESULTS.md`。整場失敗又沒有逐支前綴時，沒被點名的列是「同場未提交」。
- `test_gen_scenes.py`：`python geometry-core/framing-template/core-probe/test_gen_scenes.py`，Ran 11 tests in 2.228s，OK。沒有編譯、沒有跑原生核心、沒有跑 oracle selftest。

## 跳過了什麼

64/64 可施工，`conflict_codes` 都是空的，跳過清單是空的。程式仍會跳過 `buildable` 為假，或 `conflict_codes` 非空的排法。合成小 golden 的測試蓋到這兩種，證明跳過不是死碼。

F1 客廳八個排法的支數是 108、116、109、111、108、116、109、111，全部寫出，沒有為了 64 支上限抽料。場景標了 `# probe-capacity`。讀 `current_geometry.c` 的 `WORLD_MAX_TIMBERS`（64）與錯誤字串「角材的數量超過上限」。這是讀原始碼，不是實跑。

孔邊上、golden 種類仍是 `boundary` 的 40 支（整條 24、被主支截短 16）暫寫 `secondary`，`pending` 為 `hole-perpendicular`。

## 待裁定

見 `mapping.md` 的「待 Claude 裁定」。這裡不重做選擇。

1. 孔邊上種類仍是 `boundary` 的料：`secondary`（I21 孔邊可為 secondary、D17 垂直主支軸、R18 孔邊不算 onBoundary；oracle 建構註解稱柱面料為 secondary）對 `custom`（D15 沒有軸向義務）。`boundary` 與 `primary` 兩種已由 I20、I21 排除，不是待選項。
2. `rc_parallel:custom` 的 priority 寫 3。條文只要求 custom 的 N≥1，頂延伸段則要大於 2（I22）。沒有條文說只能是 3。

## 最不確定的 3 件事

1. 孔邊垂直料的角色。場景暫用 secondary，沒有另做一份 custom 場景，所以這次探針量不到 custom 方案。若裁定是 custom，要重出這 40 支再跑。
2. D7 不寫長度，錨點是引用。核心接受只表示這支 `place` 過了當下的不變量，不表示導出的 L 或足跡矩形等於 oracle。本探針只記接受或拒絕；接受時若 stdout 有 `L=` 會附上，但不拿它當幾何驗收。
3. B=33 與承載面 `origin 0 0 2500` 不在 golden。沿用既有天花場景。golden 沒有第三維，場景也沒有寫 `column`。

## 1 mm 突變

`build(delta=1)` 把第一個可施工排法的第 0 支 x0、x1 都加 1。測試套件用 `assertRaises` 接住，所以 11 項仍是綠的。另一次不接住的失敗原文：

```
F1客廳 / 左上起鋪,板長沿Y / 編號 0 / boundary / oracle [0, 0, 5000, 27] / scene [1, 0, 5001, 27]
共 1 支不符
```

提交版的 `delta` 預設是不偏移。

## 實跑前該知道的限制

- 逐支前綴會拿掉先前被拒的料。後面的擋面因此和整場一次放不同。`results.json` 的 `omitted` 記下那些被拿掉的編號。
- 32 支孔邊 `rc_parallel` 的長度伸出孔邊，仍用 `at-face`。預期觸發 I22（V_EXTENSION）。沒有改成 `at-line`，也沒有縮短。
- 4 支 `rc_parallel:custom`（F1 右上／右下板長沿 Y，以及左下／右下板長沿 X，golden 編號 14）與凹角牆線共線，但和該邊沒有正長度交集，整段落在另一肢。R6(c) 的 at-face 要求與引用邊重疊，所以這 4 支用 `at-line`。矩形沒有改。其餘 20 支 custom 貼外輪廓，用 `at-face`。
- `git check-ignore -v` 對 `gen_scenes.py`、`scenes/f1-00.scene`、`index.json`、`run_probe.sh`、`mapping.md`、`parse_results.py`、`test_gen_scenes.py` 沒有輸出，這些路徑沒有被忽略。沒有改 `.gitignore`。
- 原生核心尚未實跑。`run_probe.sh` 沒有在這台 Windows 上執行。
