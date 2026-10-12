# K2a 歷史正常集合縮編：政策落地驗收交接

P-064已定並在#201實作；產品/測試受測d9c5aef86274045a46aa4d40ba1b0f58a51582e8。原d8a曾通過定向/全量，但後依最新I68限縮集合來源，兩者收據不得混用；原25f3506/6e3c35c歷史收據維持原範圍。
原件：tests/evidence/k2a-p064-20261012/；場景在tests/k2a_zip_browser.cjs normalConfirm：真來源1/2、有效編輯來源2的另一草稿、capacity基底1且refs=[]，無lost/orphan。例外來源由既有grid-editor-drafts/1 schema判定，不存新可信旗標；第一份超大單份仍拒。
| 反例 raw草稿bytes | 完整single封套bytes（+117） | 目前新接納 | 目前歷史集合移除另一份／確認 | 裁決後須觀察 |
|---|---|---|---|---|
| 130955 | 131072 | 接受 | 捨棄/確認、完整World/草稿UndoRedo、正常/13獨立服務冷讀通過 | 正控制保持全部raw/id/pin/refs逐字不變 |
| 130956 | 131073 | 可加入多份集合；首份單份拒 | 原集合縮成一份成功、存/17、冷讀raw不變 | 縮至130955後保存/13，新瀏覽器冷讀一致 |
| 131072 | 131189 | 同上；內層/集合上限不放寬 | 同上 | 同上；不截raw，不給一般payload容量信用 |
P-064由#199原writer寫入I68，head d95e5c35c66e9d42ea46f982dde37368468b6583已交sync/check/原41原件；本線已讀diff，尚未merge。D56/R54原文不改；P059與P064各守原適用範圍，依完整UTF-8封套實算，不把此夾具+117當通用raw閾值。
落地案例1：對兩個歷史大份先真ZIP保存/冷讀，再分別普通捨棄另一份與真preview/confirm；檢查指定draftId清除、剩餘raw逐字、完整World與附件同一步Undo/Redo，以及再次保存/另一服務冷讀的表示與能力。
落地案例2：取消/過期token/拒絕/遺失回覆沿G07/G08，沒有部分World、附件或history寫入；prepare及begin候選容量守門維持。
落地案例3：保留新正常接納130956/131072拒、130955正例；依裁決精確界線寫+1真內容/UTF-8跳脫負例，其他附件/完整manifest上限不得因遷移獲一般豁免。
落地案例4：原/13、原6a/17、孤兒/永久lost保存冷讀、同id不復活、純移除lost拒、未知schema/剝能力/降版負例全部回歸；遷移不得改這些既定語意。
指定變異：移除政策的精確邊界/歷史適用條件、改raw、錯能力/表示、只改World不清指定草稿、漏Undo/Redo附件、去prepare或begin預驗；逐個編譯/語法過後由具名斷言驗紅、還原驗綠，錯誤/skip/timeout不算killed。
交付收據：凍結產品與測試來源/完整SHA，原命令、父exit、raw輸出、runtime/session/live binary/sidecar及前後hash；新測試登記runner，expected由原流程產生；核心ledger依來源、include閉包、變異、裁判（run_tests.py及TESTS引用夾具）四組指紋判斷，任一變動須重跑mutate.py更新受影響結果；四組皆同且帳本有效才可沿用，--check只驗新鮮度、不算重跑。本次純文件修正無新增核心變異覆蓋。
#199原writer負責P063/P064與唯一閱讀器/revision/LF hash/相容；#199合併後本線用merge commit承接，不另開競寫。當前#201產品驗收不取代最終條文整合與正式七job。
GEO-219：無新入口；#201 base維持axiom/adopt-drafts-topology-k2a-20261011，B2最終整合/full CDP/正式七job仍未驗。CI 受帳號計費阻擋,正式合併裁判由本機 WSL 收據提供。未跑WSL，不合併、不force push、不關PR。
