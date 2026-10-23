# 本輪權威來源與適用範圍

已普通 fetch 到 owner 專有 ref（不寫共用 FETCH_HEAD）：main=`feb502d7b3bade2334733a4349c87ff91b88621e`；handoff=`acd1289228d490c68a139cf17e02fdc1f3cb247c`。本次 root 已 fetch 的 `origin/pr-333` 為 `3d9bd9476b5eda05e1cb92338ee741b90019dff2`。沒有據此聲稱 #288 已進 main。

已讀並封完整原 bytes：main `決策佇列.md` 的 2026-10-12～15（:102–460）、10-22（:676–806）、10-23（:807–840）；#333 的 `geometry-templates/woodworking/FIELD-RULES.md`。原 Git 讀取指令、退出碼、stdout/stderr、環境及各 immutable SHA 在 receipt.json/subcommands；原文 snapshot 與 SHA256 也在 receipt.json。

- 幾何核心是可遷移概念的組合；木工是可解耦的模板。模板規則不能反向變成 K 的領域規則。料長續接仍在本輪範圍外。
- 間距的目標是滿足上限、相鄰記號一致、板邊有支撐與主支連續。1830/5 與現場 1–2mm 誤差不能被擴張為額外硬門檻；「450」已撤回。端面頂角材、RC 先貼邊材；斜釘／側釘工法不是新增 app 規則。
- 10-22 的端面補充取代「懸空容許量待定」；沒有 h_max 數值。壁柱兩案都合法時 B1 原縫併料優先。
- #314 Q3 採使用者所選的有序判定：先改卡，再依換來源當下有效值驗保值；Q4 將來明示刪除後同 id 重建不延續例外。當前沒有新增刪網格指令。不得把協調者推論或舊草稿當成已核可 SSOT；本輪實作授權來自目前使用者明示指示，公理／決策佇列不由本 owner 改寫。
- 10-23 #318 核可閱讀 A，完整條文依指定 v3；只放行固定 boundary 外輪廓邊端點的既定例外，不外推到延伸段、primary/secondary/custom、無接觸或有足寬 RC 卻未貼料。SSOT／該 source 仍是 #318 owner 的單一寫入範圍。
- FIELD-RULES 自述不是公理層，是逐字引文索引；引文外文字不冒充使用者原話。此頁本身不能作未定案條文的實作授權，其來源正文採舊 main `4ccced59...`，與本輪 snapshot SHA 分開記錄。
- 10-12～15 合併列車、相關 job 與長期達標可合授權，以及 10-22 雲端驗收原文都已讀；目前工作以使用者最新順序和 root 的共享檔／資源排程為準。本子代理不自行合併 PR、force push、改隊列／公理或操作使用者電腦。

新工作順序由 root 傳達為 #318→#314→combined→#323→noWood→#324；已在跑的 #323 native 不打斷。固定 S3b 的 #314 v2 工具保留，不重做；slot2 先交 #318 原七項再接 #314。
