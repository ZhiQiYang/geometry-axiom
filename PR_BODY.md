下料清單原本有 N 個群組、每群又各存 N 個角材 ID；這份候選把 ID 改成報表自有的總 N 格儲存，群組只存 first/count。群組規格排序、群內宣告次序與報表按值複製自含行為保留。原分群／群組排序的時間仍是 O(N²)，這次只處理 O(N²) 儲存。

本 PR 疊在 #343 的 branch 上，產品基底是 ccfaf057088a80c7aad4049f1c67e5eedfc2fdec。容量仍64；沒有改公理、決策、K、原 timeout 或性能門檻。header 的報表布局已改，repo 內所有 C/H 渲染與原 harness 同步，外部 C ABI consumer 是否存在尚未知。

唯一 current-state 矩陣：

| 項目 | 實際來源／SHA | 原退出或狀態 |
|---|---|---|
| product SHA | 39273bc0229fbbb16565134e1f8fad3a0d598c31 | 公開可解析；source clean |
| evidence head | a5f1806fb3cad2dada1a56e79e01d54f9f86700f | 只新增本 PR 的 `evidence/geo300-cut-list-storage-20261024/`；正常 push／ls-remote 0 |
| 五leaf候選靜審 | 外部 immutable candidate，逐bytes等 5fa4d7de498362885fb5c06c77a54a81fa42e73f | 66 checks／0 findings，靜態非C實證 |
| source／expected 靜審 | 固定5fa source＋單一 expected8→11候選 | 22 checks／0 findings，其餘JSON逐值相同 |
| report-policy 原正式入口 | `python3 -B tests/test_geo261_wood_report_policy.py`，本S預期11方法／9控制 | UNRUN |
| 原報表逐bytes、五新控制真0/1/0、16MiB | 本S | UNRUN |
| full native／6 browser／ledger／架構 | 本S | UNRUN |
| performance／P189／512功能 | 本S | UNMEASURED／UNRUN；產品仍64 |

保原8方法／4控制／全部具名 CHECK 與 CLI 精確文字，新增3方法／5控制：交錯群組的非單調 ID、滿容量全異群、按值 copy 後抹除原報表與輸入；offset／ID值／逆序填入／N誤拒及每群N陣列復發控制。最後一刀以同一變異 header 重編 client 與 cut_list.c，finally 還原，不能把不同結構布局混連造成的錯誤當反證。新結構 size 檢查由 scalar 欄位及 padding 推導，沒有新性能數值門檻。

新增真方法登記使 `py:test_geo261_wood_report_policy` count8→11；其他 expected 欄位保原值（native30／faces45／noWood13）。本S尚未執行 `mutate.py --check` 或任何全帳本；最後統一由 root 在最終列車 SHA 產帳本。#343 原34/64／tuple收據只屬原SHA，不拿來覆蓋本leaf。

完整靜態原件包 [STATIC_PREPARATION_ORIGINALS.tar.gz](https://github.com/ZhiQiYang/geometry-axiom/blob/a5f1806fb3cad2dada1a56e79e01d54f9f86700f/evidence/geo300-cut-list-storage-20261024/STATIC_PREPARATION_ORIGINALS.tar.gz)，625186 bytes，SHA256 `95ddcc7f453831004aea0c3c924d655571ceb701dae8f90572450b7c715f9e0f`；320原件＋INDEX共321 regular members，全檔回讀原bytes/hash。source／expected正常推送原 streams 全保；原 allowlist add1／sparse restore1也保留，後續精確tracked-file處理成功，沒有 force push。

正式 runner 正在準備並等待 root 時槽：原 report case 沒有持久化 C 子程序 stdout/stderr，故先綁已受審的被動 CompletedProcess 觀測與原 NativeBuild cleanup audit，保原 return／exception／args／timeout；本包收錄封存時仍peer-pending的觀測準備快照；current `1ac22c23067503b0379fff3e39aa91a5862ac5ee6394eecc36c9731fb47e2532` 的後續19＋8項靜審原件，待正式驗收包一起推，沒有宣稱已執行。所有 C／perftest 均未啟動。沒有獲准 skip；尚無新產品紅燈可分類，因正式項尚未跑。NOT READY，不合併。
