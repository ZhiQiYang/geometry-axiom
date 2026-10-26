此變更在全部 fact ID 唯一且仍在既有容量內時，以每個完整座標平面的單一覆蓋面索引取代兩兩遮蓋查詢，並以穩定 index merge 取代 member face 的 insertion sort。排序共用原 sorted／scratch，僅用一個 face 暫存重排；RC 前綴、完整 uint64 order、同 order 的宣告／側面順序與公開欄位保持。重複 ID（包括被過濾的 fact）與超容量輸入保留原後備。

基底是 `codex/geo260-ac23-proof-20261024`，接續 #341 的活集合與一次壓緊前置。正常 bounded／unique 的排序改為 O(F log F) 比較＋O(F) 重排；duplicate／overflow 平方排序與配對、超容量 memmove、cut-list 平方儲存及呼叫量問題仍在。沒有宣稱整個 collector／load 已解除平方成本。

| 唯一 current-state 矩陣 | SHA／結果與範圍 |
| --- | --- |
| Product SHA | `ccfaf057088a80c7aad4049f1c67e5eedfc2fdec`；包含排序產品 `cc2ea1b3b42291f6ebb0ead6bd1c2180920d7041` 與 contact-sources 的精確控制錨點維護 |
| Evidence head | `a934a554ae58f16f124f1b264523947f170b3f0b`；只改本 PR evidence prefix，產品與上述 S 相同 |
| Base | GEO260 E `df230da57619e437c30527dbede8c67fd0ec6b50`／產品 `eb846c345881cc6fc73a53c457a291175365b88c` |
| 原 wood-contact-world | **exit0**；12 方法／41 具名正常 0/1/0；0skip；147 builds全0 |
| 原 contact-sources | **exit0**；15 方法／11 具名正常 0/1/0；0skip；85 builds全0 |
| 原 Reading A native | **exit0**；7 方法／12 具名正常 0/1/0（11 W＋1 H）；0skip；86 builds全0 |
| 本 S 部分 native 合計 | **34 方法／64 控制／318 builds全0**；primary／reaper／launcher／host tool0，source HEAD／tree clean；actual peer1222／0 |
| tuple 明確撤回／恢復 | 原受影響一方法／8控制每phase，**fixed0→舊tuple撤回1→restored0**；77×3＝231 builds全0；outer0、HEAD／tree／index還原clean；actual peer693／0。不是完整15方法／全部11控制或whole-opt撤回 |
| 上輪 Scc2 真紅 | wood12/41 exit0、contact-sources15 exit1、ReadingA7/12 exit0；318 builds全0／0skip、outer1。舊 placement-order 控制被快路旁路，原meta正常失敗1；原件與有限actual peer95／0全保，沒有移標 |
| 靜態／工具審查 | 排序283／0、單leaf15／0、r2 runner10／0、tuple工具26／0；各自 scope 限於靜態，不替代上述實跑 |
| 既定 16MiB stack | 上述三套與tuple都維持原limit並通過。本 PR 新增四個 size_t[2432] 區域陣列，兩階段共用；此64位環境陣列資料約77,824B，compiler frame／完整場景上限未另量 |
| 整條快路語意撤回 | **UNRUN**；本 S 另規劃8原正例等價0/0/0，不計killed、不冒完整12方法suite；與已完成tuple反證分開 |
| 性能／正式 P-189／容量512 | **UNMEASURED／UNRUN／未完成未驗**；沒有新數值門檻 |
| 完整 native、browser、全帳本、架構 | 本 S **UNRUN**；最終全帳本／架構由主代理統一處理 |
| skip／仍紅／READY | 本 S 上述原三套與tuple皆0skip，指定範圍綠；舊Scc2紅保留，其他未跑不計通過。性能／512未完成，**NOT READY** |

相對基底共五leaf：W `contact_world.c`、原 C harness、原 wood-contact Python suite、expected 單一 count，以及 contact-sources 的單tuple維護。兩個新增方法對應 wood-contact count10→12，其餘 expected 逐值不變（native30、faces45、noWood13等）。原方法 AST、CHECK、ASSERT、timeout與容量保留。原 placement-order／stable-ties 兩刀移到正常 comparator，另補 legacy 專刀保持原失效原因；contact-sources 同名 ordering 控制也精確移錨，沒有放寬斷言。

新排序只在 bounded／indexed／全部 facts ID唯一時略過原 insertion loop；duplicate／overflow原迴圈逐字保留。相等order合併取左，直接比較完整uint64；member suffix 的 destination→source cycle只用一個face暫存，RC前綴不動。相同 ContactFaceIndex 隨後完整重建plane metadata。新正反例逐欄檢查所有公開face欄位，涵蓋FREE RC、三元cycle、非2冪、相等order、完整64位、零／奇數cap與tail、duplicate last-order／stable sides，以及 member capacity+1後備。

遮蓋索引保單一真實覆蓋面，不把兩個半面合成見證。RC包含free fixity，member仍按原contact_earlier嚴格先後批次入索引，同order不互遮；lo／hi保strict-overlap與full-cover、完整GeoCoord。原過濾重複facts、零／反向跨度、完整座標、local plane offset與大buffer後備案例保留。64個控制都要求原 baseline0／具名正常ASSERT1／restored0，compile、crash、timeout或skip不算kill。

新三套於2026-10-23 23:03:46.221263～23:04:07.906571 UTC在固定 S完成；tuple三phase於23:04:13.900627～23:04:25.287954 UTC完成。兩項依root授權序列執行，各自fresh workspace通過原100MiB preflight，沿原16MiB、secondary鎖、子時限與完整streams；沒有新checkout、沒有與性能並行，真終態已釋slot。這些時段是執行紀錄，沒有當作效能比較。

前輪 Scc2 已跑完全部三套，唯一紅是 contact-sources 舊控制仍撤已被正常快路旁路的 fallback insertion break；原mutant `PASS ordering`／0，導致原meta-test唯一failure1。修復只將tuple移到真comparator，保原case、具名ASSERT、全部class AST與時限。明確撤回再現同一meta紅，恢復後綠；正常新comparator mutant仍必須由原 ordering ASSERT殺死。這是裁判定位維護，不是編譯失敗充紅，也不是whole優化語意差異。

完整原件在 [evidence/geo300-contact-index-20261024](https://github.com/ZhiQiYang/geometry-axiom/tree/a934a554ae58f16f124f1b264523947f170b3f0b/evidence/geo300-contact-index-20261024)。`MEMBER_SORT_ACCEPTANCE_ORIGINALS_AND_PEER.tar.gz` SHA-256 `2d4c3fdccf4d08f6590a72cd961bc8b1121dc076fe241b25d7736c19e4b044db`，10,636,252B；1498原檔／56,913,484B加index共1499 regular成員逐byte回讀。包含r1真紅、r2全三套、tuple三phase完整指令／exit／streams／env／SHA、原build logs與實際compiled C、before/after patch、靜審／actual peers及metadata更正。Git blob `ada21922c305ce4896e09e3366813123db2dc233` 直接入庫；原raw全部保留。

原sparse apply-check1、原stderr尾空白的diffcheck2、reviewer初checker錯誤與出版approval參數錯誤均分類保留。原stdout／stderr bytes不改，沒有重跑洗掉紅燈。先前正文的協作審查同意曾如實標成producer-saved訊息、非正式report；正式獨立report已補入此包。NativeBuild logs／native events是完整解碼文字，非解碼前OS bytes；最外host tool exit依API metadata，沒有獨立host OS capture，reaper／driver／三套原c387 stdout／stderr完整。

歷史 S1ee `1ee4e830399b124ebd63c5ff51064d87e53f38d9` 的33／56／302，及#341 Sc493的32／46／282維持原SHA與原封包。最不確定的是完整場景stack與實際成本收益；whole-opt八正例、正式性能與容量512均未完成。N128/256/512提議值未採為門檻，不改公理或決策佇列，尚未建議合併。
