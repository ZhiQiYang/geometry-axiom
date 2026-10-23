# P88：真實滑鼠輸入前確認控制項位置穩定

P88 在 390 px 版面切換 `#refGuideMode` 時，原 helper 可能沿用重畫期間取得的座標，點擊後沒有取得指定焦點。本補丁只改 `geometry-web/grid_rule_lines_test.js` 的 P88 輸入準備：重新取得目前節點，確認節點及矩形跨兩次畫面更新保持相同，且位置確實命中目標，再送出該次唯一真實點擊。

準備與精確焦點判斷共用原 25 秒；原 12 次嘗試上限、斷言、golden 及 CI 時限不變。新增的是輸入前的觀測，沒有強制 focus、DOM click、寫入欄位值，也沒有錯點後再次點擊補救。

| 唯一 current-state 矩陣 | SHA／原退出碼／狀態 |
| --- | --- |
| product／正式受驗 F | `3d681636902371ecc528b20f51eea33e272581c9`，公開 SHA；來源前後同 SHA、空 status、同 index |
| 本補丁 source commit | `8bce9239c014f070740455556c8ee1176c500af3`，唯一修改 P88 測試檔；已由主代理合入 F |
| 子代理 evidence head | `2b72d3fabacd2d8ac96c19c22e74ba7b94f2e2eb`；`evidence/geo288-p88-20261023/` |
| 最新已讀審查 | handoff `acd1289228d490c68a139cf17e02fdc1f3cb247c` 的 `handoff/pr-reviews/288.md`，2026-10-23T12:35:32Z、head `ee28481` |
| 新 F 完整 canvas 連續三輪 | exit **0／0／0**；每輪 full completed、2267／0、P88=143、P73=69、golden matched、skip=[]；1741.884／1748.520／1765.120 秒，均在原 35 分鐘內 |
| 新 F 原生 rAF 受控反證 | fixed／withdrawn／restored 原 outer、workflow、Node 各 **0／1／0**；總 driver／outer／launcher **0／0／0**；三階段前提有效，固定與恢復完整原 P88 143 斷言，撤回觸發下列原精確焦點失敗 |
| 帳本與架構 | 主代理在 F 已核 `mutate.py --check` 及架構三條原裁判，各 exit 0；收據屬主代理整合 evidence |
| source 語法與差分 | `node --check geometry-web/grid_rule_lines_test.js` 及 source `git diff --check` 各 exit 0；原 helper、golden 與產品檔未改 |
| 允許的 skip／範圍 | 正式 canvas 沒有 skip；反證外部 loader 只載入原 P88，明列省略其餘 grid 模組，partial 不比全 job golden，不能充作正式 grid |
| 本子代理未執行項 | 新 F 正式 grid、native 補項、P52/P73 專項、其他 Chrome 版本及其餘 oracle 反證由主代理排程；本正文不宣稱整份 #288 全綠 |
| 最不確定之處 | 沒有 Paint/compositor 畫面證據，不能證明真人從未看到中間位置，也未窮盡按下滑鼠期間的重畫；原自然紅沒有 pointerdown trace，不能回填唯一歷史原因 |

撤回修正時的原失敗為：

```text
UI condition timed out at === P88. 原生來源子線顯示、完整引用、兩面及正式重開 ===: document.activeElement===document.querySelector("#refGuideMode")
```

三階段使用同一個已存在的真 query、成功 renderer 與原 scroll-restore callback。唯讀原量測在真 native rAF 入口前得到 `(293.75, 627.5)`，當時命中 mode；原 callback 依原 this／args／guards 執行一次後，舊點已命中 ratio label。撤回版原樣送出舊座標，真 trusted pointer 命中比例列並以原焦點 predicate 失敗。修正版與恢復版在該目標量測後的唯一真實點擊之前重新觀測，使用 y=602.5 命中 mode。沒有手改 scroll／rect／focus／值，也沒有人工另呼叫 callback。

這證明此有效交錯下的舊座標缺陷及修正效果。獨立代理分別核對三階段原輸出、來源與工具綁定、原座標及真 pointer；另一代理核對產品保全與既有 trace，未建立新的產品交互紅燈。它仍不能證明所有真人交錯安全；若另有實際可見互動失敗，需修產品並重新固定 F，不能只加測試等待。

正式命令、完整環境、原始 stdout／stderr、各層退出碼與 SHA 均收在 `final-canvas-three/` 及 `native-raf-result/`。反證完整包 `NATIVE_RAF_RAW.tar.gz` 為 22,446,502 bytes，SHA256 `3f107c0424c62844eaeac3ab6086ea75b7ebc6cc3c9e829dd61c34eedcb52e4a`，349 檔 roundtrip 全一致；各 phase/tmp 整樹（含 profile、cache、feedback、編譯產物）排除範圍明載於 manifest，原磁碟仍保留。

歷史結果保留：原 F `13d02c1db7022145a52ee063286a558e595eb212` 三次完整 canvas 為 **1／0／0**，所以分類為間歇紅。先前真 query 實驗固定／撤回／恢復皆原 exit 1、總 driver 2，原因是工具的位移前提未成立，並非原焦點反證；原件仍完整封存，沒有以本次成功覆蓋。新反證依該實驗觀察到的原 renderer／scroll 恢復短窗設計另一個明列的排程交錯，並非把失敗實驗重抽成綠。
