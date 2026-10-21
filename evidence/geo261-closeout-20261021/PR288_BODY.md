# GEO-261：幾何核心與木工模板解耦整合

本 PR 將共用幾何核心 K、木工模板 W 與宿主 H 分層，保留來源身分、完整 roots 集合、拒絕契約與舊場景重播。本次補上有截止時間的 browser 狀態等待與空態同步，並在不改 P-177 守門次數／時機及原容量下，減少載入中的重複解碼、查找和大型暫存複製。

完整本機驗收已在同一公開 L3 完成，結果如下。提交供新 SHA 複審；不以此文件自行解除合併阻擋。候選由 `codex/geo261-closeout-20261021` 提供，PR 來源分支仍為 `architecture/geo261-integration-20261016`，來源更新與合併由使用者執行。

## 來源分欄

| 身分 | 完整 SHA／識別 | 範圍 |
|---|---|---|
| 產品／見證 S3 | `19401ca5448e162ee6140fed37b64b83b31ddec8` | 最後變更為既有 host_authority 突變錨點；完整帳本實跑來源 |
| 架構產物 A2 | `cbefb39b47fb0edcfaf003d2c1101929fea244c8` | 四產物實際重產來源 S2 `cabe824128be31d0039dc6c94fa3f04cfb722a6b`；後續 611 inputs 與四產物原 bytes 相同 |
| 帳本／整合受驗 L3 | `6589248c9a94bdf0460d8f84dd1610e51048188b` | S3 的直接子提交，只改原始帳本 JSON；其餘 1009 個受驗來源檔原 bytes 相同 |
| 證據／稽核 E | 本檔所在的交付證據提交，完整 SHA 見交付回報 | 只新增證據根及精確 Git 資料規則；不冒稱產品在 E 重跑 |

75 筆帳本 execution 忠實記錄 S3，不改寫成 L3／E。架構登錄現為 611＝333 owned＋278 exclusions，796 edges、0 diagnostics；較交接的 601 多 10 個受驗工具輸入，四產物的原 sourceBaseHead 保持 S2，沒有偽造 S3 重產收據。

## 本輪驗收

| 驗收 | 本輪結果 |
|---|---|
| S3 全量帳本、check、check --killers；L3 預設 check | 皆 exit 0；78＝70 killed＋1 crashed＋4 equivalent＋3 retired；75 execution 均綁 S3 |
| 架構 CLI／兩套架構測試 | CLI exit 0，333 sources／796 edges／0 diagnostics；205／205、18／18 皆 exit 0 |
| native 完整 `run_all.py --build` | exit 0；224 suites／188 Python modules；5187 pass／0 fail／1 原 GDI skip，1829.681556 秒，原 2100 秒／16 MiB 不變 |
| replay | native 內 6／6，exit 0 |
| canvas | 2261 pass／0 fail／0 skip、85 段 golden 相符；Node 與全部外層 exit 0；2062.211496 秒，原 2100 秒內 |
| assembly／documents／grid／space／timber | 150／47／350／242／79 全通過；各 Node、wrapper、launcher、工具真退出皆 0；原 full／partial 範圍不變 |
| Q38 | 42＝41 killed＋SPM24 equivalent；正式 exit 0；baseline 27／20 |
| Q38 的 12 控制 | 9 survived＋3 unlabelled；原 raw gate exit 1，預期結果檢查與外層 exit 0 |
| §7 整卡／公理突變 | 53 killed／5 killed，正式 exit 0；整卡 baseline 43、每案指定 case 復原綠；公理 baseline 44、每次復原 44 全綠 |
| P-189 | 六階段與真 wait 皆 0；175 等價場景、36 有效樣本、16 controls；N16／32／48／64＝1.075985／1.087069／1.610790／1.482303×，全部 ≤2× |

完整 argv、cwd、環境、起訖、退出碼及原始輸出見[驗收總表](https://github.com/ZhiQiYang/geometry-axiom/blob/codex/geo261-closeout-20261021/evidence/geo261-closeout-20261021/驗收總表.md)；帳本的 closure／oracle／tool／compile hashes 與原件見[帳本來源與命令](https://github.com/ZhiQiYang/geometry-axiom/blob/codex/geo261-closeout-20261021/evidence/geo261-closeout-20261021/帳本來源與命令.md)。L3→E 只容許證據差異，交付回報另列 E 完整 SHA 與只讀驗證結果，不能把 E 說成產品重跑來源。

## 修正與突變自證

P52 保留原幾何斷言，等 timber 3 geometry 與交易完成；在真 fetch 延遲 6000 ms 下 43／43，精確撤回後唯一 P52-5 轉紅。P72B 核新文件及完整就緒，撤回與 hold-navigation 控制命中預期拒絕；P73 的 guard／metrics 撤回命中具名失敗，原 golden 不減。

性能正向 `6c6937708fa31790586d6c31c2984070e6bf885a` 通過，公開負控 `4bd19f91c434417f1c4431128c55285f4b11d3c3` 精確還原 H／K 三個產品檔後，唯一 N64＝2.514533× 被原門檻拒絕。該負控 ref 只供稽核，不可採入產品。最後 L3 另有上表完整重跑。

L2 完整 native 的兩紅是 footprint 突變錨點匹配數 0；S3 只同步既有測試常數，保留 count==1、精確 marker 與 0→1→0。修復前正式 exit 1 與修復後定向 18／18、8 controls 的原件均保留，且已重新產生全帳本、重跑 L3 全驗收。詳見[修正與突變自證](https://github.com/ZhiQiYang/geometry-axiom/blob/codex/geo261-closeout-20261021/evidence/geo261-closeout-20261021/修正與突變自證.md)。

## 限制與審查

原 P52 WSL 故障未自然重現，原 P73 失敗瞬間 DOM 未保存，不能定論歷史排程故障的唯一原因。本機環境為 Linux／GCC 14.2／Python 3.12.14／Node 24.19／Chromium 151；Windows／WSL／遠端 CI 未驗，截圖未逐張人工評讀。native 唯一 skip 是原允許的 Windows GDI 資源測試；canvas 保留 P38 的 1 個預期 uncaught exception。P-189 是本機一次完整交錯輪的結果，不推論其他環境。

M20 為重複異常退出的 crashed，不能稱 assertion killed；M36 的 7143 歷史差分不當成本輪重跑。core 帳本工具保存結構化結果與子程序輸出 hash，未另存全部 core 子程序 raw stdout／stderr；完整頂層輸出不能補此缺口。原始 wait、工具觀察轉錄與傳輸日誌分別標示；一份歷史封包 peer 首敗未另存完整輸出，不補造。正式紅燈、invalid、自然負控存活與前置失敗依實存原件保留。 本輪五 browser peer 的兩次資料探索只保存真工具退出碼與摘要，不能冒稱有完整輸出流；這項限制與正式測試原件分開標示。

定長 decoder 未新增專屬撤回控制；H／K 三檔性能撤回只證明該組修正對原門檻的必要性，不單獨量化 codec／contact 每項效益。P73 未新增 RC-only 空態專用回歸。非 current footprint 依有效 store 的容量不變條件，不擴張到損毀 store。既有 P-190 殘餘風險仍在：旋轉 box frame 可讓局部面名落到不同世界面，MODEL-SOURCES.md 已記錄此界限，本輪未宣稱補上該比對。

2026-10-20T14:42:46Z 審查兩阻擋一須改的逐項回覆已備妥，回覆檔與[原文](https://github.com/ZhiQiYang/geometry-axiom/blob/codex/geo261-closeout-20261021/evidence/geo261-closeout-20261021/review/最新審查原文.md)公開於證據根；是否接受修正仍待複審。HANDOFF 第 7 節不代決，#323 等後續產品未混入本 PR。
