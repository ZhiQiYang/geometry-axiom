PF-2 的完成面若沿某軸完全位於板縫內，原本會逐列檢查不存在的板本體。原 R10 P2 輸入會先掃 5,000 萬個空 row，才由原縫線容量拒絕。本修正利用既有交丁的奇偶兩相位，先確認實際 row 範圍是否可能有板；只有所有相位都空時省掉 body 迴圈。

raw seam 列舉、4096 容量、錯誤類型、裁切與有板時的順序保留。小測例仍要求零片合法且保有六條 raw seams；另一相位有板、負 row、轉置與貼齊邊界也納入測試。成本反證比較兩個同為 seam-capacity 拒絕的輸入之真函式呼叫數，不新增時間門檻。撤回會移除完整優化，恢復會重新編譯原候選。

這張 draft 疊在 #346，順序是 #343 → #346 → 本 PR → 512；後續 512 需一般 merge 本分支。參照 #128 R10 P2 與 #300 前置，不關閉 #128 或 #300。

## 唯一 current-state

| 欄位／gate | 目前值或退出碼 | 精確界線 |
|---|---|---|
| product SHA | `324034812bb6effca68e0413bc0468595337b317` | 產品一 leaf、測試兩 leaf、expected 10→13 |
| evidence head | `6d9d46e8d16af75351924c6d47a078d3eb647cc0` | 只加原件與 UNRUN 進度，沒有重標舊來源結果 |
| base | #346／`a5f1806fb3cad2dada1a56e79e01d54f9f86700f` | source parent；未改其他人的分支 |
| 外部 patch／正式 source diff 檢查 | 0 | `git apply --check`、`git diff --check`；非產品執行 |
| `python3 -B formula_probe.py` | 0 | 純 Python 1150 案、488 全空、19 首 phase 空而後有板；非 C 驗收 |
| 獨立靜審 | 239/0、40/0、23/0 | 產品草稿、companion、公開四 leaf source |
| 原完整 panel suite | **UNRUN** | 原十方法與十 controls 保留，新增三方法；expected 13 目前只依 AST |
| 新成本撤回／恢復＋三 semantic controls | **UNRUN** | 真 C 操作數、正常 assertion 紅與恢復綠尚未取得 |
| PF-1／PF-2／PF-3、完整 native、受影響 browser | **UNRUN** | 不借 L、#343 或 #346 的歷史收據 |
| 最終突變帳本／架構三裁判與收據 | **UNRUN** | 主代理依最終來源統一重產，這個子代理沒有另跑帳本 |
| 允許的 skip | 沒有新增 skip，也沒有已實跑 skip | 正式項依原裁判；此 draft 不以未跑當通過 |
| 合併狀態 | **NOT READY** | 正式項、反證、帳本與架構未完成 |

[PROGRESS.md](https://github.com/ZhiQiYang/geometry-axiom/blob/6d9d46e8d16af75351924c6d47a078d3eb647cc0/evidence/issue128-empty-panel-rows-20261024/PROGRESS.md) 與 [RAW_INDEX.json](https://github.com/ZhiQiYang/geometry-axiom/blob/6d9d46e8d16af75351924c6d47a078d3eb647cc0/evidence/issue128-empty-panel-rows-20261024/RAW_INDEX.json) 綁定 322 個封存原件、指令、環境及 SHA。archive SHA-256：`e1149775a43e15da5b7de1f887d6491248b12c0d3af5ba084c35346b38609cc1`。公開 source 23/0 審查另存同目錄。

準備中 `git add` 曾因 ignored native 目錄提示退出 1；四個 tracked leaf 當時已全部 staged，後續逐位元組核對並正常提交，原錯誤保留。companion peer 的初 matcher 誤判與修正前稿也保留；它們都不是 C 產品紅／綠。

本片不改公理、決策佇列或 UI。staggered raw seam 自身的空外層列舉尚未優化；JSON 精度、正式 PF UI 回執及 allocator 失敗契約另案。最不確定的是尚未執行的真 C 成本與整合結果。原 60 秒單例時限、既有斷言與 golden 不變。
