本 PR 接手並取代 #337，整合 #299+#316、#314 題3鎖定比較器及 #318 已核可閱讀A；#323來源已全在列車，效能與負控制修正在本線完成。仍是 draft，未達 READY-TO-MERGE。

## 唯一 current-state 矩陣

本表取代先前正文狀態；舊結果僅留於 Git/evidence 歷史。產品 F=`f64d638f15c48d2b9723b7ae9d230fb5dacb82d9`；架構裁判 P=`17b3576434ffd0833056668898e1fd1a8cc2d560`；架構採用/上游合流=`4f4a24d76e816274bfae06868b4dbf31f0860299`；evidence head=`504933473d7b9bdfc5964f73402a710f1222fc96`，均已一般推送。最終全清單 SHA 尚待全帳本重產後固定。

| Gate | 實測來源 | 原 exit／結果 | 狀態、允許 skip 與限制 |
|---|---|---|---|
| #323 fixed-three | F | 0；13+22+15=50，19 controls | 綠；四新增+兩漂移修復0/1/0，獨立346checks；等價control仍0/0/0 |
| #323 原36次timing | F；base b74f9a2／main adbaebf9 | 0；N32/base .8118354877；N64/main1.2648005782 | 原≤1／≤1.3，其他N16/48亦綠；無重抽、無skip |
| #323 原4次profile | F | 0；calls64/32=364369/82668=4.4076184255 | 原≤4.5綠；perf/profile獨立358checks；原wrapper1仍含ABC紅 |
| #323 歷史175場景／350組exact ABC | F對歷史base | 1；3診斷差異 | 紅燈保留：#299有意新增V_EXTENSION定位邊/區間，stdout與stderr皆有後綴差異；不得稱整組綠。詳下節 |
| I11新增場景＋原scene runner | F | 0；單場景exact、166/0/0 | 綠；不是fullnative；獨立87輕核及formal binary hashes核對 |
| #323 完整memo撤回／恢復 | F | 未完成 | 執行準備中，不能借舊S失敗作本F反證 |
| #314 six suites／Node inspector | F | 0／0；103／13項 | 綠；Node是VM/nativebridge，非browser；獨立541checks |
| M121 原mutation CLI | F | 0；build0/0/0、test0/1/0 | killed真反證；全帳本未重產 |
| reader三條 | F | 0/0/0；51項 | 原件已完成，獨立peer封存中；無skip |
| 閱讀A native／oracle | F | 0／0；7項、12組0/1/0／14項 | 原件已完成、peer中。native41子row SHA原為null；父c387/前後Git綁定，來源hash原件保留、獨立核對中，未回填原件 |
| 架構三原裁判 | P | 0/0/0；generic205、product18 | 綠；manifest撤回0/1/0、四檔Linux重產，獨立686checks；無skip |
| 全突變帳本 | 待最終來源 | 未重產；歷史3417 --check=1 | 107stale/3retired/13unrun；root將整份123筆重產一次，不冒綠 |
| 完整native | 待最終來源 | 未跑 | 不用partial代替；原ulimit16MiB |
| canvas／assembly／documents／grid／space／timber | 待最終來源 | 六項均未跑 | Chrome156/Node24可用；不允許以環境skip冒綠 |
| P52／Q38／§7／P-189 | 待最終來源 | 未完成 | 原門檻／assertions／goldens保持 |
| 閱讀A矩形逐毫米／579與oracle專項 | 待最終來源 | 未完成 | 原quick全量及RC-run oracle兩個精準源撤回待跑，不用14個oracle單元取代 |

目前沒有新增允許skip。正式完整清單及全帳本未完成，本PR不可合併。

## 產品與診斷差異

#314 指定3b0b634f的17個完整產品／裁判blobs與M99–M121已在Claude起點內；逐byte核實，沒有為形式而覆蓋閱讀A。保留10-24核可的RC未覆木連續段量法；#335施工順序缺口依核可決策獨立追蹤，不另造公理豁免。

#323採成功接觸memo，完整保留每consumer相依kind/order；四個新contact負控制與兩個漂移負控制有單一具名ASSERT的0/1/0。原效能分母與門檻未改。

`QUESTIONS.md` Q-323-ABC列3場景：`_role_priority_mutant.scene`、`_s1_p8_l_room_primary_through_reflex_extension.scene`、`_s1_p8b_l_room_primary_through_reflex_extension_hi.scene`。#299提交6366304新增錯誤定位邊與區間，因此歷史base完整stdout/stderr不同。dump、完整有序來源圖、五guards與允許／拒絕相同；原compare先assert失敗，後續四元組另以獨立審查核，不冒稱原compare走完。正補同列車僅撤回memo的175場景嚴格全輸出/graph/guards對照與性能反證；不忽略文字、不撤銷#299功能、不換性能分母。等待的是審查界線，其他工作照常執行。

## 證據及並行工作

`evidence/geo337-train-20261024/PROGRESS.md`、各逐檔index與壓縮包保存原命令、exit、完整輸出、環境與實際SHA。已封source/fixed-three、#314及架構；perf/ReadingA封存接續推送。子代理peer數量是證據審查，不冒充產品測試數。

最新上游Claude f702與main425已普通merge；本輪只架構digest/derived、#333文件與證據，產品C/JS/測試相對F未變。18:25Git認證失效原件保留，18:55重試恢復並補推；無forcepush。Chrome156.0.8078.47、Nodev24.19.0、NotoCJK均在雲端。

#324與noWood各自疊在列車，不等合併才驗收；#324請求已推交接分支。#325/#331/#333不寫他人分支。本PR取代#337，但不自行關閉或合併任何PR。
