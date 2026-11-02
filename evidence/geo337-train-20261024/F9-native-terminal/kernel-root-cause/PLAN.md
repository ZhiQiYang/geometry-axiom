# F9 native：#314 K 層範圍誤判；外部草案，未施作

原 assertion 位於 `tests/test_geo314_commit_paths.py:261`：

```python
self.assertEqual("", changed.stdout + added.stdout,
                 "I24 submission policy must not change K files")
```

其 `changed` 是整個目前 working tree 與 `4b665fae21ab63aaffb7d84f6a32d5a469ba1675` 的 K 層差異。F9 的實際唯一差異為 `geometry-core/kernel/source.c\n`，因此正式 native 會紅。這是歷史基底測試把其他工作線改動誤歸給 #314，沒有證據顯示 I24 規則移入 K；不是環境錯誤。

唯讀 Git 原流已證：

- #314 原實作 `32f42e3d991c7d2d916d21bfe8ac5d3dd0f9b131` 相對該 integration base 的 K 差異為空；使用者指定的舊 #314 head `3b0b634feb54266700cc61f26c34d7aeac4c0314` 也為空。
- 列車之後只有兩個提交改 K：`9430bae568feb98805072930c92f9a03a1250d4e` 重用 edge index 已探得的空槽；`81b6c388f8b73e9aaf885b1d948e5f306b77bafd` 混合 generic provider 的 hint bucket。完整差異僅 `source.c`，沒有 I24/W domain 狀態或比較器；來源與原場景判決不在本次重新驗收。
- 這兩筆都有既有 `tests/test_geo261_source_index.py` 的語意及 whole-withdrawal 工作量反證。#314 後續 `f61413ba785b67d2f455e4977e8b8da06050d654` 只改 W `grid_application.c` 與 #314 測試，沒有 K。
- 最新 generic K 提交 `81b6c388…` 與 F9 全 K 樹完全相同。I24 原實作與 generic K head 均為 F9 可解析 ancestor，避免依賴未合入的遠端分支。

`PROPOSED.patch` 只改該測試的範圍綁定，保留原 `INTEGRATION_BASE` 與相同測試數 11。新增兩個不可浮動的完整 SHA：I24 原實作、已審 generic K 樹。測試同時要求：

1. I24 原實作相對原 integration base 的 K 差異仍嚴格為空。
2. 現行 **全部** K tracked bytes 必須與 generic K 樹完全相同；原 untracked K 檔案拒絕檢查保持。

沒有按路徑排除 `source.c`，沒有接受任意新 K 差異，也沒有把基底浮動成 HEAD/F9。新 generic K 採入日後仍需明確更新、審查固定 SHA；只動常數偷偷納入 I24 K 邏輯不在本次允許範圍。其他 10 個方法 AST 與測試總數完全相同。

## 待原 F9 全部 gates 收齊後的反證

由 root 在新的隔離修正來源執行，保留同一個被驗產品 closure，禁止修改當下 F9：

- fixed：套草案後跑原具名 K-scope 方法，應 0。
- withdrawn：恢復 F9 的原測試 bytes，產品仍是同份列車，應 1，病因必為 `geometry-core/kernel/source.c`；不能用 Git 缺物件或啟動錯誤當反證。
- restored：放回草案，應 0；保存三相命令、退出碼、完整輸出、來源 SHA／patch hash。
- guard negatives：在乾淨私有 checkout 分別（a）額外改 source.c，（b）改另一個 K 檔，（c）stage 新 K 檔，（d）加 untracked K 檔；每個都須原 assertion 1，撤回自己那一項後原方法 0。這證明沒有用泛化白名單放寬 K 防線。這些可做微小檔案突變，不編譯，不碰收件原來源。
- 歷史 I24 guard 的負例另用 tiny Git fixture：指定的 I24 專屬提交若新增 K 變更，即使目前樹等於已審 generic tree，也必 1。fixture 不代替真列車正例。

應同時重跑完整 `tests.test_geo314_commit_paths`（11 項原方法）確認 route／baseline／W-H 邊界未漂移。測試檔變更後先 `mutate.py --check`，過期即按規則在所有修正固定的新最終來源整份重產；架構 closure 收據照規則更新。受影響正式 native 必重跑，其他 gates 由最終 closure 分析判定；不挪用或改標已完成 F9 的任何收據。

本目錄只有唯讀 Git 指令與外部 proposed source/patch；未執行任何產品測試、mutator、編譯、checkout 或分支寫入。根因分析不是已修復／已驗收宣稱。
