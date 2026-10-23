# #324 替代線進度（最新列車合流）

產品 source S：`57b680140da2c6b77ab0d362a72029d8d7c9334b`；incoming train：`504933473d7b9bdfc5964f73402a710f1222fc96`；前一 evidence E：`c8806b5f1aa6363d573b30a9df1748e61e1b9ccf`。此 S 已一般 push／ls-remote 核同。

普通 merge 保留原兩 leaf Grok blobs；對 train 非 evidence 差恰原三檔；expected 只 host_sources39→45，其餘 registry metadata 精確等 train；SSOT／決策佇列 blobs 精確等 incoming train。所有原 merge 命令、exit、stdout/stderr、環境、SHA 在 merge-originals。沒有 rebase／force push／合併 PR。

本次只同步 root 已推的 Claude／main／P17 架構產物，沒有執行任何產品、裁判、Chrome、build 或 ledger。架構原四檔屬 incoming train 的原 sourceBaseHead；#324 owned W leaf／excluded test 的適用性仍須原三裁判與四檔刷新，不能冒本 S 已 fresh。tests/mutation_bridge.py 的 oracle hash 也讀 tests/*.py，原 mutate --check 仍必跑，整份帳本由 root 統排。

唯一 CURRENT_STATE.json 保留16列 UNRUN，原 exit／executionSHA 全 null。三 predicate v2 原 driver／60秒／具名正常紅與逐案0/1/0計畫不改。新 merge 靜審與正式同 SHA 驗收待 root 排槽；不把舊 f121 的靜審外推本 S。

## 合流獨立靜審與 manifest 自索引修正

新來源 S 的合流窄審已完成254 metadata checks／0 findings；原 peer 保於 revision-3-peer-and-manifest，不把此結果外推正式16 gate或整包驗證。完整前一18條出版命令與原 streams 同封。

自查發現原E792的root manifest把前一版同名manifest也列為self-entry，只有此metadata自索引過期；原manifest完整bytes另存，所有其它列冊檔已逐bytes/hash驗證未變。新root manifest明確排除自身，原snapshot以獨立revision member守門；原出版1／raw whitespace2與完整raw全保，沒有改原輸出、產品碼或測試。正式16列仍UNRUN。

## 套件peer1的驗證時點澄清

原package peer1019項有1 metadata finding，報告完整保留於revision-4-validation-timing。上節「其它列冊檔未變」與原JSON true，精確指publisher開始寫新metadata之前、對E792 snapshot逐檔驗證的時點；不指E495或此後生成的PROGRESS也維持原hash。E495合法追加6行，前後與append的精確hash/bytes及原E495 manifest另封。原source／命令raw未改，原peer1不回寫，342檔新manifest的原hash核對結果保留；本次只追加時點限定並重新列冊current所有檔。16正式仍UNRUN，新的限定等待獨立窄複核。

## 三predicate實際補證

固定公開產品 S57b680140da2c6b77ab0d362a72029d8d7c9334b 的獨立薄checkout，原v2工具未改，list／dict／feature三原method各真0／1／0、正常具名unclassified診斷、還原bytes與來源前後clean。setup＋actual約2.714秒；無R3、編譯、Chrome或效能量測。完整52內命令＋10外命令streams／37inputs／三還原樹／凍結工具已逐byte封包，producer roundtrip全同。獨立actual peer551 checks／0 findings；這三列PASS，另13列仍UNRUN，沒有把mock native運輸方法當完整45／native／browser。

原package peer1019報告exit_code1與其helper實際process0分欄澄清，原JSON／舊E不覆寫，澄清原件同封；該metadatafinding沒有改動原test或source。

## 七個原pure Python module：99/99

固定同S57，原_unittest_runner完整host_sources45、source_runtime10、kernel_runtime10、rectangular_python9、host_world8、kernel_compatibility1、domain_source_pins16，全部原exit0、0fail／0skip、來源初末clean。無C、browser、R3或全域binary cache。原65／18／16獨立actual peers322／356／604 checks均0。affected-importers列只部分7/9，host_native30與default_native13真C依賴待槽；fullnative／expected aggregate與六browser未跑。

原setup sparse add不支援flag129／collector2（0tests），與domain_pins少原tracked5431B fixture所致15pass1error／原exit1全部原件封存；只修物化配置後重跑受影響項，未改test／assert。原wrapper未在事前request pin hash、c387沒有timeout_seconds欄的證據限制照保。CURRENT_STATE兩句舊allunknown角色文字只在此actual批同步為逐列真狀態，不回寫原E。

## 兩原native importer module：43/43；指定九module總142/142

固定S57薄source，原host_native30完整30/30（含真fresh fallback編譯），原private binaries.main build bridge/model-base exit0，原default_native13完整13/13、0fail／0skip；原outer／collector0，493Git inputs原始/LF初末同、HEAD/status clean與ls-files --stage輸出同，不冒.index檔bytes。全程secondary.lock序列，20:23:54終態正常釋鎖。

前七99加此43＝指定九module142/142；actualCommands是各原_unittest_runner.py，準備版run_all --build --only診斷未執行，沒有冒aggregate結果。原compile900s／host fallback60s／default捕捉30s與各module1200s保留。完整公開stdout/stderr、raw Gitbatch493inputs、兩ELF與sidecars全部封包；原程式內部未公開pipes不另冒逐條流。fullnative＋expected、registry-list、六browser、mutation check及架構等12列仍UNRUN。
