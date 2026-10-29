容量64→512的placed load、canonical replay、sequential history各批均已在原600秒內完成；history的I8a確認流程已修，原幾何／保存／Undo／Redo斷言全數保留。完整套件1200秒預算與上游鏈仍未閉合，維持 Draft、未達合併條件。不剪依賴圖、不修改公理、I33或既有時限。

| 唯一 current-state 矩陣 | 固定身分／實際結果 |
|---|---|
| 完整PR head／evidence E | `2b9b9086470b5abb30383f7617cc51c737c123ec`；新測試／history execution C=`75481194f3b85a6b07e11896403633d7d0fa0d6f`。E只追加原件，execution不移標 |
| 產品／已完成正式execution F2 | `b595e55952d5d66de95024432e1b29bec7525e9b`；完整原件evidence E=`b872264006f400d600c801fe8c096d5679ad9013`，不移標execution |
| 原B | `9a8584f57be7935604c3bad4c2481945a6ec3d9f` |
| 直接base／阻擋1 | #347 分支current ref（Git及API git/ref同值）=`8bb0359331365c6f3a96872620427cf7847fcb50`；相對新E **behind3／ahead28**。REST PR物件base.sha另回歷史快照`2e8a6ed20325aa4842dcd0f89eacd598662be598`，相對它**behind2／ahead28**；兩種身分分開，原審查behind2保留。#343→#346→#347仍未修鏈，一般merge及逐leaf重審待鏈閉合 |
| 最新隔離候選（尚未採入產品） | `codex/geo300-consumer-scope-20261028` @ `8b128aa7bf53b41b493dd3a0bee49f0d53391254`；K有序scope／完整hash重用、H未使用raw facts延後。9ac來源120項119過1個新測試定位錯誤，8b只修唯一anchor後新7全過、三項具名撤回0/1/0；H9與其餘產品/測試不變。172完整有序圖已exit0。原新fixture/anchor紅均保留，未說一次完整120綠 |
| 候選3949真512 load | `3949deb9e565a9e5aeca5bc475ec646e77cc6546`，261.840563475秒、exit0、RSS222088KiB、原placed_geometry過；stdout與舊F2/C全等。只有單個load，不冒8b或完整H7結果 |
| 候選8b完整H7 | **正在實跑，尚無終態**；00:12:43Z起，固定`8b128aa7bf53b41b493dd3a0bee49f0d53391254`，原八項整suite1200秒/每batch600/stack16MiB。原run_all.run_process及kill_tree控制整套時限，遠端checkpoint時間也計入；不延長或取最好樣本 |
| 原B 512 placed load | 真timeout600.013933527秒、exit-9、wait4 RSS279492KiB；兩份歷史timeout也都在initial load，不冒稱replay/history各自已執行逾時 |
| F2正式512 load | **已實跑**482.595614208秒、exit0、wait4 RSS251460KiB；原幾何/ID/definition hash/reference斷言通過 |
| F2 canonical replay | **已實跑**500.587198156秒及529.473388700秒、均exit0，RSS256668／256564KiB；原第一方法全數斷言通過 |
| F2 sequential/history原紅 | 第二方法load492.981413560秒、sequential子程序496.086327713秒均exit0；但原test:279要求delete直接成功，實際I8a預覽必須確認，**方法exit1**。兩方法總2511.530170054秒、2tests／1failure／0error／0skip |
| I8a測試修復與512 C | **已實跑原第二H7 exit0，1test／0fail/error/skip，966.209439335995秒**；load468.402912679994秒／RSS251368KiB、sequential＋confirm＋history491.646997819秒／RSS456208KiB，各batch原600秒。真7支0/1/0具名撤回命中placed-delete-confirm-must-commit；C清潔7支也exit0 |
| F2→C沿用邊界 | 四產品子樹／192來源檔／62步build flags及第一H7方法、setup、fixture、batch、validator同源，詳E的closure原件；F2首方法按此保留原execution，**不是C重跑**。兩版ELF hash不同，不冒binary相同。整個測試module有新helper/方法，不能說全tests閉包相同 |
| F2 source-index | 29項、0fail/error/skip、exit0；原21保留，4新增正例及4具名撤回已實跑。可選uint32索引溢位回原線性搜尋，權威size_t ID/count/ordered arrays未縮窄 |
| H/W修補控制 | **F2已實跑32項exit0**：H6＋W14＋W容量7＋H7其餘5，118.664619289秒、0failure/error/skip。原版本具名撤回也保留各自execution |
| B→F2 exact graph | **已實跑**172原根scene×4程序，共688次；stdout/stderr、所有seal的完整有序圖、五guards及seal次數逐byte一致，exit0，無白名單。O0單翻譯單元診斷，不冒分離K/W/H正式build；容量額外N64/N128圖比較未跑 |
| profile | 原B N12814.914534721秒；F2 N12810.398193599秒，均exit0且stdout byte相同。全部中間樣本與-pg原件保留；profile累積child_maxrss含compiler，不能作產品RSS或推定512全通過 |
| mutation ledger | F2 `python3 -B tests/mutate.py --check` 真exit1：107stale、13unrun、3retired；需完整重產，尚未綠 |
| 架構／完整整合／阻擋3 | 原三裁判與四檔、完整native、六browser及其餘專項尚未完成；expected新增登錄依完整census待重產。原run_all H7 Python suite1200秒、native job35分鐘不變，F2第一方法六批已1516.046849611秒，**完整H7時間預算仍不符**；不以單batch600秒代替整組通過 |
| 允許skip／合併狀態 | 目前已跑項0 skip；完整native沿原具名允許清單（Linux無Windows GDI），不新增豁免；未跑明列未跑。不是READY-TO-MERGE、不合併、不force push |

原始證據：[本輪6076檔完整raw與manifest](https://github.com/ZhiQiYang/geometry-axiom/tree/18c0056d9004353cdd90099ff1fa93fe0d85f841/evidence/geo300-capacity512-20261024/packed-index-b595e559)。RAW.tar.gz 6,346,587bytes，SHA256 `33a3b5ad029f7d084f38fca9f0453514d1608f556d1c078c02d17e22e27a025d`。原F0f/F73/F1各保原execution SHA，歷史失敗不得改標或抹除。

正式命令（observer只保存原流、binary hash及wait4 usage，不改原assertions、commands或timeout）：

```sh
GIT_NO_LAZY_FETCH=1 TMPDIR=/dev/shm/pr348-run-temp python3 -B /dev/shm/pr348-run-formal-v3.py --root /dev/shm/pr348-formal-b595 --out /dev/shm/pr348-formal-placed-b595-v2 --durable /workspace/pr348-formal-placed-b595-v2 tests.test_geo261_timber_capacity_host.TimberCapacityHost.test_real_placed_64_and_512_load_dump_and_canonical_replay tests.test_geo261_timber_capacity_host.TimberCapacityHost.test_real_placed_512_sequential_replay_and_safe_513_history
# 21:13:05Z開始，終態exit1，2tests/1failure/0error/0skip，2511.530170054秒。
```

[F2完整兩方法、32項控制、帳本check及static-pg原件](https://github.com/ZhiQiYang/geometry-axiom/tree/b872264006f400d600c801fe8c096d5679ad9013/evidence/geo300-capacity512-20261024/formal-f2-b595e559)：1680檔，RAW.tar.gz 4,358,709bytes，SHA256 `63836ba927e531676aabc56729e69ecd2f324dbbc9914f296f66b0f966ed4036`。
[I8a小世界0/1/0原件與完整原fixture](https://github.com/ZhiQiYang/geometry-axiom/tree/75481194f3b85a6b07e11896403633d7d0fa0d6f/evidence/geo300-capacity512-20261024/history-protocol-20261028)：實際命令`python3 -B /dev/shm/pr348-history-protocol-check-v2.py`，outer0；fake child僅驗觀測工具deadline，不冒產品通過。

[C完整512 history原件、逐項沿用閉包與環境](https://github.com/ZhiQiYang/geometry-axiom/tree/0cd9739e7701293a42e244dcf2b2f51e71ea7216/evidence/geo300-capacity512-20261024/history-complete-75481194)：630檔，RAW.tar.gz 1,768,895bytes，SHA256 `6c34c809d679cb25276371807b05c0b7a46241cdf5bd9c7a82772c41b9e81677`。正式命令：

```sh
TMPDIR=/dev/shm/pr348-run-temp python3 -B /dev/shm/pr348-run-formal-v4.py --root /dev/shm/pr348-active --out /dev/shm/pr348-history-c754-formal-v2 --durable /workspace/pr348-history-c754-formal-v2 tests.test_geo261_timber_capacity_host.TimberCapacityHost.test_real_placed_512_sequential_replay_and_safe_513_history
# 22:24:24Z–22:40:30Z；observer exit0，launcher exit0，完整原參數與三流在RAW。
```

「各batch低於600秒」不等於整個方法低於600秒；原第二方法真實總耗時966.209439335995秒。原首方法六批1516.046849611秒，所以完整H7 suite1200秒仍不能宣告通過。C首輪工具session中斷留下SIGKILL，沒有完整終態／沒有600秒逾時判定；原件保留，這次獨立背景重跑才是完整結果。

環境紅燈保持獨立：F1兩輪曾因Git補抓歷史objects填滿/tmp使收據不完整；F2首輪64 references在/tmp滿時失敗，後續自有512程序因已確認環境錯誤被中止outer130，非性能timeout。相同ELF在恢復空間後64完整輸出與先前smoke逐byte相同。原生libc tmpfile仍使用實體/tmp，不能只看TMPDIR；正式重開前核兩實體掛載的原64MiBreserve，期間不取件/發布，每batch完整raw立即壓縮持久保存。沒有刪除原件、fixtures或indexedGitobjects。

剩餘不確定：全suite時間預算、全帳本/架構及上游來源鏈。2026-10-28 fresh讀handoff與遠端，#343 a934a554ae58f16f124f1b264523947f170b3f0b、#346 eaf15e239324a6464a04740647afccce3a3c17c7、#347 8bb0359331365c6f3a96872620427cf7847fcb50均未變，仍有鏈阻擋。另觀測到既有dump在滿碟時仍報ok:true但輸出4096bytes的錯誤處理缺口，原件保留，未擅改該協定。

[候選完整原件與逐execution結果](https://github.com/ZhiQiYang/geometry-axiom/tree/dbdf68cf0181e84171d61d7164d1beb7b70556e9/evidence/geo300-capacity512-20261024/hotpath-candidate-f5806c60)：4094檔，RAW.tar.gz 3,769,944bytes，SHA256 `d9dcb7ffd944f4c952d3a47e819aae9f3ca95cf71088e55fe2fafababf4ccb80`。原正式F2/C不變，候選尚未合入PR348，不將候選unit綠冒作full native綠。

[候選f580的172場景完整圖原件](https://github.com/ZhiQiYang/geometry-axiom/tree/e4d00c43ed204aa3f07606a86cd625c59dce2184/evidence/geo300-capacity512-20261024/graph-candidate-f5806c60)：23:24:53Z–23:25:39Z，exit0，344個新child；舊B沿固定E18逐檔核收未重跑。所有原stdout/stderr、ordered graph、5guards、allseals一致。2444檔，RAW.tar.gz 2,808,004bytes，SHA256 `f39ac6dabee46f8fbdcf2c9ef8219a5249c8ec353a443669ac3e496268868e44`。此候選尚未採入PR348；正在隔離驗證的scope索引原型需要自己的新證據。

[最新候選原件](https://github.com/ZhiQiYang/geometry-axiom/tree/2b9b9086470b5abb30383f7617cc51c737c123ec/evidence/geo300-capacity512-20261024/hk-candidate-8b128aa7)：6671檔，RAW 5,298,656bytes，SHA256 `b9c259b159cf98b98450edef410b6369d4bb8a4e0ad613af6dae2ea459fe6818`。一次N128配對3949 5.134406→8b 4.933180秒，原流相同；只診斷，不外推正式512。原f580圖／各效能樣本保持歷史execution。

[3949真512載入原件](https://github.com/ZhiQiYang/geometry-axiom/tree/a6e20eb481cf8a5822ce225e68f73cb6f994ac95/evidence/geo300-capacity512-20261024/scope-load-3949deb9)：RAW 1,066,380bytes，SHA256 `e6908d2924052c8ce397d8cae07f61bb3445d00e7c5591613008df66cbff9a23`；261.840563秒的原600限制沒有變。現在workspace233472B不足原400KiB文字規劃，所以完成batch改推獨立receipts branch並GitHub blob實bytes讀回；v5工具前置紅、v6小history smoke綠皆保留。真/tmp64MiB、發布64MiB reserve、mount/quota不變，未刪未知快取。這是持久化安排，不是降低產品驗收。
