# PR217 承接 main 後的明示範圍驗證

測試對應的PRhead固定為2c409ca681c8025a4cd01a0e34be731cce7f4787，已正常雙親承接main e95437877ed15e819fdd3dba3ce5a9d43b84eeda；compare的merge-base即此main、behind0。此證據提交放在獨立evidence分支，不再移動受測PRhead。

測試副本不是完整clone；逐檔從受測head讀取Git blob SHA，與本地bytes計算SHA比對：native42quoted-include來源、4個fragment gate裁判/場景、mutation工具及139場景runner，共48個版本化檔完全相同。source-audit.json保存每檔blob SHA，沒有不符。不能據此宣稱所有repo檔均已物化。

必要fragment gate重新fresh編core/bridge/fault並實跑：五命令exit0，外層工具返回exit0；來源/裁判前後一致、各次raw輸出/命令/耗時/binary SHA保留。mutation --check exit0，40killed/1crashed/4equivalent/3retired、0stale。帳本仍綁原本明示d487本地快照，這輪只檢查現行同一closure/oracle的freshness，沒有將帳本HEAD改寫成合流SHA。

以本次fresh core跑tests/run_tests.py：139pass/0fail/0infra、exit0。這只是core CLI場景，不是tests/run_all.py完整native、也不是正式七項；不得把本次結果移算為B2全量通過。正式列車仍需最終來源完整native與七項。產品碼維持已審的heap/B1版本，main的公理、閱讀器及其他物件保持。
