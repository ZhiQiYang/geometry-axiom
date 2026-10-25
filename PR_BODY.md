# 已同步 main 並採入 #314 修正；新來源驗收待執行

本檔上半部是唯一 current-state；完整舊文只在最末歷史區塊。維持 draft，未標 READY-TO-MERGE。未將 PR 合入 main、未部署。

| 身分 | 完整 SHA／意義 |
|---|---|
| 新產品／裁判來源 S10 | `82c922a3941525d3a094ac0158bdc7dea57ea360`，已一般推送，兩個變動葉皆從 GitHub 下載完整 bytes 核對 |
| main 同步 parent | `405f8c5e1a637a16cbe47470faf5ae1fa02b8676`；一般 merge 到列車，未寫 main |
| 前一完整證據 E／另一 parent | `249a05ed4c8a085bdf3353ac781638f2a9b3d460`；217葉、190 unique blobs 遠端核對0，獨審5066/0 |
| 目前證據 E／完整 #314 及新來源採入封包 | `d45e66aebdcd27602134990eefb6a5d0ff9bad21`；publication／remote verification均0，46個unique blobs全bytes／SHA256／Git OID核對通過 |
| 正文版本 | 本份PR_BODY.md對應上述E；前一D=`5ce9141d4eccfb98a22fb67f0519c12254cd7ffc`僅為E249歷史快照 |
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
| Q38 | F9原完整44項／launcher exit0；43killed＋SPM24 equivalent（不是skip），SPM38/40保原ModelError。原件2051/0、獨立對抗無阻擋；完整封包待出版。S10未重跑 |
| §7 axiom mutations | F9原exit0，baseline與五次restored各44tests，V01–V05全killed；完整206檔包已在E249交付。S10未重跑 |
| 帳本 | F8全123原0、F9 tracked check0。S10尚未實跑check：改動test.py會進mutation_bridge的全tests/*.py oracle指紋，預期部分stale，不能用core指紋不變宣稱有效；依規則仍整份重產，不只改過期列 |
| 架構三條／四檔 | F9三原judge0/0/0；604 inputs不含這兩變動葉，但舊SSOT快照不可移標。S10／後續final三judge與當次收據待執行 |
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

最近已讀審查為handoff `fd35d1415` 的2026-10-25T14:35:15Z、head3447ab3：B1需完整native、B2其餘清單、B3實際merge、C1證據head。此次S10實際完成main→train同步，B3所述衝突已解；B1/B2仍未解除，C1已在本份正文以完整目前E同步。六browser原件先前已在E249（canvas／assembly分別其祖先Eaea／E3447）完整交付，詳歷史索引。

共同環境仍使用原有tmpfs `/dev/shm`，各browser來源、port、TMP隔離，未改掛載／配額／安全設定。各原取樣shared-SHM used max：assembly第二次229765120、documents262922240、grid320098304、space383094784、timber416649216 bytes；是共享掛載取樣峰值，不是連續真峰值／job獨占峰值，不外推R8。

下一步：保持原25,165,824B（24MiB）WS及後續runtime資源守門，僅回收確定本任務已完成可重建純source/cache，保留所有fixture、原始證據、Git objects與未提交修改；為S10建立乾淨SHM pool/seed，原check後整份123重產，再採入帳本固定正式final並跑必要架構、完整native及其他尚未跑專項。待候期間完成Q38與新來源完整收據持久化、更新正文和handoff，不宣稱全部完成。



原始完整封包及歷史：[PROGRESS](https://github.com/ZhiQiYang/geometry-axiom/blob/d45e66aebdcd27602134990eefb6a5d0ff9bad21/evidence/geo337-train-20261024/PROGRESS.md)、[#314兩輪原件](https://github.com/ZhiQiYang/geometry-axiom/tree/d45e66aebdcd27602134990eefb6a5d0ff9bad21/evidence/geo337-train-20261024/F9-geo314-counterproof-terminal/)、[S10採入原件](https://github.com/ZhiQiYang/geometry-axiom/tree/d45e66aebdcd27602134990eefb6a5d0ff9bad21/evidence/geo337-train-20261024/F10-source-adoption/)。
