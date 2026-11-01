# #314 帳本容量事故與完整環境重試

兩輪都固定實跑來源 S：`9b65f047d5fd470cdc89ce45e613d06af493b616`。此提交只封存診斷，不是新最終驗收 F，也沒有把原紅改綠。

第一輪原 `python3 tests/mutate.py` 退出2，outer1：/workspace滿造成M63還原測試、M64還原build與M65目錄建立受阻；checkafter及source_after未錄到。57個core execution原已完成（52 killed、4 equivalent、M20 crashed），M20不冒稱斷言killed。

容量修復僅釋三個已公開且乾淨可Git重建的舊main比較clone，真回收3,045,318,656bytes；原parent raw前後hash保留。修復全部guard／argv／退出碼／完整streams／hash已封入同archive。

第二輪新out／新cache不覆第一輪raw。private scratch僅排三類歷史evidence，完整C閉包、505個oracle inputs、40個oracle hash與RESTORED36方法先核完全相同。以原CLI跑全40個bridge IDs，原57core紀錄保留；這不是單次full0。各原命令、真退出碼與完整輸出見ROUND_SUMMARY與原receipt，原後處理例外也照保，沒有重寫結束碼。

本輪發現M110首個bridge equivalent與既有runner的執行入口／execution validator不相容，原工具會寫invalid而非真等價execution。接下來依原核心規則精準修runner：明示equivalent且真baseline/mutant/restored完整survived才記equivalent，其他崩潰／斷言／受阻不冒等價。先做真CLI/bridge撤回0/1/0，再凍結新S整份重產100筆，舊57execution不帶入新S。

archive所有成員均解包逐bytes/SHA-256核同；ELF僅列hash及原sidecar，完整top-level命令streams與bridge已落盤raw保留。原core每內層編譯／oracle的原raw沒有逐檔落盤，不聲稱補捕到不存在的streams。
