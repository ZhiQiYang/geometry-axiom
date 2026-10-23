K＋矩形格網模板的隔離建置補上 `geometry_woodworking`／`geometry_app` 真匯入拒絕，以及 K 引用可取得 W 標頭的 quoted／angle 守門。原11項功能／反證與斷言保留，新增兩項後共13項。已一般 merge #318 正式來源交棒，精準更新共用 expected 11→13；**編譯與動態驗收尚未執行**。

獨立安裝只取 K exact／geometry／grid、矩形格網模板與測試共11檔。sentinel 套件實際可取得，不能以缺套件冒匯入拒絕；K→W 控制各加一行真標頭 include，要求先成功編譯／連結／exact-cells，再由原 source gate 取得0／1／0。尚未有原始動態結果。

| 唯一 current state | SHA／原 exit | 範圍與限制 |
|---|---|---|
| 產品／測試來源 | `9b201164ed31069843a2b9f3787ea8ae8e22e231` | 已普通push，遠端exact SHA同；含前棒來源聯集 |
| 證據 head | `6f2e5e27d2f949ef63d198ceac0630a352f6b397` | revision-3封原Git完整streams與source交棒／count更新收據，動態仍未跑 |
| #318正式 source棒 | `ae74e51bba1efef48949c077635966273a9e8990` | 相對fdac首父的非evidence blobs/modes零差；這是source交棒，沒有宣告動態綠 |
| 一般 merge／來源發布 | 原collector 0 | merge `9129cb954412dcd23575185fa7e5e7b2c96e8959`，無rebase／force；乾淨worktree與remote同 |
| 測試方法／expected | 靜態13／登記13 | 只改此suite 11→13，其餘expected資料不變；不是實跑Ran13 |
| 原11檔閉包／葉檔 | hash維持 | 葉檔SHA256 `e948fb78e81a075875a45041009fb379e58d783c8d6b579cd9fa2f81cd40910e`；沒有帶入木工W或H編譯來源 |
| 完整隔離13項 | 未跑 | 等root安排重工作槽，沒有新增允許skip |
| import blocker反證 | 未跑 | fixed／withdrawn／restored預期0／1／0，斷言不動 |
| K→W guard／angle parser反證 | 未跑 | frozen collector七phase預期0／1／0／1／0／1／0，兩種真include各有內層0／1／0 |
| 對抗審查 | R2靜審無確立新阻擋 | #314已核葉檔與collector；本source合流／count及真same-SHA動態結果待再審 |
| 全域突變帳本 | 本子項未重產 | 只由root在共同最終SHA整份重產一次 |
| 完整native／browser／架構 | 未以此source重跑 | 不把前棒或歷史F13結果外推成新source全綠 |

本子項直接只改隔離測試葉檔與其expected count；一般merge保留#323→#314→combined→#318的來源聯集。K架構原裁判仍負責完整來源契約，此小型source守門只宣稱literal include檢查，不冒完整C前處理器分析。待root資源槽後，以此已公開source跑原collector，封完整原streams，再交#314做對抗審。

最不確定的是尚未實跑的編譯與三類撤回反證，以及整個前棒聯集尚未收齊的正式驗收。編譯失敗、crash、watchdog、unittest error或未允許skip都不能算成功突變反證。不force push、不合併PR。
