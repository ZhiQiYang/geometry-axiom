# #128 R10 P2：外部補丁與驗收設計

固定來源為 `7af8c5d80d34cb4f49d01ba67deb78a3a6d725db`。本資料夾沒有修改 repository、開分支或執行 C；`PRODUCT_ONLY.patch` 只是可審閱草稿，不能單獨合入。

## 根因與有限修正

原 `geometry-templates/woodworking/native/panel_layout.c` 的本體候選計數只在內層 `k` 迴圈增加；整個沿軸 bbox 落在縫內時，外層 `r` 仍逐列增加。`size=(1,1), gap=1, origin=(0,0), straight, F=[0,100000000]×[1,2]` 會先走 50,000,000 個沒有板片的 row，然後才由原有 4096 條 raw seam 上限拒絕。

本草稿只在原 body 迴圈前檢查實際 row 範圍內最多兩個相鄰 row。直排只有一種有效位移，交丁只有奇偶兩種；若兩者沿軸都沒有本體 bbox 交集，後續所有 row 也不會有。只有此時省掉 body 迴圈。候選存在時原列舉次序、容量計數、裁切、錯誤順序全保留；未嘗試提前以 seam 容量覆蓋原先可能較早出現的 geometry error。

raw seam 的獨立列舉、中心／半縫 band、capacity 與 failure cleanup 一字不改。零板片不代表零 seam，也不是非法輸入。這依 I52、R42、I57 保留既有幾何與容量契約，不需要新的公理或數值門檻。實際來源由 H `pf_build` 委派 W `wood_pf_build`，最後進入本 W evaluator；不是再改舊的 H 相容入口。

**有限範圍：**這次僅消除 body 外層的全空列舉。staggered raw seam 本身也可能有空內層、長外層，尚未在本草稿優化。不得稱整個函式已為 O(1)、所有空列舉已消失，亦不把此因果當成 #209 P78 timeout 的根因。

## 先驗與固定／撤回／恢復

1. 原 `tests/test_geo261_panel_native.py` 與既有 `tests/geo261_panel_harness.c` 所有方法和斷言完整保留，包含原 frozen judge differential。原 `tests/test_panel_fill_layout.py` 18 方法、PF-1 與 PF-3 邊界也保留。
2. 新增小對照：`F=[0,10]×[1,2], size=(1,1), gap=1, straight` 應為 `WOOD_PANEL_OK`、零 tile/fragment/whole，raw seam 仍有六條；精確 seam 軸、鍵、座標與原 frozen evaluator 比較。加入轉置、負座標／起點及貼齊邊界對照，不把只接觸邊線算成正面積板。
3. 一相位空、另一相位有板：`size=(1,1), gap=2, stagger_axis=v, delta=1, F=[0,9]×[1,2]`；偶數 row 無板、奇數 row 1 有唯一板 `(i,j)=(1,0)`、body `[3,1,4,2]`。負 row 對照使用 `F=[-6,3]×[1,2]`，保留 row -1 的板；再轉置驗 u stagger。這會抓只檢查第一個 phase 而誤略過有效板的修法。
4. 大空板對照使用原 R10 的 10,000 與 100,000,000 長度，兩者都要原 `WOOD_PANEL_SEAM_LIMIT`、清空全部輸出、`clip_status` 保原值。不以 `OK`、截短 seam 或空結果取代拒絕。
5. 成本測例不訂 wall-time 新門檻：只在隔離測試版的 `panel_layout.c` 編譯單元以 `-Dgeo_alternating_shift=pf_probe_alternating_shift` 導向 shim；shim 計數並委派原 K 函式，K 產品不改。對 straight 的兩個大空板輸入，seam 路徑不呼叫 shift，故量到的是 body phase 工作。要求計數有實際發生，且 10,000 與 100,000,000 的工作次數相等；另保原 status／輸出斷言。這是同一空結果隨長度延伸的精確操作量關係，不是提高時限或新增效能數值比率。原 suite 子程序時限維持 60 秒。先核 shim 能觀察正常有板呼叫、輸入輸出與無 shim 原執行一致；未完成這些前不宣稱成本 gate 有效。
6. 撤掉本 patch，原成本關係必紅：公式預期是 5,000 對 50,000,000 次；固定與恢復都是最多兩個 present phase。必須保存實際 C 原始數字、指令、OS exit、完整 stdout/stderr、來源與執行檔 hash。**現在沒有任何 C 紅／綠收據。** 不把公式結果冒充 mutation killed。
7. 另做獨立反證：只查第一個 phase，步驟 3 必紅；空 body 直接 return OK，步驟 2 的 seam 與步驟 4 的 status 必紅；強迫空板非法，步驟 2 必紅。每個固定／撤回／恢復都需原 assertion failure，不接受 crash、timeout、setup error、skip 或 test error 混算。

若改產品／tests，主代理在最終來源統一重產帳本、架構與受影響正式項；本草稿不改 ledger、不更改 expected count、不借 L 的舊收據當新來源全綠。原 C 成本、HTTP 輸出、整套 native／browser、記憶體及 sanitizer 目前全部未驗。

## 其餘 R10 問題不混入

P1 的 JSON number 大整數 transport、P3 未來 UI 回執、P4 allocator 失敗契約與 P5 歷史突變工具混 error 的風險都另列。E1 的 64／127 byte 厚度已由 #242 修復，不重做。本文未改 `公理層.md`、`決策佇列.md`、閱讀器或 Grok 分支。
