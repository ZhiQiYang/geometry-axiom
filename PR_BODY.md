K＋矩形格網模板的隔離建置已有真功能測試；本分支補上 `geometry_woodworking` 的明確匯入拒絕，以及 K 以引號或角括號引用已安裝 W 標頭時的分層守門。原 11 項功能／反證與斷言保留，新增兩項後共 13 項。實作已推，**動態驗收尚未跑**。

獨立安裝只取 K 的 exact／geometry／grid、矩形格網模板與測試共 11 檔。匯入控制建立真可取得的 sentinel 套件，要求由 blocker 拒絕 `geometry_woodworking`、`geometry_app` 等名稱，不能拿缺套件當成功。K→W 控制各加唯一一行 quoted／angle include，要求先成功編譯、連結、執行 exact-cells，再由同一 source gate 取得 0／1／0；目前是待執行的測試程式，尚未有原始三態結果。

| Current state | SHA／原 exit | 範圍與限制 |
|---|---|---|
| 測試來源 SHA | `21957a45142dadc0787e8970da976ab249b4b6d1` | 已普通 push，遠端 exact SHA 相同；沒有改產品 C／公理／決策佇列 |
| 目前 evidence head | `21957a45142dadc0787e8970da976ab249b4b6d1` | 自有 evidence prefix 的 PROGRESS 與 revision-2；尚無動態收據 |
| Tiny sparse worktree／來源發布 | 原 Git exit 0 | 乾淨 worktree；只取 11 檔及規則／自有 evidence，沒有編譯 |
| AST 與固定撤回 anchor | 0（只做靜態） | 13 test methods，blocker／K guard／literal parser 各一處 |
| 完整隔離測試 13 項 | 未跑 | 等 #288 獨占 heavy 時段結束後由 root 安排 |
| import blocker 反證 | 未跑 | 固定／撤回／還原預期 0／1／0，斷言不動 |
| K→W guard、angle parser 反證 | 未跑 | 新 driver 嚴核七 phase 0／1／0／1／0／1／0；兩種真 include 各有內層 0／1／0 |
| 對抗審查 | 第一輪已指出並修補靜態繞路 | #314 發現 angle include 漏抓；新來源待其再審。#318 的原靜態審不能代替新收據審查 |
| 共用 expected count | 尚待交棒更新 | `py:test_rectangular_template` 仍登記 11，來源已 13；不宣稱目前完整 native 綠 |
| 全域突變帳本 | 未重產 | 只由 root 在共同最終 SHA 整份產一次 |
| Native 全清單／browser／架構 | 未以本子項重跑 | 不把本子項或歷史 F13 綠項冒稱新來源驗收 |

共用順序 #323→#314→combined→#318→本子項；#318 正式 source 交棒後普通 merge 前棒，再更新共用 count、固定最終 SHA 並重跑受影響驗證。既有 K 架構原裁判仍負責完整來源契約；此小型隔離測試只宣稱 literal include 的專案閉包，不冒稱完整 C 前處理器分析。

最不確定的是尚未實跑的編譯／兩種 include 反證，以及 #318 合流後 11 檔 closure 是否仍充分。沒有允許新的 skip，沒有把編譯失敗、crash 或 watchdog 算成有效突變自證。不 force push、不合併 PR。
