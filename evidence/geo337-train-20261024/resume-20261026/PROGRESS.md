# #338 current-state：候選 cbf0fb62 的帳本與架構已驗

2026-10-26 UTC。本文件取代此路徑先前的 current-state；舊提交仍保留歷史原件。尚未 READY-TO-MERGE。

固定候選 F：`cbf0fb621888596aa14ad5f2349b503e23b1b72d`，分支 `codex/train337-recovered-evidence-20261026`。一般 push 與遠端三個原件完整核對 exit 0；獨立採入審查 5019 checks／exit 0。原 #338 列車仍是 `a6f4013364e21bcb7239b5dcc25caac0f6d61f77`，本輪未改其 ref 或正文。證據 E 是本文件所屬提交，由對應 prbody 另固定完整 E SHA，產品與 F 相同。

F 只採入 S10 原帳本、a6 架構 report、a6 架構 receipt 三葉，其他產品／測試／SSOT 不變。manifest／scan 原 bytes 不變。帳本自然 execution heads 保持 S10；receipt 生成來源保持 a6；新四項裁判真正執行來源是 F，沒有互相移標。

| Gate | 實際退出碼／結果 | 來源與剩餘工作 |
|---|---|---|
| 全123帳本 | S10 exit 0；114 killed／5 equivalent／M20 crashed／3 retired | `82c922a3941525d3a094ac0158bdc7dea57ea360`，完整原件已採入，不重跑已有效生成 |
| tracked `mutate.py --check` | **0**；123/123，stale／survived／invalid／blocked 全0 | 真正 F；M20 原 crashed 分類保持 |
| architecture contract | **0**；798 edges，diagnostics 0 | 真正 F；604 closure 不變 |
| architecture unit | **0**；205 tests、0 skip | 真正 F |
| product architecture | **0**；18 tests、0 skip | 真正 F |
| native | F9 exit 1：5327 pass／1 fail／1原允許GDI skip | 新 F UNRUN；原 `/tmp` 128MiB 准入不足 |
| 六 browser | F9 六組原正式 exit 全0；歷史環境失敗仍保留 | 新 F canvas／assembly／documents／grid／space／timber 全 UNRUN；原容量不足 |
| Q38 | F9 完整44項 exit0，43 killed＋SPM24 equivalent | 保 F9 身分，完整原件已於 E9 交付 |
| reader／§7 axiom | F9 reader 0/0/0、axiom 0 | 歷史來源；card 等未完成項不冒綠 |
| #323 R8 | 原效能項全部達門檻，outer exit1保持 | 不重抽36個原樣本，不用新掛載結果替換它 |
| #323 exact | F9 outer/stage/audit 0，175場景／350列 | 依原已核實三差白名單；不外推P-189 |
| P52／P-189／card／required-eight／PF3／whole-memo／RC／#314／Reading A | 仍有未跑或未閉合項；P-189原exact紅燈保留 | 逐項補正式終態，不能以封包核對代替產品驗收 |

新 F 四項原始 RESULT SHA256：`4ef99c7b38f0ab5f451e508d6fffd4e78e30d52a6df133f9a9fd7f9210359784`；獨立 actual peer 12837 checks／exit0，SHA256 `2d1576d20796f86ed99c948e3222c3dc39d37bb648db052994c1a6190bebeb1c`。原始命令、stdout、stderr、環境、SHA、exit與一般FF紀錄全部封存。

第一批完整原件已於 `f90db245f228b7a95a800cab176c3f9ca497133f` 持久化：27檔、25唯一遠端blob完整核對，含17組原件的24,966檔案／7,905目錄／189,987,205原始bytes。封包SHA256 `ac08de092c1ceefd01e01cec3091c69183aa834d31ac197c05b0b535f4694ce6`，遠端交付獨審127009 checks／exit0。第二批保存其完整審查稿、其他獨審、API批准原件核對及#300靜態盤點，無產品變更。

a6 三原裁判0/0/0與四檔組裝0也保留；組裝RESULT `a532b83a67e19b37e2cf724fb4d9ec86753b3a090de554093646b2e2c3d1b2df`，獨審2620 checks／0。新 F 驗收期間3763 selected leaves、5 fixtures、604 raw/LF/Git inputs、source index、publisher及old workspace保全。3763葉這個checkout不是native6997或browser3759的驗收來源。

## 空間與拒絕紀錄

原3156葉清理被自動審核拒絕；命令未啟動、刪除0、原true請求撤銷，不拆批或換路徑重試。範圍為2439來源副本、691 Chrome cache、2私有index、24ELF，另原工具包含108個空目錄。26原index/ELF raw＋gzip完整保全與遠端核對已交付E9；不因此推定刪除獲准。另165個GPU cache不屬此範圍，也未執行。精確scope、毛bytes、ownership限制與排除項見本批approval-packet；協調者負責取得具體批准。

native真正使用`/tmp/geometry-tests`，目前未達原128MiB准入；新browser的單job原416MiB＋thinseed增量也未達原兩OWN合計2GiB規劃守門。實際SHM掛載仍有大量空間，不代表可忽略已保留的規劃上限。browser可逐job物化／驗收／封存，不需六份同時物化；本輪沒有創建seed/cache或修改守門。任何批准後仍須fresh consumer、來源與容量檢查，不宣稱107,233,280B毛回收就足夠。

## 批准、下一步與其他工作線

原2026-10-25 10:39:52Z使用者留言已透過GitHub API核實：ZhiQiYang／id59477728與GET /user相同；只批准#323既有三差白名單。最新a6的P-189／跨SHA沿用文字仍只查到Claude轉錄與ChatGPT審查引用，沒有對應新的原始使用者批准；比較器保持原規格。具體原件及剩餘選項列於QUESTIONS。

接著先完成本輪原件封包與遠端全文核驗、更新對應prbody。空間可合法准入後，原native來源一般transition到F、原native＋六browser＋適用專項繼續；全綠前不標READY-TO-MERGE。

平行#300靜態盤點已通過獨立審查：新F三個效能前置都已實作；#348缺F中的四個快路。兩次原600秒逾時皆在同一140-byte四命令preload batch，沒有可封存的partial stdout/stderr；原observer已具備保存該輸出的路徑，不能說漏實作，也不能歸因loadfile。目前#348的sequential-history組合是1048命令，歷史F0f則1046；兩者都不是該兩次失敗的實際四命令輸入。該工作不重抽效能、不改產品，完整原件與獨審另批交付。

所有未完成項繼續明列；沒有合併PR/main、部署、付費、改安全／掛載設定或新增公理。
