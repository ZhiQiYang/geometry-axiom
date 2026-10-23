# #299＋#316：新整合基底進度

本頁記錄準備工作，不是新整合 SHA 的正式驗收。原正式產品為 `5bfadf187e615ba0fb8466753b63ce3044ef7d1c`，其公開證據 HEAD 為 `139ab64ca5f88e89bb4e95921675b998457026aa`；全部歷史收據保原 SHA，不改標新基底。

| 已完成項目 | 指令／結果 | 下一步 |
|---|---|---|
| 目前回報收件匣 | `python3 geometry-web/feedback_cli.py list`，退出 0，無未處理回報 | 合流後維持原回歸 |
| 權威 handoff refresh | `git fetch origin handoff/codex-takeover-20261021`，退出 0；固定 `ea2748248d47563f8559638ccb70ec0ed21910d9` | 最終交付前再 fetch |
| combined 原件完整保存 | `python3 -B collect_preparation.py`，退出 0；README、指定 patch、八個 `_gen` 檔均保原 bytes；299/316 review 檔不存在 | 對照前棒 union，不覆寫舊修復 |
| M89–M98 靜態錨點 | `python3 -B check_combined_anchors.py`，退出 0；十個 ID 唯一，old anchors 各恰一次 | 新合流 SHA 再查；動態反證另跑 |
| #288 grid/timber 對抗審查 | `python3 -B review_grid_timber.py`，退出 0；核原 F13 收據、workflow blob、完整小 streams/hash、scope/埠/暫存與版本，未重跑 job | 原結果交主代理；不代替 canvas |
| #314 對抗審查 | 靜態提出相同最終 ref 但不同 ordered facts 的正反例，owner 接手 | 等新 leaf 修正與同 SHA 0／1／0 |

grid/timber 原測試 SHA 為 `13d02c1db7022145a52ee063286a558e595eb212`，原 job 退出皆 0；356／0 與 79／0 分屬原 partial scope。這兩份原 job 是串行使用同一乾淨來源 checkout，本次沒有補造獨立平行 checkout，也沒有解包重核所有 tar members／screenshots。

本次尚未普通 merge #314，尚無新的產品／測試 SHA；native、六個 browser、專項、三條架構與突變 freshness／重產都沒有在新堆疊執行。未啟動重工作，避免與主代理 R3 工作互相干擾。待 #314 共用檔交棒後一般 merge，解真衝突，排定必要原測試及精確 0／1／0；完整帳本由主代理最後一次重產。

對抗審查者為 #323 owner；這份準備收據的同儕審查仍待回覆。來源與正文分支僅一般 push，不 force push、不合併 PR、不改公理層或決策佇列。
