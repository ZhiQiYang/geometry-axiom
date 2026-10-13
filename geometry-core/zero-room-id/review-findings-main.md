# K2b 對抗審查結論(2026-10-10,opus;審查員規則不得寫檔,由主迴圈照錄)

結論:**須先改**(無阻擋)。最小修改 S1–S10 各改一句條文或一段契約,外加 IM/PC 驗收;改完即可寫入並實作。狀態:未啟動修訂,待使用者決定。

## 須先改
- S1 roomId 守門與 PC03/I⟨K2b-3⟩「過期仍可保存」矛盾(featureProposal 每次寫入驗整份 envelope,reference-workspace.js:433-440)→ roomId 只驗格式,存在與否交給 roomsPin 判過期。
- S2 匯入規格改名「新名稱須未被使用」會撞同批匯入名稱,D6b 允許重宣告 → 有效值靜默改變(反例:來源 柱寬=27、柱寬2=40,目標 柱寬=30,改名為柱寬2)→ 改為「目標與本次匯入全部名稱都未使用」,加 IM 驗收。
- S3 保存前同步失敗時保存行為未定義(12 列×原字串可超 1 MiB;manifest 共用 8 MiB,project-store.js:34、503);暫停先釋放編輯器再寫,失敗無法回到 active 前狀態 → 保存照常、草稿不寫並明確提示;暫停先驗容量再釋放。
- S4 新分析靜默覆蓋另一錨點已保存草稿(確認框只看記憶 session,room-collection-workspace.js:370)→ 有附件時開始新分析須明選「捨棄已保存候選」。
- S5 暫停/保存前同步讓自己的 session 立刻失效(candidateStamp 含 revision 與 undo 頂端,reference-workspace.js:148-150、room-collection-workspace.js:154;setFeatureAttachment 會 history.push + dirty(),:488-489)→ 定受控續用規則(寫入成功後重新蓋章)或明定 session 退休改由附件恢復。
- S6 保存前同步做不到同步(roomsPin 要非同步讀原生 D3 再 SHA-256;save() 同步呼叫 flush,:1516),且漏了 :1381、:1440、:1464 三條路徑 → pins 在分析與接受時算好快取;flush 只在 session 新鮮時沿用;列出全部 flush 呼叫點。
- S7 匯入確認走 REST,但回執與 history.observe 只走 /api(先例 assembly-confirm,assembly-workspace.js:286、serve.py:176-203);reference-workspace.js:418-419 的 dirty()/notifySceneChange 也要加 definition-import-confirm;§3「兩 PR 只在 project-store.js 重疊」不成立 → confirm/cancel 改走 /api 橋接指令,§2.7 補列 reference-workspace.js,§3 改寫。
- S8 D⟨K2b-2⟩「唯一共同基準」與保留圖頁 P 衝突(既有 adopt 會移除 P,reference-workspace.js:552;MR03)→ 明寫 legacy 圖頁不是共享基準、不受 SourcePlane 約束。
- S9 I⟨K2b-1⟩ 狀態轉換與現行程式不一致(未配對 line confirm 把全部房間標需重新關聯,project-store.js:901-905)→ 改為「需複核,或身分無法確認時需重新關聯」。
- S10 身分分類漏 D28 面套用穩定字串 id(ENGINEERING-SPEC-API.md:15);R⟨K2b-3⟩ 未處理 `surface N` 要求 boundary 與 placement 同號(web_bridge.c:409-462)→ 補 D28 分類;§四改為「其他型別配號另案」。

## 僅記錄
- 起草者自承 12 點中 1、2、3、5、6、7、8、9、10、12 不阻擋;11 併入 S9。
- 配號(IM01/05/06/14 對 parameters.inc:305-315 與 WORLD_NEXT_ID)正確;規則不引用卡片/規格/材料,閉包無循環或懸空。
- 零房交易可行(grouped、history-begin/abort、undo 還原附件已有機制),需把 grouped 白名單擴到 room-candidates。
- 小錯:room-outline-candidate/1 無 validator,實際項目為 {edge,length,kind};「過期仍可保存」出自 K2a 的 D⟨K2a-2⟩ 非 D⟨K2a-1⟩。
