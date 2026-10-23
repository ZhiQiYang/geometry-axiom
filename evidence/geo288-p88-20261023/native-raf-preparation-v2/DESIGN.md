# P88 原生 scroll-restore rAF 交錯反證設計（尚未執行）

這是以新觀測提出的另一個明列排程，不覆蓋前一組未成立的 query-release 診斷。基準固定公開 F `3d681636902371ecc528b20f51eea33e272581c9`；三個階段只預列一次 fixed／withdrawn／restored，撤回階段僅在記憶體載入原 P88 `c4725960…`，fixed／restored 使用 F 原件 `8106476b…`。原產品、helper、斷言、golden、時限不變。

新依據是三個原 trace 均出現：真 after-query 的 `paintQuery → renderFaceInspector` 重建 inspector；renderer return 時 parent.scrollTop 為 0、mode 中心 y=627.5；原 app.js 的 rAF callback 依原 seq／bid／scroll guards 恢復 parent.scrollTop=25、mode 中心 y=602.5。舊自然紅記錄的 click y=627.5 與這個短窗相符，但尚未證明就是當次自然根因。

採用「把原量測安排在真 native callback 的入口前」；**不暫存後手動 invoke callback、不凍結整個 70ms、也不重新排另一個 rAF**：

1. 保留先前原 `#refGuideCreate` 量測後 arm 的單一 context/token，以及真 query line102 的原 parsed response object barrier。原 makeCtl 的 scroll／sleep70 先原樣執行。
2. 第一個合資格 `#refGuideMode` 原 measure eval 到達時，外部 wrapper 把**原 expression 的單次求值 thunk**交給 pending measurement，再釋放真 held response。此時不預先執行 expression，不改內容／回傳值。
3. 只辨識這次真 `paintQuery` renderer 內 app.js 原 scroll-restore callsite 登錄的 rAF；同時核 callback.toString() 與固定 F 中獨一 callback 原文字完全相等。其他 rAF 原樣委派。目標仍由原 native requestAnimationFrame 登錄與呼叫，回傳原 native request ID；cancel 也原樣委派，若目標被取消則 proof 前提失敗。
4. native dispatcher 真正呼叫該 wrapper 時：先求值一次原 measure expression；接著**同步、立即** `Reflect.apply(originalCallback, this, nativeArgs)`，不插 await、不改 this／timestamp args／原回傳／原 throw。原 callback 一次、原 guard、原寫入全部自行執行。即使量測或觀測出錯，也必須讓原 callback 照原樣執行；錯誤另分類，不能當反證。
5. callback 完成後才讓原 measure 的 CDP 回傳 resolve。記錄 callback 登錄 stack、native id／entry／this／args、renderer序號、query token、量測前 node／rect／scroll、原 callback 後 node／rect／scroll與舊點 elementFromPoint。必須真的看到原量測命中 mode，而原 callback 後舊點命中真 ratio label/select；不手改 scroll／rect／focus／值。
6. 原後續控制流程繼續：withdrawn 使用原座標發真 CDP mouse，必須原 exact-focus predicate 的原25秒逾時 exit1，不能以工具前提紅、transport／watchdog逾時或crash代替；fixed／restored 以同一原量測起步，接著其候選 probe 重新穩定／量測，真 click 命中 mode 並完成原 P88。段數由固定F的原golden讀取（目前143），不另設門檻。三階段同一排程控制；全部收齊。

守門與限制：

- 只有一個預先宣告的 query／renderer／callback／measure token；缺件、被取消、重複登錄、callback不符、context改變、原 guard 未造成預期位移，均工具紅／未證，不能人工補救或重抽。
- 原函式文字不改，只用外部依賴／native callback wrapper；原 source/index/head 必須全程乾淨。正典、公理、決策檔不動。
- 只控制原唯讀量測相對於原 callback 的順序，保 callback 自身 native dispatch、this／args、once/cancel；同步量測與記錄有非零開銷，不宣稱無觀測擾動。
- 若原 callback throw，保留原 throw，且診斷不成立；觀測錯誤不得覆蓋原例外。wrapper ownership 不同時 cleanup 不強蓋，記完整性錯誤。
- 缺 native callback 的工具等待最多沿原25秒，不能延長原 focus 或 workflow 限制。正式 canvas 三輪完全不注入這些工具；此工具只在它們收齊、root排程准許後執行。
- 這可證明一個真 renderer／原 rAF 的有效交錯會使原測試用舊座標，但即使0/1/0成立，仍不能回填先前無pointer trace的自然紅一定來自同一query。
