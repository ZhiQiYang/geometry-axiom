# PF-5：明選完成面、雙層幾何與交界診斷

工作包 M 的設計／獨立 oracle 候選；基底為
`48d5f3887e8cb8d222307db62dbdea287fda8442`。這份文件與 Python 工具沒有改公理、產品命令、原生交易或一般 UI。

## 1. 來源、已存在能力與本片邊界

規範來源是 `公理層.md` 的 D1、D2、D3、D4、D41–D45、I52–I57、R41–R46。
決策脈絡是 [#128](https://github.com/ZhiQiYang/geometry-axiom/issues/128) 的 PANEL-FILL、STRUCT-FROM-FINISH、Q47、決策 F／PF0；
交付範圍是 [#467 工作包 M](https://github.com/ZhiQiYang/geometry-axiom/issues/467)，共同規則沿用 [#454](https://github.com/ZhiQiYang/geometry-axiom/issues/454)。
`PRODUCT-VISION.md` 是產品方向；需求帳 R02 是需求／完成度記錄，兩者沒有覆寫公理的效力。

現有 `geometry-core/panel-fill/PFH-NATIVE.md`、`tests/test_panel_fill_host.py` 已記錄並測試 R41 的原生派生宿主、分量、孔、負側 frame、typed h、D7 使用與重開。
`geometry-web/panel-fill-workspace.js` 也已有 UI1 派生宿主入口。
所以 PF-5 的下一片應銜接既有幾何，完成可理解的選面、空間脈絡、障礙預覽與交界展示，不能把 issue 的背景敘述解讀成原生完全沒有做。

這份 oracle 是**獨立、唯讀的幾何診斷工具**。它不被產品 import，也不是第二套執行期求解器。
輸入／輸出採專用 `pf5-geometry-input/1`、`pf5-geometry-output/1`，不是既有 native JSON／scene API。
它不產生可存成 D4 定義的宿主資料；輸出 `host` 只是板背 frame 與區域的數學見證。

明確未涵蓋的項目如下。

- 原生 R41 完整 edge key、typed source ordered set、每段 fixity、截段序號／總數及 stale key 行為。輸出固定標明 `edgeIdentity: "not-modeled"`；相同位置的 `b20`／`c20` 只保留各自診斷，沒有聲稱替代 edge identity。
- 原生容量、材料版本／參數來源解析、D4 的 fill／host identity、依賴圖、preview／confirm、取消／undo、存檔／重開。解析值的來源閉包仍由原生驗證。
- R42 板材拼排／錯縫／接縫、R43 承接量、D7 實際角材、PF6 配材、主承重層、吊點或承載安全。
- 非 D2 的斜向／任意旋轉平面、斜切板厚、斜接斷面、原生產品的成功驗收或 L4 CI。

## 2. 能直接由定義推出的幾何

一份完成面的使用者意圖是明選的 `frame=(O,U,V,N)`、結構側 `s∈{−1,+1}`、平面區域 `F` 與 typed 障礙清單。
面材厚 `t` 和角材斷面 `[A,B]` 都必須明選並解析成正整數 mm；本層的 `h=B`。
`A` 會影響實際角材與承接，**不會改變 R41 的層厚或裁切**，因此本工具只保留／驗證 A，沒有拿它產生角材。

令 `n=sN`。材料層沿 n 的範圍是 `[0,t]`，角材層是 `[t,t+h]`。
每一個**被選中的**障礙分別與兩層做正體積相交：只有投影在 F 內有正面積、normal interval 又有正長度的交集，才裁掉該層的投影。
面接觸、邊接觸、點接觸都不裁。
牆面必須沿它自己的 n 判斷，不能使用世界 z 當通用高度軸。地面與 `s=-1` 也走同一個定義。

板背 frame 必須是 `(O+t n, U, sV, n)`，原完成面的 `(u,v)` 對到宿主 `(u,s v)`。
原因是 `U×(sV)=sN=n`；而 `(s v)(sV)=vV`，同一個世界位置沒有因為換宿主座標而漂移。
有效區域全部保留，包含孔、多個內部連通分量與合法空集合；兩塊只在一點相接不合成一個分量。
若同一分量產生孔接外環等不能表成 R41 輪廓的退化，本工具整次拒絕，不補 bounding box。

Q47 的三個已決例子換成 mm，明示樑底為 2500、面材厚 9、角材高 30：

| 明選完成面高度 | 材料層 | 角材層 | 定義結果 |
| --- | --- | --- | --- |
| 2600 | 2600–2609 | 2609–2639 | 兩層都與樑相交，各自裁切 |
| 2400 | 2400–2409 | 2409–2439 | 兩層都通過 |
| 2480 | 2480–2489 | 2489–2519 | 材料通過、角材裁切 |
| 2491 | 2491–2500 | 2500–2530 | 板背碰樑底，材料不裁、角材裁切 |
| 2461 | 2461–2470 | 2470–2500 | 角材頂碰樑底，兩層都不裁 |

測試另明選樑頂 3000，才構成完整 AABB。表中值是具名測試的輸入，不是產品預設尺寸。

## 3. 哪些事情不能從房間、樑、t、h 唯一推出

這四類資料不足以決定天花到底選 2600、2480 或 2400，也不足以決定要一個平面或多個高低面。
D41 已要求完成面 pose／高度明示；Q47 的自動只涉及每一份已選完成面的兩層如何與已選障礙相交。
包樑底面與側面各是另一份完成面，沒有自動新增的授權。

因此本工具要求呼叫端提供**已明選的完成面集合**。房間 AABB 只提供空間背景；它不會生成六面、不會把越出房間的完成面偷偷裁回去，也不代表 D5 的成員關係。
完成面本身可以是任意簡單正交多邊形加互不接觸的孔，並非只支援矩形。
障礙也不按距離、名稱或位置自動納入；`obstacles: []` 與沒有填 obstacle 欄位不同，前者是明選空清單，後者是無效輸入。

### 明選較高天花、較低樑底與側封的見證

`step_faces()` 明選三份完成面，並明選樑盒 `(40,0,2500)` 到 `(60,100,3000)`：

| 面 | 明選世界位置與範圍 | 結構方向 | 兩層結果 |
| --- | --- | --- | --- |
| 1：較高天花 | z=2600，x=0…31、y=0…100 | +z | 各 3100 mm² |
| 2：較低樑底面 | z=2461，x=31…69、y=0…100 | +z | 各 3800 mm²；角材頂只碰樑底 |
| 3：側封 | x=31，y=0…100、z=2461…2600 | +x | 材料 13900 mm²；角材 3900 mm² |

31／69、兩個高度、側封範圍都是測試作者明選，並非 oracle 依 t／樑寬自動計算的政策。
材料層看得到兩條 100 mm 的共邊：`(31,0,2600)–(31,100,2600)` 與 `(31,0,2461)–(31,100,2461)`。
側封與較低面的板層有 8100 mm³ 的正體積交疊；工具如實列出，仍保持 `joinPolicy: "unselected"`。
這個見證展示幾何和未選收邊的差別，沒有把共邊當作已完成施工接法。

拿掉第 3 面後，結果仍只有原本的兩面，沒有補出側封；兩個可見面最小 L1 距離為 139 mm、沒有共邊，接法仍未選。
這可以呈現未封的高低面關係，不會逕自判斷使用者一定想封閉它。

## 4. 交界輸出與待選收邊

每一對已選完成面都輸出下列唯讀關係，已扣掉各自材料層的障礙裁切。

- `sharedEdges`：兩份有效可見區域邊界的共同線段及長度。共同邊可以來自外環、孔邊或障礙裁切邊；此處沒有 source key。
- `visibleContactDimension`：可見面交集維度，2 為面、1 為線、0 為點、−1 為沒有交集。
- `minimumL1Gap`：兩個有效可見區域在世界座標的最小 Manhattan 距離。它是明確命名的距離指標，不是某一施工縫寬；有空區域時為 JSON `null`。
- 四對 `panel-panel`、`panel-timber`、`timber-panel`、`timber-timber` 的層包絡交集：正體積、接觸維度與 `overlap/touch/separate`。
- `joinPolicy: "unselected"`：沒有選擇自動修邊政策。

角材層是**可能容納角材的包絡**，不是已放入的實際木料。包絡重疊不等於實際木料相撞；包絡碰到也不代表 R43 支撐成立。
跨完成面支撐不能繞過 R43 的同一 typed host 限制。診斷不新增「跨面接觸即違法」或「重疊即可承載」的公理。

以下是設計候選，沒有替使用者採用其中一種；若要做成自動命令，需先有明確授權的政策。

| 候選 | 需要明選或補足的資料 | 本片處理 |
| --- | --- | --- |
| 各面保留獨立邊界，交界開放 | 各面範圍與原意 | 列出空隙與接觸；不自動補側封 |
| 明選平接及哪一面到哪一個終止面 | 接法方向、兩個明選終止面、材料厚度、需要的縫 | 可由明選 D41 定義表示；不自動延伸或退讓 |
| 一面覆蓋另一面 | 哪面覆蓋、覆蓋量／終止面、留縫 | 分開列候選，不默認天花優先或牆優先 |
| 斜接／倒角 | 明選接法與新的實體斷面規格 | 現有正交區域＋整層包絡不能證明斜切實體；本片不生成 |
| 共用跨面骨架／承重 | 原生宿主、成員、支撐與工程設計規格 | 不由共邊推論，也不在本片建立新支撐規則 |

建立一份**使用者明選的**獨立側封完成面已有 D41 依據，本身不需要新增公理。
未定的是自動選高度、包接優先、延伸／退讓／斜切、跨面共用骨架等政策。

## 5. 專用診斷格式與執行

輸入與輸出均為封閉 schema：每一層的鍵名固定，未知欄位拒絕，避免把 `autoTrimApplied`、`loadBearingPassed` 或新幾何欄位默默忽略。
只有 `label` 是不影響幾何的展示名稱。所有長度／位置嚴格使用整數 mm；布林與小數不能冒充整數。
座標、解析長度與所選障礙的 local projection 遵守 D1 的 ±100000000；面材厚和 A/B 必須正值。
finish id 是正 uint32，b/c obstacle id 是 uint32，物件 identity 不使用座標上限。
frame 只接受 24 種右手 signed-axis frame，搭配兩種 side 共 48 種。

以下是完整的 `example()` 輸入，數值均明選。

```json
{
  "schema": "pf5-geometry-input/1",
  "room": {"min": [0, 0, 0], "max": [100, 100, 3000]},
  "obstacles": [
    {"ref": "b20", "min": [40, 20, 2500], "max": [60, 80, 3000]}
  ],
  "finishes": [
    {
      "id": 1,
      "label": "explicit fixture face 1",
      "frame": {
        "origin": [0, 0, 2480],
        "u": [1, 0, 0], "v": [0, 1, 0], "n": [0, 0, 1]
      },
      "side": 1,
      "region": {
        "outer": [[0, 0], [100, 0], [100, 100], [0, 100]], "holes": []
      },
      "obstacles": ["b20"],
      "thickness": 9,
      "section": [27, 30]
    }
  ]
}
```

將它存成 `input.json` 後執行：

```sh
python tests/pf5_geometry_oracle.py input.json > candidate.json
python tests/pf5_geometry_check.py input.json candidate.json
python tests/test_pf5_geometry_oracle.py -v
```

constructor 成功 exit 0，無效輸入／無法表示的退化 exit 2；checker 通過 exit 0，契約不符 exit 1，讀檔／JSON 失敗 exit 2。
成功不會留下部分結果。工具 stdout 的 JSON 可以保存作診斷證據，但不能直接當 `.scene` 或 `panel-fill-transaction/1` 載入。

## 6. 獨立性、掃描與真來源突變

constructor 使用掃描線將 F 分解成直條矩形、逐一做矩形相減，再取消相反邊，組回外環與孔。
checker 沒有 import constructor 或產品幾何，沒有共用 parser／normalizer／建構 helper：

1. 自行檢查原始 room、全部含未選障礙、frame、材料值、typed refs、孔拓撲及 closed schema。
2. 以所有原始／候選關鍵座標分割平面；對每個精確半整數測點，直接映回**原始世界座標 cuboid**，掃 normal 的 open cells，驗每層有無正體積碰撞。
3. 對預期占有的 cells 另做四鄰 flood-fill，驗每個內部連通分量、孔／外環、CCW/CW 與候選矩形覆蓋一致。不能只因面積相同就過關。
4. 只有在區域已獨立驗對後，交界體積才以世界座標 critical-cell 三維積分計算；constructor 則是兩兩 AABB 交集體積加總。共同邊以線上的分段測點覆蓋驗證，不沿用 constructor 的合併演算法。

測試包含 Q47、精確接觸、垂直／負側、48 個 frame/side 組合、孔與凹形、全部分量、點接分量、空 G、六面房間、明選高低面／側封、未選障礙、原始無效輸入及輸出污染負控制。
1 mm 掃描有 388 案：樑 x 最小值 −21…101（123）、樑 y 最小值 −61…101（163）、樑底 2440…2520（81）、兩面相對位移 −10…10（21）。
每案都跑完整獨立 checker；不是抽一張 golden 圖或只比總面積。

來源突變可重跑：

```sh
python tests/pf5_geometry_mutations.py \
  --base 48d5f3887e8cb8d222307db62dbdea287fda8442 \
  --out /tmp/pf5-source-evidence-new
```

這支程式只讀 repo，把三份 Python 檔複製到臨時目錄，對每個具名 target 寫入實體來源變動，實跑 baseline／mutant／恢復，記錄原檔與變異檔 bytes、SHA-256、命令、環境及 raw logs。
每次要求 `0/1/0` 且 mutant 由具名 assertion 失敗；ImportError、SyntaxError 或 unittest execution ERROR 不能充作證據。
輸出目錄必須是新的，不覆寫舊證據，也不修改官方 mutation ledger。

| 真來源突變 | 撤回的性質 |
| --- | --- |
| `PF5_CONTACT_IS_COLLISION` | 把開區間 `<` 改成閉區間 `<=` |
| `PF5_COLLAPSE_TWO_LAYERS` | 兩層錯誤合用 `[0,t+h]` |
| `PF5_WORLD_Z_INSTEAD_OF_NORMAL` | 牆面錯用世界 z |
| `PF5_FORGET_SIDE_IN_BOARD_BACK_FRAME` | 板背 frame 忘記 `sV` |
| `PF5_FORGET_HOST_REGION_REFLECTION` | 宿主區域忘記 `v→s v` |
| `PF5_DROP_LATER_COMPONENTS` | 只留下第一個分量 |
| `PF5_AUTO_INCLUDE_UNSELECTED_OBSTACLES` | 自動納入未選障礙 |
| `PF5_AUTO_CHOOSE_JOINT_POLICY` | 偷選天花覆蓋牆的接法 |
| `PF5_CHECKER_BLIND_TO_ALL_CORRUPTION` | checker 一律回成功 |
| `PF5_CHECKER_IGNORES_WINDING` | checker 不驗外環／孔方向 |
| `PF5_CHECKER_IGNORES_RIGHT_HANDED_SOURCE` | checker 放行左手來源 frame |
| `PF5_CHECKER_ACCEPTS_UNDECLARED_POLICY_FIELDS` | checker 放行未授權政策欄位 |

**證據的意義須分開**：只套 T 的紅是「工具入口不存在」這一個具名 contract assertion；其餘幾何測試明示 skip，不算已完成先紅的產品幾何回歸。
P 加入診斷工具後，幾何例／掃描與具名來源突變才可執行。
直接污染輸出、確認 checker 會拒絕，是另一種負控制；它不能冒充來源撤回的 0/1/0。
這些都不是 PF-5 產品 P、native 完整 R41 相符證明或官方 Geometry CI 的結果。

## 7. PF-5 產品切片與任務 A 的介面

既有原生 R41 是產品幾何權威。後續產品片應先確認原生狀態欄位與 renderer 的真實接口，不把上面的診斷欄位名假裝成已存在的 API。

| 切片 | 使用者看得到的結果 | 驗收路徑與依賴 |
| --- | --- | --- |
| PF5-V1：顯示已存在的完成面與派生層 | 空間視圖能辨認所選完成面、板背與實際有效區域；保留孔／所有分量 | 資料由既有 native state 取得；沿用既有 renderer／選取機制，驗負側、垂直、空 G；共用 A1 的真實宿主 bbox／empty／來源／型別／h |
| PF5-V2：明選空間表面並確認 pose／障礙 | 選地、牆、天花或明選其他面；清楚顯示高度／方向與障礙逐層結果 | 重用 UI1 的定義與 preview/confirm；缺 t/h 明示，取消不變；材料版本與 h 來源不由畫面猜 |
| PF5-V3：明選多高度與側封的關係檢視 | 能同時看到已選高低完成面、側封、共邊、未封處與包絡交疊 | 三面見證與漏選側封對照；joinPolicy 不自動定案；不能將包絡當實際木料／支撐 |

任務 A 的 A1 是一般／派生宿主的真實 bbox／empty、來源／型別／h，以及參數使用處與 I38 說明。
A2 是一般／派生宿主卡片的角材／格線縮圖、面內唯讀 typed 導覽、來源面相關物件與選取尺寸；這部分的 UI 取捨仍待核。
PF-5 負責完成面與派生層的幾何含義、所選障礙的說明、有效區域呈現與完成面編輯流程。
PF-5 沿用既有 renderer／選取機制，以穩定 typed identity、原生 pose／region 串接上述共同宿主資料、呈現與導覽；工程座標取自原生資料。
新的 camera／深度引擎工作不屬於 A 已承諾的範圍，也不列作 PF-5 前置。

本片只新增 `tests/pf5_geometry_*.py`、`tests/test_pf5_geometry_oracle.py`、此說明與獨立 suite fragment，不碰 PF6 的 App 入口，也不把 PF4B snapshot 修改包進來。
PF5-V1 要改哪些 renderer／App 檔、疊哪個 A/PF6 head，應在第一片產品 T/P 前另釘完整基底與順序。
測試登錄使用既有 `init-suite` 生成的 `tests/suites.d/py__test_pf5_geometry_oracle.json`；沒有改既有斷言、golden、aggregate manifest、timeout、exclusion pin 或官方衍生證據。

目前驗證只到本機 Python 診斷工具及其裁判；本片沒有編譯 native、沒有實跑 Chromium、沒有提出產品 PR，也沒有主張 PF-5 一般 UI 已完成。
