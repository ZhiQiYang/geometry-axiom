# #211 reference_fragment_candidate heap 修正（部分）

只把此函式的 World 候選從 stack 移到每次呼叫獨立的 heap；副本內容、求值順序、全域診斷保存／還原與輸出賦值不變。三個返回路徑皆釋放。malloc 失敗在任何狀態變更前回 false；尚未對 OOM 做故障注入。

基底固定為 main 3156cc1c9dc4d2abc9c833974769d3ec66a9d46e。Linux / GCC 13.3.0 / Python 3.12.14；與前兩輪同環境。build stdout/stderr 保留；core、bridge、撤回修正的 mutant bridge build 皆 exit 0。

回歸命令：python tests/diagnostics/reference_fragment_stack.py <core> <bridge>。core 在16 MiB檢查既有場景；bridge在8 MiB核load/dump均ok:true、精確 definition_sha256 和 guide 原文。原 core+bridge：exit1，bridge SIGSEGV；fixed：exit0；實際把函式撤回到stack、重新編mutant bridge（fixed core不變）：exit1，bridge SIGSEGV。原stdout/stderr見各檔。先期診斷已在改產品前實跑相同場景的紅綠差異。

16 MiB 原CLI139場景修後139pass/0fail/0infra，exit0；runner stdout完整與原版逐bytes相同，fixed-native16.log保留。三個bridge場景的16 MiB原/修版exit、stdout/stderr均完全相同（comparison.json）。這是有限範圍的對照，不能宣稱所有產品行為不變。

這是產品碼，須走合併列車7項。完整native未跑；現有native收據只含139CLI場景。CLI8 MiB仍有其他大型框架，apply_subgrid_line兩份World尚未修；#211不可結案。前兩輪診斷證據保持。没有改公理、閱讀器、UI、workflow stack或測試期望數；新回歸是手動診斷入口，尚未登記進run_all。
