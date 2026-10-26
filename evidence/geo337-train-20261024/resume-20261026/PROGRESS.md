# 2026-10-26 原任務恢復：已完成原件回收

此分支只交付已執行的證據，沒有採用新帳本、改產品或移動列車分支；未標 READY-TO-MERGE。完整驗收尚未結束。

| 身分 | 完整 SHA／範圍 |
|---|---|
| 原始執行來源 S10 | `82c922a3941525d3a094ac0158bdc7dea57ea360` |
| 本次回收分支 parent | `a6f4013364e21bcb7239b5dcc25caac0f6d61f77`；只有決策新增，相對原 E3e4 無產品或測試修改 |
| 舊正式執行 F9 | `4f8a794f4167c3562eb182045102e86e9e37cca9` |
| R8 執行 F8 | `75a1e93811a52b69385cbdaf6a09d773ed9052ad`，保留原有效取樣，不重抽 |
| 回收分支 | `codex/train337-recovered-evidence-20261026`，由 root 唯一寫入；當次提交 SHA 由 Git 與發布原件辨識 |
| 最終驗收 F | 尚未固定；不得把此 evidence commit 或 a6 當成已通過的新 F |

| 項目 | 真實結果與限制 |
|---|---|
| S10 完整 123 帳本 | 正式 exit 0，2026-10-25 16:05:01.489647 至 17:30:37.969428 UTC；114 killed／5 equivalent／M20 crashed／3 retired，120 自然執行項的 head 全為 S10。四階段原退出碼 1/0/0/0，原 stale 紅燈保留。 |
| 帳本完整原件 | 封包 1284 members／52,999,273B；gzip 9,025,694B，SHA256 `1ffc61c1c0d8713653d599e34f2f3882b0535817097ffc44bc05a4b4a3b2a97e`；恢復後重新核全部成員與原件一致，沒有重跑 mutate。生成帳本 SHA256 `a4b5f1957e4bde6d30e4c05328e8a8dc1282fa811c52260eb01670cd560d56e7`，尚未採入產品路徑。 |
| S10 架構四檔 | 組裝 exit 0；原三裁判 0/0/0、generic 205／product 18、零 skip，604 輸入吻合。manifest／scan 不變，只 report／receipt 變更。歷史九組反證仍屬原 M6e50，未冒重跑。 |
| a6 架構界線 | a6 決策檔 SHA256 `e6f2aee291850d9aaf8cc0026994f6c86894bb2a7849798ddd11cd63c5558740` 不同於 S10 `fe822051…`。本批四檔只代表 S10，下一個 final 的快照須重新固定。 |
| F9 Q38 | 原完整 44 項 exit 0；43 killed＋SPM24 equivalent，不是 skip。完整346檔／14,674,721B，既有gzip及完整原流一併回收。未將執行 SHA 改成 S10/a6。 |
| 新 final native／六 browser／Reading A oracle | 尚未執行；F9 native exit 1、六 browser exit 0 都仍屬歷史。最新審查 2026-10-26T06:43:48Z 明列此批仍需執行。 |
| R8 與其他專項 | R8 原36性能樣本與原outer1完整保留，沒有重抽、沒有移標。P52／card／P-189／required-eight／PF3／memo／RC 等未驗或歷史結果維持原狀，不以封包核對冒全綠。 |

環境已能執行，Git fetch／GitHub API 唯讀成功。預設沙箱的 /dev/shm 視圖不同；用正式 require_escalated 確認原兩個 OWN 目錄、封包與私有 publisher 均仍在。原 full123 和暫存保全程序都已退出，沒有重啟；本機目前未見仍執行的正式測試。原 /workspace checkout 與私人 publisher 皆乾淨，HEAD 分別 E70 與 E3e4，未重設它們。

使用者已要求原任務繼續；協調者另提 Claude session f46787ac 可能接手。這次實際查得 a6 的決策敘述提到該 session，但最新 API 留言與正文未給出可驗的工作占用／驗收結果。為避免競寫，本批僅用獨立回收分支，不修改 train、prbody 或 handoff 分支。這不是已確認另一執行者停止，也不是已驗收完成。

批准邊界：2026-10-25 的 #323 三筆白名單原留言已核實 OWNER 身分。a6 新增的 P-189／沿用裁決含「協調 agent 整理，非原話」；目前只讀到 repository 轉錄與新審查的引用，沒有取得新的原始批准紀錄。因此本批不修改任何 comparator，不擴張原批准，也不把未跑項當沿用通過。待核實問題記於 QUESTIONS.md；不妨礙本次原件回收。

容量：恢復時 /workspace 可用 4,386,816B、/tmp 27,676,672B。原 native 實際輸出仍在 /tmp，128MiB 門檻不足；已完成的 26 index/ELF 保全 exit0，原件未刪、尚未遠端交付。沒有採用未完成的退役計畫。這次只在原 OWN 內發布證據，保原 2GiB 規畫及 64MiB reserve，完整 source／fixtures／Git objects／未提交修改不刪。

本批另包含 S10 來源準備／preledger 的完整封包（1214 members／23,510,881B；gzip SHA256 `b23b3662c4f35d59c047ad138e5e843ec1ac79bcb2fde2b9062d5fc521ac8305`），以及 native 退役前的26個raw與26個gzip完整保全、127條原命令和原owner收據。原資料均仍存在；沒有回收空間或冒作native入場通過。出版器的Git環境隔離與遠端清單schema修正，分別有純記憶體0/1/0反證，原失敗保留；未改產品裁判。

下一步：先核實回收分支的每個遠端 blob 全 bytes/hash，讓原件離開揮發性儲存；再按真正 final SHA 採用帳本與相符架構快照，完成 native／browser／oracle 和其他仍缺正式項。寫入分工未核實前可在本root獨占候選分支驗證，不改原train；候選新F須另明列，不能把本次證據提交冒作已驗。所有舊失敗及未驗項保留。不合併 PR、不部署。
