# #297 真原生探針與 Linux 架構驗收

兩項真 execution 都是 `7a0e6dd81c54066995981393925fa46a815de2f8`。#297 在03:46:09–03:47:27 UTC完成，原registry core建置exit0（15.145188秒）、原probe exit0（62.550101秒）。64個完整原場景／2936支全接受；逐支L、原點、A0足跡全符，容量拒絕／規則拒絕／錯誤／幾何不符／未跑為0。

F1八排法為95／97／96／98／108／110／109／111支，合824支；每場第65支以後合312支也全接受。不把未測的116支排法或512所有情境由此推成通過。512完整路徑另見已發布H7真execution256747。

實際命令：`CORE_BIN=/dev/shm/pr348-probe297-7a0e6dd8/build/core TMPDIR=/dev/shm/pr348-probe297-7a0e6dd8/tmp bash geometry-core/framing-template/core-probe/run_probe.sh /dev/shm/pr348-probe297-7a0e6dd8/run`。core由同M原`tests/binaries.py` registry編譯，原O2與16MiBstack、每次核心原120秒不變；未覆寫CORE_TIMEOUT/PROBE_SCENES_DIR。capture安全環境欄未列CORE_BIN，以原build.log實際輸入路徑、固定executor及ELF/sidecar補證，沒有重跑。探針原CORE_MAX_TIMBERS=64只產生歷史capacity註記，不截斷原輸入，也不是本產品容量判決。

架構03:50:27–48 UTC在同M乾淨獨立checkout跑原三條：

- `python -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json`：exit0，604 inputs／334 owned／270 exclusions／798 edges／0 diagnostics。
- `python -B tests/test_architecture_contract.py`：exit0，205／205、0 skip。
- `python -B tests/test_product_architecture.py`：exit0，18／18、0 skip。

原Linux driver重產四檔，已採入純稽核提交 `d8550079d640347fade3124087464ce3bc4a6ce4`；manifest bytes保持原登記，不改政策／SSOT。receipt保真M execution，closure `0c738c2c8b39b8cc4904bd39121f8ec9412f072cb2be6351b55e5b9f49f6fad0`，不冒自指artifact commit。

同伴核原probe311份raw、195build來源／185include閉包及所有L/XYZ/A0；架構核29命令、604原Gitblob與SSOT前後。另有本輪八產品檔組合靜審，未見新阻擋；這些不是另一次產品執行。原流、ELF、fixtures、命令、工具、前後四檔均在RAW.tar.gz，逐member hash/mode見MANIFEST。可讀原件在readable，複製保持原bytes、無JSON改寫，對照READABLE_MEMBERS。

原件共488檔，archive 6984698bytes，SHA256 `8669fe290da4b155cc21d3fce903e892b5f5b4ac2a2002128b96e7126f40de20`。完整123帳本仍在原輪執行；census／完整native35分鐘／六browser未完成，維持Draft／NOT READY。這次不重抽舊效能、不改原H7／probe門檻、不合main／PR。
