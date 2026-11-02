# #343 monotonic sort 正式驗收

產品與實際執行來源：`aa16e73d6e1f2965e0a911581e2a545aaaf66870`，普通單親接在 U `ca7838e0f4950452b9befcf40899d606db9b81fa`。分支 `codex/train337-monotonic-sort-20261024` 已正常推送。

三個原 suite 全部退出 0：wood-contact 13/13、contact-sources 15/15、reading-A 7/7，共 35 個方法，零跳過。332 次原編譯／連結全部退出 0；外層、subreaper、driver 都退出 0，214 個來源檔案及 HEAD 在執行前後相同且乾淨。

整段優化撤回／恢復的實測 `contact_order` 呼叫為 128／896／128，原生程序退出碼為 0／1／0；撤回時精確輸出 `ASSERT:monotonic-linear-order-lookups`。128 面來自 64 個成員事實，另保兩個 RC 前綴，計數只含成員排序區間。三版本的十組語意案例全部正常通過。

四個細部控制各正常退出 0／1／0：漏判逆序與漏看最後一面均在 `monotonic-last-inversion-full-fields` 轉紅；截斷順序值在 `monotonic-full-uint64-fields` 轉紅；漏更新 previous 在 `monotonic-middle-inversion-full-fields` 轉紅。七個實際編譯的 included translation unit 在編譯前逐位元組保全。編譯失敗、crash 或 timeout 沒有算成成功反證。

完整原件包有 4533 個 member、37,366,878 原始位元組，gzip 5,984,655 位元組，SHA256 `b6ddba01b0e15b7aa17cef1239508ed438da997c9650a132c596a44e0f0e1abe`。每個 member 已與原路徑逐位元組往返核對。原 source publisher R1 的 ignored-parent `git add` 退出 1 保留，R2 核對既有四個正確暫存檔後正常提交／推送，439 個 Git 指令皆退出 0。

尚未執行此來源的完整 native、六個 browser、帳本／架構重產與原 O2 效能量測。U 的歷史 N64/main `1.429347781620555 > 1.3` 仍是紅燈；此正式功能／工作量驗收不代替效能裁判。#341 四類成本驗收亦不由本案例代替。

下一步：主代理普通合入此已驗證來源，固定新的整合來源，再跑原效能裁判及最終全專案驗收。此線沒有合併 PR、force push、修改公理層或決策佇列。

狀態：定向驗收全綠；整體仍非 READY-TO-MERGE。
