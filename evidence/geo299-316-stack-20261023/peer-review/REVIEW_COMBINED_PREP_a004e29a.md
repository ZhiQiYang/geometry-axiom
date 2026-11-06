# combined 準備證據對抗審查

受審來源 Eprep：`a004e29a34b5fb880690e544057e90386e47e75a`，正文 Dprep：`f9ee52d12cb94055c330b37b3d77eb2768d12a96`。審查者為 #323 owner，範圍是來源／SHA／scope／ID／歷史結果標示與準備收據，不是新堆疊的產品驗收。

**本次未找到可確立的 metadata 阻擋。** `OWNERSHIP.md`、`PROGRESS.md`、`REVIEW_314_INITIAL.md` 與 `PR_BODY.md` 均明列新 stack 尚未產生／未跑；沒有把歷史 F5bf 或 #288 F13 的綠燈套到未產生的新 final SHA。這個結論只接受準備證據的標示，不能作為合併許可或動態驗收全綠。

## 已獨立核對

- 本地 source HEAD 為 Eprep、prbody HEAD 為 Dprep，兩工作樹 clean。Eprep 只新增 `evidence/geo299-316-stack-20261023/` 五項產物；F=`5bfadf187e615ba0fb8466753b63ce3044ef7d1c` 到 Eprep 的產品、tests、`公理層.md`、`決策佇列.md` 路徑差異為空。三份正文附件的 Git bytes 與 repo 外待審原件全等；正文 Dprep 也與待審稿全等。
- PREPARATION 固定 handoff `ea2748248d47563f8559638ccb70ec0ed21910d9`。11 份快照（HANDOFF、combined README、指定 rebased patch、八份 `_gen` 輸入）逐項重新 `git show`，原退出皆 0，bytes 與 SHA256 全部符合。該 handoff 的 review tree 確無 `299.md`／`316.md`；文件沒有假稱已讀這兩份留言。
- 對目前 `tests/mutate.py` 只做 AST／字串基數核對：數字 M ID 唯一、最大 M98；M89–M98 十個原 anchor 各恰一處。這支持既有 ID 邊界及靜態準備敘述，不能證明 killed、freshness 或新 stack 上仍唯一。沒有 import／執行 mutation 工具。
- #288 的 grid／timber 原收據均綁 F=`13d02c1db7022145a52ee063286a558e595eb212`、原退出 0。兩份 receipt hash、36 個具名小 command/script/version streams 的 bytes/hash、各原 stdout 指定 footer 行均重新核合。grid 為 completed partial／GEOMETRY_GRID_SYSTEM_ONLY、356／0、golden 未比；timber 為 completed partial／GEOMETRY_TIMBER_ONLY、79／0，原 included／omitted 保留。文件明列串行共用同一乾淨來源 checkout，沒有冒稱本次新平行測試或 full canvas。
- 歷史 F5bf 的原 FORMAL_SUMMARY 與本輪正文引用相符：native 224 suites／5184 pass／0 fail／1 原允許 GDI skip，七 job 原退出 0、三架構 0／0／0。正文仍保留 ENOSPC／同 S bridge subset、未捕獲 core streams、reconstructed-not-captured C 等歷史限制，沒有用準備工具退出 0 抹去那些原失敗。

## 仍須保留的界線

1. 新基底普通 merge、conflict closure、最終產品 SHA、native／browser／專項、精準反證、架構與帳本都尚未完成。本次不將「已推」或「metadata 審查未見問題」改寫成產品審過。
2. #314 的 ordered-facts 問題只在本輪檢查其文字、來源與待驗表述；沒有在此重作產品診斷或獨立驗證新 guard／M121。其實作審查與真 0／1／0 另行完成；M110 equivalent 仍須保留。
3. 未解包或重核 raw tar members／screenshots，未重新執行歷史 M89–M98，未檢查 Windows／MSVC，也未讀取 live GitHub API 或保證遠端 PR metadata 已更新。本次只核指定本地可解析 Git 物件、已提供小原件與文案。
4. 合流後再檢查全部 ID 聯集；目前 max M98 只屬尚未合入 #314／#318 的來源，不可外推新 stack 的 ID 邊界。

純讀核對明細另存同目錄 `COMBINED_PREP_REVIEW_CHECKS.json` 與 `COMBINED_GRID_TIMBER_SMALL_FILE_CHECKS.json`。前一份並保留 reviewer selector 第一版誤讀合成 `MA` ID 的退出 1；修正為僅選數字 M ID 後核對完成。這是審查小工具的篩選錯誤，未算成產品測試或突變判決。
