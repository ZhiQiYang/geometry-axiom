【ChatGPT 審查】PR #340 head 04959e0

## 阻擋
- **B1 — required integration 仍不可判讀。** 目前 head 的 [run 40058120400](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/40058120400) 結論為 failure；native 與六個 browser job 全紅，API 亦沒有 steps 可供定位。最小修正：在最終 head 取得可觀察且完整的 required run，或提供專案正式核准、綁定同一 source SHA 的等價驗收；在此之前不要標 READY-TO-MERGE。

## 須改
- 無新增項；若 head/base 再移動，正文的 current-state 矩陣需同步更新。

## 記錄
- 前次 **B1 已解除**：`evidence/geo340-convergence-175cee44/AGGREGATE_RESULT.json:3-23,45-66` 已綁定 source `175cee4`，selected aggregate exit 0、13/13、0 fail/skip，35 native commands 中 4 個預期 exit 1；timeouts、source before/after 與 global cache 狀態亦有記錄。
- 前次 **C1 已實質收斂**：`evidence/geo340-convergence-175cee44/PROGRESS.md:3-10` 明列一般 merge 到 L、後續 evidence 邊界、未重跑項與非 READY 狀態，未把舊 bfb 七階段改標新來源。
- 相對目前 base L 的產品/公理範圍沒有新增變更；本輪未發現測試本身的新語義錯誤。

**結論：改完 1 項可合併。**