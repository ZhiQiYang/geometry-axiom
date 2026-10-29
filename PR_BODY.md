R04：將角材容量由64擴至512，超量仍回CAPACITY，保留全部世界／history，不截斷。此PR仍為draft，尚未達合併條件。

## 唯一 current-state 矩陣（2026-10-29 02:40 UTC）

| 欄位／gate | 來源與實際狀態 |
|---|---|
| 完整 PR head／evidence E | `986feab13663b64f3e60658613916602f5b06574` |
| 正式產品 F2／history測試 C | `b595e55952d5d66de95024432e1b29bec7525e9b`／`75481194f3b85a6b07e11896403633d7d0fa0d6f`；新候選尚未合入本分支 |
| 目前上游 #347 head | `8bb0359331365c6f3a96872620427cf7847fcb50`；目前正式分支相對此ref behind **3**／ahead **34**。原審查的「相對目前base behind2」是當時snapshot，仍保留歷史，不能冒稱已追齊 |
| 阻擋1：來源鏈 | 隔離S=`796cd282693736af61c1b0d6c8ff91f03437a175`已一般merge私有M347=`291511caf4860638d6286b3b5b0cd17335c3b921`，含精確#343 a934a554ae58f16f124f1b264523947f170b3f0b、#346 eaf15e239324a6464a04740647afccce3a3c17c7、#347上述head，逐leaf確認只補evidence祖先。正式348待採入候選；原上游分支未改，其未跑gates未解除 |
| 阻擋2：512正式 H7 | **S已實跑但紅**：01:53:42–02:13:42UTC，1200.106348秒timeout，原exit=null。7方法ok；最後第二次512canonical未完。不得稱整套綠 |
| S 已完成單批 | 512load196.159859／195.964秒、sequential＋真I8a確認/history224.795秒、第一canonical228.876秒，各exit0、原600秒內；未完008不算通過 |
| 新候選產品／測試來源 | 產品`622b665423a55b4042a638589d2cd1efff427c7e`；只加測試的`256747c5c8f8f8934eeb08ae404dee1f67591508`，在`codex/geo300-dependency-hints-20261029`正常push，尚未採入正式產品 |
| 新候選受影響回歸 | 256747完整35項：新7＋原H13/W15，exit0、0fail/error/skip；三處各不同具名撤回0/1/0。622b的172凍結root scenes：plain/trace/stdout/stderr/有序圖及guards比較exit0，原baseline不重抽。這批新原件待下一次收件，不以S封包代替 |
| 新候選完整 H7 | 256747於02:38:14UTC正式開始，仍原600／1200秒與16MiBstack；本次正文時**尚未取得終態**，不得預列通過 |
| S before/after profile | 原B=`9a8584f57be7935604c3bad4c2481945a6ec3d9f` N128原14.914534721秒，S6.484310795秒、exit0/gprof0；input.scene/stdout/stderr逐byte等，原B不重抽。診斷不替代512正式gate |
| K/H先前回歸與反證 | K15 exec`edc57cd4a8f7e4eb5813d51435c4732b7d75b793`、H18 exec`057884a4388e72312067385b9cf738431d8d69e3`各0；172圖exec`4b17edac67648fb5f6048b05114a66e99eb1846a`為0。到S的185 build leaves／172輸入閉包有原件；execution不改標S或後續256747 |
| 保留原紅 | legacy98 exec4b17整輪exit1，唯一測試舊錨點失效，修後H18另列；原512600秒失敗、各未採候選、8b與S1200秒紅、環境中斷均保留，不覆寫或抽最好樣本 |
| 全突變帳本 | 尚未在最終採入來源整份重產。S的123項僅純anchor預檢，不是正式mutation判決 |
| census／架構／完整native／browser | 最終採入來源尚未完成；不以局部回歸代替。原35分鐘native、原各job時限與assertions不變 |
| CI | 先前七項runner0／steps空白只代表未執行；本正文未重查最新run，CI狀態保留unknown，不宣告產品紅綠 |
| 合併狀態 | **NOT READY／draft**。不合併PR/main、不forcepush、不改公理層 |

實際命令與收據：

- H7：原`tests.test_geo261_timber_capacity_host`八方法，外層`tests.run_all.run_process(...,1200)`；各產品batch原600秒、`ulimit -s 16384`。完整argv／build／環境／source／streams／退出或timeout欄位在各REQUEST/RESULT。
- 新35：`python3 -B /tmp/pr348-runs/run_formal_v2.py --root /dev/shm/pr348-diagnostic-c754 --out /dev/shm/pr348-remaining-tests tests.test_geo300_remaining_depend_hint tests.test_geo261_load_residual tests.test_geo261_contact_sources`，77.553515490秒，exit0。
- S profile：`python3 -B /tmp/pr348-runs/profile_capacity.py --root /dev/shm/pr348-diagnostic-c754 --out /dev/shm/pr348-profile-s796-n128 --count 128`，實際execution為S；當時來源與ELF身份已封，不將現在checkout當當時來源。

[S完整原件、閉包、原紅與profile](https://github.com/ZhiQiYang/geometry-axiom/tree/986feab13663b64f3e60658613916602f5b06574/evidence/geo300-capacity512-20261024/depend-hints-s796cd282)：6818members，RAW12,935,646bytes，SHA256`53301a3b89478646a27e1fad1c80284d7a558f06d09c0720bb9023e02e54eb15`，已逐member核對，遠端blob實際bytes讀回一致。

收據工具額外同步Git/API有20.641385秒落在舊1200內；這不是原產品測試的一部分，但不能斷言是唯一超時原因。新版原測試／量測主體不變、時計不暫停，改每批先持久/tmp fsync，整套終態後再發布。舊smoke工具87fd與補metadata-fsync後417eca的函式控制分別保原版本，不冒稱完整H7。

原/tmp native cache已另[可逆保全](https://github.com/ZhiQiYang/geometry-axiom/tree/986feab13663b64f3e60658613916602f5b06574/evidence/geo300-capacity512-20261024/native-cache-preservation-20261029)，遠端原bytes核同；未刪來源、不冒native已跑，也未擅認F9 ELF身份。新generic hint4096 slots為每ctx增加30,720B；H先兩ordinal增加8192B、最新definition ordinal再4096B，均明列成本，不隱藏記憶體交換。

歷史矩陣只保存在Git歷史與[evidence PROGRESS](https://github.com/ZhiQiYang/geometry-axiom/blob/986feab13663b64f3e60658613916602f5b06574/evidence/geo300-capacity512-20261024/PROGRESS.md)的歷史區；不與上表並列為目前狀態。
