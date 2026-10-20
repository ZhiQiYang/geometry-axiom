【任務】修正 PR #323(codex/geo261-load-residual-20261020)審查找到的阻擋

接續你上一件工作,在同一個分支 `codex/geo261-load-residual-20261020`(head `aa66aced`)上繼續。commit 訊息以外,所有說明一律用繁體中文。
- 環境連不到 GitHub API。審查全文在 PR #323 的【Claude 審查】留言,你看不到,所以重點都寫在下面。
- 完成後:
  - 更新分支 `codex/geo261-load-residual-20261020-prbody` 的 `PR_BODY.md`;
  - 兩個分支都一般 push,不要 force push,不要合併。

## 阻擋(必修)
1. **兩個既有 harness 編不過。**
   - 原因:`geometry-app/native/world_validation.inc` 的 `app_world_validation_context` 改成兩個參數,`user` 也從 `World*` 改成 `AppValidationInputs*`。
   - 要改的舊呼叫:
     - `tests/geo261_world_validation_product_harness.c:35,49,54`(單參數呼叫);同檔 `:42,45` 把 `World*` 當 user 傳進 `app_validation_*`。
     - `tests/geo261_host_facts_authority_harness.c:269`(單參數呼叫);同檔 `:266-268` 同樣把 `World*` 當 user 傳。
   - 受影響的 suite:`py:test_geo261_wood_world_validation`、`py:test_geo261_host_facts_authority`。
   - 修好後這兩個 suite 要全綠。不准刪除或放寬它們的斷言;harness 原本要驗的事,改完後必須照樣驗到。
2. **`py:test_mutation_anchors` 轉紅。**
   - 原因:`reference_sources.inc:524` 把 `wood_definition_sources_placement(...)` 換成 `reference_member_anchor_read(...)` 之後,`tests/pf3_mutation_check.py:37` 的 host-identity 錨點出現 0 次。
   - 修法:依 `PF3-NATIVE.md` 的規則重新下錨,讓新錨點對準語意上相同的那道 host-identity 守門,並附上該工具自己的實跑收據(工具完整跑一次,原始輸出保存在證據目錄)。
3. **`py:test_geo261_contact_sources` 轉紅。**
   - 原因:`contact_sources.c:126` 改寫成 `collection_ref` 之後,`ContactSourcesBoundary` 的 subTest `feature-edge` 的錨點消失(`1 != 0`)。
   - 修法:
     - 重新下錨,讓 feature→collection 依賴邊的控制重新有牙。
     - 新加的 W `geo_eval_depend` 的 dependency kind 也要有突變保護:把 kind 改錯時必須轉紅。

## 須改
4. **「永不失效」突變在產品裡是等價突變。**
   - 原因:產品的 memo 都已零初始化(`reference_check_all` 的 `={0}`、`current_geometry.c:6221` 的 `inputs={0}`),拿掉 memset 對產品沒有影響。
   - 真正需要失效保證的是 `ReferenceEval.member_reads`,目前沒有任何突變覆蓋。請補具名突變,每個都必須讓測試以具名斷言轉紅:
     - 拿掉 `id==id` 比對;
     - 拿掉 anchor miss 時的 `footprint_valid=false`;
     - 拿掉 `placement==request->placement_id`;
     - pose 命中時把 kind 寫死(`reference_sources.inc:837` 附近);
     - cross-consumer 突變要涵蓋 pose depend(:837)與 W collection depend,不只原本的 3 處。
   - `has_edge` 一類的檢查要同時驗邊的 kind 與順序,不只驗「有沒有這條邊」。

## 建議
5. `reference_sources.inc:618` 的 contact footprint 命中路徑缺 `geo_eval_is_sealed` 守衛(其他三處都有)。請補上,讓 sealed 狀態下的行為與原本相同;若你判斷產品路徑到不了,也照樣補,並在 PR_BODY 寫明理由。

## 驗收
- **一定要跑完整 `ulimit -s 16384; python3 tests/run_all.py --build`,並交出結果。** 上一輪寫「執行中」卻沒交,這次不可以。
  - 預期只會紅兩項:
    - `mutation:check`:帳本過期,由維護者重產;
    - `py:test_product_architecture`:應為綠,若紅照實寫明原因,不要改清單。
  - 其他任何紅燈都要修好,或照實報告。
- 不變量 A/B/C(175 份場景:stdout 逐位元組相同、每次 seal 的完整圖序列相同、五個守門計數相同),在新 head 上重跑一次並更新證據。
- 每個新突變的失敗訊息原文都要放進證據。
- 效能:在新 head 用同樣的交錯量測重跑 N=16/32/48/64。
- 不准動:
  - `tests/mutants_results.json`;
  - `geometry-core/domain-decoupling/` 的架構清單與收據;
  - `公理層.md`、閱讀器;
  - BACKLOG.md、決策佇列.md。

## PR_BODY.md
- 逐項寫出第 1–5 項怎麼處理,並附 commit。
- 附完整 run_all 的合計列與每個紅燈的說明。
- 附新突變表(突變內容 → 失敗訊息原文)。
- 附更新後的效能表。
- 最後列「最不確定的地方」。
