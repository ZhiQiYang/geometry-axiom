# #299＋#316：合流來源已推，動態驗收待跑

目前產品／測試來源 S 為 `15a735951a36b6fe52e0291152f335139e6921ad`，來源分支 `codex/geo299-316-combined-20261022`。一般 merge 的兩個 parent 為前版 combined Eprep `c940a6543029a94d443709ebdcbd63828fdfef1d` 與 #314 source `8033aa756c62f654333c24d1276d4b61beb31a45`；後者已包含 #323 `5c29eba30a40f20ea5c7eb8dc139e5788235d3b6`。commit／push／ls-remote 均退出0，工作樹乾淨。主代理整合分支未由本代理寫入。

| 目前項目 | 原命令／結果 | 限制與下一步 |
|---|---|---|
| 一般 merge 前棒 | `git merge --no-ff --no-commit 8033aa756c62f654333c24d1276d4b61beb31a45`，原退出1 | 六個 conflict 已精確解完，原1與輸出保留 |
| 衝突解決 | `python3 -B resolve_source_union.py`，退出0 | 僅解析／保留原件與聯集，沒有執行產品、測試或 scanner |
| 原正典機械生成 | `python3 -B geometry-guide/sync_axiom_reader.py`，退出0 | source 是尚未 commit 的 merge tree（HEAD c940＋記錄的 merge variant），其後固定為 S；不是三條 reader 裁判 |
| 小型 source 靜態覆核 | `python3 -B inspect_merged_sources.py`，退出0 | 111個數字 ID 唯一；14個選定 anchors 各1；8個 suite 方法數與登錄相符；不是動態測試／freshness |
| 完整 cached whitespace check | `git diff --cached --check`，原退出2 | 全是前棒原 streams、main README 與決策原空白；保留原 bytes。精確自撰相關 paths check0 |
| source publication | 原 commit／push／ls-remote 各0 | 已把完整 S 交 #318；本代理此後只改 own evidence／另 prbody，不再改 shared source |
| 新來源正式 native／六 browser／專項 | **未跑** | P88 專責獨占重工作，未啟動 compiler、Chrome、benchmark 或 scanner |
| 新來源三架構／三 reader 裁判 | **未跑** | 不能以 sync 生成0或舊 receipts 冒新來源通過 |
| 新來源帳本 freshness／完整重產 | **未跑** | 全帳本只由主代理在最終來源一次重產 |
| #314 M121 精確0／1／0 | **未跑** | 靜態接受新guard的範圍，正常斷言反證仍待同來源實跑 |

六個 conflict 為 `.gitignore`、architecture report／scan／receipt 三檔、`tests/mutants_results.json`、mutation migration owner map。allowlist 保兩側；owner map 保 M89–M98 及 M99–M121 的精確聯集，另保23個 stagger IDs／61個 added IDs 的斷言。M89–M98 沒有更名或撞號；M102 隨前棒新參數改 anchor，M103／M105／M121 選定 anchors 均在新來源恰一次。

舊帳本只做 record 聯集：保 combined 的88個原 records，再保前棒獨有的22個原 records，共110。每一項 execution／verdict／來源欄位保原；M121 沒有捏造 record、仍為 unrun。這不是執行或重產，不宣稱它們在 S 上 fresh。雙方原 JSON 與兩側完整四檔 architecture 原件由 Git parents 與本次 raw stdout 保留。

有效來源 manifest 自動合併兩棒：保 #314 `stagger_facts.inc` 的 H 登記／八個 W identifiers，以及 combined 的 `wood_contact_boundary_edge` guard 與具名死 API `wood_contact_footprint_collides` 退休。scan／report／receipt 保前版 combined c940 的完整舊來源產物，其真 `sourceBaseHead=3a165ef5...` 不改標 S；它們無法證明新 manifest／closure，明列待 root 最後重產。未放寬 architecture policy 或以舊 receipt 假稱新來源綠。

`公理層.md` 與 `決策佇列.md` 正規化 bytes 逐一等前棒8033，沒有改字；`current_geometry.c` 保完整 CRLF／零 NUL。canonical 仍只有原正典一份，沒有手改嵌入 JSON、另造閱讀器或放寬斷言。八個靜態方法數為 contact15、host-facts22、load13、stagger47、contacts10、contact-world9、world-validation14、wood-grid23。

#314 新 leaf 的對抗靜審見 `REVIEW_314_f614_STATIC.md`。上一版 Eprep／Dprep 的 metadata 對抗審已由 #323 owner 完成，報告留在 `peer-review/`；本次 S 的合流 resolution 對抗審已交同 reviewer，尚未回覆，不能沿用舊 metadata 接受當新產品審過。

歷史獨立產品 F `5bfadf187e615ba0fb8466753b63ce3044ef7d1c`／證據 E `139ab64ca5f88e89bb4e95921675b998457026aa` 的原七項全0、原三架構0／0／0仍只是歷史結果。#288 F13 grid／timber 的原 partial 收據對抗審亦只屬原 F13。Windows GDI 原具名允許 skip、ENOSPC 原失敗與未捕獲舊 core inner streams 等限制保留，不轉成 S 的全綠聲明。

下一步由 #318 接 common/canonical 棒；本代理封存本次指令、退出碼、完整原輸出、環境與 SHA，更新 prbody 的唯一 current-state 矩陣。所有正式動態結果待主代理排程，完整帳本／architecture 最終重產由主代理統一處理。不 force push、不合併 PR。
