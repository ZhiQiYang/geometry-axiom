# #338：S10 原始收據已回收；最終驗收仍未完成

此正文供原 #338 接續使用，沒有建立替代產品 PR，沒有將 PR 合入 main。以下是本次唯一 current-state；舊矩陣均為歷史。

| 身分 | 完整 SHA |
|---|---|
| S10 全帳本／架構執行 | `82c922a3941525d3a094ac0158bdc7dea57ea360` |
| 已讀列車 head | `a6f4013364e21bcb7239b5dcc25caac0f6d61f77` |
| 已交付證據 E | `9a57aea2128a7bc3985064932c24e2229fd8fcb8`，獨立分支 `codex/train337-recovered-evidence-20261026` |
| F9 歷史正式來源 | `4f8a794f4167c3562eb182045102e86e9e37cca9` |
| F8／R8 歷史來源 | `75a1e93811a52b69385cbdaf6a09d773ed9052ad` |
| 新候選 final F | 尚未固定；未宣告全綠或 READY-TO-MERGE |

| Gate | 真實結果 | 新 final 的界線 |
|---|---|---|
| S10 全123帳本 | exit 0，114 killed／5 equivalent／M20 crashed／3 retired；120執行head皆S10。初次stale check exit1保留 | 已生成，尚未採入產品路徑；不因決策文字變動重跑已有效全帳本 |
| 架構三條／四檔 | S10 0/0/0；generic205、product18；604輸入。四檔組裝exit0 | a6決策snapshot已不同，下一候選須綁相符快照；不冒S10原件為a6當次執行 |
| native | F9 exit1：5327 pass／1 fail／1允許GDI skip | #314修正反證0/1/0及S10 focused已完成，完整新final仍UNRUN |
| canvas | F9 exit0：2267 assertions、85 golden | 新final UNRUN |
| assembly | F9 r2 exit0：150 assertions；r1 socket環境exit1保留 | 新final UNRUN |
| documents | F9 exit0：47 assertions、8 screens | 新final UNRUN |
| grid | F9 exit0：356 assertions | 新final UNRUN |
| space | F9 exit0：242 assertions | 新final UNRUN |
| timber | F9 exit0：79 assertions | 新final UNRUN |
| Q38 | F9完整44項exit0，43 killed＋SPM24 equivalent；完整封包此次已交付 | 保F9來源，不移標 |
| §7 axiom／reader | F9原axiom exit0，reader三條0/0/0 | 保原來源；§7 card等未完成項另列 |
| #323 R8 | 原36樣本：N16/base `0.9834192453688345`≤1，N32 `0.9007932884873169`≤1，N48 `0.7392862448969592`≤1，N64/main `1.2846970752586067`≤1.3，calls64/32 `4.407618425509266`≤4.5 | 原outer1與原取樣保留，不重抽 |
| #323 exact comparison | F9 175場景／350列，outer/stage/audit 0；依已核實OWNER三差白名單 | 不等於P-189接受或整組ABC全綠 |
| P52／card／P-189／required-eight／PF3／whole-memo／RC／#314專項／Reading A | 仍有未跑或未閉合項；原P-189 exact紅燈保留 | 不用封包核對、工具合成測試或歷史取樣代替新final正式結果 |
| required CI替代 | 尚不成立 | 完整native、六browser、Reading A oracle及適用專項仍需收齊 |

唯一允許的native skip仍是原Linux缺compiled Windows GDI harness項。沒有新增skip、放寬assertion/golden/時限/效能門檻。

已交付1058檔，普通push exit0；606個唯一遠端blob全bytes/SHA256/GitOID核對exit0。含S10全帳本1284成員封包、S10架構四檔及命令、Q38完整346檔封包、S10來源準備/preledger1214成員封包，以及26個舊index/ELF的raw＋gzip保全。原資料均未刪除；空間回收不是產品驗收。

[進度與下一步](https://github.com/ZhiQiYang/geometry-axiom/blob/9a57aea2128a7bc3985064932c24e2229fd8fcb8/evidence/geo337-train-20261024/resume-20261026/PROGRESS.md) · [待核實項](https://github.com/ZhiQiYang/geometry-axiom/blob/9a57aea2128a7bc3985064932c24e2229fd8fcb8/evidence/geo337-train-20261024/resume-20261026/QUESTIONS.md)

批准界線：2026-10-25 #323原留言已核實OWNER身分。a6新增P-189／沿用文字目前是repository轉錄與新審查引用，尚未取得新的原始批准紀錄；因此本批沒有修改比較器、沒有擴張舊白名單，也沒有把原未跑項冒成沿用通過。可獨立完成的回收與候選驗收持續推進。

目前阻塞：自動核准審查拒絕3156葉暫存退役，理由是含私有index與ELF的完整範圍缺少明確授權。命令未啟動，刪除0，原true請求已撤銷，不拆批或改路徑繞過。原native的/tmp128MiB門檻仍不足；協調者正在取得具體範圍批准，其他架構與候選來源工作照常進行。這項拒絕不代表產品測試失敗。

Claude session f46787ac 的目前寫入占用尚未由API資料確認。為避免競寫，回收與候選工作使用root獨占分支，原train HEAD/index/ref未修改。此正文保存在該分支對應prbody，未自動覆蓋原#338正文或請求檔；整合時須依真候選F更新矩陣。
