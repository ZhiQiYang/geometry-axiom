# #198 凹口／尖脊：來源、案例與原收據映射

本輪唯讀核對支持把 **#198 保留為供負責人核收的關閉候選**。原始 A/B 缺陷已有具名測試、修正前後輸出與撤回／恢復反證；目前 main 仍保有相同分類函式與相關測試片段。這不是目前 main 或新候選 F 的執行驗收，也未關閉 issue、改分支、編譯或執行 native。

## 固定來源與批准邊界

- 本輪核對的 main：`405f8c5e1a637a16cbe47470faf5ae1fa02b8676`。
- 精確舊基底 #196：`635dd86ee368579aec444fb3ba16e48bccf4877e`。
- #202 最後交付：`137427563de2e94e41d067282266c232f176f0d8`。它是 evidence 補交提交，不能稱為最早產品修正提交。
- #202 初始修正後 probe 標記 head：`bd5715c318ed17a4f9ff4f9263d3dc9ccb75bcbb`；最新角點修補 product commit 是 `adfb5d87eb174cc19ffd15be7bbfdbf1ad607aa6`，其 aggregate 受測來源為 `1b5919787df1124c0eb6122a886d4403ada21fd2`。三者用途不同。
- #291 第 18 班受測 head：`e8eb1da51f3b21df15869338a7e36e76e584ff9e`；merge commit：`772b97f5f79df99378dacb92b5f8eb359b5e57bc`。
- 本輪找到並核取的較晚正式 native 原件：#288 F13 `13d02c1db7022145a52ee063286a558e595eb212`，執行於 2026-10-23。
- API 原文保存在 `issue-and-pr-sources/stdout.bin`，包括 [issue #198](https://github.com/ZhiQiYang/geometry-axiom/issues/198)、[唯一原實跑留言](https://github.com/ZhiQiYang/geometry-axiom/issues/198#issuecomment-6110479792)、[#202 正文](https://github.com/ZhiQiYang/geometry-axiom/pull/202)、[#291 正文](https://github.com/ZhiQiYang/geometry-axiom/pull/291)。本輪未依 API 轉述新增任何公理、數值門檻或木工規則推論。

## 精確案例 → 現有測試 → 原件

以下路徑／行號以本輪 main 為準；固定來源永久連結可由完整 SHA 與路徑核對。

| 案例／契約 | 原始精確輸入與幾何 | main 現有斷言 | 已核對的原件／限制 |
|---|---|---|---|
| A：四角在內但跨凹口 | 輪廓 `0,0 100,0 100,100 60,100 60,40 40,40 40,100 0,100`；足跡 `[30,70]×[50,80]`。交集是 `[30,40]×[50,80]`、`[60,70]×[50,80]`，各 300 mm² | `tests/test_core_integrity.c:365`，特別 375–377：回傳 `<0`；`tests/test_reference_contract.py:106`：查詢 R7、非單一矩形、apply 拒絕及 dump 不變；`tests/run_tests.py:36`／`_ax_r7_notch_disconnected.scene` 要求具名 R7 拒絕 | `before/probe.json` 誤列 hole `[30,50,70,80]`，但 apply 到後續重驗已遭拒、dump 不變；**不能說舊版成功提交錯孔**。`after/probe.json` 查詢與 apply 明確 R7 拒絕。撤回 native／bridge 具名 A 紅，場景錯誤診斷不符；恢復皆綠。 |
| B：四角在外但尖脊穿入 | 輪廓 `0,0 100,0 100,50 60,50 60,90 40,90 40,50 0,50`；足跡 `[20,80]×[70,80]`；交集 `[40,60]×[70,80]`，200 mm² | `tests/test_core_integrity.c:378`：回傳 `>0`、`OBSTACLE_SPLIT`、精確 `[40,70,60,80]`；`tests/test_reference_contract.py:119`：精確清單、apply 成功、產生第二片且非 hole；`tests/run_tests.py:37`／`_ax_r7_ridge_crossing.scene` 驗座標及無孔 | before 清單空、apply 因 R15 不存在拒絕；after split 精確且 apply 成功。撤回 native／bridge 具名 B 紅、場景紅；恢復綠。本輪純 Python 另核歷史 after dump 的 z=0 兩片無重疊，聯集恰等於原輪廓扣除 200 mm² 接觸，餘 5600 mm²。 |
| B 的 cut-strip 呼叫路徑 | 同尖脊輪廓；樑沿 x 20→80、at 75、width 10、`cut-strip` | `tests/test_reference_contract.py:247`；`tests/run_tests.py:39`／`_ax_r7_ridge_strip.scene` | 原撤回 bridge 第三個失敗方法及場景 FAIL；恢復 PASS。這只證既有平面 strip 再分類，不擴大為所有樑／立面障礙的精確交集。 |
| 真孔／無接觸／貼邊對照 | 真孔 `[10,20]×[10,20]`、遠離 `[110,120]²`、單側貼邊 | native 383–392；bridge 256–267 | 原五方法撤回組仍含兩個通過的控制，恢復五方法全通過；避免把所有輸入一律拒絕當修正。 |
| R14/R15 與交易界線 | 未選到複雜柱，不阻擋明確指定合法 c2；未裁 strip 仍驗後續缺失 id／跨拆分線 | bridge 240–245；78–95；相關 `_ax_r14_uncut_strip_multiple_pieces.scene`、`_ax_r15_uncut_strip_missing_item.scene` 已在 runner 34–35 註冊 | 第一輪全撤回含合法 c2 控制；後續整合 F13 reference 51/51。原 issue 的 R14 下游風險不是只靠 A/B 兩個返回值推定已修。清單遇退化項仍整份報錯，不能宣稱 UI 可從錯誤清單選 c2。 |

現行三個產品呼叫點為 `current_geometry.c:8140`、`:8811`、`:9088`；分類函式自 `:7989` 開始。它掃全部輪廓頂點形成 slab、配對垂直邊交點，只允許單一連續精確矩形，另保留閉合集合／角點接觸拒絕。這是既有實作與測試的描述，沒有新訂 R7 政策。

## 已驗證的歷史收據

1. **最初反例及撤回／恢復**：`tests/evidence/geo198/before/probe.json`、`after/probe.json`、`remove-fix/results.json` 與六份原 log 已讀回。舊產品 `current_geometry.c` 的 `9e2ae4fb…` SHA-256 確實等於精確基底 #196 的 Git blob 內容 hash；但是 before probe 自己記的 head 是 `d44d784a7fcf06103ae2c5a5d9321549611a3007`，並明記可能有未提交修改，故不把 head 欄當乾淨來源證明。after 也有同樣 note。實際來源／binary hash 依原 receipt 保留，沒有在本輪重新核讀已不存在的 ELF。

   | 原 runner | 撤回真 exit | 恢復真 exit | 原輸出 |
   |---|---:|---:|---|
   | native integrity | 1 | 0 | 撤回 147/164，具名 `counterexample_A < 0` 與 `counterexample_B > 0` 失敗；恢復 164/164 |
   | bridge 五方法 | 1 | 0 | 撤回 3 failures（A、B、strip），恢復 5/5 |
   | scene runner | 1 | 0 | A、B、strip 撤回 FAIL、恢復 PASS；完整原混合文字／JSON log 保留 |

2. **F13 原完整 native**：`evidence/geo261-final-13d02c1d/receipts/native.json` 原 workflow exit `0`，原 shell step `actual_process_returncode=0`，1683.926773796 秒，`over_ci_timeout=false`，前後 checkout 皆乾淨 F13。原命令是 workflow 的 `ulimit -s 16384` 加 `python3 tests/run_all.py --build`。這是 2026-10-23 的歷史執行，不是本輪新跑。

   已讀回 222,197-byte `native-01.tar.gz`，SHA-256 `4ac2c0d5ff5c5607fb5e500b66953329a44309d191be711f53f2c17318869879`。只取出以下五份原件並逐 byte 核對 receipt 內 hash，保存於 `f13-selected-originals/`：`c_integrity.log`、`core_run_tests.log`、`py_test_reference_contract.json`、`py_test_reference_contract.unittest.log`、`steps/01.stdout`。結果為 integrity **432/432**、scene **165/165**、reference **51/51**；A/B/strip 三場景原 log 均 PASS。完整 archive 原件也保留，未假稱本輪核驗了其中每一個 member。

3. **#291 七項**：API 正文報同一 e8eb1… 來源七項 exit 0、native 3354/0/1、canvas 2211/0，另明示 native/canvas 超原 CI 分鐘及 canvas exception 原值 1。原件指向本機 D: `train18p157-formal-r2/verified-r1/certificate.json`。**本輪未讀該 D: 原件，僅列為轉述的歷史來源，不以正文取代已核 hash 的原收據。** 先前第 13 班原紅與第 18 班 R1 非排他／P76 失敗也不改寫。

## 來源片段身分與本輪分析

`compare-source-fragments-f13` 的純 Python 靜態比對 exit `0`：#202 137427…、#291 e8eb1…、#288 F13、main 405f8… 四個來源的下列內容全同：

- `classify_rect_outline` 原 bytes SHA-256：`d7ffda4b031ffbd49d1516fd45949afd3e5b284c107c010512b6be48a19776c8`。
- `test_rect_outline_counterexamples` 原 bytes SHA-256：`1faaf4d42edf6be6ba7b8d1379ba960c8a06696418ed020dd592e9dd2c9b89f6`。
- 18 個相關 bridge 方法／fixture helper 的 AST 定位原文字 body hash、A/B/strip 三個 scene 註冊值，以及三份 fixture 原 bytes。

`SOURCE_FRAGMENT_IDENTITY_F13.json` 保存每次唯讀 Git argv、exit、完整 blob hash、函式原文與行號；原三方比對另保留。**這是片段身分，不包含全部呼叫者、型別／容量、編譯旗標、bridge 啟動與依賴閉包，因此不能自動授權將 F13 全綠搬到 current main／主代理新 F。**

本輪 `verify-historical-receipts` exit `0`；`check-recorded-geometry` exit `0`。後者只用既有 raw 字串作整數格集合比對：A 兩塊各 300 mm²；B 原面 5800 mm²，交集 200 mm²，保存的 z=0 兩片為 5400+200=5600 mm²、無重疊且差集相等。歷史 dump 的 boundary 3 位於 z=70，未混入原 z=0 面片。這只驗整數開格的面積／內部集合，不證零面積邊界拓撲、ghost 像素或新來源 runtime。

## 尚未證明的部分與最小下一步

- **沒有找到 A/B 原始規格未被測試覆蓋的確定新反例**。目前不應另加臆測公理或修改 golden。
- 本輪未做 current main 或新候選 F 的 native／browser 執行，亦未建完整跨 SHA 依賴閉包。需要當前正式驗收結論時，優先引用主代理已排程／已回收的同來源完整 native，核對其 `c:integrity`、`core:run_tests`、`py:test_reference_contract` 原 log；不為 #198 重跑一份相同且已有效完成的驗收。
- #198 原文提到 ghost 為下游風險；這份原生／橋接映射沒有替代可視 ghost 行為的瀏覽器驗收。舊 README 也明列單矩形清單格式、樑初始 bbox、立面及多區投影能力界線，不能因 #198 修正就宣稱這些功能都完成。
- 可把本映射交給負責結案者核對原 issue 範圍，再決定是否關閉；代理不關 issue、不合併 PR、不替使用者宣布全專案完成。若要補充目前來源收據，只補原件索引／閉包缺口，不新增未批准門檻。

## 取樣與工具記錄

API 僅精讀 issue #198（最後一則留言）、PR #202（最後兩則）、PR #291（最後一則），完整 argv／exit／原 bytes 在各 `RESULT.json` 與 `stdout.bin`。所有正式記錄的 Git／Python 讀取與分析 exit 均 `0`；沒有產品測試被執行。

首次定位廣搜誤納歷史大型 JSON，產生 3,556,619-byte 搜尋原輸出，已保留，隨後改為精準路徑，未清理原件。一個臨時顯示指令曾把 scene 的混合 log 當純 JSON 而 `JSONDecodeError`、exit `1`；這是本輪閱讀工具錯誤，不是場景重跑紅燈。後續直接核原文字中具名結果，沒有改原 log 或產品斷言。沒有任何大型 checkout、native 128 MiB 工作資料、編譯或額外測試 fixture。
