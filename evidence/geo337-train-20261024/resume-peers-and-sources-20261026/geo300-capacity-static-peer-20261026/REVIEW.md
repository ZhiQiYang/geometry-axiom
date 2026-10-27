# #300／#348 靜態成果對抗審查

結論：新版靜態報告可收進 evidence；審查 exit 0，沒有剩餘阻擋。這不是產品或容量驗收通過。

已獨立核對原112檔、新版115檔 manifest 與33組完整 capture 流。只有 REPORT.md 改字，原報告／manifest 保留，來源與原收據均未改。

四組撤回片段取自同一固定 F 的測試原件。全部反向後，兩個 C 檔逐 bytes 等於 #348 head；少撤任何一組都不相等。這只涵蓋兩個檔案，沒有執行 C 或證明效能收益。

H7 79、83 都是完全相同的140-byte四命令批次。兩次約600.11秒 TimeoutExpired，原 returncode 是 null，stdout/stderr 是 captured:false；未捕捉不等於空輸出，不能歸因 loadfile，也不能宣稱 history 已執行。

兩處初稿問題已定點修正：原 observer 已有例外部分輸出保存路徑，不需重造；1048是目前 #348 的 AST，歷史 F0f 同 DSL 會是1046，兩者都不是原失敗的四命令。原稿與初始 findings 均保留。

固定來源：F `cbf0fb621888596aa14ad5f2349b503e23b1b72d`；#348 `9a8584f57be7935604c3bad4c2481945a6ec3d9f`；歷史 H7 `0f695866c0ba12d2c70dfd7d40628d0fda0f905f`。

完整來源 pins、可／不可推論與兩份分項審查見 REVIEW.json。沒有 Git/API/產品/效能重跑，沒有修改 collector 或 gate，沒有 READY-TO-MERGE 宣告。
