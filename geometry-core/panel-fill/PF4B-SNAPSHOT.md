# PF-4B 第一片：明示導出普通 D29 值快照

基底：`48d5f3887e8cb8d222307db62dbdea287fda8442`。依據 `公理層.md` D29、D30、D42、D43、I8a、I37、I52、I55、I57、R44；本文件不新增公理或使用者決策。

這一片交付可直接操作的原生工程交易入口。導出結果是既有 D29 普通無限格網來源，兩軸均為 `repeat-panel`；沒有新的保存記錄、快照物件種類、隱藏更新鏈或快照專用 reader。後續編輯、D30 配置、D10 使用、保存及重開均沿既有普通來源契約。

## 與 PF-4A 活引用的區別

| 項目 | PF-4A `from-fill` | 本片 PF-4B |
| --- | --- | --- |
| 定義 | D10 保存試排 id | 新建 D29，保存當步整數值 |
| 試排來源變動 | 沿完整下游重算 | 已導出 D29 維持原值 |
| 座標框架 | 完成面計算後依 R41 映到衍生板背框架 | R44 完成面來源框架的 P、g、a；之後由 D30 明確配置 |
| 試排／邊界／材料依賴 | 活引用 | 無；名稱提及試排並不構成引用 |
| 導出動作的結果 | 不適用 | 只有新來源，不自建衍生宿主、D30 或 D10 |

當使用者要保留目前排法作為比較方案，或把它配置到另一個邊界並依普通來源契約另行編輯時，可以明示導出快照。要讓既有支架位置繼續跟隨原試排縫位時，則使用 PF-4A 活引用；來源變動或刪除不會自行把這兩種關係互換。

## 原生入口與預覽

沿用現有 `engineering-preview <JSON檔>`、`engineering-confirm <token>`、`engineering-cancel <token>`，交易 schema 仍是 `engineering-transaction/1`：

```json
{
  "schema": "engineering-transaction/1",
  "expectedRevision": 12,
  "operations": [{
    "op": "export-fill-grid-snapshot",
    "value": {
      "fillId": 1,
      "id": 71,
      "mainAlong": "none"
    }
  }]
}
```

`expectedRevision` 必須取當前 reader 的實值，例中的 12 不是預設值。`fillId` 必須是目前候選中的既有正整數試排 id；`id` 是未用的 uint32 D29 id，0 也合法。碰到既有 id 以 `R44 NEW_ID` 拒絕，即使同名或同值也不覆寫。多次導出可同批明列不同新 id；任一步失敗，整批不提交。

`mainAlong` 必填，接受 `none`、`u`、`v`，直接沿 D29 原有 W source role 對映為 0、1、2；不由板材長短、交丁軸或既有角材猜測。可省略 `name`，此時名稱為 `試排 <fillId> 快照`。明填名稱沿 D29 1–96 UTF-8 bytes、不可為空、不可含控制字元的規則；同名不表示同身分。其他欄位一律拒絕。

預覽在既有 `before.geometry.gridSystems`／`after.geometry.gridSystems` 顯示 D29 的完整定義、name、mainAlong、應用及配置。新增項只有 after 出現，兩軸沒有 `parameterRefs` 或 `cardReference`。完整候選依原工程交易重驗、seal、token、確認再驗及 history 提交；取消、違規、重複確認、過期確認均不提交。這一片不擴張 PF-6 App 的操作入口或 UI 能力清單。

## R44 的值與編號

先由現有來源求值器取得當下有效 P、g、δ。length 與 width 依 D42 的明選 `lengthAlong` 對映，不按數值大小交換。板厚及門檻仍須合法；它們不是新 D29 的來源。H 僅對本試排使用的 gap、stagger、threshold 參數引用求當步閉包，使用新求值標記；後面的參數修改不能回頭改變已複製的值，與本次捕捉無關的可修復中間參數也不被提前重驗。完整候選結束時仍全量重驗。

直排的兩軸保存 P、g、a 原值。交丁被錯開軸保存 `anchor = a + δ`、`stagger = −δ`；另一軸維持 a。D43 板列 p 對應 D29 cell `q = p − 1`，所以：

```text
新中心 = a + δ + P + floor(g/2) + k(P+g) + (q 為奇數 ? −δ : 0)
       = c(k) + (p 為奇數 ? δ : 0)
```

這個等式適用負 signed k／p、正負 δ、0 縫寬和奇數縫寬；不把 δ 取 modulo，也不把查詢可見線改存 EXPLICIT。`a + δ` 超出 D1 時拒絕，不偷偷改索引或挑另一個相位。

## 明確的能力邊界

這個基底的 `PanelFill` 及 `wood_pf_parse` 尚不支援 `seamOverrides`／`panel-fill-seam-overrides/1`。因此本片只導出原生已能建立的直排或交丁週期定義，**沒有完成非週期覆寫拒絕、等週期覆寫允許的完整 R44 功能**。

導出還會對完整 canonical D42 定義檢查本片認識的欄位。日後只擴充來源 parser 而未擴充出口時，新增欄位會以 `R44 SOURCE_FORMAT` 拒絕，避免默默忽略。未來覆寫能力必須在同一變更補上：逐一檢查全部明示中心，含可見範圍外的 signed 鍵；有效中心非原週期即拒絕；全部恰等原週期時允許導出；不得丟覆寫、取近似節距或輸出可見 EXPLICIT。現行原生測試只能驗未知覆寫在原 parser 被拒，不能把它算成新出口這兩條未支援分支的殺突變證據。

本片未提供 App 按鈕、HTTP adapter、畫布交互或 L4 操作證據；PF-6 App 的 47 個變更檔不屬本片。來源格式相容性及同一 `.scene` 冷開由原生測試驗證，不等同正式專案瀏覽器驗收。

## 測試與登錄

`tests/test_panel_fill_snapshot.py` 是獨立新 suite，沒有改任何舊 suite、golden、timeout、pin。它只共用 PF-1／PF-2 的 transport 與建置治具；signed 座標、band/cell、D30 平移的預期值均由測試中的輸入常數獨立算出。

| 具名項目 | 驗證內容 |
| --- | --- |
| PF4B-01 | 預覽完整揭露、新來源、主方向、同候選確認、一次 revision |
| PF4B-02 | 非正方形材料兩種軸映射、signed 無限來源、g=0／3 |
| PF4B-03 | 交丁雙軸、正負相位、負 band、g=0／3、結構側 ±1，逐線逐段 oracle |
| PF4B-04／05 | 修改／移除原來源後獨立；同批多個捕捉各取當步有效參數 |
| PF4B-06／07 | 不借未來合法參數；可修復的無關公式前綴有原交易控制組 |
| PF4B-08／09／10 | 新 id、同名不合併、名稱／未知欄檢查、同批碰撞、原 16 容量與整批回滾 |
| PF4B-11 | 取消、過期、同批單次 undo／redo |
| PF4B-12／13 | 只保存普通 D29；全新原生程序冷開；普通來源再編輯與 D30 錨點平移 |
| PF4B-14 | **基底已綠**的原生未知覆寫拒絕；不算新增反例 |
| PF4B-15／16 | 交丁平移 anchor 超 D1 拒絕；大負 δ 與 0 縫寬保留原值 |

suite 片段由原 `tests/native_registry.py --init-suite` 產生，保持 `pending-ci-census`。本機實跑、紅回歸及具名撤回原件由工作包交付索引列出；正式 CI 必須先量測與原工具導入 count/cost，再跑六片及 complete，不能以這份本機紀錄填入正式 CI 收據。architecture 新 H helper 片段由原 `fragment_manifest_files` encoder 產生；沒有手寫 AE 衍生收據或刷新舊 pin。

本機如因 GCC 記憶體回收時機而被系統終止，可僅調整 GCC `ggc-min-expand`／`ggc-min-heapsize`，仍保留原 `-std=c11 -O2`。必須記錄實際編譯器、flags、binary bytes/hash 與原 sidecar；在原 build lock 內複製到任務獨立路徑，沿原 freshness verifier 讀取。缺 binary、編譯失敗或跳過不是通過，本新 suite 會將既有 helper 的 SkipTest 轉成 `PF4B_BUILD_REQUIRED` 失敗。
