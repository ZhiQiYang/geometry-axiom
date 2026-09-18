# 跨面共用基準：獨立審查記錄

日期：2026-09-18。審查者：`datum_planner`，獨立於核心／Web 實作 agent。
基線：`3c827ea84bf3ecfedbda063bca1e77c1f5f066d5`。

審查結論：核心幾何／交易與公理一致性審查通過，未發現尚存的程式碼阻斷問題；閱讀器來源同步驗證通過。五項呈現與 ID 邊界問題已修正並複核。A8 真實瀏覽器僅完成建立／引用／預覽；取消、確認與手機批註操作仍受環境限制，**不宣稱全部驗收完成**。是否接受此已知驗證範圍並合併，由主 agent 按使用者授權作最終判斷。

## 與使用者討論的一致性

- 共用的是房間座標的定位基準面，各承載面保留自己的參考線身份；沒有把兩面局部數字碰巧相等當成共同世界位置。
- 只做 X/Y/Z 軸向基準，規格值與有理比例有明確來源；不開放任意斜面或未定義世界幾何引用。
- 無限線本體與可見裁切分開；看不到不代表不存在，材料條件未放寬。
- 改共同來源依賴跨面重算，先預覽後原子提交。畫布卡片的移動不改幾何。
- 未占用 D19 / I24 / I25 / R22 / R23 等既有預留條號。

## 條文 → 核心入口 → 驗證證據

| 條文 | 實作入口 | 已核對證據 |
|---|---|---|
| D6c / I7a | `reference_types.h` 的 DatumPlane；`references.inc` 的 reference_eval_datums、datum_guide_geometry | 三軸 × 全部合法有號正交 frame 的世界平面成員性；平行／重合拒絕 |
| D6a / D6b / D6c | reference_eval_text、reference_quantity | spec-only 守門、無裸 mm、缺來源拒絕；負數先 floor 再轉 frame |
| D6 / D9 / I7 | reference_eval_guide；`current_geometry.c` 的 guide_line_get_local_segments | 孔洞兩段同一 id、面外零段但可引用、自帶矩形亦裁切 |
| I8 / I8a / R2 | reference_rebuild；`transactions.inc` 的 apply_scene_line、reference_stage | 跨面成功／失敗／取消／過期、局部中線相同的世界 frame 變更、整筆 undo/redo |
| I13 / R6 | reference_eval_timber 與既有跨距／碰撞驗證 | 隱藏 guide 不授權面外材料；原局部同面同軸與依賴重算合約通過 |
| I10 / I23 | 既有 grid 生成與索引守門；未修改其有界生成條件 | 既有 `test_grid_move_and_disappearing_index` 與奇數 gap 合約通過 |
| R13 | proj_rebind_aux 依實際 clip 判斷 guide 歸屬 | 隱藏線拆片拒絕；可歸片的 datum guide 保留相同基準與世界座標 |
| R4 / I9 | reference_dump、reference_dump_guide | dump/load/dump 相同、spec→datum→guide 順序、既有已廢除語法仍拒絕 |
| D12 / I14 | confirm 排除 canvas-pos 純展示差異 | 移動畫布後確認仍合法，當前卡片位置不被候選覆寫 |
| 正典閱讀器 | sync_axiom_reader.py 的 source_clauses、new_blocks、validate | 五道 assert、獨立來源逐字比對、可重現與批註保存測試通過 |

條號掃描矩陣只當導航，不作為以上證據的替代。

## 審查者實際執行

```sh
gcc geometry-web/web_bridge.c -lm -o /tmp/geometry-tests/bridge-review
GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge-review python tests/test_datum_contract.py
GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge-review python tests/test_reference_contract.py
python geometry-guide/sync_axiom_reader.py --check
python tests/test_axiom_reader.py
git diff --check
```

- 新基準合約：9 / 9 通過。
- 既有引用合約：25 / 25 通過。
- 閱讀器同步：8 / 8 通過；68 條文，382 個 blocks，5 則原批註。
- 對 Git 基線比較：批註內容、documentId、baseDocumentHash、歷史例圖資料及 example block IDs 完整保留。
- 重跑同步器前後逐位元組相同。
- 故障注入：雜湊與雙 JSON 自洽、但正文違反 SSOT 時拒絕；可見 DOM 錯字亦拒絕。

## 已修正並複核的呈現問題

1. Web 角材預覽已顯示完整長軸／A 軸／B 軸，不再只列 origin＋長軸。
2. guide 預覽已含世界方向，能區分 frame 改變而局部方向、世界起點相同的情況。
3. CLI / GDI 已列受影響 guide 的新舊世界方向與位置。
4. GDI 固定長度字串裝不下完整影響時，現會拒絕確認並保留 World，不容許只看部分預覽就提交。此 Windows 路徑已做程式碼複核，未在本環境執行原生 GDI。
5. `newid` 的 datum 建議值已避開 uint32 回繞後的既有 ID；0、1、UINT32_MAX 共存時的案例已在重新編譯後實測通過。

## 驗證範圍限制

初始 Cloud Browser 無法開啟 file:// 正典及本機 localhost，兩者均為 URL policy 限制，未嘗試繞過。
實作 agent 後續以受管預覽的正常站點入口，完成建立 spec／datum、兩面引用、放材與 500→900 跨面預覽。具體數值與限制見 `tests/evidence/datum-browser-observations.md`。
取消按鈕被自動核准審查拒絕，之後連唯讀檢查也被拒，故停止該瀏覽器流程；未改用其他控制器規避。取消／確認／過期／undo／redo 的同一 C 命令路徑已有合約測試通過，但不把核心測試說成瀏覽器實測。
最後增加的 A/B 軸與 guide 世界方向呈現已靜態審查，未在被封鎖的瀏覽器重跑；正典閱讀器的批註 runtime 與 iOS 亦未新增實機驗證。
靜態 DOM／來源檢查不宣稱已完成 iOS 觸控、軟鍵盤與實體裝置下載驗證。

## A1–A11 交付判定

| 驗收 | 審查判定 | 證據／限制 |
|---|---|---|
| A1 世界共用基準與有號 frame | 通過 | 全有號正交 frame、三軸世界平面關係；跨兩面共享高度 |
| A2 唯一交線 | 通過 | 平行／重合拒絕，候選失敗 World 不變 |
| A3 線存在與裁切分離 | 通過 | 孔洞兩段、面外零段、隱藏來源仍可被合法引用 |
| A4 材料與局部引用守門 | 通過 | 面外放料拒絕；跨面／錯軸拒絕 |
| A5 跨面依賴及 frame 世界姿態 | 通過 | bridge 完整資料與 CLI 複核；最終 UI 呈現靜態檢查 |
| A6 交易／取消／過期／undo/redo | 核心通過 | 瀏覽器取消／確認未完成，勿混稱 |
| A7 dump/load 與既有引用合約 | 通過 | round-trip 與 25 項既有引用合約 |
| A8 真實 UI 操作 | 部分完成 | 建立、兩面引用、預覽已觀察；取消／確認／undo/redo受阻 |
| A9 grid / R13 交界 | 通過 | grid 索引消失保護、隱藏 guide 拆片拒絕與 datum 歸片 |
| A10 閱讀器同步 | 結構／來源通過 | 五assert、8項測試、批註/圖片保留；runtime／手機未新增實測 |
| A11 可審閱 Git 交付 | 待主 agent 最終核對 | 分支／PR／base-head與合併由實作及主 agent 統一處理 |
