# PR217 c75f238 審查 M2：最佳化模式不得省略裁判

M2成立。run_fragment_heap_gate的每個子程序明確使用複製後移除PYTHONOPTIMIZE的env；其他環境值保留。reference_fragment_stack、fragment_oom、fragment_gate_timeout三支獨立driver在import後用非assert的`if not __debug__: raise RuntimeError(...)`拒絕最佳化執行，涵蓋環境設定與-O/-OO，不會因assert被省略而寫PASS。gate本身沒有以assert作驗收，parent最佳化可以執行，但回歸child一律保留assert。

實跑對照（Linux／stack16MiB）：

1. 正常產品 + 修後gate，parent設定PYTHONOPTIMIZE=1：exit0，三次fresh編譯、stack回歸與guide OOM五命令皆0；來源／裁判／binary指紋與raw输出見fixed-*。
2. 受控副本保留heap、撤回B1三態修正，並撤回本次M2清除env與driver guard：同parent最佳化，gate exit0，OOM錯誤交易仍印PASS，重現假綠；before-*保留實際JSON與收據。這是明示的組合撤修，不冒稱它是某一個遠端head。
3. 同一個撤回B1的產品副本，保留本次M2防護：parent最佳化下gate exit1，在OOM必須拒絕交易的assert轉紅；after-*保留完整輸出。不是child啟動或編譯失敗。
4. 逾時handler撤修：舊式無guard timeout driver在PYTHONOPTIMIZE=1下exit0／PASS，raw stdout遺失仍未拒絕。修後timeout driver在同模式exit1，明示Verification requires assertions，未冒稱執行產品。兩者輸出分別opt-timeout-before與opt-timeout。
5. 修後OOM driver對舊fault bridge、stack driver在最佳化模式同樣明示拒絕exit1；正常模式timeout回歸exit0。四檔py_compile exit0。

prepare_opt217.py保留實際生成受控副本的過程；原B1版本include來自前輪暫存副本，與b2be的heap/false語意相同。正常與撤修三組gate的全部編譯／回歸raw stdout/stderr、命令／退出碼／耗時及SHA都保留。

本輪無產品碼、SSOT、suite期望數或native變異oracle修改。B2仍保留：尚未承接最新main或交精確最終head完整native／正式七項；這些額外gate與受控副本不是全量驗收。PR保持draft，不合併、不關#211。
