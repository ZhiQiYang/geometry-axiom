# #318 列車：Claude 雲端 session 接續收據（2026-10-23～24）

分支 `claude/sharp-bohr-9flfm7`，PR #337（draft）。本目錄只收原始輸出；交接摘要見 PR #337 的交接留言。

## 提交（依序）

| 提交 | 內容 |
| --- | --- |
| 8ce7c6bf | 閱讀 A 的 RC 面改量「還沒貼料的連續一段」；rc_through_reflex 的 I19 移到歷史政策負控；oracle／原生正反例、控制 rc-lining、突變 M151 |
| 1dcb1f31 | oracle README：例外三不適用 custom 併料 |
| 964e914d | 一般 merge main 48b45265；架構報告兩邊段落、收據保留本線版本；更新 5 個過期 exclusion LF digest |
| 074a004a | 決策佇列記 RC 面量法；正典閱讀器同步（只多 M151） |
| 0fd8cacf | 公理層.md 補 RC 面量法兩句；補登記 pr318-reading-a、pr318-rc-run 兩筆 POST_APPROVAL_REVISIONS；閱讀器同步 |
| 3cbeb759 | 建模執行器釘 0fd8cacf（LF c66c48e5…）；a00ba9e9 進 PRE_READING_A_AXIOM_VERSIONS 與 CARD_REFERENCE_AXIOM_VERSIONS |
| f7026c11 | run_axiom_mutations.py 的 exclusion LF digest（3cbeb759 漏更新） |
| f1f2e8d0 | test_geo261_mutation_migration 的突變對應表補 M151（8ce7c6bf 漏登記） |

## 收據

| 檔案 | 跑在哪個樹 | 結果 |
| --- | --- | --- |
| native/run_all-f7026c11.* 與 run_all-logs-f7026c11.tar.gz | f7026c11，`ulimit -s 16384`（同 CI native job） | exit 1，4122 秒；230 項中 mutation:check FAIL（帳本過期）；有計數的 5309 個測試：5305 過、3 失敗、1 允許 skip（Windows GDI） |
| native/INVALID-stack8192-run_all-3cbeb759.out | 3cbeb759，預設 8 MB stack | 無效：沒照 CI 設 `ulimit -s 16384`，原生 World（約 4.7 MB）在 stack 上，大量 -11。保留原件，不當收據 |
| native/integrity-stack8192.out、integrity-stack16384.out | 同一個 integrity 執行檔 | 8 MB：segfault（139）；16 MB：432/432 通過 |
| native/native7.* | 8ce7c6bf 的原生來源（提交前同內容） | test_geo318_reading_a_native 7/7；12 個控制全部 0/1/0（含 rc-lining） |
| oracle/oracle_lining_proof.json | 8ce7c6bf 的 oracle | RC 面量法：建構端、檢查端撤回各自 0/1/0 |
| oracle/mutants-only.out、quick.out | 8ce7c6bf 的 oracle（之後 oracle 檔未再改） | 兩者 exit 0；quick 562 秒，39850 次建構失敗 0、528／1056 凍結正例全 buildable、579×8=4632 全可施工 |
| golden/prove_golden_witness-074a004a | 074a004a | exits 0/1/0，passed |
| golden/make_golden-byte-compare.sha256 | 074a004a | 獨立重產與 oracle-golden.json 雜湊相同 |
| reader/* | 074a004a；*-0fd8cacf* 為 0fd8cacf | sync 0、--check 0、test_axiom_reader 51/51（before-sync 檔是加 M151 後、同步前的 6 個預期失敗） |
| architecture/*-f7026c11.* | f7026c11 | architecture_contract 0 diagnostics；test_architecture_contract 0；test_product_architecture 18/18 |
| adoption-modeling/test_domain_decoupling_adoption-074a004a-RED.out | 074a004a | 紅：本線先前寫入的閱讀 A 條文未登記（0fd8cacf 修） |
| adoption-modeling/*-3cbeb759.* | 3cbeb759 | adoption 15/15；model compatibility 44/44；§7 V01–V05 killed、exit 0 |
| q318-1-cli/* | 3cbeb759 的 core | Q318-1：兩種放置順序都拒絕（exits.txt），見 issue #335 |
| ledger/mutate-check-*.out | ae74e51b（改動前）與 8ce7c6bf | 兩者都是 107 stale；8ce7c6bf 多出未跑的 M151 |

## f7026c11 完整 native 的失敗

0. `mutation:check`：全突變帳本過期（107 stale、M140–M151 unrun），要在最終共同來源上重產，不是測試斷言失敗。
1. `py:test_geo261_mutation_migration`：M151 沒登記在突變對應表。本 session 的漏失，f1f2e8d0 修正，該套件在 `ulimit -s 16384` 下 15/15。
2. `py:test_geo261_wood_contact_world` 的 `free-end` 控制：錨點 `||face->fixity==WOOD_STOP_FREE` 在 contact_world.c 出現 3 次，控制要求恰好 1 次。改動前的 #318（9c534879）同樣 3 次、同樣失敗，是閱讀 A 原實作帶進來的，未修。
3. `py:test_geo261_load_residual` 的 `test_cross_consumer_mutant_reports_missing_dependency`：預期 `ASSERT:cross-consumer-placement-edge-missing`，實得 `ASSERT:cross-consumer-footprint-edge-missing`。在 9c534879 上同樣失敗，未修。

f1f2e8d0 之後沒有重跑完整 native，只重跑了受影響的套件。
