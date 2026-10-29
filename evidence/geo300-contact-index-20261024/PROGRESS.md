# GEO-300 遮蓋索引、穩定排序與反證維護進度

Product SHA `ccfaf057088a80c7aad4049f1c67e5eedfc2fdec`。正常bounded/unique排序＋單一遮蓋面索引維持原幾何、順序、容量與duplicate/overflow後備；本批只有evidence，不再改來源。

| 目前原件／範圍 | 真結果 |
| --- | --- |
| 原wood-contact | 12 methods／41具名正常0/1/0；exit0、0skip；147build全0 |
| 原contact-sources | 15 methods／11具名正常0/1/0；exit0、0skip；85build全0 |
| 原ReadingA native | 7 methods／12具名正常0/1/0；exit0、0skip；86build全0 |
| 三套合計 | 34 methods／64 controls／318builds全0；23:03:46.221263～23:04:07.906571Z；primary/reaper/launcher/host tool0，sourceclean；actual peer1222／0 |
| tuple明確回撤恢復 | 原一method／8controls每phase，fixed0→舊tuplewithdraw1→restored0；23:04:13.900627～23:04:25.287954Z；77×3＝231build全0，outer0、HEAD/tree/index還原clean；actual peer693／0 |
| 既定16MiB | 上述真測試全部維持原limit；未另量compiler frame或完整場景上限 |
| whole-opt撤回／效能／P-189／512 | 8正例語意等價0/0/0仍UNRUN、不計killed；性能UNMEASURED、512未完成 |
| 全native/browser/ledger/architecture | 本S UNRUN；NOT READY |

舊 Scc2 三套 wood0／contact1／ReadingA0、318build0 的真紅與完整原件全保：contact-sources舊placement-order控制仍撤已旁路fallback，原native PASS ordering0導致原meta唯一failure1，不是compile/crash。只重錨tuple到正常comparator，保原ordering ASSERT／案例／全部function AST與時限；修前紅有限peer95／0。明確tuple撤回再次重現同一meta紅，恢復綠；此不是whole優化語意反證，也不冒完整15方法／11控制的三phase重跑。

MEMBER_SORT_ACCEPTANCE_ORIGINALS_AND_PEER.tar.gz 保存1498原件／56,913,484B，加index共1499regular成員逐byte回讀。包含r1真紅、r2全三套、tuple三phase的完整指令／exit／streams／env／SHA／compiled C與build logs、before/after單leaf、靜審與actual peers及原metadata錯誤；舊raw不刪不覆。初sparse物化失敗、原stderr尾空白diffcheck2、reviewer初checker與出版hash參數錯誤均分類保留，沒有subject重跑洗白。

三套與tuple按rootgrant序列執行，每次fresh workspace>原100MiB，16MiB／child限／secondary／完整streams全原；沒有新checkout、無性能或全帳本。23:04:25終態已釋slot2。最外host tool exit依原API metadata，沒有獨立host OS capture；NativeBuild logs/events是完整解碼文字，不宣稱解碼前OS bytes，原c387 raw stdout/stderr完整保留。

S1ee的33/56/302及Sc493的32/46/282維持歷史SHA；沒有移標。下一步公開包與正文獨立審查、再依root安排未跑的whole-opt語意等價、性能與其餘gates。正常排序與遮蓋查詢改善不等於整個collector/load已O(FlogF)；duplicate/overflow平方後備、cut-list與call-growth仍在，不改SSOT、決策或數值門檻。
