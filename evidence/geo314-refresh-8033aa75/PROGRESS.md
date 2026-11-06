# #314 來源更新進度

產品／測試來源 S：`8033aa756c62f654333c24d1276d4b61beb31a45`。本目錄是 S 的證據出版，沒有把出版 HEAD 當成另一輪產品受驗 SHA。

## 本輪已做

- 讀取 handoff `ea2748248d47563f8559638ccb70ec0ed21910d9` 的 `handoff/pr-reviews/314.md` 與 issue314 草稿，依本次使用者明示實作授權、2026-10-22 題 3B／題 4 鎖定決策實作。舊草稿的「待核可」與舊 agent 推論不當作 SSOT 已修改或默認逐條核可的證明。公理與決策文字不改。
- 產品 leaf `f61413ba785b67d2f455e4977e8b8da06050d654`：最終 ParameterRef 相同仍須辨識該軸有序事實；有序事實存在且舊／新 stagger 值不同時，先依原步驟歸因，再用原保值來源切換規則。無事實的保留引用改卡例外仍保留。
- 新增同終態正反例：舊 A400；先改 A500→解除500→綁回 A500 放行；先解除400→改 A500→綁回 A500 拒絕。兩者 final stores／source 相同，但最後一步是否保值不同。沒有為中間變動、最終回同值另增限制。
- 普通合併前棒 #323 `5c29eba30a40f20ea5c7eb8dc139e5788235d3b6`，merge commit `c939d4f35ec6083e7c661f50a0e90fe3ded9f440`。保留 `AppValidationInputs`、load residual 註冊與 shared expected union：contact15、hostfacts22、load13、stagger47。
- M99–M120 原樣保留（原歷史判決21 killed＋M110 equivalent）；新 M121 明確撤除這次 guard，M102 只隨實際呼叫重錨。101 個頂層 registry ID 全唯一；M102／M103／M105／M121 的原碼 anchor 各恰一。這是靜態資訊，未當作 mutant killed。
- 原 `python3 -B geometry-guide/sync_axiom_reader.py` 機械生成 exit 0，stdout／stderr／環境／原 HEAD 與工作樹 input hashes 見 `reader-sync-source/`。此命令實跑於 c939 的未提交 source 工作樹，receipt 如實標示，內容後已提交 S；不冒稱在乾淨 S 跑了 reader 裁判。
- Python AST、小型 blob／CRLF 核對完成；SSOT／決策 bytes 與前棒完全同一，current_geometry.c 無 lone LF；`git diff --check` exit 0。沒有編譯、測試、Chrome、scan、benchmark 或 ledger 重產。

## 當前結果與待跑

| 項目 | 本輪結果 | 下一步 |
|---|---|---|
| 原 reader sync 機械生成 | exit 0，raw 已存 | 在最終合流後執行原 reader 裁判 |
| 本輪 AST／唯一 anchor／shared count／保護文字 bytes | 靜態核對完成 | 不代替動態驗收 |
| 新同終態正反例、M121 真撤回／恢復 | 未跑，exit=null | 待 root 資源時槽取得同來源 0／1／0 與原輸出 |
| 原 #314 47 方法、ordered facts、route、mutation migration | 未跑，exit=null | 與前棒合流後依槽位執行 |
| 新來源 native／6 browser／ASM／三架構 | 未跑，exit=null | 不沿用 cc67 綠作為 S 綠 |
| 原 `mutate.py --check`、整份帳本 | 未跑，exit=null；舊帳本 stale | root 最後統一重產一次 |
| 架構四檔 | 保留原 #314 全套舊 schema／內容；新來源 stale | root 最後 Linux 統一重產與原三裁判 |

原 cc67 的全部收據仍在歷史證據提交 `1e9f4873e6563bb4b90595bb1965532ea98619b3`；原七項 wrapper／outer 1（assembly 出版衝突）、補出版 0、M110 equivalent 0／0／0 都保留原角色，不改判成這次 S 的通過。沒有合併 PR、force push 或改寫原證據。

已交棒 combined owner，後續 canonical／共用檔順序為 #314→combined→#318→無木工。最不確定的是這次新 guard 的真負控尚未動態驗證、混合 parameter-package／realloc／OOM／完整 P177 全域動態範圍仍不足；不以靜態接線替代實測。
