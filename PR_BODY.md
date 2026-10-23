本 PR 補 Q38 AC23「面材貼齊角材」的具名反證。新增 u/v 兩個字面幾何案例及各自專用 SPM43／44，保留原42cases、28methods、產品、公理與判官；目前仍是 draft，完整整合清單未完成，不可合併。

唯一 current-state 矩陣如下。Current source C=`eb846c345881cc6fc73a53c457a291175365b88c`：普通合流 #300 `aa0e3938f17dc996ef5e7410db4844b31856d2a6`，再唯一登記 native28→30，已一般推送。Base branch=`codex/geo300-prerequisites-20261024`。Evidence head E=`df230da57619e437c30527dbede8c67fd0ec6b50` 已一般推送；新完整44在C真執行完成。歷史實跑 S=`af4fd36c17d05b5da2411b70266ed040e22a6561`、歷史證據 `5c5b63f967a33e75f299250f97629325fff2a775` 分開保留，不把歷史focused結果改標C。

| Gate | 實測來源 | 原 exit／結果 | 範圍與限制 |
|---|---|---|---|
| 新原完整44-case Q38閘門 | C | 原exit0；43killed、SPM24 equivalent | 39native＋5model，無裁項／explore；20:53:16→21:08:13Z，原600／900秒不變 |
| 新baseline／setup／source | C | native0、29方法；model0、20方法；setup／外層皆0 | 零skip；539 tracked inputs初末bytes同、HEAD／clean同；原42gate compile＋1private setup，共43build |
| 新全44獨立對抗審查 | C／原包Eef840 | actual1682／0、public678／0 | 44完整原registry／named causes／原pipes及320公開members皆核；不聲稱逐build C／ELF仍留存 |
| 合流／expected登記 | C | 靜審14 checks／0，未執行aggregate | 唯一native28→30，保noWood13／faces45／woodcontact10；原兩個test leaf等S，AST30；不冒新C動態綠 |
| 原 selection／exception-evidence Python 單元 | S | 0；Ran30、OK | 初末HEAD／clean；不是native aggregate30 |
| 第一輪原 native focused gate | c9269e136f3b40fbb5f9b5e13daa79a32d88efc4 | 2；baseline29，原27過、新2 errors | 新測試錯讀id包裝層而KeyError；只1 build、mutants未啟動，原紅完整保留 |
| schema修正／修正後原focused gate | S | 兩處id→value.id；gate0、baseline29／0 | 六個literal rect asserts全保；SPM43／44各1、killed，都是唯一指定AC23的正常AssertionError；3 builds、585份實際C及3 ELF原hash保留 |
| 原baseline恢復 | S | 0；Ran2、OK | 每個控制真0／1／0；相同baseline ELF bytes的私有可執行副本，原保留件不動 |
| 歷史實跑獨立對抗審查 | S／原包E023339 | actual1252／0；public2354／0 | 全文及原出版raw已在E；審查數不是產品測試數，不冒新C已跑 |
| 完整native30 aggregate／6browser／帳本／架構 | 待最終整合來源 | 本分支未跑 | native30只是登記已完成；原全帳本123個M定義未改，本分支未重產 |

允許skip：無。每個baseline仍須原零skip，原exception／cause／verdict判官不變；41個killed為AssertionError，SPM38／40保原宣告且具因果標籤的ModelError，不改稱AssertionError。新SPM43／44沿用各原SPM03／04故障及相同PAIR_CORNERS跨層閉包，各自只認新AC23的具名失敗，避免其他TOUCH先紅遮住面材回歸。兩個幾何例沿用27／346／373／400 mm與板厚6 mm，第二個只交換u/v，六個矩形期望值均是獨立字面量；I45／R36既有「正面積才重疊、等號接觸合法」未新增數值門檻。

合流帶入W `model_sources.py` 與 `native/contact_world.c`。雖section-profile本體不變，同bridge／model消費閉包已變，因此在C真跑原全44，不能只繼承af4 focused結果。新執行只保原工具實際公開的compiler文字logs、binary／source-tree hashes及完整c387 pipes；未另旁錄每build清理前的C／ELF，不宣稱那些未公開原件已保全。

歷史完整原件在 `evidence/geo261-final-af4fd36c/geo260-ac23/`：封包1148 members、4,014,694 bytes，SHA256 `228b54b277678d8dda80a1f67a025ac7602ca6d21914243c13f1042df510155d`。逐檔hash／來源／排除清單在RAW_INVENTORY.json；ELF只排除Git封包，原件仍留雲端。actual report SHA `19aa5a34d342745f19e135c8235568fe22b064d6348a1aff2b0e7279c625f1be`，public原包／body report SHA `a81e4c9f165f7a8436bb33b380cc33cbf57a544ac11858a98f0c2ef55507a28b`。新全44原件在 `evidence/geo261-final-eb846c34/geo260-ac23/`：320 members、949,070 bytes，SHA256 `09e6aab47aab1f744905b27bd7bdc7c5b3a7ea721ce5d728198245987b11b04d`。完整actual peer SHA `d803d95d9c31c18cd3e71949c263469de3f3087ce9112d002c5b2ef9e66eb852`、public原包peer SHA `0a8d9cb76a6860ae5e2d18bb2bbc6ef1f99263e7eb139777ae63d4aa20724977`及原出版raw一併封存，沒有重測。

首輪c926未在後續schema編輯前另錄final-clean，照實保留；修正輪af4初末HEAD／clean已封。原子exception row沒有SHA欄，未事後填造，以父命令與原輸入間接綁定。合流時sparse未物化expected檔的預檢FileNotFound1亦保原件，補同Git路徑後才登記；未改寫歷史或以環境錯誤算killed。本份證據不外推列車新SHA全綠。
