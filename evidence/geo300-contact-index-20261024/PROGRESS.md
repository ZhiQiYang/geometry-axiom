# GEO-300 唯一 ID 遮蓋查詢與穩定 member 排序進度

目前 product SHA `cc2ea1b3b42291f6ebb0ead6bd1c2180920d7041`，父 E `4f456effd0a53ec45e575c2ce3596825b8dc937a`。只改 contact_world.c、原 harness、原 Python suite 與 expected 的 wood-contact 11→12；其餘 registry、SSOT、決策與容量未改。正常 bounded/unique 路徑共用既有四陣列做穩定 index merge 與單 face permutation；duplicate／overflow 保原 insertion loop。

| 目前 SHA 的項目 | 結果 |
| --- | --- |
| 排序草案獨立靜審 | 283 checks／0 findings；只有靜態，不是 C 實證 |
| 原三套 | UNRUN；預期 12＋15＋7＝34 方法、41＋11＋12＝64 controls |
| 既定 16MiB／compiler frame | 新來源 UNRUN／未另量，未新增或加大索引陣列 |
| 整條快路撤回 | UNRUN；另規劃 8 原正例語意等價 0/0/0，不計 killed |
| 性能、P-189、容量512、全 native/browser/ledger/architecture | UNMEASURED／UNRUN／NOT READY |

歷史 S `1ee4e830399b124ebd63c5ff51064d87e53f38d9` 已實跑 33 方法／56 正常0/1/0／302 builds，全0、0skip；這些結果只屬原 SHA。原 1140/0 actual peer 與 1571/0 public peer、366 成員原件包完整保留，不能標為新排序實跑。#341／Sc493 的32／46／282也保原SHA。

本次 Git-only 出版第一輪 apply-check exit1：薄 checkout 未物化原 tracked tests/run_all.expected.json，原 stderr／退出碼全保。沒有產品 patch 或 C 執行；r2 只從同 HEAD 精確 restore 該原檔，再套完全相同的凍結 patch，一般 commit/push0且遠端同 SHA。未重寫失敗原件。reviewer 的初始 expected-schema checker 錯誤也與修正版一起保存，不是 subject 紅燈。

MEMBER_SORT_STATIC_ORIGINALS_AND_PEER.tar.gz 保存四leaf前後、patch／設計／純AST、原機械 roundtrip、兩輪 Git-only 指令與完整 streams／exit、runner綁定及靜審；全部成員逐byte回讀。此封包尚無34／64動態結果。

下一步：root ReadingA 專項真終態後取得 secondary 槽，在新固定 SHA 跑原三套與全部具名正常 ASSERT0/1/0；OUT／TMPDIR 用新的 workspace 私有路徑，仍守原100MiB、16MiB與子時限。成本性能不與 root 全帳本並跑。duplicate／overflow平方後備、cut-list平方儲存與呼叫量問題仍在，不宣稱整體collector/load已O(FlogF)。
