# #123／#54／投影：640 的獨立範圍實跑

此增量包只收 clean `640a81443b3d070dba3d8a0aa52adb2d64cebe0b` 的實際七個範圍，以及獨立 oracle／來源證據。不同範圍不相加，未改綁文件 head，也不宣稱後續 compact-delete 候選、完整CDP／Space或Windows已通過。前期紅／綠證據見 sibling `ui-single-room-prior-public-v4`；其 manifest SHA-256 為 `3f2abb29f759de73c6e4c72323ead0c42aab763ca4e6391f63d41f9802ae8e9d`，本包不重複其28份trace。

| 獨立範圍 | 原始結果與界限 |
|---|---|
| #123 六組＋四個 header hit 斷言 | 198／0，actual exit0，acceptance completed true，probeVerified true，正式 committed oracle、無 sourceOverride；不代表43項／fullCDP／Space |
| #54 原十正常場景＋六 negative | 273／0，actual exit0，completed true；原十場景含mobilePNGnotch及PDF-Ltransform全部完成；單房既有契約 |
| 正式 unchanged EDGE38 | 38／0，actual exit0，completed true；本輪實際 Node／Python／Chrome／owned native 身分完整；舊38的 Node unknown 不回填 |
| GRID_SYSTEM_ONLY partial | 346／0，actual exit0，completed true；P70／71／78／87／88，未比golden。**當時 observer 僅捕到 dash launcher，實際Chromium ELF身分unknown**；原receipt的execution-verified字樣保留，不能因此宣稱所有執行檔身分已核對 |
| corrected-v2 projection 十案 | 10／0，actual exit0，completed true；另審 expected-only BH constant，舊3／7與8／2保留原範圍／版本 |
| unchanged same-owner 兩案 | 2／0，actual exit0，completed true；desktop／390，獨立於上述十案 |
| separate plan／BOM／row-blur／S2 supplement | **108／3，actual exit1，acceptance completed false，probeVerified false**；原scratch sourceOverride `43a3d2b6adf011dec05f85af71c14d0de110e24071b69b5bd636dcf30d0e72ca`。inner completed true僅指四組均嘗試，三組未完成，不宣稱產品通過 |

#54 六個成本測量在PDF／PNG各有 candidate12／14／16與manual16／20／24；協定為 `room-direct-row-dimensions/1`，同已校準來源、camera、snap=false、review／草稿／起終點及ordered final vertices，包含真尺寸改正和全邊輸入。Import/calibration、Save/New/Open明示排除。各案例分開，不和較短P79協定合計；machine wall time不代表人的操作時間，也不擴張到#87多房。

supplement 原plan16成功；BOM12、row-blur20、S2 56在各自1382px先發錯，不能宣稱其600／390後段完成。診斷分別為測試漏掉真HTML impact preview確認、測試點擊disabled控制、helper重複toggle後點closed summary。這些是要另審新oracle前提的失敗，原log／source及108／3保留；不能把診斷寫成產品PASS。

## expected-only oracle 與獨立 actor

corrected-v2 executor SHA-256 `9594ab91fbddabc71ad43970d6dbe771ba5e450531c692e1918e573548ec937d`，ledger `102935b2423c419397db347ce961953be774e1eac7ab092211c43850b30b1d64`。只把BH有序native hole常數從500,500起點改成正常手勢一直產生的800,800起點；沒有循環容忍、排序或放寬幾何／斷言。原37個assert AST、其他AST／fixture／instrumentation不變。

獨立子actor `/root/race_review/hole_order_oracle_review` 核對f980／c0四份normal control與兩份held原始完整World／native／trusted trace。158是證據檔案核對數，不是158產品測試。初次wrapper-schema reader錯誤與第二次空responsebody誤判原件保留；trace沒有保存app.js response body，故served bytes身分unknown，不冒稱驗過。新十案10／0在獨審通過後實跑。

## 原件、公開投影與下一步

[manifest](manifest.json)逐輪記完整受測SHA、clean狀態、命令、退出碼、實際來源／執行檔身分、原始log與receipt的hash／路徑標籤；publicFiles逐檔記公開bytes／hash。UI三次gate的實際source快照逐檔保留，以原hash去重到executed-source-bytes並提供每個scope的原snapshot路徑映射；沒有用現在source補綁旧測試。

完整World保原bytes。合成trace若含machine／workspace／isolated feedback／profile路徑則明示path-only public projection，原ZIP／entry與公開hash分開，binary screenshots/resources保持原bytes。未收入大張單獨截圖、private queueDB／events／ownerthreads、user feedback、真使用者來源、profile directories或native binary bytes。

原完整CDP2207／0／0只綁 clean `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`；#173Windows1692／2、exit1、completed false仍未核收，dot正在核七份原始日誌，partials不相加、不宣稱golden。c0的Resume4／0與四unit131／0／1保留在prior包原SHA；舊wrapper1 metadata matcher與補件不刪除。新候選後續需完成採納的compact-delete及獨立完整CDP／Space與四組reviewed新oracle實跑；本包保留640GRID執行檔身分缺口，下一輪observer修正不能倒填當時身分。缺queue v6保歷史v5／currentunknown，不建空DB；CI無runner／steps為未執行，帳務／安全設定不改、零步驟不重試。
