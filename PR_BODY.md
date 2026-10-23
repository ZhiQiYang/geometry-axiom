本 PR 接手並取代 #337，整合 #299+#316、#314 題3鎖定比較器及 #318 已核可閱讀A；#323來源已全在列車，效能與負控制修正在本線完成。仍是 draft，未達 READY-TO-MERGE。

## 唯一 current-state 矩陣

本表取代先前正文狀態；舊結果僅留於 Git/evidence 歷史。產品 F=`f64d638f15c48d2b9723b7ae9d230fb5dacb82d9`；架構裁判 P=`17b3576434ffd0833056668898e1fd1a8cc2d560`；架構採用/上游合流=`4f4a24d76e816274bfae06868b4dbf31f0860299`；新測試來源 S=`ec8e0d7e18aefa9b6b6b0cd26206ba720ea735f0`；evidence head=`2d1570691e4a29aafebdc0a4e739787d3fcdddaa`，均已一般推送。最終全清單 SHA 尚待全帳本重產後固定。

| Gate | 實測來源 | 原 exit／結果 | 狀態、允許 skip 與限制 |
|---|---|---|---|
| #323 fixed-three | F | 0；13+22+15=50，19 controls | 綠；四新增+兩漂移修復0/1/0，獨立346checks；等價control仍0/0/0 |
| #323 原36次timing | F；base b74f9a2／main adbaebf9 | 0；N32/base .8118354877；N64/main1.2648005782 | 原≤1／≤1.3，其他N16/48亦綠；無重抽、無skip |
| #323 原4次profile | F | 0；calls64/32=364369/82668=4.4076184255 | 原≤4.5綠；perf/profile獨立358checks；原wrapper1仍含ABC紅 |
| #323 歷史175場景／350組exact ABC | F對歷史base | 1；3診斷差異 | 紅燈保留：#299有意新增V_EXTENSION定位邊/區間，stdout與stderr皆有後綴差異；不得稱整組綠。詳下節 |
| I11新增場景＋原scene runner | F | 0；單場景exact、166/0/0 | 綠；不是fullnative；獨立87輕核及formal binary hashes核對 |
| #323 完整memo撤回／恢復 | F | 0/1/0；4.407618→6.053833→4.407618 | master/reaper/outer皆0；同列車175/350完整tuple全等；獨立6655checks。原47MB包尚僅雲端，下一批推送 |
| #314 six suites／Node inspector | F | 0／0；103／13項 | 綠；Node是VM/nativebridge，非browser；獨立541checks |
| M121 原mutation CLI | F | 0；build0/0/0、test0/1/0 | killed真反證；全帳本未重產 |
| reader三條 | F | 0/0/0；51項 | 原件與獨立629checks peer已推；無skip |
| 閱讀A native／oracle | F | 0／0；7項、12組0/1/0／14項 | 原件與獨立629checks已推。native41子row SHA原為null；父c387/前後Git及70C/H實際輸入獨立間接綁定，未回填原件；原ELF已由測試清理，只保原hash |
| RC-run精準builder／checker撤回 | F | 各0/1/0；原單一方法（6個assert） | actual377checks／0、包382checks／0；原件已推，非逐毫米quick |
| M151 owner-map 修正 | Claude 8f9301fc固定Git bytes | 0/1/0；每輪原15項 | 唯一撤回紅為完整registry相等斷言；獨立241checks，已普通merge到S |
| free-end唯一錨點修正 | 4f4原test／只修一葉variant | 1/0/1/0；每輪原9項 | 原紅AssertionError 1 != 3；fixed/restored各18 controls 0/1/0，獨立1328checks；已採用到S，不冒S fullnative |
| S原帳本檢查 | S | 1，過期 | 原check輸出完整封存；新兩tests葉改變bridge oracle hash，完整重產改在下列b6公開來源執行 |
| 架構三原裁判 | S | 0/0/0；generic205、product18 | 綠；S四檔Linux重產已於E9a05採用，604-input closure不變，獨立781checks／0及完整原件已推；舊P反證仍保原P角色，無skip |
| 全突變帳本：舊來源環境失敗 | 4f4a24d7 | 原CLI2／root1／原check2；108／123 | M118還原build的smoke目錄Errno28，接著M119 mkdir亦Errno28，20:44:44由原CLI提前結束；98killed／5equivalent／1crashed／3retired／1blocked，15未跑。M20按原policy為crashed，非assertion killed。原1272members完整原流與2031／2556checks獨審已推，紅燈不改標 |
| 全突變帳本：修正後來源 | b6e1e454（C/tests同S ec8） | 執行中；21:00:13 UTC已啟動，尚無最終exit | root原123完整重產；原core編譯cache只由原指紋判可沿用，仍重新跑全CLI，不搬舊判決JSON，不改原child時限或M118判定 |
| 完整native | 待最終來源 | 未跑 | 不用partial代替；原ulimit16MiB |
| canvas／assembly／documents／grid／space／timber | 待最終來源 | 六項均未跑 | Chrome156/Node24可用；不允許以環境skip冒綠 |
| P52／Q38／§7／P-189 | 待最終來源 | 未完成 | 原門檻／assertions／goldens保持 |
| 閱讀A矩形逐毫米／579與oracle專項 | 待最終來源 | 未完成 | 原quick全量未跑；RC-run兩精準反證已另列，不用14個oracle單元取代逐毫米專項 |

目前沒有新增允許skip。Linux僅保留原Windows GDI允許skip，完整native未跑前不預報實際skip數。正式完整清單及全帳本未完成，本PR不可合併。

## 產品與診斷差異

#314 指定3b0b634f的17個完整產品／裁判blobs與M99–M121已在Claude起點內；逐byte核實，沒有為形式而覆蓋閱讀A。保留10-24核可的RC未覆木連續段量法；#335施工順序缺口依核可決策獨立追蹤，不另造公理豁免。

#323採成功接觸memo，完整保留每consumer相依kind/order；四個新contact負控制與兩個漂移負控制有單一具名ASSERT的0/1/0。原效能分母與門檻未改。

`QUESTIONS.md` Q-323-ABC列3場景：`_role_priority_mutant.scene`、`_s1_p8_l_room_primary_through_reflex_extension.scene`、`_s1_p8b_l_room_primary_through_reflex_extension_hi.scene`。#299提交6366304新增錯誤定位邊與區間，因此歷史base完整stdout/stderr不同。dump、完整有序來源圖、五guards與允許／拒絕相同；原compare先assert失敗，後續四元組另以獨立審查核，不冒稱原compare走完。同列車僅撤回memo的175場景／350組嚴格全stdout/stderr/有序graph/guards對照與性能反證已完成（獨立6655checks／0）；它是新增因果證據，歷史ABC紅燈仍保留。兩支撤回ABC ELF只有事後補hash；逐場景五guards由原equivalence紀錄，沒有350份獨立guard raw，不虛構。不忽略文字、不撤銷#299功能、不換性能分母。等待的是審查界線，其他工作照常執行。

## 證據及並行工作

`evidence/geo337-train-20261024/PROGRESS.md`、各逐檔index與壓縮包保存原命令、exit、完整輸出、環境與實際SHA。已封source/fixed-three、#314、架構、ReadingA完整原件與RC精準反證。#323正式perf/ABC/memo五包47,120,357B尚僅雲端，已推小交接與actual peer，完整原件接續推送；不把摘要當作完整輸出。子代理peer數量是證據審查，不冒充產品測試數。

最新上游Claude8f9301fc與main425已普通merge；相對F產品C/JS未變，tests兩葉分別補M151登記與free-end唯一錨點。每個修正均保原完整斷言，撤回／恢復原件已推。18:25Git認證失效原件保留，18:55重試恢復並補推；無forcepush。Chrome156.0.8078.47、Nodev24.19.0、NotoCJK均在雲端。

#340原13項與7phase反證已真0/1/0/1/0/1/0，530actual／949publication checks獨審0；普通merge本列車後source4d3，原受測bfb SHA保留。#339的9個指定importer模組142／142與3組predicate反證全綠，source1f0已普通merge #340，原受測S57與當前source分列；整體native/browser/帳本仍未完成。#300候選c493的原三套驗收已取得10+15+7=32項原exit0，獨立actual審查與封存中，效能未跑；GEO260 af4的兩個focused控制各0/1/0已真完成，原c926 schema紅保留。各線不把部分驗收當全綠。#325/#331/#333不寫他人分支。本PR取代#337，但不自行關閉或合併任何PR。

`QUESTIONS.md`另保Q-314-SSOT與Q-335-CLI：Claude最後交接轉述使用者暫緩把I24/D29/D10b稿寫入SSOT，本輪維持已指定比較行為，不擅改公理、決策或相容版本；此轉述不冒逐字核可。13mm薄牆階正例B的CLI兩種初放路徑缺口仍另列#335，不以oracle通過宣稱CLI已支援。先準備反例與可逆方案，其餘驗收持續。

已封存10個root自有退休checkout的9510個immutable原碼副本（966個不同payload），完整可還原原件／映射／工具／指令與原exit0已推E b6e1e454；回收216,199,168配置bytes。Git objects、fixtures、收據與所有mutable/mutant/trace來源保留。這是儲存維護，不是產品gate。完整最終清單繼續執行，不因draft或待審而停工。

舊全帳本終態更正：前一版正文的「仍執行中」來自當時中間JSON；outer原收據確認20:44:44已因兩次磁碟不足退出2。原interim與錯誤輸出保留，當前矩陣已更正；67個core原stream映射未失配，但mapping工具因全CLI失敗原exit1，不能因此冒全123已驗。新來源的原全123已於21:00:13 UTC啟動；正式開始原件與30checks工具獨審已封存，尚未宣稱通過。
