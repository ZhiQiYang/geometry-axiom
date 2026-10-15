# PF-3：PF-H 相依與歷史基準

本分支沿用 `feat/pf3-panel-fill-20261013`。任務 22 依 P-098，已一般 merge
PF-H #227 的 `4be9ff3453202984433c9256dff9dd60d5c8437a`，並接上最後新增證據的
最新 head `303fec02257d21cf719287045a718665c3283006`，PR base 改為
`feat/pfh-derived-host-20261013`。PF-H 已有雲端交付，正式 WSL 七項仍待本機列車，
沒有將「開 draft」本身當成前置交付。

順序仍為 PF-2 → PF-H → PF-3 → PF-6 → PF-4 → PF-5。
PF-H 提供 D4／R41 真宿主與 D7／保存接入；PF-3 重用其真足跡及 PF-2 的
排板結果，僅做 D43 有效縫與 R43 承接。介面與驗收範圍見 [PF3-NATIVE.md](PF3-NATIVE.md)。

## 原始紅基準（保留原件，不重新解讀為通過）

`tests/evidence/pf3-dependency-20261013/` 是來源 `16a6f48`／PF-2
`077165010377cca974bece7fcda930cd005490a9` 的歷史原件：fresh bridge
建立 D41、材料／參數及 D42 後，effectiveSeams／support／derivedPlacement
三欄皆 null，`PF3_SUPPORT_MISSING` assertion actual exit 1。
首次 wrapper 變數拼錯及重跑分開記錄。原件逐 byte 保留，並非 PF23／PF24 收據。

## E1 原 oracle 與合法宿主

P-103（#227／6152304537）已將原 E1 數字限定為純 R43 演算法輸入，
另建 E1-legal 真宿主場景；P-116（6177092438）將 V 向料角色更正為 primary。
不豁免 I19／I20／I21，不用一般 placement 冒充宿主，文件衝突由 #230 追蹤。

- 原 E1：足跡 [90,120]×[0,300]，三段 10／20、10／5、10／20。
  X5 時仍三段；E2／E3 均為一段 10／20。不是合法 D7 場景。
- E1-legal：兩支 boundary 為 [0,1000]×[0,27]、[0,1000]×[273,300]，
  primary 為 [90,120]×[27,273]。E1 五段；兩端 100／900，中間 10／20、10／5、10／20。
  E2／E3 中間合併，總共三段。兩套數字各自保留，並核對同輸入結果全等。

PF-H 的來源收據與本片新增結果分列；具體執行及未驗項目見本輪 evidence 索引。
無可見入口；維持 draft。雲端 native,非正式 WSL 收據。
