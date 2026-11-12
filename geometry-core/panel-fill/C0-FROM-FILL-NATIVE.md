# C0：from-fill 原生來源前置切片

本切片以 `7a2b16d4f16d6e208461cf8b3dda09cdf89a0386` 為基底，承接已採納的 D10、D42、D43、R41、R44。它提供 PF-6 所需的活來源主格與真衍生宿主驗收；沒有把 R03 規則 oracle 宣告成產品配方產生器。需求帳 R03 的產品層級仍依正式 PR／合併／App 操作證據更新，單獨交付 diff 不升為 L2、L3 或 L4。

## 原生入口

```text
grid G on P from-fill F [main-along u|v|none]
```

`F` 必須是現有 D42 鋪排，`P` 必須是由同一個 `F` 推導的 R41 承載面。普通放置面、另一個 fill 的宿主、現有直接軸／system／binding 主格都不能借用身分轉成 from-fill。每個面仍遵守既有單一主格限制。

同一 from-fill 的 `main-along` 可以改動；省略時保留原偏好，`none` 清除偏好。偏好不改變格線幾何。軸由鋪排推導，不能混入直接座標、工程尺寸綁定、D19 子格或 D19a 子規則。既有 D58 配置來源限制亦維持。

## 索引、板背與交丁

來源索引 `k` 是 signed lattice index，沒有改成畫面取樣陣列的序號。先依 D42 在完成面求縫中心（含奇數縫寬的整數取值），再依 R41 將 v 映到結構側：`v_back = structureSide * v_finish`。負側不重新編號，也不再算一次半縫。

D43 板列 `p` 的範圍是另一軸的縫 `p-1` 到 `p`；這不同於 D29 cell 的 `p` 到 `p+1`。負奇數列仍是奇數列。錯縫線必須指定列：

```text
guide 21 P v grid:G:u:0:band:-1
place T on P at-line grid G u 0 band -1 between tA tB +v +n
```

沒有錯縫的軸禁止附加 band；錯縫軸缺 band 會拒絕。D7 足跡必須落在該列合法範圍。query 與原生 DrawTarget 共用分段；視窗取樣包含錯開後才移入畫面的來源線。

## 保存與候選更新

保存只寫一行 `grid G on P from-fill F ...`，不把格線展開成 EXPLICIT 快照。新的 `wood.grid.from-fill/1` 保存作者定義；`wood.grid.from-fill-value/1` 承載求值結果。既有 grid application schema 與 wire bytes 保持相容。

來源圖經同一候選的 finish provider 取得 fill 定義、尺寸、結構側與交丁值。來源修改會經既有 I8a 預覽與完整世界重驗：合法變更一起更新 guide／D7；碰撞或缺來源則整筆拒絕，取消不寫入，確認只形成一個既有復原步。dump/reopen 必須保留來源閉包。

bridge 的軸定義仍是 `{mode:"from-fill", fillId, axis}`。唯讀求值資料另放在 `evaluatedFill`，包含 side、staggerAxis、已映射的 staggerDelta、`bandIndexSpace:"panel-row"`；lattice 的 baseCoordinate／pitch 已映到板背框架。App 讀入適配使用這些資料，禁止將來源主格當成可拖移的直接格線或子格父格。

## 驗收入口

```bash
python tests/binaries.py build bridge
python tests/test_panel_fill_grid_source.py -v
node --test tests/test_panel_fill_grid_read_compat.js
python tests/pf_from_fill_oracle.py --bridge /absolute/path/to/fresh/bridge --output /absolute/path/to/oracle-native.json
```

原生 suite 含 13 個父方法：來源身分與保存、signed k／結構側、來源修改與歷史、錯誤來源零寫入、雙軸／雙側／負 band、D6a／D7 帶列限制、真繪圖窄窗、I8a 逐值預覽與真 D7 碰撞、來源變體防借用、離屏索引與溢位、來源閉包重開、逐支 oracle、偏好與幾何分離。

F3 次臥、F4 走道各八種排法共 16 案、592 支，以真正 finish surface／panel fill／derived host 建立；每支 native references 的 origin、axes、length、A 四角足跡與 frozen oracle 比對，再在全新程序重開重驗。角色、priority、B、位置、來源索引、anchor 與 selector 同時核對。測試 adapter 使用既有 core-probe 的角色／擋面規劃，不能據此聲稱產品已能自動產生 R03 配方。

## 尚待後續切片

- PF-6 的 R45 建議 builder、完整候選外層交易、選取集合及單次確認。
- PF-4 的 App 建立／對齊入口與獨立 D29 值快照。
- PF-5 剩餘空間與樑分層流程，以及真衍生宿主的面內操作路由。
- R03 的配方產生、配方意圖保存、確認成為正式物件與完整 App 入口。FT-S1 A 已拍板，不重開選項；未採納的正式條文不得由此實作偷渡。
- F5 孔邊垂直料在現有 probe 仍有待裁角色；本驗收不把它自動指定為 secondary，也不把 F5 計入 592 支。
- F1 大房的容量與 R04 另案驗收；本切片不提高 64 支限制。

完整 repository mutation ledger 與 `run_all.expected.json` 必須由官方 runner 在正式候選來源上重新產生；本 diff 不手填數量、不改舊 golden、不沿用過期的 killed 收據。本文不是正式 CI、Windows 實機或 L4 完成聲明。
