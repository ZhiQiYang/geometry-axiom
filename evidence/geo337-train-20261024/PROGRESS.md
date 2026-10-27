# #338 唯一 current-state：固定 F 的正式驗收與尚缺項

2026-10-27 UTC。正式產品／execution **F=`cbf0fb621888596aa14ad5f2349b503e23b1b72d`**；本次證據父 **E′=`e5da59b7e570a360f99ee07e2194c938da0c2626`**，新的證據 head 為本文件所在提交，完整 SHA 由發布原始收據確定。只更新證據與本 canonical `PROGRESS.md`，不改產品／測試；`resume-20261026/PROGRESS.md` 保持歷史導向。

**固定 F 的 native 與六個 browser 正式命令皆 exit0；專項尚未全閉合，#338 仍 draft，未標 READY-TO-MERGE。** 最新已知 PR 留言為 [6432307291](https://github.com/ZhiQiYang/geometry-axiom/pull/338#issuecomment-6432307291)；本次 handoff 分支最新 ref 仍 **UNKNOWN**，不宣稱已 fresh fetch 或替代後續審查。a4bd77e8 已撤回，不把它或 F9 的收據移標 F。

## 唯一 current-state 矩陣

| 項目 | 真實結果／範圍 | 固定原件與接收狀態 |
|---|---|---|
| F native | 雲端正式 **0**；230 suites、5328 pass、0 fail、1 原允許 GDI skip；1886.996秒 <2100、stack16MiB；mutation check0／stale0 | [E732ef20e](https://github.com/ZhiQiYang/geometry-axiom/tree/732ef20e34876379a37eb69693a481becebea43e/evidence/geo337-native-validation-20261027)，我方接收peer0。這份雲端原件與 Claude WSL約7361秒樣本分開；沒有把WSL重新計時或移標為雲端通過 |
| F canvas | 正式／完整wrapper鏈 **0**；2267 assertions、85 golden sections逐段相符、0 skip；1749.408423772秒 <2100 | root91441／4dc6ef；9327檢查0；4 workflow圖＋27 runtime PNG逐檔hash；本次 `F-canvas.tar.gz` |
| F assembly | 正式／完整wrapper鏈 **0**；150 pass、0 fail／skip、9 workflow圖；192.930640466秒 <900 | E′ `recovery-bundle-20261027/F-assembly.tar.gz`，9151檢查0；golden bytes保全不冒稱完整canvas比較 |
| F documents | inner／outer **0**；47 pass、0 fail／skip、8圖；70.973913210秒 <600 | E45dd4d662eac9297eda8473742c9943a1cb336cb完整包；E′補兩個`.git`共146B及1271目錄metadata，無ignored runtime遺漏 |
| F grid | 正式／完整wrapper鏈 **0**；356 assertions、0 skip、4 workflow圖；464.329781552秒 <900 | E′ `recovery-bundle-20261027/F-grid.tar.gz`，9137檢查0；partial模式不冒稱完整canvas golden比較 |
| F space | 正式／control **0**；242 assertions、0 individual skip、原2組omission；213.725140721秒 <900 | 9164檢查0、33 runtime PNG；本次 `F-space.tar.gz`。原省略組為timber-material、timber-source-guards |
| F timber | 正式／control **0**；79 assertions、0 individual skip、原5組omission；123.625623627秒 <1200 | 9114檢查0、10 runtime PNG；本次 `F-timber.tar.gz`。原省略space-height-library、projection-lifecycle、projection-placement、space-flow、projection-close |
| F Reading A／oracle／RC／reader | 外部原正式 **0**，本方窄核收 **0**；quick391.726秒、528 step＋1056 mirrored全部可施工、0 missing／non-buildable；原golden／RC builder／RC checker各 **0／1／0** | [E7886f2e](https://github.com/ZhiQiYang/geometry-axiom/tree/7886f2eaa3da7f9f4855104ca4b028d2d06ce6da)。quick原有 **6 個 C11_MAIN_NOT_BUTTED known-defect觀察**仍保留；不是全專案零缺陷。原native覆蓋oracle14／reader51／required-eight681，沒有冒稱另跑selected wrapper |
| F PF3 | 外部正式 **0**；745.697秒，baseline／semantic-removal／restored為20／19原assertion／20，0 error／skip；本方窄核收與對抗審查 **0** | [E1d9b980](https://github.com/ZhiQiYang/geometry-axiom/tree/1d9b980defec2659d7b08ee0a3ac782e00354780/evidence/geo337-pf3-20261027)。本方review已在本地，remote接收報告待後續小收據公開；未重新下載／重核producer archive／ELF |
| F Q38 | 外部正式 **0**；820.152秒，full44＝41原assertion kill＋2原ModelError＋SPM24 equivalent；native baseline29／model20、0skip；本方窄核收與對抗審查 **0** | [Edd2cbf6](https://github.com/ZhiQiYang/geometry-axiom/tree/dd2cbf6a558b4af240ab4702cc8402621380881b/evidence/geo337-q38-20261027)。SPM38／40原ModelError保留，不冒稱43個assertion kill；本方review已在本地、remote報告另發，producer archive／ELF未重新下載重核 |
| F P52放置後timber耗時 | 本方 **UNRUN**；已委派外部owner，尚未收到終態 | full canvas內P52斷言不能替代這個獨立計時專項；不重複啟動 |
| F whole-memo反證 | **UNRUN／未閉合** | 不用PF3、native或帳本頂替 |
| #323 R8效能／profile＋175ABC | R8 execution `75a1e93811a52b69385cbdaf6a09d773ed9052ad` 各效能原門檻綠但 **outer1**；175ABC execution `4f8a794f4167c3562eb182045102e86e9e37cca9` 原 **0**；**未閉合到F** | 36份原樣本保留、不重抽、不能移標F；與P-189各自的main／base／final比較分開，不借用其base |
| P-189 strict／跨版本exact | **strict pending／原紅保留** | 不擴大#323三差白名單、不改golden／門檻、不重抽取較好樣本 |
| F 全123帳本／check | S10全帳本 **0**；F check **0／123** | S10=`82c922a3941525d3a094ac0158bdc7dea57ea360`；114 killed、5 equivalent、M20 crashed、3 retired；120 execution heads與原失敗保留，已有效不重跑 |
| F 架構三條 | **0／0／0** | F後跑正式judge與產品內於a6生成的architecture receipt分開；798 edges／205 generic／18 product／0skip，不把a6生成身分改成F |
| F §7 axiom／card | 兩原正式 **0**；axiom44baseline＋5 red1/restored0；card43baseline、53實體突變全red1/restored0、116ELF完整 | axiom E2d576269ab85ef64a921bc4b15d013ca2ef5b4fb；card E047d93f01ba1bd349ebc256c4e8d19209bfd0f49；不重跑 |

所有browser的完整source3759、private index與原golden bytes保全均已核0。assembly／grid／space／timber使用各原workflow範圍；省略組是原分工，不是新增skip。完整canvas才執行85段golden嚴格比較。舊F9（4f8a794f4167c3562eb182045102e86e9e37cca9）的native5327pass／1fail／1GDI skip與六browser綠只保留歷史，未挪進上表。

## 本次三個browser與小型接收原件

`final-browser-delivery-20261027/` 一次收四個自然包：space、timber、canvas及接收／前次發布原流。三個browser原選取分別為624／599／678 regular files，原始bytes為43,084,061／34,671,214／54,737,704；各自完整原命令、環境、SHA、stdout/stderr、退出鏈、runtime圖、index、golden、目錄與非regular metadata保留。只排除審過的兩個source copy各exact3759 tracked葉，保留`.git`與全部ignored runtime／其他葉；不跟隨socket／symlink、不刪原件。

canvas開始03:49:51.577366Z，結束04:19:00.985789Z。完整原stdout有兩處BrokenPipeError文字，屬同一段伺服器回覆失敗及其處理路徑的診斷；完整上下文保留，不按grep文字判產品fail，也不宣稱已證明與某個abort的因果。原expected fb-auto-probe造成1個已預告例外，P53 surfaces transport與P57 receipt abort是原負例；沒有把partial job的0exception／network-null條件套入full suite。

前次六包發布E′已實際普通快進成功：root49365／322bc2，69命令、207完整stream、454核對0，精確16葉（15新payload＋1既有blob alias），provider保全。這15份新remote readback合計100,217,727B已公開且逐byte核對，本次以新tree/path→同一immutable Git blob引用原完整stdout，保留固定E′、原path、OID、size與SHA256映射，不再複製或下載同批payload。所有**新**封包仍需完整遠端readback；新E″的真發布結果以新原始收據為準，不預先宣稱工具準備等於交付。

外部native只引用固定E732原件，本次收我方兩份接收peer及review工具，不重包19個遠端原件／ELF。Reading A只收本方review／fetch工具、兩版接收peer、selected-fetch結果map、manifest原hash索引、兩份靜審，以及新讀回的F golden-witness driver完整capture；不重包外部112個選讀payload或137個producer原件。限制保留：本方未直接讀兩個native producer tarball，Reading A只核112/137、未下載generated golden與variant副本；已核其原byte comparator／manifest／pinned worker／source guard，不冒稱另作完整producer重驗。

## 已保留的失敗與授權邊界

原card第一次GitHub blob API回422（約74MB base64 stdin完整保留），第二次Git2.52 promisor metadata fetch造成2,422,150,411B本地repack，均未push；根因、原流、合成本機0／1／0反證及後續no-fetch成功原件已在E′公開。大Git objects留原地，不刪、不重包。曾誤讀regex JSON跳脫的核收判斷已明確撤回，原錯判、CORRECTION及corrected peer並存，沒有改本來正確的executor或重跑發布。

R8固定源75a1e93811a52b69385cbdaf6a09d773ed9052ad比例綠但outer1、F9 exact0、P-189 strict原紅仍分列保存。使用者原引述與Claude整理、API帳戶核實與驗收語意批准是不同證據；不由已合入、外部成功、repo轉述或本方接收擴大P-189白名單、豁免stale／survived／invalid／blocked。

目前來源仍依先前已核handoff8992388515172d068ee1e28526e1103ff18aa4f2的01:48更正回F；其後handoff最新ref未知。a4bd撤回原件、CI runner_id0／steps=[]的未執行結果保留，不拿它判產品紅綠。

兩OWN最多8GiB是任務規劃；原`3P+L*65536+M*8+67108864`、64MiB發布保留、fresh真掛載free／cgroup與原產品時限都維持。只在完整最壞成本及peer後一次封包／普通no-fetch發布；新hash-object使用原檔argv，無payload stdin副本。缺失PSI寫unavailable，不能當零壓力。原3156＋108空目錄回收107,233,280B與extra168回收22,892,544B均有批准及原件，不重做、不擴刪。

## 下一步

採入程序以固定收據記錄：本束遠端原件核對後，可把最新recovery E″一般merge進既有train，保留單一canonical進度；舊E′草稿request不作執行依據。本文件的current矩陣固定產品F與各gate execution身分，**不斷言目前train是否已採入**；普通merge的新M與真退出碼由後續採入收據記錄，不預宣稱成功。這是工作分支同步，**不是合併PR或main**。正文由主代理在M＋E″確定後一次更新；繼續處理尚缺專項與最新審查。未部署、付費、變更安全設定或新增公理。
