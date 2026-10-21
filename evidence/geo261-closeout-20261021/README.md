# GEO-261 接手複驗證據

同一公開 L3 的完整 native、六 browser、Q38、§7、replay 與 P-189 已完成。這是候選分支 `codex/geo261-closeout-20261021` 的交付證據；PR #288 的來源、正文、留言與合併仍由使用者操作，複審尚未完成。

已完整讀交接 commit `59796b1af9259eb23d30134c2ce5a56317a06091`，未合併交接分支。已讀[2026-10-20T14:42:46Z 最新審查及使用者補充](review/最新審查原文.md)，使用者確認這是 7dae 最後推送後唯一新留言。

## 先讀

- [本輪完整驗收命令、退出碼與原件](驗收總表.md)
- [帳本來源、closure／oracle／tool hashes 與保存範圍](帳本來源與命令.md)
- [修正、精確撤回自證與限制](修正與突變自證.md)
- [PR #288 逐項回覆](PR288_REVIEW_REPLY.md)、[新正文](PR288_BODY.md)、[使用者操作清單](PR288_USER_ACTIONS.md)
- [交付 E 的範圍與可核對方法](交付說明.md)、[環境收據](environment.json)

## 來源與本輪結果

| 身分 | 完整 SHA／識別 | 範圍 |
|---|---|---|
| 產品／見證 S3 | `19401ca5448e162ee6140fed37b64b83b31ddec8` | 最後變更為既有 host_authority 突變錨點；完整帳本實跑來源 |
| 架構產物 A2 | `cbefb39b47fb0edcfaf003d2c1101929fea244c8` | 四產物實際重產來源 S2 `cabe824128be31d0039dc6c94fa3f04cfb722a6b`；後續 611 inputs 與四產物原 bytes 相同 |
| 帳本／整合受驗 L3 | `6589248c9a94bdf0460d8f84dd1610e51048188b` | S3 的直接子提交，只改原始帳本 JSON；其餘 1009 個受驗來源檔原 bytes 相同 |
| 證據／稽核 E | 本檔所在的交付證據提交，完整 SHA 見交付回報 | 只新增證據根及精確 Git 資料規則；不冒稱產品在 E 重跑 |

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

架構三項驗證原件在 [CLI](architecture-L3/README.md)、[native 205／18 引用核對](architecture-L3-native引用/README.md)；來源綁定在 [snapshot](source-binding-L3/來源綁定/snapshot-L3.json)。E 的完整 SHA、提交後驗證與正常推送結果由交付回報提供；本檔不冒稱在 E 重跑產品。

## 歷史原件

當輪舊 README 的未來式按[交付說明](交付說明.md)解讀，不能覆蓋最後總表。L2 的[完整 native exit 1](native-L2-failed/verification.json)與[S3 錨點修復](host-authority-anchor-fix-S3/README.md)保留；兩紅都來自舊 footprint 錨點，S3 修正後完整重跑。

舊 L43 與候選的 P-189 紅燈，見 [L43](p189-final-L/README.md)、[codec](p189-codec-trial-7ad3216a/README.md)、[contact](p189-contact-trial-85dc4fff/README.md)；[6c 正向／4bd 精確撤回](footprint-p189-pair-evidence/README.md)保留負控原 exit 1。舊 GCC ledger 的預設 compiler 檢查失敗與共用 baseline 補正見[專屬說明](ledger-A-gcc-history.md)。P52／P72B／P73 的初次無效控制、自然負控存活與接受器修正同樣保留，不以挑選綠燈取代完整紀錄。

## 未驗與最不確定之處

原 P52 WSL 故障未自然重現，原 P73 失敗瞬間 DOM 未保存，不能定論歷史排程故障的唯一原因。本機環境為 Linux／GCC 14.2／Python 3.12.14／Node 24.19／Chromium 151；Windows／WSL／遠端 CI 未驗，截圖未逐張人工評讀。native 唯一 skip 是原允許的 Windows GDI 資源測試；canvas 保留 P38 的 1 個預期 uncaught exception。P-189 是本機一次完整交錯輪的結果，不推論其他環境。

M20 為重複異常退出的 crashed，不能稱 assertion killed；M36 的 7143 歷史差分不當成本輪重跑。core 帳本工具保存結構化結果與子程序輸出 hash，未另存全部 core 子程序 raw stdout／stderr；完整頂層輸出不能補此缺口。原始 wait、工具觀察轉錄與傳輸日誌分別標示；一份歷史封包 peer 首敗未另存完整輸出，不補造。正式紅燈、invalid、自然負控存活與前置失敗依實存原件保留。 本輪五 browser peer 的兩次資料探索只保存真工具退出碼與摘要，不能冒稱有完整輸出流；這項限制與正式測試原件分開標示。

定長 decoder 未新增專屬撤回控制；H／K 三檔性能撤回只證明該組修正對原門檻的必要性，不單獨量化 codec／contact 每項效益。P73 未新增 RC-only 空態專用回歸。非 current footprint 依有效 store 的容量不變條件，不擴張到損毀 store。既有 P-190 殘餘風險仍在：旋轉 box frame 可讓局部面名落到不同世界面，MODEL-SOURCES.md 已記錄此界限，本輪未宣稱補上該比對。

最不確定的是原 WSL 現場 P52／P68 的唯一阻塞原因，以及本機性能樣本跨環境的代表性；已有的精確撤回與正式全量結果不能補造當時缺失的追蹤。

HANDOFF 第 7 節事項不代決；下一順位只讀準備在[後續工作](後續工作/README.md)。任何新審查先取得全文並逐項處理，不因本輪測試通過直接快轉整合分支或合併。
