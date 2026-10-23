此變更在全部 fact ID 唯一且仍在既有容量內時，以索引處理兩個原平方成本：每個完整座標平面的單一覆蓋面查詢，以及 member face 的穩定放置排序。排序共用既有 sorted／scratch 陣列，僅用一個 face 暫存做 permutation；RC 前綴、完整 uint64 order 與同 order 的宣告／側面順序保持。重複 ID（包括被過濾的 fact）與超容量輸入保留原後備。

基底是 `codex/geo260-ac23-proof-20261024`，接續 #341 的活集合與一次壓緊前置。正常 bounded/unique member 排序改為 O(F log F) 比較＋O(F) 重排；重複 ID／overflow 的平方排序與配對、超容量 memmove、cut-list 平方儲存及呼叫量問題仍在，沒有宣稱整個 collector 或 load 已解除平方成本。

| 唯一 current-state 矩陣 | SHA／結果與範圍 |
| --- | --- |
| Product SHA | `ccfaf057088a80c7aad4049f1c67e5eedfc2fdec`；父 E `17e74d3233a76b1967cd132ccb69769e7f9a41a3`，產品與 `cc2ea1b3b42291f6ebb0ead6bd1c2180920d7041` 同 bytes，僅修 contact-sources placement-order 控制錨點；expected 保12 |
| Evidence head | `03c8b4a203323d49b7f42a1775271c79021c08bf`；只改本 PR evidence prefix，產品與上述 S 相同 |
| Base | GEO260 E `df230da57619e437c30527dbede8c67fd0ec6b50`／產品 `eb846c345881cc6fc73a53c457a291175365b88c` |
| 排序靜審／runner 綁定 | 283 checks／0 findings；contact-sources 單leaf15／0；r2 runner機械綁定10／0、tuple受控工具26／0，均未執行 C |
| 原 wood-contact-world | **UNRUN**；本 S 預期 12 方法／41 具名控制；原 11 方法 AST、CHECK、ASSERT 與時限保留 |
| 原 contact-sources | **UNRUN**；本 S 預期 15 方法／11 控制 |
| 原 Reading A native | **UNRUN**；本 S 預期 7 方法／12 控制（11 W＋1 H） |
| 本 S 部分 native 合計 | **UNRUN：34 方法／64 控制**；不繼承下列歷史綠燈 |
| 歷史 S1ee 實跑 | 僅 `1ee4e830399b124ebd63c5ff51064d87e53f38d9`：33 方法／56 原具名正常 0/1/0、302 builds、三套 exit0／0skip；actual peer1140／0、public peer1571／0 |
| 上輪 Scc2 真紅 | `cc2ea1b3b42291f6ebb0ead6bd1c2180920d7041`：wood12/41 exit0、contact-sources15 exit1、ReadingA7/12 exit0；318 builds全0、0skip。唯一舊 placement-order 控制被新快路旁路，原meta正常失敗1；本輪紅原封保留 |
| 整條快路撤回 | **UNRUN**；本 S 另規劃 8 原正例 fixed／withdrawn／restored 語意等價 0/0/0，不計 killed、不冒完整 12 方法 suite |
| 既定 16MiB stack | 新 S **UNRUN**；共用同四個 size_t[2432] 固定長度區域陣列，未新增／加大陣列；額外一個 face 暫存，compiler frame／完整場景上限未另量 |
| 性能／正式 P-189／容量512 | **UNMEASURED／UNRUN／未完成未驗**；沒有新數值門檻 |
| 完整 native、browser、全帳本、架構 | 新 S **UNRUN**；最終全帳本／架構由主代理統一處理 |
| skip／仍紅／READY | 新 S 尚未執行，不計通過；Scc2原meta紅1保留，另有歷史sparse物化環境失敗；**NOT READY** |

排序部分為 W `contact_world.c`、原 C harness、原 Python suite，以及 expected 單一 count 四檔；另有 `tests/test_geo261_contact_sources.py` 的單tuple錨點維護，共五leaf。只在 bounded／indexed／全部 facts ID 唯一時略過原 insertion loop；duplicate／overflow 原迴圈逐字保留。相等 order 合併時取左，完整 uint64 直接比較，不截32位、不相減。排序僅處理 member suffix；原同一個 ContactFaceIndex 隨後重建 plane metadata，不把四陣列移到 fallback frame。

原 placement-order／stable-ties 兩控制移錨到正常路徑的真 comparator，保原 case、同名 ASSERT 與 timeout；另補兩個 legacy 專刀保持原後備的「不排序／不穩定」失效原因。新增一方法與八控制，合12／41，逐一釘唯一原碼位置。正例逐欄檢查全部公開 face fields，涵蓋 FREE RC 前綴、三元 cycle、非2冪 merge、等 order、完整64位、零／奇數cap與tail、重複ID last-order／stable side、member capacity+1。每控制仍要求 baseline0／具名正常 ASSERT1／restored0，compile、crash、timeout、skip 都不能算 kill；本 S 動態尚未跑。

遮蓋查詢保單一實際覆蓋面：兩個半面不能聯集合成一個見證。RC 包含 free fixity，member 仍按 contact_earlier 的嚴格先後批次入索引，同 order 不互遮；lo／hi 保 strict-overlap 與 full-cover、完整 GeoCoord。既有零／反向跨度、過濾重複 facts、完整座標與容量後備的原斷言仍保留。

新靜態原件在 [evidence/geo300-contact-index-20261024](https://github.com/ZhiQiYang/geometry-axiom/tree/03c8b4a203323d49b7f42a1775271c79021c08bf/evidence/geo300-contact-index-20261024)。`MEMBER_SORT_STATIC_ORIGINALS_AND_PEER.tar.gz` SHA-256 `f0d6d8b6776013e7e74fe669a13e0b854f47b591aabb1458a90c4ee90e8bc297`，171 原檔＋index 共172成員逐byte回讀，含前後四leaf、完整 Git 指令／exit／streams、patch roundtrip、靜審與當時未跑的 runner 綁定。

Git-only 出版第一輪 apply-check exit1，唯一原因是薄 checkout 未物化原 tracked `tests/run_all.expected.json`。沒有套產品 patch 或啟 C；r2 只從同 HEAD 精確 restore 該原檔，再套相同凍結 patch，一般 commit／push0且遠端同 SHA。原失敗完整保留，沒有刪測試或放寬來源守門。reviewer 初版 expected-schema checker 的2個 metadata findings／exit1與修正版283／0也一起保留，未當作產品紅或重跑 subject。

上輪 Scc2 已於22:47:26.381006～22:47:48.756991 UTC跑完全部三套；wood／ReadingA通過，contact-sources唯一舊反證仍撤 fallback insertion break，原mutant輸出 `PASS ordering`／0，使原meta-test產生唯一正常failure1。147＋85＋86＝318 builds全0，outer／primary／reaper／launcher皆1、source HEAD／tree clean，沒有用編譯或crash充紅。新leaf只將該tuple改到正常 `return left<=right;`→`return true;`，維持原ordering案例、具名 ASSERT、全部class AST、15方法／11控制與時限。新S的綠燈尚未跑，另將留原受影響方法的fixed／舊tuple撤回／restored 0/1/0（8原controls，非完整15方法或11控制）。

本 E 已公開r1原inner/top receipt與完整紅stderr、單leafpatch／manifest／peer／普通push證據；其餘全raw／compiled C／logs仍在原路徑保全，完整封包與actual/public peer待下一實際批次，不宣稱已公開全raw。`git diff --check` 原exit2只指原stderr第8行尾空白，原bytes保留；精確排除此一raw路徑的其餘staged檢查0，沒有修改原stdout／stderr。

歷史 S1ee 的實跑為2026-10-23 21:55:09.059797～21:55:31.974441 UTC，11／15／7方法、33／11／12反證、131＋85＋86＝302 builds全0，原driver／reaper／launcher／host tool0、HEAD／tree／clean保持。原 `THREE_SUITES_ORIGINALS_AND_PEER.tar.gz` SHA-256 `09b50ede5a8e932ef8bb6b69348a810ebbf1db7433908b02e83b751d8172f24d` 保356 raw／20,889,604 bytes及工具／peer，共366成員，沒有改標新排序來源。NativeBuild logs／events 是完整解碼文字，非解碼前OS bytes；最外 host tool exit依原API回覆，沒有獨立host OS capture，reaper／driver／三套原streams有c387收據。#341／Sc493的32／46／282也維持原SHA。

下一步是在固定新 S 用新的 workspace OUT／TMPDIR 跑原三套34／64，並做上述tuple撤回／恢復原method，沿原100MiB preflight、16MiB、secondary鎖、子時限與完整streams，不與root全帳本並跑性能。最不確定的是完整場景的stack與實際成本收益；八正例快路撤回、正式效能與容量512均未完成。N128/256/512的提議數值沒有採為門檻，不改公理或決策佇列，尚未建議合併。
