# #314 新S整份突變帳本重產

實跑產品／裁判來源 P=新S：`c4aad5d7bb98ea864639f9e6d85c99bb2613c24b`；開始與結束 HEAD 相同，工作樹全乾淨。

| 原命令 | 實際退出碼 |
|---|---:|
| `python3 tests/mutate.py --check`（完整重產前） | 1 |
| `python3 tests/mutate.py`（不帶 IDs、整份100筆） | 0 |
| `python3 tests/mutate.py --check`（完整重產後） | 0 |

原 outer／reaper退出0。100筆=91 killed、5 equivalent、M20 crashed、3 retired；97個真execution.head全為上述新S，沒有把原舊S的57筆execution拼入。M20原三次同夾具存取違規照列crashed，不冒稱斷言killed。新增M99–120共22筆：21 killed，M110有真baseline/mutant/restored 0/0/0的equivalent execution。

58個未變C的合法原編譯快取（57mutant＋baseline）先以新S原fingerprint/cache_state核hit、複製bytes/hash一致，保原sidecar與原編譯來源；每個原oracle仍在新S整份重新實跑。編譯快取不當作舊execution證據。private scratch只排歷史evidence，完整Cclosure／505 oracle inputs／40原oracle hash與RESTORED36方法先核相同，沒有改原判準或使用者鎖定決定。

本輪先前容量full2／retry40原1與M110原invalid都在公開診斷D `01f1130fd0e93f61c698a963ee74ea349ac6820d` 原樣保留。runner精準修正只支援明示equivalent的完整真execution，原honesty suite74/74通過；真CLI／真bridge修正撤回0/1/0原輸出收於real-equivalence-proof。負控invalid且無execution，不冒killed；單筆proof不冒globalstrict0，本輪全100與strict原0才是整份帳本有效證據。

ASM錨點修正另以同一精簡private clone、原test_mutation_anchors三方法完成真正修正撤回0/1/0。原001收錄器因unittest字串repr換行誤判而退出1，原baseline0、撤回1與兩個正常AssertionError完整保留；002只補讀原finding與缺少的還原0，不重跑前兩相，不改產品或斷言。完整原兩輪與outer收於real-assembly-anchor-proof；FIX_PROOF_INDEX逐項區分修正自證與舊範圍產品mutations、環境retry及未適用項。

archive完整保存原命令／退出碼／top-level與bridge已落盤完整stdout/stderr／環境／SHA／工具與sidecars，全部逐member解包bytes/hash核同；原core子層未逐檔落盤streams只保其原structured outcome和hash，不捏造原raw。可重建ELF列hash，source clone可由真Git來源與原側錄重建，原雲端檔案仍保留。
安裝後原canonical sync／reader --check／mutation --check均退出0，公理層／決策佇列／Backlog／白話bytes保持相同；mutationcheck只用本輪private cache。帳本保真execution來源，不改寫成保存提交。

下一步：一般推送帳本保存提交L，在乾淨L以Linux重產架構四檔和原三裁判，固定公開A=正式驗收F；完整native與六browser仍由root排同一F，這裡不預填其結果。
