# K3 對抗審查要點與主迴圈裁決(2026-10-09 17:05)

審查員(opus)結論:**須先改**。審查員角色規則不得寫檔,本檔由主迴圈照錄。
狀態:**修訂暫停**——把修訂指示送回原起草 agent 時被 auto mode 權限分類器拒絕(無說明);主迴圈未以其他方式繞過,待使用者決定是否放行。

## 須先改 → 裁決(依授權 L,暫定)
- F1 歷史群組內每行都直接改正式 World(current_geometry.c:4066-4072;confirm 可在群組內 transactions.inc:551;公理層.md:572)→ 每一筆成功的原生變更都算提交,history-end 不算;R⟨K3-1⟩ 刪「歷史群組結束」;L-04 期望反轉。
- F2 組構批次 delete/create-instance 重用最小空號(assembly_generation.inc:105-115),鍵比對誤判延續,違反 D34(公理層.md:497)→ 首版把組構生成角材排除在身分帳與證據目標外。
- F3 漏列 eng_definition_hash(engineering_bridge.inc:6-16)→ 以去身分 dump 計算,加入 L-12;補 source-inspector.js:199、model-update-app.js:194 影響。
- F4 原生只有 g_definition_revision,world_definitions_equal 只略過 canvas_pos(current_geometry.c:3808-3815)→ 改採 Q13-B「啟用即讓預覽過期」,擴充 L-16 涵蓋工程/參數/組構/斷面批次預覽與場景匯入。
- F5 至少 11 處提交點,漏結算會讓存檔重開被整份拒絕 → 橋接器指令分派處單一結算點;dump/保存遇不完整身分帳一律拒絕。
- F6 條號建議與 PF-0 r1 衝突 → 全用佔位,寫入時配號。
- F7 與 K2b D⟨K2b-4⟩ 身分分類互斥 → K2b 補 (f) 類「存在期記號:不跨專案,匯入一律新配」(已通知 K2b 起草者)。
- F8 E-06 照字面做不到(current_geometry.c:11609-11613)→ 改寫。

## 範圍縮減(採審查建議)
- K3-Q15 改採 B:record.input.base_scene 保持去身分,另存各根物件身分引用;模型雜湊不改,保存格式號不整批改號。
- 切分:K3-L(七種鍵,排除組構生成角材;建模只在建立模型時去身分)→ K3-48 → K3-44(Q15-B)。

## 僅記錄(修訂時一併寫入)
測試宿主禁止重用區段;檔案複製後 projectId 相同屬共享存在期;D34 實例更新保留角材 id(assembly_generation.inc:111);「內容指紋」寫成 definitionFingerprint/valueFingerprint;桌面版 GDI(current_geometry.c:4772)不設區段 → 已啟用專案在桌面版無法新建物件(已知限制);F1b 新紀錄 base_scene 來自 load_base(model_update.py:396);I8a 第 596 行與第 587 行一起修;原生成本 ≤480 鍵×24B≈11.5KB/World。
