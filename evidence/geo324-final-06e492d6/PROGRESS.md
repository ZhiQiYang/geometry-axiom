# #324 替代線進度

產品來源 S：`06e492d6d59c1ab2c5505e5300f7542f7063468d`。分支 `codex/geo324-faces-20261024`；此批只封存準備與原件，全部正式 gate 尚未執行。

已完成：從 Grok `4e176e830b691269cc72d021ce7e1bc0b167d621` 開自有分支，普通 merge main `eda91c8593f0795278f7f16ff8b93d147a4fdaa7` 無衝突；merge 原 exit0、一般 push0、ls-remote0且同 S。相對 main 只原三檔／121+/2-，兩個 leaf blobs 保 Grok 原 bytes；expected 只 host_sources39→45，其餘 JSON metadata 逐項同 main。SSOT／決策 blob 精確同 main，沒有改字。薄 checkout 原47files／1,037,381B，沒有複製 Git objects。

已讀最新 handoff d193946b8e0fbda024d3b134c4851e9393a43d38 的324審查及17:01作者雲端交接。原 Windows45 tests與零步驟 Actions失敗保其原角色，不是本輪 S 的結果。原 startup feedback list 首次因薄 checkout 漏 feedback_store 而 exit1；只補物化該既有依賴後 list0（沒有未處理回報），完整兩次原件同存。沒有改產品或測試。

環境：繼承 PATH 下 google-chrome 真 FileNotFound，原準備 collector1保留；依既有安裝路徑補 PATH 後 `google-chrome --version`0=156.0.8078.47、`node --version`0=v24.19.0。不重新安裝、不把環境命令當產品 gate。

三 predicate 各自 baseline／withdraw／restored 的外部補充收據工具已備，僅AST0、尚未執行；原 tests/assertions 不變。原內建 helper 最後只 restored 第一個 case 的範圍如實記錄。GATE_PLAN與CURRENT_STATE_PREPARED列16個UNRUN項，沒有以準備0冒綠。

下一步：root排新train的一般合流順序，固定真正 final SHA，再按磁碟／slot跑原 registry、full native＋expected、六browser、affected importers、三predicate原method各0/1/0、mutation --check、原架構三條。原帳本過期與四檔架構刷新如實列，完整ledger由root統一排。最多2重活；canvas／perf獨占。尚未merge train，沒有編譯、Chrome、bench或測試執行。全部產物交p88_priority獨立對抗審；審查目前pending。
