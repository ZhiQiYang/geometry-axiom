# #299＋#316：定位邊診斷與死碰撞轉接器退休，重新整合待驗

非 boundary 角材超出定位邊時，保留 `V_EXTENSION` 的原裁決，補足料件、定位邊與實際超出區間；移除沒有產品 caller 的 H wrappers 及死 W footprint API，保留活 I11 放置與 H／W 重驗，並以相同局部 UV 的雙承載面正例保護「只比同承載面」。本補丁不改公理層或決策佇列，尚未合併 PR。

使用者最新指示改為在目前整合分支之上準備 #323 → #314 → 本 combined → #318。此分支目前只新增準備收據，**還沒有合入前兩棒，也沒有新堆疊的正式驗收結果**。原獨立補丁的全綠結果保留其原產品 SHA；不能轉作新基底綠燈。

| 目前身分 | 不可變 SHA／狀態 |
|---|---|
| 來源分支 | `codex/geo299-316-combined-20261022` |
| 目前 evidence HEAD | `a004e29a34b5fb880690e544057e90386e47e75a`；只比前一 E 追加準備證據 |
| 尚未合流的目前產品 | 歷史 F `5bfadf187e615ba0fb8466753b63ce3044ef7d1c` |
| 歷史正式證據 E | `139ab64ca5f88e89bb4e95921675b998457026aa` |
| 歷史原 base | `4b665fae21ab63aaffb7d84f6a32d5a469ba1675` |
| 這次已讀權威 handoff | `ea2748248d47563f8559638ccb70ec0ed21910d9` |
| 新基底／新 final SHA | 待 #314 普通 merge 前棒、交接後固定；目前未產生 |
| 新對抗審查 | #323 owner 進行中，未稱審過 |

本次只使用 `handoff/drafts/combined/rebased-546e2eb2/patch.diff` 與 `_gen` 追溯原設計，不重疊套用兩份 individual patch，也不以舊生成物覆蓋既有修復。fresh handoff 中沒有 `handoff/pr-reviews/299.md` 或 `316.md`，因此沒有聲稱讀到這兩份不存在的留言檔；最終前會再次 fetch。

以下是唯一 current-state 矩陣；歷史欄不能取代新堆疊實跑。

| Gate／項目 | 新堆疊 execution SHA／exit | 已保存歷史結果／允許 skip | 目前狀態 |
|---|---|---|---|
| native `ulimit -s 16384; python3 tests/run_all.py --build` | 尚無／未跑 | F5bf：0；224 suites、5184 pass、0 fail、1 個原允許 Windows GDI skip | 合流後按閉包驗證 |
| canvas | 尚無／未跑 | F5bf：0；2267 assertions、full、golden matched | 合流後待跑 |
| assembly | 尚無／未跑 | F5bf：0；150 assertions、原 partial scope | 合流後待跑 |
| documents | 尚無／未跑 | F5bf：0；47 assertions、原 documents harness | 合流後待跑 |
| grid | 尚無／未跑 | F5bf：0；356 assertions、原 partial scope | 合流後待跑 |
| space | 尚無／未跑 | F5bf：0；242 pass、full-space-suite，原 omitted timber groups | 合流後待跑 |
| timber | 尚無／未跑 | F5bf：0；79 pass、原 partial scope | 合流後待跑 |
| mutation freshness／完整帳本 | 尚無／未跑 | F5bf check 0；原 88 筆帳本的 execution S 保留原 SHA | 最後完整重產由主代理統一執行 |
| 三條原架構裁判 | 尚無／未跑 | F5bf：0／0／0 | 新合流來源待重驗／重產 |
| combined 專項與突變自證 | 尚無／未跑 | 原 M89–M98 正常斷言 killed；fixture／reader 精確 0／1／0 見原 E | 待 shared baton 及主代理測試槽 |
| 本次只讀準備工具 | E139 開始／各 0 | fetch、原件快照、十個 anchors 靜態唯一、grid/timber 原收據對抗審查 | 僅準備完成，非正式 gate |

原 F5bf 的 Chrome156／Node24／Noto CJK 與原 workflow 收據、完整已捕獲 streams、環境及 SHA 保存在 [歷史正式摘要](https://github.com/ZhiQiYang/geometry-axiom/blob/139ab64ca5f88e89bb4e95921675b998457026aa/evidence/geo299-316-final-5bfadf18/FORMAL_SUMMARY.md) 與 [原 metrics](https://github.com/ZhiQiYang/geometry-axiom/blob/139ab64ca5f88e89bb4e95921675b998457026aa/evidence/geo299-316-final-5bfadf18/FORMAL_METRICS.json)。原完整帳本曾因 ENOSPC 中斷後在相同 S 只補受阻 bridge subset，不宣稱單次 full 命令退出 0；85 份 mutant C 明列 reconstructed-not-captured，未落盤的舊 core 內層 streams 不補造。這些歷史限制維持。

本次保留 combined ID M89–M98。靜態 AST 只證明十個 old anchors 在目前產品各恰一次，不代表 mutants 已重跑或帳本 freshness；#314 的 M99 起 ID 與 #318 預留區由主代理統籌。canonical reader 依 314 → combined → 318 交棒順序，僅走既有同步器。

本次作為 #314 對抗審查者，已提出「同一 final ParameterRef、不同 ordered facts」正反例，owner 接手；目前未見新 SHA 動態 0／1／0，因此仍列待驗，不以靜態推演宣稱已修。這次 shared source 尚未改動，也尚未跑 compiler／Chrome／benchmark，以免與 #288 的 R3 正式工作互相干擾。

準備收據、逐 member hash 與進度見 [PROGRESS.md](https://github.com/ZhiQiYang/geometry-axiom/blob/a004e29a34b5fb880690e544057e90386e47e75a/evidence/geo299-316-stack-20261023/PROGRESS.md)。下一步是普通 merge #314 已推送分支、保留 #323／#314／combined 共用檔聯集，再固定新產品 SHA、執行受影響正式項與精確反證，最後由主代理統一帳本與合流。

最不確定處是新基底上三份補丁的共同 closure 尚未動態驗證；此外目前沒有 Windows／MSVC 測試，GDI 只保留原 Linux 允許 skip。尚無新的全綠聲明。GitHub API 存取受限，此處只提供已推送的來源與正文分支檔，不聲稱已更新 GitHub PR 正文或已建立新 PR；不 force push、不合併 PR。
