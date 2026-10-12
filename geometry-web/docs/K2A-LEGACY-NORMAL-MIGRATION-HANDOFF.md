# K2a 歷史正常集合縮編：政策落地驗收交接

依 dot 6119066258；這是待裁決的驗收清單，不是新政策、產品完成或本輪實跑。既有產品/收據 head：fe927abf0c9bdc64e39b02dbe6d845edda51d1bd；真 browser 受測25f3506c，aggregate受測6e3c35c2，範圍不得混用。
原件：tests/evidence/k2a-normal-shrink-20261012/{README.md,zip-browser.log,results.json,runall-parent.json}；指定場景在 tests/k2a_zip_browser.cjs 的 normalConfirm：兩個真原生來源1/2、有效編輯來源2的另一草稿、capacity基底1且refs=[]，無lost/orphan。
| 反例 raw草稿bytes | 完整single封套bytes（+117） | 目前新接納 | 目前歷史集合移除另一份／確認 | 裁決後須觀察 |
|---|---|---|---|---|
| 130955 | 131072 | 接受 | 確認、原生Undo/Redo、正常/13獨立服務冷讀已驗；普通捨棄/局部歷史已VM驗 | 正控制繼續成功，全部raw/id/pin/refs及完整World逐字保留 |
| 130956 | 131073 | 拒絕 | 普通捨棄仍拒；真preview後prepare拒，未改World/草稿/history | 按裁定的有界表示/遷移合法縮編，不再只以事前拒絕充完成 |
| 131072 | 131189 | 拒絕 | 同上 | 同上；不得擴成一般payload信用、截字串或暗留未獲准的正常singleton/17 |
原公理owner須交：承接分支與完整head、裁決位置、適用歷史包與辨識/保存重開規則、精確bytes界線及拒絕條件，逐項說明與I68正常單份及D56/R54 raw/交易一致性如何對齊；既有P059只涵蓋自動lost/orphan/必要升版，不自行擴用。
落地案例1：對兩個歷史大份先真ZIP保存/冷讀，再分別普通捨棄另一份與真preview/confirm；檢查指定draftId清除、剩餘raw逐字、完整World與附件同一步Undo/Redo，以及再次保存/另一服務冷讀的表示與能力。
落地案例2：取消/過期token/拒絕/遺失回覆沿G07/G08，沒有部分World、附件或history寫入；prepare及begin候選容量守門維持。
落地案例3：保留新正常接納130956/131072拒、130955正例；依裁決精確界線寫+1真內容/UTF-8跳脫負例，其他附件/完整manifest上限不得因遷移獲一般豁免。
落地案例4：原/13、原6a/17、孤兒/永久lost保存冷讀、同id不復活、純移除lost拒、未知schema/剝能力/降版負例全部回歸；遷移不得改這些既定語意。
指定變異：移除政策的精確邊界/歷史適用條件、改raw、錯能力/表示、只改World不清指定草稿、漏Undo/Redo附件、去prepare或begin預驗；逐個編譯/語法過後由具名斷言驗紅、還原驗綠，錯誤/skip/timeout不算killed。
交付收據：凍結產品與測試來源/完整SHA，原命令、父exit、raw輸出、runtime/session/live binary/sidecar及前後hash；新測試登記runner，expected由原流程產生；核心ledger依來源、include閉包、變異、裁判（run_tests.py及TESTS引用夾具）四組指紋判斷，任一變動須重跑mutate.py更新受影響結果；四組皆同且帳本有效才可沿用，--check只驗新鮮度、不算重跑。本次純文件修正無新增核心變異覆蓋。
本線可準備/實作已定政策的非受保護區段；公理/白話/唯一閱讀器仍由原writer修文、sync→check→原41、來源revision/LF hash/相容閘同批交付，未取得承接與裁決前不另開競寫。
GEO-219：無新入口；#201 base維持axiom/adopt-drafts-topology-k2a-20261011，B2最終整合/full CDP/正式七job仍未驗。CI 受帳號計費阻擋,正式合併裁判由本機 WSL 收據提供。未跑WSL，不合併、不force push、不關PR。
