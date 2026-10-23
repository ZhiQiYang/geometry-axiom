# 新列車進度（取代 #337）

本線 `codex/train-337-continue-20261024` 依最新授權持續推進，不等交接、PR 號碼或審查才做下一件。只普通 push／merge，不合併 PR，不寫 Claude／Grok 分支。

## 唯一 current-state

- 產品來源 F：`f64d638f15c48d2b9723b7ae9d230fb5dacb82d9`，已普通 push 並核對遠端同 SHA。
- 起點：Claude `3cbeb75926bb188e6c8f153d182303feadfa27dc`；已用一般 merge 合入 main `eda91c8593f0795278f7f16ff8b93d147a4fdaa7`，合併提交 `3417ab932e40431fc99ca74e50762149ebfc09f8`。此次 main 差異只有歷史證據，產品與裁判未改。
- 審查來源：已 fetch 交接分支 `821fc049c2aecdd4fdacb9e53c21a7db4c8e0890` 並讀 337.md 分工更新。其「舊比較器」描述與實際檔案不同；以下記錄原件比對結果，不憑留言推定產品已驗收。
- #314：指定 `3b0b634f` 的 17 個完整產品／裁判 blobs 已在起點中；M99–M121 的 23 筆定義及六 suite 共 103 項也相同。獨立審查 116 checks exit 0。沒有缺失可移植，保留列車新增閱讀 A。新 F 的六 suite 103 項及 Node inspector 13 項已回報 exit 0，M121 原 CLI 0、build 0/0/0、normal assertion 0/1/0，正交獨立 peer；Node 結果不是 browser gate。
- #323：來源產品與測試已完整包含在列車；只在此線修。F 新增成功接觸資料 memo，每個 consumer 保留原相依 kind/order；修復 footprint-order API 與跨 consumer 負控制漂移。四檔 candidate 與採用結果逐 byte hash 一致；候選獨立審查 116 checks exit 0。13/22/15 原 suite 已真 exit 0（50/0/0）；19 組 controls 經獨立 346 checks／0 findings，四新增與兩修正的原 0/1/0 皆核對；效能尚未量測，沒有收益結論。
- 帳本：合入產品前的 `3417ab93` 初始 `mutate.py --check` exit 1：107 stale、3 retired、13 unrun。須整份重產；該探測不是新 F 的正式 gate。
- 閱讀 A：保留 10-24 已核可 RC 未覆木連續段量法與 SSOT；#335 雙放置順序是已獨立追蹤的問題，不以未核可新公理修補。reader／oracle／7 native suites／掃描仍待新 F 正式驗證。
- 完整 native、六 browser、P52、Q38、§7、P-189、323 原 ABC／效能／profile 與撤回反證、架構三裁判及四檔收據、全帳本：均未宣告新 F 通過。後續原始 exit 逐項加入，允許的 skip 只依原裁判規則。
- 環境：Chrome 156.0.8078.47、Node v24.19.0、Noto CJK 已在雲端可用。已驗證清理 446 個可重建 ELF，回收 441,847,808 bytes，保留原 hash、收據、fixtures、Git objects；第二批 source 清理被 peer 發現保全漏洞，尚未執行，正在改為正向白名單。
- PR 請求已推交接分支 `09b77824770c9abc8030e8bdf8cfe52a65b280f8`；pr-status 尚未列新號。正文在 `codex/train-337-continue-20261024-prbody`，尚不可合併。

## 接續順序

1. 收齊新 F 的 #323 fixed-three 與 #314 正反例；兩個重測 slot 分別執行，效能／完整 canvas 必須獨占。
2. 跑原 #323 效能與 source-call 裁判並做同 F 的 memo 撤回／恢復。分母、36 次量測、4 次 profile、N32/base≤1、N64/main≤1.3、calls≤4.5 不變；紅燈照實分類，不重抽取代。
3. 修正收齊的缺陷後固定正式來源，整份重產 123 筆突變帳本及 Linux 架構四檔，再完成完整清單。不同來源歷史結果不填成當前綠燈。
4. #324 及 no-wood 各自分支直接一般 merge 新列車，不等列車入 main；各自工具和產品由另一代理審查，不爭用目前重測 slot。#325/#331/#333 仍由 Grok 負責。

封存包 `source-checkpoint.tar.gz` 與逐檔 `SOURCE_CHECKPOINT.json` 保存來源比對、採用指令／exit／完整輸出／環境及已完成的獨立審查。所有收據 SHA 分欄記錄；不以 evidence commit 冒充實際測試產品 SHA。未達 READY-TO-MERGE。

## 已完成並封存：#323 原 fixed-three

F `f64d638f15c48d2b9723b7ae9d230fb5dacb82d9` 的 load 13／host 22／contact 15 全部通過，原 runner、reaper、outer 各 exit 0；source 前後 HEAD／index／status 一致且 clean。74 筆原執行 JSONL 中 19 組 controls 逐筆核對；四個新增 contact controls 與兩項修復 controls 為具名單一 ASSERT 的 0/1/0。原 placement-key-single 等價控制仍是 0/0/0，沒有冒稱 killed。

原命令、環境、輸入、編譯／測試完整 stdout/stderr、sidecar、時間、hash 與獨立346checks收於 `residual-three-f64d638f.tar.gz`；`RESIDUAL_THREE_F64.json` 列逐檔 hash，已從壓縮包重新逐檔核對。這只證明三個專項，不是完整 native 或性能通過。

後續 #323 原 v3 prepare／build／compare 真 exit 1/1/1：列車新增唯一 I11 根場景，原171守門拒絕，後兩階段前置不成立。原失敗完整保留，正在 peer 精確允許該新增場景的外部工具適配，原175集合／比較斷言／性能門檻不變。

架構原三條 F64 真 exit 1/0/5：generic 205項通過，scanner 與 product setUpClass 被同一 run_axiom_mutations.py 的既有 exclusion hash 過期擋住；product 是 Ran0，沒有18項pass。正準備唯一hash更新與Linux四檔，不等待Windows。

2026-10-23 18:25 UTC GitHub 認證查詢開始失敗。此前產品F、E59447bfe、正文5478dcbf已推；本節與其封存先本地提交，尚未推送，不能標成遠端完成。按最新授權繼續工作，約18:55 UTC重試一般push。交接分支NEXT及324請求也已本地提交f4df23f5，尚未推。同步程式已由先前請求建立draft #338，最新審查仍待下次可fetch時讀取。
