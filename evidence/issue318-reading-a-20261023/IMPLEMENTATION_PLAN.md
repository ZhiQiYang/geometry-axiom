# #318 閱讀 A 實作與對抗驗證計畫

權威：handoff `ea2748248d47563f8559638ccb70ec0ed21910d9` 的 `handoff/pr-reviews/318.md`，留言 `6357744513` 第 3 版；main `feb502d7b3bade2334733a4349c87ff91b88621e` 的決策佇列 2026-10-23 核可閱讀 A。條文候選與逐條 diff 在 `axiom-candidate/`，獨立文字對抗審在 `/workspace/kernel-no-wood-prep/REVIEW318_CANDIDATE.md`。本文件是尚未執行的計畫，不能當驗收結果。

## 原生路徑

例外屬 W。保留 K 的完整端面判斷、`geo_strip_intervals`、I5 完整足跡、I20 整條邊覆蓋與 I22 的原路徑。W 以具型別的 self member／邊界／已放 member facts 判斷，H 只傳事實與來源，不從角色字串在 K 放行。

W 判準需要同時核對：self 是 boundary；完整 footprint 位於有效區域；定位邊確為所覆蓋的外輪廓 FIXED 邊且整條被覆蓋；所驗端點恰等定位邊端點且為固定段端點；至少一段正長度接觸同承載面已放角材的既有 D11 擋面。只在該端點解除唯一／全寬／嚴格較低優先級的要求。目標角色任意，不追加「對方兩端先驗有效」的新條件。

**不限制目標料的長軸朝向。** D11(W) 的「垂直」指接觸面相對被放料長度軸。I20 要求同承載面的 boundary 全同向，v3 正例 B 正是兩支同向 boundary 的 footprint 邊局部接觸；擅自要求目標料長軸垂直會把核可正例再拒絕。

RC 判準量實際有限 RC 面原跨度，不能量扣掉角材後的餘隙。某個能放下本料寬的 RC 面若在端面仍有正長度裸露，就不能靠例外三放行。實際連續共線的 RC 面若被 polygon 額外頂點拆開，須量連續真面，不能把 30 mm 拆成 15+15 就各稱短於 27。原 `geo_loop_is_valid` 未禁止兩段相鄰共線邊，故這個反例有意義。無接觸、只有單點或只碰 RC 不算角材接觸；不設新接觸最小值或懸空上限。

自動跨距選擇與 revalidate 必須遵守同一完整判準，且不能因例外而把區間延伸出合法 footprint。`between` 是選擇器而不是新增幾何，須保留指名來源與歧義的可觀測行為。所有非例外端面維持原 full-width／priority／FREE 規則。

正式 helper 不得只有一個會被 caller 忽略的 bool：至少分清「不適用例外／適用且接受／有局部角材接觸但長 RC 裸露而拒絕」。最後一款不能回到舊 C8 的 indoor-only 判斷而被蓋成通過。反之，原本單一全寬 RC 擋面的 boundary 角落、沒有局部木接觸者仍走原完整候選規則；本款不能抹掉其他端面既有契約，造成第一支 boundary 無法放置的死結。

## 正反例

| 情境 | 預期 | 對應風險 |
|---|---|---|
| 13 mm 牆階，27 mm boundary，同向下一支料接觸 14 mm | 接受 | 核可正例 B；不能多加目標長軸條件 |
| RC 1、13、26 mm，至少 1 mm 真角材接觸 | 接受 | 不自訂最小接觸或 h_max |
| 端面分別接觸多支已放任意角色料 | 接受 | 不強迫單一 full-width／共同平面／對方較低優先級 |
| 只有 RC／無角材／單點 | 拒絕 | RC 不得計入角材接觸 |
| 實際 RC 面 27、28、100 mm，裸露交集只有 13 mm | 拒絕 | 量真面，不量餘隙；等於料寬仍放得下 |
| 真 RC 面 30 mm，共線兩 edge 各 15 mm | 拒絕 | 額外頂點不能縮小實際 RC 面 |
| 同平面不相接、不同 component 或不同 hole 的短面 | 依各實際面判 | 不跨不相連面拼出虛構 RC 面 |
| 目標未放／別承載面／自己 | 不計接觸 | 僅已放、同承載面、其他角材 |
| 目標從錯側跨進 self，正面積重疊但返回面碰巧共座標 | 拒絕 | partial admission 不得跳過原碰撞／完整 world validation |
| 定位中段、別條同座標邊的端點、FREE 定位邊 | 不得套例外 | 精確定位邊與 FIXED 範圍 |
| 固定段未覆蓋整邊 | 拒絕 | I20、R18 原約束 |
| primary／secondary／custom 借用局部接觸 | 拒絕 | 不擴大角色範圍 |
| boundary 延伸段局部接觸、主支頂延伸側面 | 拒絕 | 保 I22 與 combined 精確診斷 |
| 更新來源 RC 26→27 mm，原例外變成裸長面 | 重驗拒絕並原子回滾 | R6(e) 必重算，不能存舊例外判定 |
| 更新／刪除唯一接觸角材 | 拒絕並原子回滾 | 不沿用過時 footprint/contact cache |
| FEATURE 接觸面移開／縮為零，raw member footprint 不變 | 不計接觸 | 必消費來源返回值，不能偷偷用 H 原幾何補回 |
| RC FEATURE 實際面 26→27，raw RC 輪廓不變 | 拒絕裸面 | 必消費返回的 RC 真面，而非只測 raw source 更新 |

## Oracle 與掃描

建構端是否宣告 `CORE_LIMIT_BOUNDARY_END_FREE` 與 C8 檢查端各依新判準重算，保留兩者不一致能被 verdict 偵測的能力。先前試跑明言只量 free-gap，不能直接當正式改法。逐點保存原基底 verdict，再對比新判定：step_core 的 528 與 step_mirror_core 的 1056 必須翻成 buildable，舊 buildable 不退步，已知 custom/extension 缺口不可順帶放行。

矩形房逐毫米與凹角 579 間掃描分別保存命令、全輸出、環境、source SHA 與結果 hash，不把手寫預期數字當掃描結果。原有 oracle quick/full checker、核心重放與相關 mutation 自證都另記範圍。

## 工作與帳本

共用來源順序 #323→#314→combined→#318→無木工。現階段只讀固定 tree、寫本 repo 外的草稿；不編譯／開 Chrome／掃描／跑 full ledger。等 combined 交棒後，在自己的分支 ordinary merge 前棒，再修改共同 leaf 及唯一 canonical reader。三條 reader 各保原始 exit 與輸出。mutation ID 必先對齊實際 registry；不私用 M99–M121 或 combined M89–M98，暫候 M140+。各修正做固定／撤回／還原 0/1/0；由 root 在共同最終 SHA 整份重產一次帳本。
