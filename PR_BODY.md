# #299＋#316：定位邊診斷與死碰撞轉接器退休，已接 #323／#314，動態待驗

非 boundary 角材超出定位邊時，保留 `V_EXTENSION` 的原裁決，補足料件、定位邊與實際超出區間；退休沒有產品 caller 的 H wrappers 及死 W footprint API，保留活 I11 放置與 H／W 重驗，並以相同局部 UV 的雙承載面正例保護「只比同承載面」。本棒不改公理層或決策佇列。

已依使用者順序，將含 #323 的 #314 來源一般 merge 到 combined 分支；source 已推並交給 #318。**新堆疊還沒有動態驗收結果**。下面只有一份 current-state 矩陣；原獨立補丁的綠燈留原 SHA，不能轉作新產品綠燈。

| 目前身分 | 不可變 SHA／狀態 |
|---|---|
| 來源分支 | `codex/geo299-316-combined-20261022` |
| 產品／tests source S | `15a735951a36b6fe52e0291152f335139e6921ad` |
| evidence HEAD E | `1722b55445b53ac37b6eac1be7b379e79c73eaa8`；S後只追加本棒 evidence |
| 一般 merge parents | combined `c940a6543029a94d443709ebdcbd63828fdfef1d` ＋ #314 `8033aa756c62f654333c24d1276d4b61beb31a45` |
| 前棒 #323 | `5c29eba30a40f20ea5c7eb8dc139e5788235d3b6`，已包含在 #314 parent |
| 最新 handoff refresh | `f6a174df42d5ff1ce670b6f8277da60c667b8965`；combined patch／八份 `_gen` 與先前 ea274 原件相同 |
| 歷史獨立產品／證據 | F `5bfadf187e615ba0fb8466753b63ce3044ef7d1c`／E `139ab64ca5f88e89bb4e95921675b998457026aa` |
| 對抗審查 | #323 reviewer已完成這次S聯集靜審，未見確立遺失／假綠；產品動態未審過 |

fresh handoff 仍沒有 `handoff/pr-reviews/299.md` 或 `316.md`，不聲稱讀到不存在的留言。補丁來源保留指定 combined rebased patch 與 `_gen`；未分別疊兩份 individual patch，也未以舊產物覆蓋前棒修復。

| Gate／項目 | 目前 S 的 execution／exit | 原歷史結果與允許 skip | 目前判定 |
|---|---|---|---|
| native `ulimit -s 16384; python3 tests/run_all.py --build` | **未跑** | F5bf原0；224 suites／5184 pass／0 fail／1原允許 Windows GDI skip | 待最終閉包排程 |
| canvas | **未跑** | F5bf原0；2267 assertions、full、golden matched | 待跑 |
| assembly | **未跑** | F5bf原0；150 assertions、原partial | 待跑 |
| documents | **未跑** | F5bf原0；47 assertions、原documents harness | 待跑 |
| grid | **未跑** | F5bf原0；356 assertions、原partial | 待跑 |
| space | **未跑** | F5bf原0；242 pass、full-space-suite，原省略timber groups | 待跑 |
| timber | **未跑** | F5bf原0；79 pass、原partial | 待跑 |
| combined W／H／core專項與反證 | **未跑** | 原M89–M98正常斷言killed；fixture／reader精確0／1／0保原E | 待同最終來源原裁判 |
| #314 M121精確反證 | **未跑** | 沒有捏造新record；靜態檢視不是0／1／0 | 待baseline／withdraw／restore正常斷言原輸出 |
| mutation freshness／完整帳本 | **未跑** | 舊帳本record union110筆，各自execution字段保原；M121 unrun | 主代理最後一次全份重產；不宣稱S上fresh |
| 架構三條原裁判／四檔刷新 | **未跑** | 舊scan／report／receipt真來源保留3a165ef5；不改標S | 新manifest／closure待主代理重產 |
| 原canonical sync機械生成 | 未commit的merge tree → S；原exit0 | 非三reader裁判；沒有手改嵌入JSON或另造閱讀器 | 僅生成完成 |
| reader三條原裁判 | **未跑** | F5bf原結果保持歷史 | 待測試槽 |
| 有界靜態檢視 | 原exit0 | 111個ID唯一／14個選定anchors各1／8個suite靜態方法數相符 | 僅靜態，不是動態驗收 |

一般 merge 原退出1，六個衝突都保原輸出並解完：allowlist、architecture三個衍生檔、舊帳本、migration owner map。產品C、manifest、registry、expected與canonical自動合併；原sync再機械產生0。M89–M98不動，M99–M120全保、M121已由主代理保留；owner map保精確聯集與23／61斷言，未放寬測試。新suite登錄與靜態方法數為contact15、host-facts22、load13、stagger47、contacts10、contact-world9、world-validation14、wood-grid23。

wood-contact-world從前棒10變9，是早先combined已退休dead `wood_contact_footprint_collides` API／collision-only單元測項；其Python與C harness逐Git blob等早先c940，本次merge沒有另外刪測。活I11 M13／M97／M98與同UV跨host正例仍保留且待新stack實跑，不能把此基數當動態通過。

舊帳本只是原record聯集，不是重產：保combined原88筆與前棒獨有22筆，沒有重標execution SHA／verdict。原manifest保#314的新H leaf／W guards與combined具名dead API退休聯集；舊scan／report／receipt保一側完整歷史，無法證明新manifest的完整closure，明列待重產。兩側四檔與原JSON保於原Git parents及本次raw，沒有把混合來源說成帳本有效或架構已綠。

`公理層.md`／`決策佇列.md` 正規化bytes等前棒8033；本棒沒有改字。`current_geometry.c` 保完整CRLF。原cached whitespace check退出2來自前棒原streams、main README與決策原空白，刻意保bytes；精確自撰相關paths check0。封存collector首版因sparse未物化evidence目錄，在archive寫入前退出1，只加mkdir後原命令0；原工具與限制保留，未改產品或測試。

本次 #314 對抗靜審接受 f614 guard的有限範圍：相同final ParameterRef不能略過同軸ordered facts；兩具名正反例隔離同最終ref／value但不同當下歸因。final值相同仍照I24保留，不新增中途限制。這不代表M121已動態證成；巢狀參數包、realloc/OOM與其他歷史未驗邊界不外推。程序授權引用本次使用者實作指示與鎖定題3B／4B，不冒稱SSOT文字已另行核可或已改。

完整本輪命令、退出碼、環境、SHA與原stdout／stderr保在 [PROGRESS.md](https://github.com/ZhiQiYang/geometry-axiom/blob/1722b55445b53ac37b6eac1be7b379e79c73eaa8/evidence/geo299-316-stack-20261023/PROGRESS.md) 與 [SOURCE_MERGE_INVENTORY.json](https://github.com/ZhiQiYang/geometry-axiom/blob/1722b55445b53ac37b6eac1be7b379e79c73eaa8/evidence/geo299-316-stack-20261023/SOURCE_MERGE_INVENTORY.json)。本次封包120 members逐檔reopen核bytes／hash；這是封存驗證，不是產品gate。新增 [同儕靜審報告](https://github.com/ZhiQiYang/geometry-axiom/blob/1722b55445b53ac37b6eac1be7b379e79c73eaa8/evidence/geo299-316-stack-20261023/peer-review/COMBINED_SOURCE_UNION_15a73595_REVIEW.md) 僅接受source聯集與待驗標示，不冒新產品全綠。

原F5bf全綠收據只見 [歷史摘要](https://github.com/ZhiQiYang/geometry-axiom/blob/139ab64ca5f88e89bb4e95921675b998457026aa/evidence/geo299-316-final-5bfadf18/FORMAL_SUMMARY.md)。原整份帳本曾ENOSPC後同S補bridge subset，不宣稱單次full命令退出0；未捕獲舊core inner streams與reconstructed-not-captured C限制維持。Windows／MSVC未在雲端驗證，GDI只保原允許skip。

最不確定處是含#323／#314的新閉包尚未動態驗證。現在#288 P88專責獨占heavy lock，本代理沒有啟動compiler、scan、Chrome、benchmark或測試；source已交#318，接續共用棒由其唯一owner處理。GitHub API存取受限，只提供已推來源與prbody檔，不聲稱live PR正文已套用。未force push、未合併PR。
