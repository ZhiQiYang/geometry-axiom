# #318 actual H witness：2b9a24af 靜態補審

被審 source/evidence head：`2b9a24af6041eae2509ac3b3212aa7b57a9afaf6`，H fixture source commit `bba68351f89bd3448dcb1462c53c23288b46e3ca`。只讀這些 Git blobs 與前版 diff，**沒有編譯、執行測試或讀成動態綠燈**。

新 `tests/geo318_host_boundary_ends_harness.c` 真正 include `geometry-web/web_bridge.c`→`current_geometry.c`→`references.inc`。它先用正式 boundary/placement parser 建幾何，再明確手建兩個 already-placed 同向 boundary World facts，直接走 `reference_check_all`：要求核可 13 mm 階差的局部接觸、無舊 full-width issue；再把第二支移入 1 mm，要求實際 I11 collector 仍收集碰撞。這補上原九個 W harness 不會直接走到的 H 接線覆蓋。

M149 只把真正 H `wood_contact_end_support_check` delegate 改回原 hits/full-count 條件。targeted 原方法對 baseline 應 0、撤回應正常 1 且 `ASSERT:actual-host-collector-accepts-partial`、原 binary restored 0；`mutation_bridge.RESTORED` 已加對應正例。native methods 由5增7，runner expected也改7。以上是來源設計核對，不是已取得這組 0/1/0。

fixture 清楚標明不是 CLI place/load/rebuild 可達性見證；不得因此關閉先前循環初放次序 QUESTIONS。現階段沒有確立新靜態 blocker，正式執行仍須排除 compile failure/crash/缺 include 的假反證。

正式收據需要保留四檔重定位的 derived source 身份：`host_executable()` 用 read_text/write_text 將 currentC／references／web_bridge／harness 重定位，包含 currentC 的 CRLF→LF 正規化。應封存原 bytes/hash、重定位 bytes/hash、include 路徑轉換及 M149 baseline/withdrawn 差異。只能說撤回版相對這個 derived baseline 變一處，不能把四個 relocated source 稱為原 F 逐位元組未改的編譯輸入。原工作樹沒有因此被寫入。
