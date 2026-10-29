# #348：完整 H7 通過，後續驗收仍進行

**Draft／NOT READY。** 已完成 512 已放置完整 H7；完整帳本、native、census、架構及 browser 尚未全數閉合，不宣告可合併。

- 正式產品 **M=`7a0e6dd81c54066995981393925fa46a815de2f8`**。
- H7／35項接線測試 execution **T=`256747c5c8f8f8934eeb08ae404dee1f67591508`**；T→M 非 evidence 差異為零，沿用原 execution，不改標 M。
- 完整 PR head／已公開證據 **E=`06b81e452c9d80c210cbf10fe2f5da8eebfc31e5`**。產品、執行與證據提交分列。

## 唯一現況矩陣

| 項目 | 真實狀態與界線 |
|---|---|
| 上游採入 | #343 `a934a554…`、#346 `eaf15e23…`、#347 `8bb03593…` 均為 M 祖先。#347 缺少上游提交數為0（behind=0）；舊 review 的 behind2 留作歷史，不宣稱上游所有未驗項因此完成。 |
| 完整 H7 | **T 真 exit0；8／0fail／0error／0skip**。inner 1142.122526秒、原外層 **1142.271674秒＜1200秒**；九批全部原0。原單批600秒、整套1200秒、16MiB stack不變。512 load、順序建立、真 preview token 確認、取消／undo／redo、513拒絕及64／512 canonical fresh replay均在原八方法內完成。 |
| 新接線與既有反證 | **T 35項 exit0**＝新7＋原H13／W15。三個不同具名撤回各真0／1／0，hash工作差為2／2／4；原值、kind、有序依賴及舊負控保留，single-equivalent0不改稱kill。 |
| 凍結場景圖比較 | 真 execution **`622b665423a55b4042a638589d2cd1efff427c7e`**，172場景原0；plain／trace完整輸出、有序圖及五guards相同。185個實際build葉及172個輸入到T、再到M閉包相同；保留622b execution，這份診斷不替代H7。 |
| N128 profile | **M 原0／gprof0，5.982724714秒**；固定原B=`9a8584f57be7935604c3bad4c2481945a6ec3d9f` 的14.914534721秒不重抽。input.scene／stdout／stderr逐byte相同；literal stdin的loadfile路徑不同，不宣稱其bytes相同。這是 separate `-O0 -pg` 單點診斷，不是正式效能裁判。 |
| 完整123帳本 | **M 於03:00:41 UTC真啟動，仍進行**。原precheck exit1／stale保留；scratch真53個bridge judge hash及完整source closure相同。尚無full-ledger／checkafter正式終態，不預填通過。 |
| 完整 native／strict census | **未完成**；定向35項及H7不能代替完整native。 |
| 架構四份產物／原三裁判 | **未完成**；待正式產物與原裁判收據閉合。 |
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
