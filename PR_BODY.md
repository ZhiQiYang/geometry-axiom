修正柱／樑 native snapshot 缺少或損壞 `faces` 時洩出未分類例外：沿公開 evaluate 路徑，保原 `UNSUPPORTED / BASE_SOURCE_BINDING / I32 / Native box source faces disagree with legacy provenance.` 四元組。這是 #324 的 Codex 替代工作線，仍為草稿，完整雲端驗收尚未執行。

| 來源角色 | 完整 SHA／分支 |
|---|---|
| 原 PR-local base | `7dae5f21c7ca401e660450d437e60ba566218da8` |
| Grok 原 head | `4e176e830b691269cc72d021ce7e1bc0b167d621` |
| 普通 merge 的 main | `eda91c8593f0795278f7f16ff8b93d147a4fdaa7` |
| 目前產品 source S | `06e492d6d59c1ab2c5505e5300f7542f7063468d` |
| 準備 evidence head E | `07615668c110684826390990cd2d6134eb6025fd` |
| 最新審查 handoff | `d193946b8e0fbda024d3b134c4851e9393a43d38` |
| 替代 head／正文 | `codex/geo324-faces-20261024`／`codex/geo324-faces-20261024-prbody` |

main→S 恰三檔、121+/2-；兩個 leaf 保原 Grok bytes，`run_all.expected.json` 只聯集 `py:test_geometry_host_sources`39→45，其餘 metadata 與 main 全等。SSOT／決策佇列 blob 精確同 main。沒有 rebase／force push／PR merge。新 train 尚未合流，正式 final SHA 未固定，不能用本輪準備冒稱列車已驗收。

原模組45是目前 expected 契約：五支公開行為方法覆蓋柱／樑 missing、null/object、非dict、int/list feature，另三 predicate controls 保原斷言。原作者 Windows/Python3.14 的45 tests exit0是歷史結果，本輪沒有重跑，不是 S 的綠燈。原 Actions39721803849七 job零步驟 failure仍只記環境。

唯一 current-state 驗收矩陣如下。`null` 表示本輪沒有原 exit／受驗 execution SHA，並非允許 skip；目前沒有新增 skip 豁免。

| Gate | 目前結果 | 原 exit | execution SHA |
|---|---|---|---|
| registry-list | 未執行 | `null` | `null` |
| native-and-full-expected | 未執行 | `null` | `null` |
| canvas | 未執行 | `null` | `null` |
| assembly | 未執行 | `null` | `null` |
| documents | 未執行 | `null` | `null` |
| grid | 未執行 | `null` | `null` |
| space | 未執行 | `null` | `null` |
| timber | 未執行 | `null` | `null` |
| affected-importers | 未執行 | `null` | `null` |
| predicate-list | 未執行 | `null` | `null` |
| predicate-dict | 未執行 | `null` | `null` |
| predicate-feature | 未執行 | `null` | `null` |
| mutation-check | 未執行 | `null` | `null` |
| architecture-contract | 未執行 | `null` | `null` |
| architecture-tests | 未執行 | `null` | `null` |
| product-architecture-tests | 未執行 | `null` | `null` |

三 predicate 的外部補充工具只完成AST檢查，待同一正式source逐案跑原method的0/1/0並封完整streams。原內建control最後只重跑第一個restored，不能靠其綠燈補造另外兩案restored輸出。feature=int被後段集合檢查擋住；同方法的list feature才殺得掉feature型別predicate。

準備／merge原件在 `evidence/geo324-final-06e492d6/`：原命令、exit、完整stdout/stderr、環境、SHA、工具與manifest一併保留。source merge／一般push／ls-remote均0；只物化約1MiB必要source，沒有build或Chrome。環境 PATH修正後 Chrome156.0.8078.47／Node24.19.0真版本命令均0；最初PATH缺Chrome的失敗與薄checkout漏feedback_store的read-only失敗均保，修正只補PATH／既有依賴物化，沒有改產品。

下一步由root排新train一般合流及重測槽，固定可解析final SHA，跑原full native＋expected／六browser／importers／mutation check及架構三條；過期帳本與四檔架構產物依原規則處理，不放寬判準、不全帳本重產於本準備回合。所有動態與p88_priority對抗審仍pending，不宣稱可合併。root依handoff/pr-requests/README送建立替代draft PR請求。
