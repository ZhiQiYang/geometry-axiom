# 512 已放置 history 正式終態

execution C：75481194f3b85a6b07e11896403633d7d0fa0d6f，乾淨checkout。2026-10-28 22:24:24Z至22:40:30Z。observer exit0，1 test／0fail／0error／0skip，966.209439335995秒；launcher exit0，966.379551744001秒。

實際命令見formal/REQUEST.json及launcher/REQUEST.json：`TMPDIR=/dev/shm/pr348-run-temp python3 -B /dev/shm/pr348-run-formal-v4.py --root /dev/shm/pr348-active --out /dev/shm/pr348-history-c754-formal-v2 --durable /workspace/pr348-history-c754-formal-v2 tests.test_geo261_timber_capacity_host.TimberCapacityHost.test_real_placed_512_sequential_replay_and_safe_513_history`。16MiB stack，原分離K/W/H O0，原每batch600秒；不是每條命令600秒。

load batch468.402912679994秒、RSS251368KiB、exit0；sequential＋真I8a確認＋history batch491.646997819秒、RSS456208KiB、exit0。原幾何／順序／dump bytes／reference／513 CAPACITY／拒絕不改World／delete／Undo／Redo／pending-redo保全斷言均跑完。單批低於600秒不等於整個方法低於600秒；方法真實總耗時如上。

新ELF SHA256 b5c8614bd264276f272aba4d62d289cac487d67c84d355c25f6a985fda3abc2a；F2 ELF雜湊不同，不冒同一binary。C load stdout SHA256 47da66d3264fbe943e01e9085d26e73f4ad7317de7e1b41d48d64fd6f4b6c784，與F2原load逐byte相同。每批原stdin含真正confirm token、stdout、stderr、fixture、build-log及wait4 usage均封存。

原F2首H7（64/512 load及兩次fresh canonical）execution仍是b595e55952d5d66de95024432e1b29bec7525e9b；closure/逐項證明產品四子樹／192來源檔／62步flags與第一方法、setup、fixture、validator不變。沒有把整個變過的測試module說成相同，也沒有把F2第一方法移標成C新實跑。F2第二方法原I8a紅保留於b8722640，C第一輪外部SIGKILL無完整終態保留interrupted/，不算600秒timeout樣本。

仍未閉合：原完整H7 suite1200秒（F2首方法六批本身1516秒）、native job35分鐘、完整census/expected（host新8項而舊登錄7、memo新6等）、全帳本過期、架構三裁判及四檔、六browser、其餘專項與#343→346→347來源鏈。未新增skip、未合併PR/main、未改公理／I33／timeout。維持Draft，不是READY-TO-MERGE。
