# 持續工作 checkpoint：F7 的 R7 已過 N64，N16 與 exact 仍紅，繼續推進

本檔是接續點，不是停工或完成報告。使用者不在，不提問、不空等；繁體中文、英文 commit。不 force push、不合併 PR、不推 claude/*／grok/*。主代理唯一寫 #338 主列車；每條來源由一人維護、另一人對抗審查。不得放寬斷言／golden／時限，不改決策佇列；公理只依已核可 SSOT 流程。

## 唯一當前狀態

| 項目 | 身份／結果 | 下一步與界線 |
|---|---|---|
| #338 主列車 | `codex/train-337-continue-20261024`；產品／測試／架構 F7=`6df0264f75e84f03adb70746b6ac3db07a9910fc`；證據 head=`5f27125c950162d9232c22bd966aad9a77e33dbd`；正文分支同名加 `-prbody`，D=`47ace3da0f416fc7b782c0ee1d240b3f1760b69c` | 本列 E／D 只由 root 的真普通 push 結果替換。產品 execution SHA 仍是 F7，不隨 evidence 前進而移標。 |
| R7 原五 stage | 真 outer exit 1；prepare/build/compare/perf/profile execution=`0/0/1/0/0`，累積 CLI=`0/0/1/1/1` | 原 36 樣本完整保留，不重抽較好的樣本。不是完整八 stage 驗收，all_required=false、full_acceptance=null；ABC_result 原欄缺席。 |
| R7 性能 | N64/main=`1.2292230778583162` ≤1.3 綠；N16/base=`1.05190582882169` >1 紅；N32/base=`0.8290229168845338`、N48/base=`0.7499983665267913` 綠 | combined 主責 N16 根因；下一個候選是 H reference_rebuild 的區域 ReferenceEval 零填移入真正 fallback。rank-bound 外稿尚未採，不混兩把產品刀。 |
| R7 原 source calls／exact | N32=82668、N64=364369，比=`4.407618425509266` ≤4.5 綠；原 175 scenes／350 runs 的同三個 stdout exact 差仍在 | 不刪 I22 診斷、不正規化整段比較。Q-323-ABC／Q-P189-EXACT 維持原待決策／判讀記錄，其他工作繼續。 |
| F7 tracked 帳本 | 原 check 仍 1；120 stale／3 retired | 完整 123 尚未重產。只有下一個穩定來源由 root 整份重產一次；保 120 個真 execution.head，採用 JSON 後 FINAL 再原 tracked --check，不篡改 head。 |
| 完整正式驗收 | 新 F7 的 full native、6 browser、P52、Q38(44)、§7兩項、P189 full+timing、required-eight/PF3/native後段、memo及其他 reader/RC/#314/ReadingA 專項未完成 | 定向測試不能冒完整 gate；原歷史來源的綠只保原 SHA。性能／完整 canvas 獨占，其他重工作最多兩個。 |
| required CI | 原 F7 run40070571951／E597 run40070806058 已讀：各7 failure、runner_id=0／steps=0 | 原 annotation 為付款失敗 OR 支出上限，已刊 current-R7-terminal；Ebd5 自身及後續新 E 的 CI 尚未讀，不移標。 |

## 本輪已公開與原件位置

- 完整 R5／R6 原件已公開於 E=`597bce63e296c85e64d33ca4496f167a599f0848`。R5 9055-member 單包、50132/0 peer；R6 9062-member 單包（9057 是準備路徑數）、50171/0 peer。原失敗、session tool-object 缺件附註、原 outer stdout/stderr 都保真，不能因出版完成改判正式 gate。
- R7 source `/tmp/geo323-final-r7-source-20261024`；tools `/tmp/geo323-final-r7-stage-tools-20261024`；原 OUT `/tmp/g337323R7`。完整原件已真封為 9128 members／31,359,550 bytes，tar SHA 前綴 `8f2420`、actual50504/0；已於 root E=`5f27125c950162d9232c22bd966aad9a77e33dbd` 普通提交／push公開 `evidence/geo337-train-20261024/full-R7-five-stage-raw/`（218葉／34,480,630B，含完整producer與原初敗）；永久Git blob=`09d8fbda73dd3995cb245be79ec7d339f3b23ade`。不得覆寫這輪 source/out 或重抽樣。
- K provider-hint 切片：S=`1449d430d1c4734bb1bc3a9f91f3851c845cc0f3`，E=`4d3ac4bf42f431c23833c8841e4a7a597d275dbd`，D=`ae5e9431bfb8feb3b8b8aa9ecce523af3135a5ea`；來源 `codex/train337-provider-hint-20261024`、正文同名加 `-prbody`。已普通合入主列車。source-index 原18與相關9/7/8全0，整刀 work0→16→0／正常0/1/0；原 edge21→31→21及原控制保持。原件 `evidence/geo323-provider-hint-1449d430/`；1579/2563/9904與452出版 peer。純 shadow 命中統計不是 wall-time 證據；R7才是新正式效能。
- #344：`codex/issue320-connection-recovery-20261024`，最新公開 S=`cbb318d76d7d242ae0db760ae15d57ef1cad4aa0`（一般 merge F7），新原 strict row9 真0。舊 S540 的 VM9／row9只屬歷史。新 fullcanvas fixed/withdrawn/restored 三 phase 仍 UNRUN，未合主列車；normalmerge403/0保原五 source 葉與 F7 source-index18。新的 E／D出版看 specials 真 RESULT，不填尚不存在的 head。
- #348：`codex/geo300-capacity512-20261024`，來源 F73=`73b21e64dce72f0d16ca29e18559c51815b9724d`，E=`9a8584f57be7935604c3bad4c2481945a6ec3d9f`，D=`1f0e9d8633c333114f2dce74315a9903e36a0dd7` 已普通 push。H3、三 helper 與 sentinel 四組定向反證完成；兩個原方法的第一個 placed512 四指令批次仍原 600 秒 timeout 紅；尚未到後續 sequential-history／canonical replay，原收件工具未留partial stdout，所以還不能只指向loadfile，容量未合主列車。完整原失敗與環境補跑分列；889 Git／286 evidence 葉出版4127/0，兩原 archive blobs 已永久引用，不可刪。

## 其他工作線：保原來源，不冒新 F7 驗收

| 工作線 | 保留身份／owner | 狀態 |
|---|---|---|
| #339／#340 | specials；原 F38／S175 | 祖先已合；#340 最新審查已解除13 aggregate缺件，仍 required CI，不自行判已接受。 |
| #341／#343 | combined；W source=`df66452e7a514032453bea93b8b18ab74d7b1457`；E=`f7a389deafed64f0f3137c0086a7033841c709e3`，D=`37a2f117529c15c6525be79b17389d47b43a9acd` | 原定向36、plane整刀0/84/0與見證反證保來源；已入列車。#341 四類 work/CPU/wall不得冒已完整。未採 rank 外稿另保，不改已公開收據。 |
| #342 | backlog 準備，原 source=`eb846c34` | 祖先已合；新 strict native30尚未完整整合驗收，當前 Q38應44。最新審查的 native30／CI／base 阻擋保留。 |
| #345 | specials；原 S=`2199cda8`，E=`99646d418bc5e886a92bfdabe33e68780e88fe3b`，D=`c5515c14ac9cb59d147563f3dd75dbde5b75ca4e` | 六次19方法／零skip真0；四控制屬等價0，不冒 functional kill。尚未有可合併裁決，未合列車。 |
| #346／#347 | combined／backlog；原 S=`39273bc0` cut-list、S=`32403481` empty-row | 原公開定向／反證保原SHA；未合列車。各既有 E／D以歷史 NEXT／該 PR原收據為準，本輪未更新；raw-seam 外稿未C。 |
| #325／#331／#333 | Grok | 不碰分支。木工端頭／固定／RC 推理先讀核可決策及 #333 FIELD-RULES。 |

更早歷史、各原工具與 source/E/D 已存 Git 的上一版 `handoff/NEXT.md`（來源 commit `230113da9b919861862eccbeb2c339bda94044e7`）。本稿不再堆疊舊 current-state；先 fetch handoff 分支，讀 `pr-reviews/*.md`／`pr-status.md`／`pr-requests/README.md`，新阻擋優先修。需要新 PR／正文就提交既定5欄 request，不等 bot 空轉；合併仍由本機處理。

## 全 native／完整帳本與空間守門

原 native ROOT 仍是 `/tmp/train337-323-f64d638f-source` 的歷史 L=`7af8c5d80d34cb4f49d01ba67deb78a3a6d725db`；尚未真正轉移。只可依新 consumer／HEAD/ref/index/sparse／逐可寫 inode／五 fixture 原bytes與Git身份守門，一般 checkout下一個穩定R；禁止 reset/clean 或刪 fixtures/收據。五 fixture L/F7 Gitblob相同不等於實體守門已過。F7相對L registry精確更新：source-index14→18、wood-contact9→14、host-sources39→45、rectangular11→13、section-profile28→30。

完整123工具原 prepare/observer/mapper保持；外部新增 `/tmp/geo337-full123-F7-admission-draft-20261024`，driver `7b6c57008921d7622ee6e47a987d7225a9318a7e53b582d3c1b9a1a5dd177eb1`、helper `bc93c7e37c29ed0ef3c93819e6e67ae0674f4b054ac7ab7df48a25ee718ba121`，52/0 static peer。只補原兩鎖內、原 formal 前的實際 TMP／WS 每 filesystem 額外配置預算，沒有改原123／120／時限。root須填真正 pinned budget、完成ROOT轉移，且先修 N16；不得從靜審推定可執行或全量帳本已綠。

**永久 `/tmp/geo337-published-archive-git-objects-20261024` 是 Git object store，絕不可作為 cache 清理、搬移或刪除。** 原 lease／alternates須保。新 storage TMP6 已真回收約309MB；所有原 archive path／bytes保留。L/U原git archive stdout加入R5/R6兩群後，8原path全保、4個新增硬連結實際回收WS 62,504,960B（06:56 UTC從22,159,360到84,664,320B）；新registry在 `/tmp/storage-maintenance-followup-20261024/L_U_R5_R6_EXTENDED_RAW_ALIAS_REGISTRY.json`，永久objects未碰。這是當時數值，仍先fresh df；所有新的工具／OUT／cache／編譯池優先用新的私有 TMP路徑，先 fresh df並保完整編譯峰值；不能只看 source物化大小。舊 alias registry只追加，不回寫歷史nlink，不把gross視為df淨增。

主代理接續：收斂 N16 的單因 H 修正與正常撤回／恢復，固定新的可解析來源後只跑所需正式輪次；同時處理 #344／#348及其他可推進線。原件、PROGRESS與唯一正文矩陣逐步普通 push，無任何停止指示。

## 最新審查與立即接續

root已fetch handoff `ef7b319101c`，新#338審查為2026-10-24T06:38:46Z／head597bce6。B1全驗收仍待，B2本輪R7的N64已綠但N16/exact未解，B3 required CI未啟動；C1舊正文已改以F7/R7終態及真currentCI，D以表內真push值為準，bot套用狀態仍查pr-status，不等待。

#339最新2026-10-24T06:38:47Z／head8f39025明確接受F38→F1的498-path closure保留142 importer與三predicate（舊B3解除），但正式11／native／browser／ledger／架構、requiredCI、#340基底接受都仍待。#324仍open的可見接替問題，請本機Claude在#324明確重導向#339並凍結／關閉舊入口；雲端未代發留言或碰Grok分支。原審查小note在 `/tmp/geo339-review-followup-ef7b3191-20261024/`。

當前H候選由combined唯一維護，backlog只寫獨立外部C harness，evidence靜審產品30/0；尚未合入列車。原O2 ELF顯示ReferenceEval 608→127,584B，persistent仍先零填不用的local，World／history BSS未增長；31/0只證真指令成本，不先宣稱能解N16。只把完整aggregate初始化延後到非persistent fallback；需真memset工作量撤回／恢復、persistent/fallback/失敗語義與原focused，再一般合流、重架構與正式性能。rank-bound外稿保持未採。H-only架構工具 `/tmp/geo337-architecture-h-local-init-tool-20261024` 已備94574f…、prior-source Me321、預期唯一input references.inc；新M尚未綁，三原裁判未在新候選跑。
