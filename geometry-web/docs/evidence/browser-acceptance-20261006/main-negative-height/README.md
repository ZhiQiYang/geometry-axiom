# main 是否有 `<rect>` 負高度/寬度錯誤(R-18 對照)

**判定:main 有。** 條件:角材工具下 `#tbAnchor` 選到「落在面外框(含 pad)之外」的參考線(guide)。

- 版本:main `6562fa53d90de22b3e5492f2083199b26377a8c2`,tree `00807ad44334e88f36313a3a8476ea7ae7d5e63d`(detached worktree D:/geo-negh-main,已移除)
- `/runtime`:`fresh:true`,version `2bbcd8fbdb1a6e8e4d5504d495d165959ad6ee03e1707ef1415050fd37f04eb6`(runtime.json)
- 環境:本機 Windows 11、playwright 1.63 bundled chromium、fresh profile、port 8875、只用合成資料。資源閘門 READY 後才啟動(閘門末行 free=1524MB cpu=46%)。
- 腳本:scan.py(`python scan.py <w> <h> 8875`);量測:scan_390.json、scan_1382.json;log:run_*.log;截圖:s0_face_*.png(場景)、s1_last_A20_*.png。

## 步驟
1. 以 `apiRequest('line …')` 夾具指令建場景(非逐步點 UI):外框 1200x800 含一孔的面 1;主網格 1(u 400/800、v 300/600);子網格 0(cell u/v min line:0,2x2 等分,bounds [0,0,400,300]);一角材 81(at-face e0);guide 11(u=120)、12(u=1190)、13(u=5)、14(u=1500)、15(u=-300)、16(v=5)、17(v=5000)。
2. `enterFocus('face',1)`、`feSetTool('timber')`;`#tbA`=`#tbB`=A(20,再 2000),對 `#tbAnchor` 全部 22 個 option 逐一設值+input/change 事件,呼叫 drawFaceEditor,收集 `.fe-anchor-band` 的 x/y/width/height、`feAnchorLineInfo`、`feAnchorCrossRange`、期間 console error。
3. 視口 390x844、1382x804 各一輪(各 44 筆=22 option x 2 個 A)。

option 清單(22):at-face e0..e3、h0e0..h0e3、at-face t81、at-line guide 11-17、at-line grid 1 u0/u1/v0/v1、at-line grid 0 u0/v0(子網格)。

## 結果(觸發者)
| 視口 | A | option value | 負值 | console error |
|---|---|---|---|---|
| 390 | 20 / 2000 | `at-line guide 17`(v=5000,距面外框遠) | height=-3880.3 / -2890.3 | `<rect> attribute height: A negative value is not valid.` |
| 1382 | 20 / 2000 | `at-line guide 17` | height=-4057.0 / -3067.0 | 同上 |
| 1382 | 20 | `at-line guide 14`(u=1500) | width=-157.04 | `... attribute width ...` |
| 1382 | 20 | `at-line guide 15`(u=-300) | width=-157.04 | `... attribute width ...` |
| 390 | 20 | guide 14 / 15 | 不負(width=19.68) | 無(視口寬度影響 gb 外框範圍) |

JSON 鍵:`scan_<w>.json` → `options[]` 中 `negative:true` 或 `errors` 非空者(`value`、`A`、`bands`、`info`、`cr`、`errors`)。錯誤每筆出現兩次,因我手動呼叫一次 drawFaceEditor 加上 change handler 自己重繪一次。
其餘 option(面邊、孔邊、一般網格線、子網格線、guide 11/12/13/16)皆無負值、無 error;子網格線的 band 受 `bounds` 限制,正常。A=2000 時觸發集合與 A=20 同為 guide 17(1382 下 guide 14/15 在 A=2000 未觸發),數值不同但結論不變。
機制:負值 = 線在 `gb`(面外框+pad,與視口相關)外超過 A/2 時,`feAnchorCrossRange` 區間與 gb 交集為空,main app.js 約 5160-5164 行未檢查。與靜態推論一致,但範圍比「僅 subgrid bounds」寬:一般 guide 即可觸發。

## 未涵蓋
- 場景用夾具指令而非逐步 UI 點擊建立;guide 14/15/17(面外)是否能經真 UI 建立未驗(UI 可能拒絕)。因此「main 在使用者可達路徑上必現」尚未證明,只證明資料存在時 main 會觸發。
- 未掃:多面、多子網格、錯位(stagger)網格的 `band` 型錨點、subgrid 線落在 bounds 外的情形、超過一個孔。
- 未量 main 在 mobile 抽屜 UI 下選 option 的操作(用程式設值)。

## 已停 PID
serve 39504(子:conhost 43532、bridge 38628),見 pids.txt、svc_stop.txt。worktree D:/geo-negh-main 已移除。


### 390
| A | value | band x,y,w,h | negative | console error |
|---|---|---|---|---|
| 20 | `at-face e1` | [1180.0, -309.7, 20.0, 1419.4] | False | 0 |
| 20 | `at-face e2` | [-309.7, 780.0, 1819.4, 20.0] | False | 0 |
| 20 | `at-face e3` | [0.0, -309.7, 20.0, 1419.4] | False | 0 |
| 20 | `at-face h0e0` | [150.0, -309.7, 20.0, 1419.4] | False | 0 |
| 20 | `at-face h0e1` | [-309.7, 280.0, 1819.4, 20.0] | False | 0 |
| 20 | `at-face h0e2` | [230.0, -309.7, 20.0, 1419.4] | False | 0 |
| 20 | `at-face h0e3` | [-309.7, 60.0, 1819.4, 20.0] | False | 0 |
| 20 | `at-line guide 11` | [110.0, -309.7, 20.0, 1419.4] | False | 0 |
| 20 | `at-line guide 12` | [1180.0, -309.7, 20.0, 1419.4] | False | 0 |
| 20 | `at-line guide 13` | [-5.0, -309.7, 20.0, 1419.4] | False | 0 |
| 20 | `at-line guide 14` | [1490.0, -309.7, 19.7, 1419.4] | False | 0 |
| 20 | `at-line guide 15` | [-309.7, -309.7, 19.7, 1419.4] | False | 0 |
| 20 | `at-line guide 17` | [-309.7, 4990.0, 1819.4, -3880.3] | True | 4 |
| 20 | `at-line grid 1 u 0` | [390.0, -309.7, 20.0, 1419.4] | False | 0 |
| 20 | `at-line grid 1 u 1` | [790.0, -309.7, 20.0, 1419.4] | False | 0 |
| 20 | `at-line grid 1 v 0` | [-309.7, 290.0, 1819.4, 20.0] | False | 0 |
| 20 | `at-line grid 1 v 1` | [-309.7, 590.0, 1819.4, 20.0] | False | 0 |
| 20 | `at-line grid 0 u 0` | [190.0, 0.0, 20.0, 300.0] | False | 0 |
| 20 | `at-line grid 0 v 0` | [0.0, 140.0, 400.0, 20.0] | False | 0 |
| 20 | `at-face t81` | - | False | 0 |
| 20 | `at-face e0` | [-309.7, 0.0, 1819.4, 20.0] | False | 0 |
| 20 | `at-line guide 16` | [-309.7, -5.0, 1819.4, 20.0] | False | 0 |
| 2000 | `at-line guide 17` | [-309.7, 4000.0, 1819.4, -2890.3] | True | 4 |

### 1382
| A | value | band x,y,w,h | negative | console error |
|---|---|---|---|---|
| 20 | `at-face e1` | [1180.0, -133.0, 20.0, 1065.9] | False | 0 |
| 20 | `at-face e2` | [-133.0, 780.0, 1465.9, 20.0] | False | 0 |
| 20 | `at-face e3` | [0.0, -133.0, 20.0, 1065.9] | False | 0 |
| 20 | `at-face h0e0` | [150.0, -133.0, 20.0, 1065.9] | False | 0 |
| 20 | `at-face h0e1` | [-133.0, 280.0, 1465.9, 20.0] | False | 0 |
| 20 | `at-face h0e2` | [230.0, -133.0, 20.0, 1065.9] | False | 0 |
| 20 | `at-face h0e3` | [-133.0, 60.0, 1465.9, 20.0] | False | 0 |
| 20 | `at-line guide 11` | [110.0, -133.0, 20.0, 1065.9] | False | 0 |
| 20 | `at-line guide 12` | [1180.0, -133.0, 20.0, 1065.9] | False | 0 |
| 20 | `at-line guide 13` | [-5.0, -133.0, 20.0, 1065.9] | False | 0 |
| 20 | `at-line guide 14` | [1490.0, -133.0, -157.0, 1065.9] | True | 4 |
| 20 | `at-line guide 15` | [-133.0, -133.0, -157.0, 1065.9] | True | 4 |
| 20 | `at-line guide 17` | [-133.0, 4990.0, 1465.9, -4057.0] | True | 4 |
| 20 | `at-line grid 1 u 0` | [390.0, -133.0, 20.0, 1065.9] | False | 0 |
| 20 | `at-line grid 1 u 1` | [790.0, -133.0, 20.0, 1065.9] | False | 0 |
| 20 | `at-line grid 1 v 0` | [-133.0, 290.0, 1465.9, 20.0] | False | 0 |
| 20 | `at-line grid 1 v 1` | [-133.0, 590.0, 1465.9, 20.0] | False | 0 |
| 20 | `at-line grid 0 u 0` | [190.0, 0.0, 20.0, 300.0] | False | 0 |
| 20 | `at-line grid 0 v 0` | [0.0, 140.0, 400.0, 20.0] | False | 0 |
| 20 | `at-face t81` | - | False | 0 |
| 20 | `at-face e0` | [-133.0, 0.0, 1465.9, 20.0] | False | 0 |
| 20 | `at-line guide 16` | [-133.0, -5.0, 1465.9, 20.0] | False | 0 |
| 2000 | `at-line guide 17` | [-133.0, 4000.0, 1465.9, -3067.0] | True | 4 |
