# #338 接續：新候選來源與剩餘驗收

候選分支：`codex/train337-recovered-evidence-20261026`。固定 F：`cbf0fb621888596aa14ad5f2349b503e23b1b72d`，父提交 E：`9a57aea2128a7bc3985064932c24e2229fd8fcb8`。一般 push 與遠端三檔全文核對已 exit 0；尚未宣告 READY-TO-MERGE。

原列車 `codex/train-337-continue-20261024` 遠端仍是 `a6f4013364e21bcb7239b5dcc25caac0f6d61f77`。為避免與 Claude session f46787ac 競寫，本輪不更動原列車產品 ref；正文由對應 prbody 與原交接 request 更新 #338，不新增替代產品 PR。此候選屬同一個既有任務的獨立恢復分支。

F 僅採入三個已有原件並經對抗審查的檔案：`tests/mutants_results.json`、`geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md`、`geometry-core/domain-decoupling/product-architecture-receipt.json`。其餘產品／測試／公理／決策不變；manifest 與 scan 也逐 byte 不變。

- S10 全帳本已真正完成，exit 0；123 筆為 114 killed、5 equivalent、M20 crashed、3 retired，120 執行 head 原值保留 `82c922a3941525d3a094ac0158bdc7dea57ea360`。不要重跑已有效的 full123，也不要把紀錄中的執行 head 改為 F。
- a6 三條架構原裁判為 0/0/0，generic 205、product 18，零 skip。四檔組裝 exit 0，604 個來源 raw/LF/Git closure 不變；架構 receipt 如實綁 a6，歷史 M6e50 反證保持歷史來源。
- 獨立 a6 source checkout 已一般 FF 到 F；原 `mutate.py --check` 與三條架構裁判真實退出碼均0，獨審12837項／exit0。完整命令、原始輸出、退出碼、環境與F均封存；RESULT雜湊`4ef99c7b38f0ab5f451e508d6fffd4e78e30d52a6df133f9a9fd7f9210359784`。3763 葉的這個 checkout 不能冒充 native 所需的 6997 葉來源。
- 原 F9 六組 browser 皆 exit 0，原 F9 native 為 exit 1；新 F native 與六 browser 尚未完成。不要用原件封包或工具合成反證冒充產品全綠。
- R8 原 36 份效能樣本與 outer exit 1 都保留，不重抽樣。#338 原裁決留言（內容為Q-323-ABC）刊載帳戶已核實，但對PR適用範圍自述「本機Claude整理，非原話」；既有#323 exact收據保持原三差限定，本輪不新增比較例外。新的P-189／跨SHA沿用文字仍僅有轉錄與審查引用，未核實對應原始批准，原比較器不變。

## 共用空間阻擋

2026-10-26 10:16 UTC 附近：兩個 OWN 去重使用量 `1,741,426,688` B，原 2 GiB 規劃上限餘裕 `406,056,960` B。單個 browser 原 416 MiB 准入尚缺 `30,150,656` B，且未含新準備產物。實際 SHM free 約 16.13 GB 不代表可以忽略原 2 GiB 規劃守門。此數字是當次觀測，執行前須重查。

native 真正使用 `/tmp/geometry-tests`；當時 `/tmp` 約 24–25 MB，未達原 128 MiB 准入。不得只設定 TMPDIR 就宣稱已繞開此需求，也不降低門檻。

自動審核已拒絕原 3156 葉清理：2439 來源副本、691 Chrome cache、2 私有 index、24 ELF；原工具另含 108 個空目錄。命令沒有啟動，刪除 0。原 true 請求已撤銷，禁止重試、拆批或換路徑執行同範圍。另 165 個 GPU cache 不在此次批准範圍內，也未執行。完整保全已交付 E9；精確範圍與所有限制見同批 approval packet。協調者取得具體批准前，不處理此刪除。

## 執行者與保全

root 是 recovery 候選與對應 prbody 唯一 writer。publisher 的 HEAD/index/原 train ref 固定 `3e4f2560aa11ed2a626db98ba5ed6f129e791052`；舊 workspace provider HEAD 固定 `70d00309d7985db722c339c77331c436d26a7ab1`。未修改兩者工作樹或原 index。

保留全部原始失敗、收據、五個 fixtures、Git objects、原取樣與未提交修改。不得合併 PR/main、部署、付費、修改安全／掛載設定或新增公理。正式程序終態以原始 result/exit 為準，不依訊息延遲猜測超時。
