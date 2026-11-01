# 來源靜讀後的收斂（動態未跑）

- `resolve_auto_span` 保留單一真正 production caller `app_member_reference_span`，移除先前為假設中的舊呼叫者留下、其實無呼叫的 private wrapper；恢復原有 member_reference 委派測試的原函式名，不放寬其斷言。currentC 保10518 CRLF、bareLF0。
- 裸 RC 拒絕沿用 SSOT I19 的 `V_CUT_PRIORITY` 碼。先前暫用 `V_BOUNDARY_END_RC` 會被原 member_reference clause mapper 的 `V_BOUNDARY` 分支誤歸 I20/R18，故修正碼與原因、保 I19 歸因。M150 將實際終點診斷改回錯碼，正常 `single-full-rc-span-refused` 斷言必紅；未執行，不冒 killed。
- 原 W 九控制、H M149 另列；加診斷控制後，M140–M150 共11全域定義，全部 unrun，native7方法含10 W/caller控制＋1 actual-H控制。完整帳本仍只由主代理在共同 final SHA 產一次。
- H derived variant 明列原raw/LF/semantic/relocated四hash，去掉variant-root後實際四檔編譯輸入只能references.inc有差異；正式執行必設repo外 `GEO318_ARTIFACT_DIR` 以保原／derived完整bytes。這些都是driver來源，尚未編譯。
