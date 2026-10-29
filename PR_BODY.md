# #348：H7、帳本、F1 原生探針與架構已通過，整合驗收續跑

**Draft／NOT READY。** 已完成 512 已放置完整 H7；native、census 及 browser 尚未全數閉合，不宣告可合併。

- 正式產品 **M=`7a0e6dd81c54066995981393925fa46a815de2f8`**。
- H7／35項接線測試 execution **T=`256747c5c8f8f8934eeb08ae404dee1f67591508`**；T→M 非 evidence 差異為零，沿用原 execution，不改標 M。
- 完整 PR head／已公開證據 **E=`75464e8cda864ebea6717f95853f724fb9278583`**。產品、執行與證據提交分列。
- 本次完整 census execution **L=`7c8e9cee4ed5b3706ee919e2831a1dac0aa55ea5`**；產品／測試仍與M一致，本次證據提交沒有改產品。

## 唯一現況矩陣

| 項目 | 真實狀態與界線 |
|---|---|
| 上游採入 | #343 `a934a554…`、#346 `eaf15e23…`、#347 `8bb03593…` 均為 M 祖先。#347 缺少上游提交數為0（behind=0）；舊 review 的 behind2 留作歷史，不宣稱上游所有未驗項因此完成。 |
| 完整 H7 | **T 真 exit0；8／0fail／0error／0skip**。inner 1142.122526秒、原外層 **1142.271674秒＜1200秒**；九批全部原0。原單批600秒、整套1200秒、16MiB stack不變。512 load、順序建立、真 preview token 確認、history、513拒絕及64／512 canonical fresh replay已驗。**取消／新token案例是7支已放置**的 `test_placed_history_uses_current_preview_token_and_one_undo`，不是512取消；兩種覆蓋分列。 |
| 新接線與既有反證 | **T 35項 exit0**＝新7＋原H13／W15。三個不同具名撤回各真0／1／0，hash工作差為2／2／4；原值、kind、有序依賴及舊負控保留，single-equivalent0不改稱kill。 |
| 凍結場景圖比較 | 真 execution **`622b665423a55b4042a638589d2cd1efff427c7e`**，172場景原0；plain／trace完整輸出、有序圖及五guards相同。185個實際build葉及172個輸入到T、再到M閉包相同；保留622b execution，這份診斷不替代H7。 |
| N128 profile | **M 原0／gprof0，5.982724714秒**；固定原B=`9a8584f57be7935604c3bad4c2481945a6ec3d9f` 的14.914534721秒不重抽。input.scene／stdout／stderr逐byte相同；literal stdin的loadfile路徑不同，不宣稱其bytes相同。這是 separate `-O0 -pg` 單點診斷，不是正式效能裁判。 |
| 完整123帳本 | **M 原 full=0／checkafter=0**，123筆：114 killed／1 crashed（M20）／5 equivalent／3 retired；零 stale／blocked／survived／unrun。原 precheck=1 保留。全份採入 `7c8e9cee4ed5b3706ee919e2831a1dac0aa55ea5`，採入後原 `python3 -B tests/mutate.py --check` 亦0；execution仍M，不改標採入或證據SHA。 |
| 完整 native／strict census | **L原完整census exit124，2100.075954秒逾時**，16:54:59.491547–17:29:59.567513 UTC。停第107/243套H7第8方法，後136套未起。102份已完成Python JSON小計1523／0／1原GDI skip，不是registry總數；expected前後逐byte不變，無可採diff。完整native仍未過，不能以獨立H7替代。 |
| 架構四份產物／原三裁判 | **M 真0／0／0**，generic205＋product18，0skip；604 inputs／798 edges／0 diagnostics。四檔採入純稽核提交 `d8550079d640347fade3124087464ce3bc4a6ce4`；receipt execution仍M，原manifest/policy/SSOT不改。 |
| #297 原生探針 | **M 真exit0**，64場景／2936支全接受，L／原點／A0全符，0容量拒絕／規則拒絕／錯誤／幾何不符。F1八排95／97／96／98／108／110／109／111支，共824；每場第65支以後共312支亦全接受。不外推未測116或其他512情境。 |
| 六個 browser jobs | **未完成**；不把其他SHA的歷史綠項改標目前來源。 |

## 固定原件

[本輪 README](https://github.com/ZhiQiYang/geometry-axiom/blob/06b81e452c9d80c210cbf10fe2f5da8eebfc31e5/evidence/geo300-capacity512-20261024/placed-h7-256747c5/README.md)／[STATUS](https://github.com/ZhiQiYang/geometry-axiom/blob/06b81e452c9d80c210cbf10fe2f5da8eebfc31e5/evidence/geo300-capacity512-20261024/placed-h7-256747c5/STATUS.json)／[完整 RAW](https://github.com/ZhiQiYang/geometry-axiom/blob/06b81e452c9d80c210cbf10fe2f5da8eebfc31e5/evidence/geo300-capacity512-20261024/placed-h7-256747c5/RAW.tar.gz)：3865檔，archive **4,872,174 B**，SHA256 `2a6798f772c50f88dc1fb4a10b51514ff767ab6144879a013dec7710bc797302`；已完成實際遠端逐byte讀回。

本包保全九批最後原流、inner REQUEST／OBSERVER、wrapper及11個本地archives。v7把同步Git/API發布移到整套終態後，原測試與計時不變；初始request checkpoint曾被一併移除，最後交付已補原件，不冒稱原初已有獨立request archive。

原600／1200超時、其他紅燈及中斷收據保留各自execution，不覆寫、不移標，也不把發布成功當產品通過。本輪普通merge只採入既有#348工作分支，未合併PR/main；不放寬I33、公理、斷言、golden或時限。

實跑命令（完整 argv、環境與原流在上列固定封包）：

- H7：`python3 -B /dev/shm/pr348-h7-256747c5-background.py`，內層原 `tests.test_geo261_timber_capacity_host` 八方法，外層原 `tests.run_all.run_process(..., 1200)`；每產品 batch 原600秒、stack16MiB。
- 35項：`python3 -B /tmp/pr348-runs/run_formal_v2.py --root /dev/shm/pr348-diagnostic-c754 --out /dev/shm/pr348-remaining-tests tests.test_geo300_remaining_depend_hint tests.test_geo261_load_residual tests.test_geo261_contact_sources`，exit0。
- M profile：`python3 -B /tmp/pr348-runs/profile_capacity.py --root /dev/shm/pr348-final-source-7a0e6dd8 --out /dev/shm/pr348-profile-m7a0e-n128 --count 128`；完整實際呼叫以固定 REQUEST 為準。

容量超過512仍回 `CAPACITY`、不截斷。索引記憶體成本保留：generic hint 4096 slots每context增加30,720B，H兩ordinal增加8192B，definition ordinal再4096B。CI最新狀態本輪未重新核實，不援引舊runner0或其他來源結果。

[H7 可讀原件](https://github.com/ZhiQiYang/geometry-axiom/tree/6061fd2b9d930b1cd233f2aabb669b943913ee3d/evidence/geo300-capacity512-20261024/placed-h7-256747c5/readable-originals)：直接抽出原 E06 封包中的 inner／wrapper REQUEST、RESULT、原 unittest.log／outer.log；EXTRACTION.json 列原封包member及逐檔SHA256，八份公開檔均已從遠端讀回核同。沒有重新執行或改標H7。

[#297／架構本輪原件與可讀輸出](https://github.com/ZhiQiYang/geometry-axiom/tree/2be7e5aa058bf5e7b14e2e33fbbf40261fe9dbc3/evidence/geo300-capacity512-20261024/probe-architecture-7a0e6dd8)：488檔，RAW 6,984,698 B，SHA256 `8669fe290da4b155cc21d3fce903e892b5f5b4ac2a2002128b96e7126f40de20`；實際遠端blob原bytes已核同。

#297沿原registry O2 core、16MiBstack及每次原120秒，使用原支援CORE_BIN：`CORE_BIN=/dev/shm/pr348-probe297-7a0e6dd8/build/core TMPDIR=/dev/shm/pr348-probe297-7a0e6dd8/tmp bash geometry-core/framing-template/core-probe/run_probe.sh /dev/shm/pr348-probe297-7a0e6dd8/run`。build0 15.145188秒／probe0 62.550101秒，全部原始場景無省略。CORE_BIN未列入capture安全環境欄，原build.log／executor／ELF與sidecar另核實，不掩蓋此收據限制，也不為它重跑。架構原三命令、205／18原日誌與舊新四檔在同包；同伴已逐原件核收，未另跑產品。

[完整帳本原件與核收](https://github.com/ZhiQiYang/geometry-axiom/tree/b72578441e69df5be7da290ffca606a458ebc3ae/evidence/geo300-capacity512-20261024/full-ledger-7a0e6dd8)：887檔含697份已保全原文字與175支原ELF；RAW 92,888,014 bytes，SHA256 `82d8535da2c13472c82d05ce1d95e5e9cfe35fe5c17a3f4f34e799db4b727a08`，實際遠端blob逐byte核同。執行區間2026-10-29T03:00:41Z–04:31:23Z，原命令 `python3 tests/mutate.py` 完整執行，不是只改帳本計數。獨立peer及原前後檢查在同目錄。


## 本次 census 原紅與處理範圍

原命令 `ulimit -s 16384; python3 tests/run_all.py --build --update-expected`，原2100秒守門終止子程序returncode -9，recorder exit124，cleanup完成。未改原600／1200／2100時限、未略過套件。進入H7前已用1103.06秒，剩996.94秒且後面仍有136套；將針對整輪實際產品與編譯成本修復，不重跑抽最好樣本。17:14:04.935–17:14:15.134有10.199秒R07局部browser重疊，來源為排程紀錄，這輪不是獨占效能樣本，不能無證據把整個逾時歸因於此。

[本次完整原件、可讀結果及獨立核收](https://github.com/ZhiQiYang/geometry-axiom/tree/75464e8cda864ebea6717f95853f724fb9278583/evidence/geo300-capacity512-20261024/native-census-L7c8e9cee)：21份原manifest檔案6,326,503 bytes，另附原MANIFEST與PEER；兩份tar為原bytes複本，沒有重封。23個公開檔均已從遠端逐byte讀回。expected SHA256 `e88f97a2c13e4ab561c071855ebf68f58bef5cec5d05ba20f453d58a23cf4209` 前後相同；帳本同樣不變。

[H7覆蓋範圍更正](https://github.com/ZhiQiYang/geometry-axiom/blob/75464e8cda864ebea6717f95853f724fb9278583/evidence/geo300-capacity512-20261024/placed-h7-256747c5/README.md)：只更正文案，原T執行身分與archive不變。六browser仍未完成，維持Draft／NOT READY。
