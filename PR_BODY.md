容量64→512的placed load及canonical replay已在原600秒內完成；history的I8a確認接線已修，512修後重驗待收。完整套件時限與上游鏈仍未閉合，維持 Draft、未達合併條件。不剪依賴圖、不修改公理、I33或既有時限。

| 唯一 current-state 矩陣 | 固定身分／實際結果 |
|---|---|
| 完整PR head／新測試來源 C | `75481194f3b85a6b07e11896403633d7d0fa0d6f`；產品四leaf仍與F2相同，僅I8a測試及證據新增 |
| 產品／已完成正式execution F2 | `b595e55952d5d66de95024432e1b29bec7525e9b`；完整原件evidence E=`b872264006f400d600c801fe8c096d5679ad9013`，不移標execution |
| 原B | `9a8584f57be7935604c3bad4c2481945a6ec3d9f` |
| 直接base／阻擋1 | #347 `8bb0359331365c6f3a96872620427cf7847fcb50`；#343→#346→#347尚未閉合。原審查相對base **behind2**；目前C fresh compare為**behind3／ahead22**。鏈修好才一般merge、逐leaf重審與受影響重測 |
| 原B 512 placed load | 真timeout600.013933527秒、exit-9、wait4 RSS279492KiB；兩份歷史timeout也都在initial load，不冒稱replay/history各自已執行逾時 |
| F2正式512 load | **已實跑**482.595614208秒、exit0、wait4 RSS251460KiB；原幾何/ID/definition hash/reference斷言通過 |
| F2 canonical replay | **已實跑**500.587198156秒及529.473388700秒、均exit0，RSS256668／256564KiB；原第一方法全數斷言通過 |
| F2 sequential/history原紅 | 第二方法load492.981413560秒、sequential子程序496.086327713秒均exit0；但原test:279要求delete直接成功，實際I8a預覽必須確認，**方法exit1**。兩方法總2511.530170054秒、2tests／1failure／0error／0skip |
| I8a測試修復 C | 已接真preview token，原delete成功／無preview及全部history斷言保留；真7支baseline0／撤回confirm→dump1／restored0，具名placed-delete-confirm-must-commit。小例執行身分為b872加測試SHA256 a6b503157d857ddcd517aecbad97c8b9a295900167372a250baaa135ab44d507，與C測試blob相同；**修後512尚未完成** |
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

環境紅燈保持獨立：F1兩輪曾因Git補抓歷史objects填滿/tmp使收據不完整；F2首輪64 references在/tmp滿時失敗，後續自有512程序因已確認環境錯誤被中止outer130，非性能timeout。相同ELF在恢復空間後64完整輸出與先前smoke逐byte相同。原生libc tmpfile仍使用實體/tmp，不能只看TMPDIR；正式重開前核兩實體掛載的原64MiBreserve，期間不取件/發布，每batch完整raw立即壓縮持久保存。沒有刪除原件、fixtures或indexedGitobjects。

剩餘不確定：修後512 history、全suite時間預算、全帳本/架構及上游來源鏈。2026-10-28 fresh讀handoff與遠端，#343 a934a554ae58f16f124f1b264523947f170b3f0b、#346 eaf15e239324a6464a04740647afccce3a3c17c7、#347 8bb0359331365c6f3a96872620427cf7847fcb50均未變，仍有鏈阻擋。另觀測到既有dump在滿碟時仍報ok:true但輸出4096bytes的錯誤處理缺口，原件保留，未擅改該協定。
