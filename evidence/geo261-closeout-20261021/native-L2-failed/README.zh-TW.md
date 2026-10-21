L2 native 完整正式驗收未通過，來源固定為 249571fe2477845d5330f6190dad965bf327f43b。來源公開分支由 root 管理；本輪實際在 detached 工作樹 /workspace/geo261-native-l2-249571fe2477-20261021 執行，沒有提交或修改產品／tests。

原始命令：timeout 2100 python3 tests/run_all.py --build。父環境明確移除 CC／PYTHONOPTIMIZE 與 registry binary overrides，stack 16 MiB；完整 env、argv、cwd 與外層 -c 原碼見 launcher/launch-dispatch.json、launcher/launcher-command.json 及 command.json。父 launcher 直接將 stdout/stderr 寫入 orchestrator.log，真 wait wrapper；wrapper 保留原 Linux subreaper 與 timeout 清理流程。沒有延長2100秒期限。

實際開始 2026-10-21T04:15:09.175935Z，結束 2026-10-21T04:45:15.783524Z，1806.607571323002 秒；全部224個suite完成，188個Python結果。5188項＝5185pass／2fail／1個允許GDI skip。timeout main child、wrapper、launcher、工具session四層真退出碼均為1；session78097，最後工具chunk4b2423。tool-observation.json是實際工具回傳的事後轉錄，不冒稱工具自動匯出。沒有重啟或重抽測試。

唯一失敗suite是 py:test_geo261_host_authority，18題中16pass／2fail。兩個具名失敗：

- HostAuthority.test_footprint_raw_anchor_bypass_fails_precise_actual_value_oracle：Control must hit once: host-footprint-actual-box-and-frame，預期1、實際0。
- HostAuthorityBoundary.test_harness_and_consumers_have_actual_value_paths_and_unique_controls：FOOTPRINT_ANCHOR出現次數預期1、實際0。

它們在 geometry-app/native/reference_sources.inc 找不到舊搜尋錨點。這是正式驗收失敗；該項突變自證尚未進入可計為 killed 的實際突變，不能算通過、crashed或假設 equivalent。最不確定的是修補後的見證是否仍能以原數值與病因判準擊殺相應錯誤，需後續候選實測；本包不作該結論。

完整600份suite raw共298700 bytes已逐bytes複製，原位置與hash/mtime在 suite-log-source-index.json。全部224預期數量匹配、missing suite log0、額外skip0。唯一允許skip為 test_gdi_contract.GdiContract.test_confirmed_failures_release_real_resources，理由 requires compiled Windows GDI contract harness；本機POSIX無Windows GDI資源，沒有將其說成通過。

同L2具名結果：architecture contract205／205、product architecture18／18、model-base replay6／6，皆無fail/skip；mutation:check為原inventory freshness exit0，沒有test級計數，不能當重跑78個突變。其餘6個exit-only入口按原 ok／exit語義核對。host_facts_authority27、wood_contact_world12、placement_definition15亦全部通過；這些不抵銷上述兩紅。

六個POSIX binary皆由本輪fresh初建，初建及結束各保存6 binary＋6 sidecar，初終bytes/hash/mtime完全相同。六個sidecar原文在 initial-build-fingerprints／final-build-fingerprints，binary原件留外部 native-binary-preservation，不混入可提交證據。原CLI tests/binaries.py status在初建／結束均exit0。browser使用自有geometry-runtime，沒有拷貝native binary給browser。source HEAD前後都是L2且clean。

前置／收據診斷也完整保留：首次外部前置在PID1/2/205/258的fd/exe權限檢查退出1，尚未建worktree或移global；root只核准精確PID＋UID＋starttime＋parent＋comm＋cmdline白名單，任何其他PermissionError仍fail。四個環境程序fd/exe未讀的限制沒有隱藏。其後一次/proc wrapper PID探針不可見而退出1，原因未定；另有真session仍running與最終真wait，沒有據此重啟。附加收集器首次誤把mutation:check的passed='-'當作'ok'而assert1，後依run_all.py原inventory note exit0語義更正；原正式verification與600raw完全未改。以上都不是新增產品測試結果。

依root後續排程，L2 Q38／controls／card／axiom沒有啟動；本包不聲稱完整7項或瀏覽器通過。四gate的138個錨點另有純靜態報告，沒有執行、不能抵銷native紅。後續新來源驗收必須另立收據，本輪不得改標來源。

本包沒有可執行binary或.py/.js工具。external-code-receipts中的.txt是本輪實際外部程序原碼收據，連同原路徑/hash映射保存，並非新增正式產品工具。原正式工具bytes未改。raw-source-index.json列每個copy的原件；artifact-index.json列本包除自身外的全部hash。此封裝只讀／複製已完成原件，沒有重跑產品。請使用者在 PR #288 保留這輪native未通過與尚未驗項；本包不提出合併請求。
