# S10 全帳本正式執行中；Q38 完整原件已封存、尚待出版

以下是唯一 current-state；完整歷史與原件見末尾固定 SHA 連結。維持 draft，未標 READY-TO-MERGE。未將 PR 合入 main、未部署。

| 身分 | 完整 SHA／意義 |
|---|---|
| 新產品／裁判來源 S10 | `82c922a3941525d3a094ac0158bdc7dea57ea360`，已一般推送，兩個變動葉皆從 GitHub 下載完整 bytes 核對 |
| main 同步 parent | `405f8c5e1a637a16cbe47470faf5ae1fa02b8676`；一般 merge 到列車，未寫 main |
| 前一完整證據 E／另一 parent | `249a05ed4c8a085bdf3353ac781638f2a9b3d460`；217葉、190 unique blobs 遠端核對0，獨審5066/0 |
| 目前 evidence E | `3e4f2560aa11ed2a626db98ba5ed6f129e791052`；本次只更新PROGRESS，普通push與遠端完整blob核對通過。完整#314／S10採入原件仍位於祖先 `d45e66aebdcd27602134990eefb6a5d0ff9bad21` |
| 正文版本 | 本份對應上述E；前一D=`74f4f0b27858568dbbd72977aee61b9030e870bf`是E d45的歷史快照 |
| 完整 index 保全 package head | `963cbfa71d01aacf9275e384cdafc67ad7dcaeeb`；362葉／169 unique遠端完整blob核0、actual7109/0；四份原index仍存在、未回收 |
| 本批 evidence 範圍 | 只更新本進度檔；Q38完整封包已備好但尚未push／remote核對，不宣稱本提交含該封包 |
| 舊正式來源 F9 | `4f8a794f4167c3562eb182045102e86e9e37cca9`，所有F9執行SHA保留原值 |
| 帳本與R8執行 F8 | `75a1e93811a52b69385cbdaf6a09d773ed9052ad`，原R8不重抽 |
| 後續正式驗收 final F | 尚待S10整份帳本重產／採入與必要架構產物固定；不得把S10與之後帳本commit混寫為同一SHA |

| Gate／工作 | 真實終態與新來源界線 |
|---|---|
| main同步＋#314採入 | S10 root executor exit0；原 `git merge --no-commit --no-ff` exit1僅決策同點插入衝突，精確解完後commit／一般push0，兩parent恰E249/main405 |
| 新來源變更範圍 | 只有 `tests/test_geo314_commit_paths.py` 與 `決策佇列.md`，mode100644。全部K、產品runtime、公理、golden、fixtures、workflow不變。決策兩塊各自逐byte保留，未新增決定或改🔒文字 |
| #314完整11項反證 | F9＋明列暫態patch：fixed0（11pass）／withdrawn1（10pass＋精確source.c FAIL）／restored0（11pass）；四類K違規各1→0，v3外層0、restoration errors空，原index與來源逐command守門全過，獨審349/0。不是S10完整native結果 |
| #314原失敗 | F9 native仍exit1，唯一assertion `I24 submission policy must not change K files`，額外`geometry-core/kernel/source.c`；v2反證外層index guard1亦保留，未改判或覆寫原index |
| 完整native | F9原exit1，1846.506872秒≤35分鐘，5327pass／1fail／1允許skip；S10／後續final完整native UNRUN，須採新帳本後跑原清單 |
| canvas | F9原exit0，2267assertions／85golden相符，1723.223173秒≤35分鐘；S10未重跑，尚不移標 |
| assembly | F9第二次原exit0，150assertions，188.843305秒≤15分鐘；第一次socket path過長環境exit1完整保存；S10未重跑 |
| documents | F9原exit0，47assertions／8screens，63.197160秒≤10分鐘；S10未重跑 |
| grid | F9原exit0，356assertions／P88=143，464.984065秒≤15分鐘；S10未重跑 |
| space | F9原exit0，242assertions，209.339秒≤15分鐘；原scope不含兩timber組，S10未重跑 |
| timber | F9原exit0，79assertions，124.531604秒≤20分鐘；原scope保持，S10未重跑 |
| Q38 | F9原完整44項／launcher exit0；43killed＋SPM24 equivalent（不是skip），SPM38/40保原ModelError。原件2051/0、獨立對抗無阻擋；完整346檔14,674,721B、gzip3,194,792B，完整封包尚未push／remote核對；封包actual2476/0及獨立審查無阻擋，原產品execution仍F9。S10未重跑 |
| §7 axiom mutations | F9原exit0，baseline與五次restored各44tests，V01–V05全killed；完整206檔包已在E249交付。S10未重跑 |
| 帳本 | S10原check真exit1：53 bridge oracle stale（52原killed＋M110原equivalent）；其餘62killed／M20原crashed／4equivalent／3retired。已於2026-10-25T16:05Z啟動原完整123重產，RUNNING，尚無正式exit；不是只更新過期53列。F8全123原0、F9check0保留原身份 |
| 架構三條／四檔 | S10三原judge真0/0/0，unit205＋product18；#314原full11與決策採納15亦0。604 inputs不變；四檔需以當次原流與新決策SSOT snapshot重產，尚未完成，歷史九反證保留M6e50身份 |
| reader三條 | F9原0/0/0，51tests、207clauses／1261blocks；公理／reader未變，S10未重跑，保留F9實際SHA |
| #323 R8效能 | F8原36樣本四時間門檻及calls比例綠，原五stage outer1保留；未重抽，也不因非效能SHM驗收外推性能 |
| #323跨版本comparison | F9原outer／stage／audit0，175scenes／350列／700原CLI，三筆精確OWNER白名單；PUBLIC完整正式原流已於E249交付。未改稱無字串差，不擴及P-189，S10未重跑 |
| P52／§7 card／P-189 | 本輪皆UNRUN；原median／5000／900ms／fix-main≤2及逐byte條件保持，P-189歷史exact紅保留 |
| #323 required-eight／PF3／native後段／whole-memo／恢復／ABC | 本輪各完整專項UNRUN；原R8單項與comparison不能代替 |
| RC builder/checker反證／#314六suite及Node inspector／閱讀A native、oracle、mutants-only、完整quick | 本輪完整專項UNRUN；不以native總表或focused proof代完整專項 |
| required CI替代 | OWNER條件是同一final七項＋專項全綠；現尚未成立。不同SHA與收件peer都不算替代條件通過，維持draft |

唯一允許的native skip仍是Linux缺compiled Windows GDI harness的 `test_gdi_contract.GdiContract.test_confirmed_failures_release_real_resources`。所有原assertion、golden、時限與效能門檻保持。

S10採入原件：兩parent正常merge，39條原命令與stdout/stderr完整保存；獨審39條原流及16項語意核對0。決策結果SHA256 `fe822051b5413fb79490b333e23f3c9d6b96959c01f937c274d3246772c15e14`，新測試SHA256 `3ace33248d6ce39b869bf09319315544610311c2ddb8434ad8a57d6a90a9f032`。新測試保留歷史I24不改K，另以固定已審完整K tree約束後續列車，沒有source.c豁免或浮動HEAD。

#314 v2原index由`3916c388…`變成`ad03de61…`，實際寫入者仍未完全確定，原outer1與完整INDEX_AFTER_FAILURE保留。v3每階段改用私有index／objects，真38commands、76streams；原index與來源保全通過，未重置或覆寫歷史失敗。兩輪完整收件1826原件／36,200,174B，3gzip共7,918,998B、actual14194/0；完整來源執行仍F9＋patch，非S10正式native。

R8完整原實測：N16/base `0.9834192453688345`、N32 `0.9007932884873169`、N48 `0.7392862448969592`（各≤1）；N64/main `1.2846970752586067`（≤1.3）；calls64/32 `4.407618425509266`（≤4.5）。其原outer1與exact原差異完整保留；F9新comparison只依已驗證OWNER當次精確三差裁決執行。

[OWNER批准原文](https://github.com/ZhiQiYang/geometry-axiom/pull/338#issuecomment-6396611849)已經GitHub API核對帳戶id/node/type/OWNER與已連接登入相同；不是以同步檔作者字串或合併事實代替批准。不延伸#323三差白名單到P-189。

最近已讀審查為handoff `604a14f93` 的2026-10-25T14:35:15Z、head3447ab3：B1需完整native、B2其餘清單、B3實際merge、C1證據head。此次S10實際完成main→train同步，B3所述衝突已解；B1/B2仍未解除，C1已在本份正文明列目前E與各完整封包所在SHA。六browser原件先前已在E249（canvas／assembly分別其祖先Eaea／E3447）完整交付，詳歷史索引。

共同環境仍使用原有tmpfs `/dev/shm`，各browser來源、port、TMP隔離，未改掛載／配額／安全設定。各原取樣shared-SHM used max：assembly第二次229765120、documents262922240、grid320098304、space383094784、timber416649216 bytes；是共享掛載取樣峰值，不是連續真峰值／job獨占峰值，不外推R8。

共同容量已明確適配並實際啟動：來源原24MiB（25,165,824B）與帳本原272MiB（285,212,672B）數值均不變。舊工具硬綁/workspace；新明示reserve/resource anchor只接受實際pool/cache/job/TMP所在同一既有SHM裝置，預設保留舊行為。source適配原小反證0/1/0、獨審217/0；full123適配原小反證0/1/0、獨審135/0。未改產品、oracle、123scope、child時限、stack或locks。S10來源準備真exit0：3763來源＋2738獨立seed、604架構輸入、五必要fixtures、342原Git命令；actual18498/0。來源與precheck完整原件正在獨立封存，不以此摘要冒已全部遠端交付。

full123確實在執行，host session26296，source `82c922a3941525d3a094ac0158bdc7dea57ea360`；root/seed由帳本獨占，其他代理不讀寫。原工具run_full_ledger SHA256 `7af6f3d7efe4987ed32ea0f356541630181fa6435684e72d83f7e3e7018148ef`，原capture/launcher保留。實際sourceprep結果pin `f1e689eb26653609943e7e899aaf6d6e8430b9d0b2291d8e1ee94ebb7c14fdf9`；filesystem admission pin `d76ac62b52b17d615952d418a3b209d072dc04608de796cdf51f7b045eb65ddf`。啟動時兩OWN共同已用952,905,728B，加1,073,741,824B額外規畫≤2,147,483,648B規畫上限；實際SHM free16,918,974,464B。這是保守容量規畫，不是連續真峰值。WS free4,636,672B只作唯讀觀察，非實際新建置mount，不再用不相關WS擋272MiB門檻。
本批完整持久化四個已終態OWN私有index cache的保全：原23,386,440B分四gzip4,547,550B，full roundtrip與actual308/0；四個原index、所有來源／既有三D／refs／objects均原地保留。尚未unlink，實際回收0；不以小量回收誤稱滿足272MiB。以新工作掛載方案優先處理整體容量，必要時再依完整原件遠端核對後單獨重新檢查是否退役可重建cache。絕不刪不可重建原始證據、使用者資料、fixtures或未提交修改。

整體路徑仍需保留差異：full123新輸出及原始raw在SHM，只有既有/tmp重測鎖仍在TMP；native原tests/binaries.py的Linux OUT_DIR卻確實是/tmp/geometry-tests，TMPDIR不會改它，須另確保原TMP128MiB與真峰值預算；browser原SHM獨立checkout/port/TMP方案已在F9實證。封包、Gitobjects、remote-verifier原流都計入兩OWN SHM共2GiB規畫，原掛載／配額／安全不改，取樣峰值不冒真峰值。正在一次列完整後續路徑與缺額，不逐job小量騰空。

native原128MiB仍查實際/tmp：TMP曾46,854,144B不足，候選方案已一次列107,233,280B（2439個Git逐byte無改來源葉、明示Chrome cache白名單、2個私有index與24個已終態ELF），已排除73個裁判／測試葉與F9六ELF。只是候選，未unlink；所有不可重建原件、fixtures、Gitobjects、dirty及使用者資料保留。index/ELF須先完整封存、遠端核對與獨審，持原鎖fresh複核後才可退役，實際回收與capture費用不能先算准入。順序browser仍採F9已驗隔離來源/port/TMP/短socket方案；任何新受影響重跑會綁新final。每份raw終態先完整封包、普通push、遠端全bytes/hash核對後才算交付，不能只留SHM。

下一步：full123背景執行期間準備順序交付Q38原件、核對新來源gate影響、準備架構四檔與native一次容量方案；帳本真終態後採入固定final，再跑完整native及所有UNRUN專項。F9六browser、Q38、axiom、reader與F8 R8維持原execution SHA，沿用仍需產品／測試／裁判／fixture閉包證據與規則，不自行跨SHA全綠，也不無依據重跑已有效樣本。維持draft，未完成替代CI條件。

本次先正常發布這份小型進度，Q38與S10完整原件依容量順序另發。已交付handoff NEXT=`b5770e23607d652eb86fb040ed94f920c1cac3ef`，遠端完整68554B／SHA256 ed20d0e8ac41bda1a07d59b8538225008125041e15f38e2bd4cd55f48f961853 核0。額外收件失誤已保全：第一輪gate分析誤含evidence binary diff，完整36files／98,525,587B已逐hash同冷存於OWN SHM，前7命令全0，第8尚未啟動即WS ENOSPC。不能刪原件或漏算容量；第二輪僅小scope純來源metadata，共722500B，排evidence後確定只兩葉變動。所有較大封包順序處理，不在背景帳本預留量外無限制增開。這是收件工具／環境事件，沒有產品測試失敗或修改門檻。


原始完整封包與歷史：[PROGRESS](https://github.com/ZhiQiYang/geometry-axiom/blob/3e4f2560aa11ed2a626db98ba5ed6f129e791052/evidence/geo337-train-20261024/PROGRESS.md)、[#314兩輪原件](https://github.com/ZhiQiYang/geometry-axiom/tree/d45e66aebdcd27602134990eefb6a5d0ff9bad21/evidence/geo337-train-20261024/F9-geo314-counterproof-terminal/)、[S10採入原件](https://github.com/ZhiQiYang/geometry-axiom/tree/d45e66aebdcd27602134990eefb6a5d0ff9bad21/evidence/geo337-train-20261024/F10-source-adoption/)。
