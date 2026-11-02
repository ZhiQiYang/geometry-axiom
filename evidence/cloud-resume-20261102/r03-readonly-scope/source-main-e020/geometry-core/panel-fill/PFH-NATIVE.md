# PF-H 原生衍生宿主（P-098／P-103／P-116）

本片接入 D4 衍生宿主、R41 重建、既有 D7 放置及 I53／I55／I56 生命週期。
沒有新增可見 UI、修改 SSOT 或實作 PF-3 的 effectiveSeams／support 產品輸出。

## 定義與保存

`panel-fill-transaction/1` 的 `put-derived-placement`：

```json
{"op":"put-derived-placement","value":{"id":10,"fillId":1,"h":30}}
```

`h` 也接受既有工程來源：`kind=literal`、`spec`、`parameter`、固定 timber 材料版本的 `B`。
不接受 D28 application。id 共用一般 placement 的空間，包含合法的 0；來源 fill 不可改指，
同 fill 至多一個宿主，同 id 不可轉換變體。刪除使用 `delete-derived-placement`。

保存只產生 `derived-placement ID definition-hex HEX`，HEX 內只有 id、fillId、h；
不保存 frame、boundary、rect、分量、環、fixity 或邊鍵快取。D12 canvas-pos 沿用原紀錄。
依賴順序為來源 boundary／RC、材料／參數、finish-surface、panel-fill、derived-placement、grid、guide／timber。

## 重建與引用

R41 共用 PF-2 的精確格網裁切原語，但分別計算角材層開區間 `(t,t+h)`。
板背框架 `(O+t·sN,U,sV,sN)`；正規外環逆時針、孔順時針。
材料按內部連通拆分，空宿主合法；孔與孔／外環相接的退化候選整筆拒絕。
F 邊繼承 fixity，切邊 FIXED；共線邊僅在方向與 fixity 一致時合併。

公開鍵是來源／段號／總段數三元組的 JSON 陣列。F 使用 `e0`／`h0e0`，障礙使用
`cID:u-`／`u+`／`v-`／`v+` 或 `bID:...`（側別在板背框架）。
來源在全部分量邊界上的極大連續段決定 segment／total；沿正規邊方向排序，重合來源保留全序。

- at-face：`place 1 on 10 at-face key-hex:HEX +u +n`。
- D18：`between key-hex:HEX1 key-hex:HEX2`，也可沿用已放 timber 擋面。
- D6a：`edge-key:HEX:u`／`:v`（HEX 是完整鍵 JSON 的 UTF-8 十六進位）。
- R18 保存註解與 native timberSupports 使用完整鍵。

衍生面不接受一般 e/h 索引或頂點引用；零個／多個完整匹配均拒絕。
多分量共用既有 contains、跨距、擋面、D17／I19／I20／I21 和碰撞檢查，沒有角色豁免或 bbox 補面。
D10／I23 的座標範圍取全部分量的聯合外接範圍，索引語意不變；D19 的 C∩F 正面積逐分量扣孔判定，
缺口或第二分量的孔不算材料。DrawTarget 逐分量畫真實輪廓，guide／grid 線只裁切一次完整集合，guide pick／hover 沿用同一可見段。
I53 要求 B=h 且 +n；只改 h 使既有 B 失效會拒絕。host 交易可同批明改 B source／override、參數，
其 before／after dependencies 在確認前公開；不自動改 B 或刪除角材。
D28 application 與 D38 live placement host 明確拒絕；現有 modeling executor 仍不支援 panel-fill/1，
不能經它做 D20 擠出。

## 容量與驗證

有界 POD 重建快取讓 World／history 保持既有複製語意；快取每次清零重建，從不 dump。
宿主共用 16 個 placement 名額；每宿主最多 8 分量，每環 32 邊、每分量 8 孔。
來源定義最多 1023 bytes、完整鍵最多 511 bytes；超限明確 I33 CAPACITY，拒絕整筆，不截短。
原生測試使用 16 MiB stack。

`tests/test_panel_fill_host.py` 涵蓋 32 題，包括 R15 的拓撲／深度／fixity／總段數案例、
來源型別、0 id、第二分量 grid／subgrid 的重開及 I23 回滾、實際 render／pick、
容量、原子 h/B 更新、拒絕回滾、保存／重開及 Undo／Redo。
原四題紅基準保留；其中 Undo／Redo 的橋接器指令更正為既有 `line undo`／`line redo`。

`python3 tests/pfh_witness.py --out /tmp/pfh-witness` 會保存 #221 的真衍生宿主原生見證、
實際 D7 足跡與全新 bridge 程序重開結果。
E1-legal 的 native 足跡餵給獨立測試 oracle 得五段，E2／E3 各三段；
原單一足跡的純演算法 oracle 保持三段／一段／一段。
`tests/pfh_oracle.py` 是測試消費者，不能當作 PF-3 產品驗收。

完整 native、官方 mutation 重生、PF-H 具名撤除負控制及來源雜湊收據見本次交付 evidence。
正式 WSL 七項仍由本機排程，本片沒有執行或冒稱通過。

## P-126 正典同步

2026-10-15 依 Claude P-126（6183800777），本分支已使用官方同步器原位重產唯一正典。
14 行追溯差異與指定推演 SHA 完全一致；`--check` 與原 41 題全過，SSOT／白話／批註未改。
最新完整 native 與來源原件見 `tests/evidence/pfh-p126-20261015/`；前輪 reader 六紅保留為歷史。
產品、32 題、11 步負控制與 50 筆突變依裁決維持前輪報告；正式 WSL 七項未跑／未排。
上列車時仍須依 P-090／P-105 在合併樹用官方同步器再次重產。
