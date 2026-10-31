# #339 的全部留言(本機 Claude 以 gh 讀取,原文照錄)

- 同步時間:2026-10-24 08:42(台北)
- 標題:fix(GEO-261): reject malformed native snapshot face catalogs
- 狀態:open


---
### 2026-10-23T22:39:42Z ZhiQiYang

【ChatGPT 審查】PR #339 head 47fd6a7

### 阻擋
- B1｜`evidence/geo339-final-1f0ebd3e/PROGRESS.md:3` 與正文一致記載正式 11 列僅 3 PASS／1 RED／7 UNRUN；mutation check 為 exit 1（107 stale、13 unrun），完整 native/expected 與六 browser 未跑。最小修正：在固定最終產品來源重產完整帳本並跑完這七列，保存原命令、exit、來源 SHA 與輸出。
- B2｜同 head 的 Actions run [40032957675](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/40032957675) 七個 required jobs 全為 failure，jobs 無 runner/steps；目前沒有同 head 的 CI 接受證據。須先排除 workflow/環境失敗並取得可審核終態。
- B3｜產品 importer 142 項與三組 predicate 0/1/0 的 execution 是 S=`57b68014`，其後才 merge #340 成 M=`1f0ebd3e` 並刷新 F=`38da31bc`。正文也承認未在 F 重跑；因此這些結果不能證明目前組合來源。最小修正：在最終 F（或等價固定 head）重跑受影響 importer、predicate 撤回/恢復及 aggregate native，不能只移標舊 S 收據。

### 須改
- C1｜#324 仍開啟且承載相同 faces 修正；本 PR 又自稱替代線。合併前須明確標記唯一 owner/接替關係並關閉或重新定向被取代線，避免兩條重疊修正各自累積收據。
- C2｜PR 目前以尚未合併的 draft #340 分支為 base；#340 未驗收前，本 PR 也無法形成可獨立接受的主線變更。請在 #340 定案後重基底/更新比較，再重跑 B3。

### 記錄
- `model_sources.py:73-89` 對缺失、非 list、非 dict、非字串 feature 統一轉成既有 I32 分類，定向測試與逐 predicate 撤回設計合理；本輪未見該葉補丁本身的新語意錯誤。

結論：目前不可合併；維持 draft。

---
### 2026-10-24T00:39:36Z ZhiQiYang

【ChatGPT 審查】PR #339 head e9ee6d0

### 阻擋
- B1｜`evidence/geo339-review-followup-F38da/PROGRESS.md:3-9` 明載本次沒有 subject execution，正式 11 列仍 3 PASS／1 RED／7 UNRUN；帳本仍 stale/unrun，完整 native/expected 與六 browser 未跑。工具綁定與準備收據不能當驗收。最小修正：固定真正 final source，跑完原正式清單並保存同源終態。
- B2｜目前 head e9ee6d0 的 Actions run [40040764499](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/40040764499) 七個 required job仍全 failure，runner 空且 steps=[]；無同 head CI 接受證據。須先解除帳戶/支出限制後真跑，或走專案正式替代驗收。
- B3｜同檔 `:3-9`：142 importer 與三組 predicate 0/1/0 仍只屬 S=57b68014；合入 #340 後的 F=38da31bc 完全未重跑，aggregate native 亦 UNRUN。最小修正：在最終 F/head 重跑 142、三個獨立撤回/恢復及 aggregate，不能只更新工具 source/output/hash。

### 須改
- C1｜同檔 `:11` 雖宣告 #339 是唯一 owner、#324 凍結，但 #324 仍是 open draft；合併前請在可見 PR/issue 狀態完成正式接替（關閉、重新定向或清楚交叉連結），不能只在本 PR evidence 自述。
- C2｜base #340 仍為未驗收 draft；等 #340 定案後重基底/更新比較，再對最終組合來源執行 B1/B3。

### 記錄
- 新增 commit 只有審查回應與執行準備，沒有產品或測試變更；它誠實保留紅燈，但未修復前次任何技術阻擋。

結論：不建議合併；維持 draft。

