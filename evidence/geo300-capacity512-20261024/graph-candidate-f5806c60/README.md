# 候選172場景：完整有序圖與原流一致

新execution f5806c60c6067a64776f979f77981e4aba087df3。2026-10-28 23:24:53Z–23:25:39Z，outer exit0，45.993538814997秒。原172場景全部比較通過，新跑plain/trace共344 child，子程序各原600秒、16MiB stack、64MiB發布reserve未改。

命令：`LANG=C.UTF-8 LC_ALL=C.UTF-8 python3 -B /dev/shm/pr348-reuse-graph/compare.py --fix /dev/shm/pr348-graph-fix-f580 --out /dev/shm/pr348-graph-reuse-f580`。建置：`python3 -B /tmp/pr348-graph-audit/compare_graphs.py build --root /dev/shm/pr348-diagnostic-c754 --sha f5806c60c6067a64776f979f77981e4aba087df3 --out /dev/shm/pr348-graph-fix-f580 --optimization O0`，兩編譯exit0。這是O0單翻譯單元診斷，不冒分離K/W/H正式H7。

舊B execution保持9a8584f57be7935604c3bad4c2481945a6ec3d9f；直接沿用E18c0056d9004353cdd90099ff1fa93fe0d85f841已發布原件，沒有重跑B、沒有移標F。先逐檔核固定manifest、172scenes、base ELF/build/REQUEST/RESULT、原stdout/stderr、完整gzip解壓SHA/bytes、5guards及all seal markers；REUSE_FILES.json記原archive member與本地核收hash。新stdin沿原scene絕對路徑逐byte相同，沒有正規化或白名單。

新plain/trace stdout及stderr相同；與B的stdout/stderr、每seal完整ordered nodes/descriptors/status/typed values/edges、五guards原文字、seal次數全部相同。RAW只收新執行與閉包工具；舊B原件沿固定E18連結，不再複製同版raw。

候選尚未採PR348產品。後續scope型索引原型是另一來源，不能沿用本圖收據冒新產品全綠。正式512/H7、全native/census/帳本/架構/browser及上游鏈仍未完成；不改公理、容量、timeout或skip。
