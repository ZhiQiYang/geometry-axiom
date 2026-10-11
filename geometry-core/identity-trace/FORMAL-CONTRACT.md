# K3 識別與追溯正式契約

2026-10-11 採納；依 `公理層.md` D59–D62、I70–I72、R56–R58、r5 提案與後續 P-053／P-057 裁決。**K3 核心、宿主及保存功能尚未實作**；本文件固定實作介面與驗收邊界，不代表 capability 或測試已通過。歷史提案原檔不改；發生差異時以正式公理及本文件記錄的後續裁決為準。

## 內容指紋

欄位正式名稱為 `definitionFingerprint`、`valueFingerprint`，均為 SHA-256 的 64 字元小寫十六進位字串。它們分別描述定義內容與有效值內容，與 `incarnation` 存在期記號分開；相同指紋不構成身分延續證據。

沿用 [來源檢查器契約](../../geometry-web/docs/SOURCE-INSPECTOR-CONTRACT.md) 的原生逐節點演算法，不另造 JS 指紋。序列化 owner 是 `geometry-web/source-inspector-bridge.inc` 的 `si_build` 與 helper：依現有型別順序產生 UTF-8 位元組，對 `s->text` 的前 `s->used` bytes 計算 SHA-256，不含結尾 NUL、不加換行，不用 `JSON.stringify()` 重新序列化。`si_node` 計算定義指紋，預設把值指紋設為相同字串；有獨立有效值序列的型別再由 `si_value` 計算。輸入容量不足或求值資料不完整時保留索引的 `complete:false`，不能宣稱完整比對。

採納時的序列化基準為 [4c6e8566 的來源檢查器](https://github.com/ZhiQiYang/geometry-axiom/blob/4c6e8566f47a90f661e355129c26fb45e19479a2/geometry-web/source-inspector-bridge.inc)，該檔 LF 正規化 SHA-256 為 `4f7d035689920ee26c471b8e21d796958ec6878a0cfc6c21ec14fff6ae97ba46`。這個固定版本列明數字格式、分隔字元、迴圈順序及局部 canonical JSON helper；下表是涵蓋範圍摘要，不能取代該序列化定義。

| 身分鍵類型 | 定義內容輸入 | 有效值內容輸入 |
|---|---|---|
| boundary | 邊界 kind、外輪廓與孔的頂點／fixity、穩定頂點 key | 沿用定義序列 |
| placement | 邊界引用、frame；無邊界引用時另含內嵌輪廓 | 沿用定義序列 |
| column、beam | 空間引用與凍結範圍；beam 另含 axis | 沿用定義序列 |
| parameter | `card<id>`；欄位另有節點與 member 關係 | 沿用定義序列；卡片單一指紋不宣稱涵蓋全部欄位值 |
| parameter-field | 型別及核心保存的算式字串 | 精確 `num/den:unit` |
| timber（不屬組構所有者） | 原生 role、priority、尺寸來源、anchor、引用、binding／override 等型別定義序列 | placed、有效截面與長度、origin、方向軸序列 |

身分帳、記號及配號器不得加入以上序列。`geometry-hash`、`eng_definition_hash`、D25 `sourceFingerprint` 等各有既有領域，不拿其中一個代替兩個逐節點指紋；需要場景 bytes 的內容領域一律依 I72 改讀 `dump-deidentified`。本契約不擴張 D59 七種鍵，材料／做法／規則的固定版本指紋不因此取得記號。

## 專案身分與確認

外部紀錄的 `projectScope` 對應其所屬完整專案的 `projectId`。先比專案身分，與目前 `projectId` 不符即為 R57 `unknown`，不得繼續用記號碰撞判 conflict 或 continuous。完整複製／分支只有保留相同 `projectId` 才共享複製時的存在期；另建專案身分或跨專案交換不構成延續。

`incarnation` 保存 D59 `E:s`；內容指紋仍獨立比較。預覽確認必須重讀目前記號及五態：任一改變即過期，即使前後都為 replaced。未啟用 World 的一般提交及匯入不結算、不配記號；只有原已啟用或本次啟用交易才進入 R56。D54(a) 共用項不在 D59 集合中，不能從 I66(f) 推出它們也有記號。

依 [P-057](https://github.com/ZhiQiYang/geometry-axiom/pull/200#issuecomment-6110795430)，R58 首版只接受 D31 dimension 型字面值欄位及 mm／cm 觀察值，mm 原值、cm 精確乘十；算式、其他型別／目標／單位拒絕。預覽、continuous、精確求值及同候選確認守門仍全部成立。這是正式條文範圍；將來擴充先改條文及驗收。

## 橋接指令對照

下表是 K3-L 的實作契約；列為新增的指令尚不可宣稱可呼叫。每個提交在指令分派層只結算一次；批次確認中的 op 不各自結算，歷史群組的每一行則各自結算。成功提交才推進正式計數器；容量不足或結算失敗不消耗該候選序號，群組先前成功步驟已用的號不退。完整規則與三個獨立驗收例見 [P-053 補充](P053-COUNTER-SETTLEMENT.md)。

| 指令／入口 | 身分帳行為 |
|---|---|
| `identity-epoch <32hex>`（新增） | 宿主專用、session 層獨立指令；E 為 32 個小寫十六進位字元。不得經 `line`、場景文字或頁面 API 設定；不改 World、history、canvas 或定義 revision。宿主於 bridge 啟動及成功整體取代後，在同一把 `bridge_lock` 內設定新 E |
| `identity-ledger activate`（新增互動交易） | 依 I71 一次啟用；不得在歷史群組或候選內。已有預覽不阻擋啟用，成功使既有預覽過期。不能在某個預覽的確認途中自動插入啟用 |
| `line`、`drag` | 成功改變正式 World 時依 R56；undo、redo、純 canvas-pos、預覽／取消及 history-begin／end／abort 不取新號 |
| `line reset` | 一筆可 undo 的提交；保留原啟用狀態及 E，清空物件並結束其存在期，不當成整體取代 |
| `engineering-confirm`、`assembly-confirm`、`section-profile-confirm` | 各一筆提交；包含組構生成路徑。若直接採用預覽 World，必須同時採用該預覽的明示刪除集合；`changed` 以結算後 World 判定 |
| `definition-import-confirm <token>`（K2b 契約新增） | 加入既有 World 的提交；來源記號不帶入。目標已啟用才對新受涵蓋鍵配號；未啟用不配號 |
| `reset`、`default`、`loadfile`、成功的 upload／load-confirm 整體載入 | 整體取代，直接還原輸入帳；開新／內建場景為未啟用。成功後宿主換 E。不是 `line reset` |
| `dump`、完整專案保存 | 寫完整帳前驗 I70，不完整即拒絕，不補號自救 |
| `dump-deidentified`（新增，正式名稱） | 唯讀；不含 `requires identity-ledger/1` 或任何 `identity` 行，其餘逐位元等於未啟用時的 dump。帳不完整也可輸出，但另附無法還原記號的診斷 |
| `source-inspect` | 同一份被讀取的 World／revision，追加 `identityLedger:{schema:'identity-ledger/1',active:bool}` 與逐節點 `incarnation`；未啟用或不受涵蓋者為 null。不得從另一份隔離快照借 live 身分 |
| `host-gate-check <desktop\|none> <line>`（新增測試接縫） | 唯讀查詢純宿主守門，不執行 line、不設行程旗標、不改 World／history／revision；依 r5 L-23 驗桌面限制 |
| 各類 prepare／preview／cancel、render、pick、read／query | 不結算、不配號、不消耗計數器 |

`identity <kind> <id> [<fieldId>] <E:s>` 只屬場景載入語法；互動 `line identity …` 拒絕。反向亦然：場景檔中的 `identity-ledger activate` 拒絕。桌面清除走互動 `reset`；桌面載入走 `gdi_load_scene_file` 整體取代。桌面沒有 epoch 宿主，依 r5 的 K3-LIM-1 實作已啟用 World 守門，不以此文件宣稱 GDI 已驗。

## 去身分與完整輸出的使用領域

`dump-deidentified` 用於建模／斷面／F1b 的來源快照與兩端比對、空間來源 pin、內容雜湊、規則案例隔離執行、場景匯出（含桌面）、回報、連線握手與恢復探針。服務過期的唯讀白名單、頁面連線階段白名單須同時包含它。逐點接線清單見 [r5 §2.5](PROPOSAL.md#25-原生介面)。

完整 `.gcanvas`、方案 `world.scene`／`final_scene`、其 manifest sceneHash、pendingLoad 與恢復打包紀錄仍用完整場景；方案隔離核對依 I72 讀完整輸入，不能輸出為模型來源。恢復先核對完整 `record.sceneHash`，再依 r5 本地剝除身分行作探針比對，不能另存一份 probeHash。K3-L 實作須以實際命令紀錄核對 r5 清單；本次沒有改呼叫點或新增執行器 capability。

## 原生明示刪除集合

依 D60，交易內任何操作曾使受涵蓋鍵不存在，就記入原生集合；最後同鍵仍在也不能抹去這個事實。候選直接確認時必須隨候選保存集合；取消、過期或取代候選即作廢。K2a 與 K3 共用同一份集合，K2a 額外需要 grid-system／grid-binding 的刪除事件，不代表這兩種鍵取得 K3 記號。

| op | 必須記錄的鍵／位置 |
|---|---|
| 互動 `delete boundary\|placement\|timber\|column\|beam <id>` | 被刪除的受涵蓋鍵；適用 line、桌面、群組及互動預覽確認 |
| 互動 `reset` | 全部受涵蓋鍵；適用 line reset、桌面清除 |
| `delete-parameter` | 卡片及其全部欄位；記錄點位於 `parameter_remove`，涵蓋工程、組構、組構生成、斷面四種批次 |
| `put-parameter` 重宣告省略欄位 | 被省略的 parameter-field；同上四種批次。即使現行 I38 已另擋住同提交重用，仍必須記錄 |
| `delete-placement` | 斷面批次刪除的 placement |
| PF-0 衍生承載面刪除 | placement 鍵；本分支只有 PF-0 條文，具體 op 名待其實作切片登記。不得略過此路徑或自行虛構現存 op |

組構實例生成／更新／刪除移除的 owned timber 不受 D59 涵蓋。本清單不放寬 I7a、I23、I37、I38、I49 的刪除保護，也不把已登記的 GEO-258 缺陷當成允許行為。新增任何會移除受涵蓋物件的 op 時，必須同時更新清單及刪除集合驗收。

## 實作驗收界線

文書檢查只證明正式條文、白話、契約、正典及版本資料一致。K3-L 須另交付 r5 L 系列、P-053 三例及本輪澄清的 native／橋接反例；K3-48、K3-44 接續各自情境。尤其須驗未啟用舊行為、共用型別不配號、跨專案先判 unknown、replaced 記號再換使候選過期，以及 R58 算式／非 mm-cm 輸入拒絕，不能用測試內自寫配號器或字串檢查冒充產品驗收。
