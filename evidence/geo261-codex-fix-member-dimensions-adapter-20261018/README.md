# 02：分離 H 成員尺寸來源組裝

受測修正為 `48fdbeaaa5c43b96a50f9406ae6429dfcb58c9fb`，基底 `e9c1509cf89e6f35d298743ec5e3368370316cf7`，分支 `codex/geo261-fix-member-dimensions-adapter-20261018`。修後及恢復兩輪各 **40/40、零 error／skip**；撤回修正後只跑兩個 boundary 測試，原禁迴圈斷言再度轉紅。沒有修改或放寬任何測試斷言。

分類為**預期過時：舊薄函式形狀未承接後加的 H 來源組裝**。原 `reference_compute_timber` 在 W 策略抽離後要求只保留委派；後續 canonical source 尺寸材料化加進同函式，`for(field=0;field<2)` 命中原形狀守門。本修正把完整來源組裝區塊移至私有 H helper `app_member_reference_materialize_dimensions`，讓原薄函式在成功後繼續呼叫原 W compute／place。這不是 W 演算法回流，也沒有改變尺寸求值或放置規則。

## 四輪正式結果

| 階段 | SHA | 實際範圍／結果 | unittest 秒 | 外層秒 |
|---|---|---|---:|---:|
| 修前 | e9c1509c | 四模組 40 run：39 pass、1 failure | 32.519 | 32.762827 |
| 修後 | 48fdbeaa | 同四模組 40/40 | 29.200 | 29.453708 |
| 撤回 | bf0dbbe1 | 只跑 boundary 2 run：1 pass、1 failure | 0.007 | 0.164336 |
| 恢復 | 48fdbeaa | 同四模組 40/40 | 30.896 | 31.084750 |

四模組為 member_reference **11**、host_authority **18**、definition_sources **7**、assembly_graph_product **4**。兩次綠燈是同一 40 項重跑，不是 80 個不同測試。撤回只驗原 boundary，**沒有宣稱撤回也跑過 40 項**。

修前與撤回的唯一失敗同為 `MemberReferenceBoundary.test_actual_reference_and_main_consumers_delegate_the_policy`，原 line 56：

```text
self.assertNotRegex(actual, r"\b(?:for|while)\s*\(")
AssertionError: Regex matched: 'for('
```

原文見 [修前](before/command.stderr)、[修後](after/command.stderr)、[撤回](withdrawn/command.stderr)、[恢復](restored/command.stderr)；精確 argv、退出碼與時間各在同目錄 receipt／process。四輪均無 timeout、interruption、launch／setup error；紅燈是原具名斷言，非編譯失敗或 crash。

撤回提交只將本次產品 hunk 精確還原，`references.inc` 的 bytes 回到基底；原測試全保留。這個負控證明原函式責任邊界守門會偵測修正被拿掉，不能當成新增幾何語義的證明。既有原生 guard controls 與真 bridge 原子交易測試在各自 unittest 方法內完成驗證；本報告只公開原 unittest 輸出，**沒有額外宣稱取得未公開的逐子程序 stdout／stderr 或暫存 binary**。

## 保留的程式與契約

固定 Git bytes 與補丁已獨立重建核對：原 `references.inc:595–612` 的 **1192-byte** 尺寸組裝區塊逐 byte 保留，原 :613 的 **281-byte** W compute／place 尾段也逐 byte 不變。原 `reference_place_geometry` 完整保留；四個測試檔與 W 模組未改。[產品差異](source-final.patch)、[撤回差異](withdrawn-commit.patch)與[區塊身份](static-block-review.json)均附原件。

`use_current_values`、saved dimensions、wanted 的短路順序不變；owned 查詢與尺寸 provider 失敗仍拒絕，owned 雙值取得成功後才寫入 A／B。非 owned 分支仍先 bind engineering，再按 field 0 → field 1 求值及寫入；若第二欄失敗，第一欄已寫入的部分候選狀態保留原行為。任何材料化失敗由 helper 回傳 false，薄函式立即 false，W compute／place 不會提前執行。沒有新增回滾、快取或另一套來源演算法。

依據為固定 e9 的 `公理層.md:75` H 組裝契約、I9（:1214–1223）的依賴與終態驗證，以及 `geometry-core/domain-decoupling/PRODUCT-ARCHITECTURE.md:176–181` 所述 H adapter 消費 K/W facts、W 保留 policy。manifest 亦將 `references.inc` 登記為 H。`6ea2d3b5` 加入策略抽離及薄函式守門；`2ba81689` 加入 typed graph 尺寸迴圈；`138595e0` 讓 owned 查詢消費 canonical source。本題不需改條文。

詳細靜態理由見 [static-block-review.md](static-block-review.md)。該文件在 before 後形成，當時的「後續尚未核收」保留作時間界線；四輪最新結果以本表與 [manual-ledger.json](manual-ledger.json) 為準。原禁 `for/while`、compute-before-place、W 邊界與幾何斷言全保留。

## 身份、環境與未驗項

四輪共 **116 個 receipt-listed 原件**已逐 bytes／SHA 重核；各輪 HEAD、來源、status／diff 都穩定。區塊重建及控制流另經獨立第二讀；collector 只整理身份與人工判讀，不從 exit 自動生成 pass／kill。大型 source 清單與 recorder 程式保留外部，公開 receipt 記錄其精確身份；公開 payload 不能重新計算未公開來源清單。原暫存 native binaries 不在此封裝。

環境為 Debian GNU/Linux 13.6、Linux 6.18.55 x86_64、GCC Debian 14.2.0-19、Python 3.12.14、Node v24.19.0、Google Chrome 155.0.8059.84（另有 Chromium 154.0.8037.57）、child stack 16 MiB；原版本輸出各輪保留。本題沒有執行瀏覽器。

此定向結果不取代最終合流來源的全量非瀏覽器、六瀏覽器、完整 mutation、產品架構與 census 驗收，也不宣稱效能改善。`test_assembly_candidate_impact` 未列入本題四模組；e64 曾有另一題 guide cache 紅燈，後已由 integration 的 `1987af50` 修正，不能把舊紅當作 e9 現況。最終整合仍須實跑，沒有刪除此驗收項。
