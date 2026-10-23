# #314 ASM cancellation anchor 修正真撤回自證

固定受驗來源：`c4aad5d7bb98ea864639f9e6d85c99bb2613c24b`；只撤回一行工具 anchor 的本地已提交負控：`238a5125c95e77d74603fdd943baaa81e140f7da`。原 `python3 -B tests/test_mutation_anchors.py` 全部三方法真退出為 **0／1／0**。負控有兩條正常 unittest AssertionError，原 finding 精確指出 tests/assembly_mutation_check.py 的 cancelled-preview anchor 在現行 engineering_bridge.inc 出現0次。產品與原測試斷言沒有改動，沒有編譯請求。

這是 **anchor 修正本身**的原三方法撤回控制；它沒有重新跑完整 ASM 產品行為 gate，不能與先前三個產品 guard mutants 的 killed 判決混稱。

001 已完成原 baseline0 與 withdrawn1，但外部 collector 對 stderr 片語的預期不符，故原 inner／outer 都是1，完整原錯誤與raw照保。002讀取同一份原負控 finding，**沒有重抽 baseline 或 withdrawn**，只完成原缺少的 restored 三方法，原退出0；002 inner／outer都0。這份封存沒有把001的1改成0，也沒有以新的測試代替原紅。

archive 保存兩次inner、兩次outer的全部原receipt／argv／stdin／stdout／stderr／退出碼／環境／SHA／tools，原CONTROL_COMMIT及精確一行WITHDRAWAL.diff，以及完整私有source的目前恢復後 `c4aad5d7bb98ea864639f9e6d85c99bb2613c24b` bytes。僅 `.git` bookkeeping 未封；負控commit原物件文字與diff、原P2工具bytes也由當次原命令stdout保留。每個封包成員path／bytes／SHA-256均已解包核同，所有原command streams也按原收據核同。

`PUBLICATION.json`／`MEMBER_INVENTORY.json`／`EXCLUDED.json`明列範圍、退出碼與hash；沒有改動／釋放任何原raw、private source或main source，也沒有啟動測試、compiler、retry、commit或push。這份小proof不冒稱整份帳本／最終F七項驗收結果。
