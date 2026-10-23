# P88 原生 rAF 三階段原件對抗審

固定來源 `3d681636902371ecc528b20f51eea33e272581c9` 的本次預列受控反證成立：原 test 為 **0／1／0**，原 driver／outer／launcher 都為0。沒有重抽或把先前無效的1／1／1改標綠。

| 階段 | outer／workflow／Node | P88原checks | 實際記憶體P88 | 本次目標真mousePressed y |
|---|---|---:|---|---:|
| fixed | 0／0／0 | 143，完整P88 | F原8106476b | 602.5 |
| withdrawn | 1／1／1 | 99，原focus裁判停止 | 只撤回c4725960 | 627.5 |
| restored | 0／0／0 | 143，完整P88 | 同F原8106476b | 602.5 |

三階段都是明列的P88-only partial，原golden Compare未跑；不冒正式grid或canvas。原完整P88 check行、精確focus predicate、25秒共同時限及原workflow時限保留。撤回fatal逐字是 `document.activeElement===document.querySelector("#refGuideMode")` 的原UI condition timeout；不是工具前提、loader、crash、CI或watchdog紅，其他failedAssertions為0。

原真source-inspect回覆經成功query106→paintQuery→原renderer；app8758原native rAF callback由native dispatcher呼叫一次、原this/args/guard保留。三階段選定原量測各只求值一次，均得到627.5且真hit mode；callback完成後舊點真hit ratio label，原p沒有改寫地回到原CDP呼叫。withdrawn的pressed/released均真的使用舊627.5，trusted label點擊轉焦點ratio；fixed/restored在任何本次目標pointer之前重新穩定/量測，第一次pointer即602.5命中mode，並非錯點後重點擊。

withdrawn的callback完成8.5ms後才pointerdown，down/up約2.8ms內各pointer/mouse capture及bubble、click的DOM快照同parent25、mode y580.5、ratio y643.4375。fixed/restored所記第一個目標輸入快照也一致。這支持本受控錯點來自已過期的量測座標，沒有觀測到該按壓區間內的位移。

**證據界線仍保留。** 本次唯讀量測安排在原native rAF callback入口前；沒有Paint、compositor或連續screenframe，不能證中間幾何從未可見，也不能宣稱所有真人互動皆安全。原F13自然1／0／0沒有pointertrace，不能把本query指認為當次自然紅唯一根因。若未來真畫面／輸入證明產品可見互動期間有錯誤位移，仍需修產品並依影響固定新F重驗；本件不是免除產品問題的證明。

已獨立核三份原stdout/stderr/command與workflow receipt hash、原source/index前後clean、實際單檔記憶體variant、相同preload/app/callback與tool/generated snapshot hashes；沒有重跑測試或改來源。三份大trace只作低記憶體原JSON投影，保原driver的trace SHA，不另重hash大檔；原封包的完整reopen驗證由publisher另列，不能以本peer代替。
