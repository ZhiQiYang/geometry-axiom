# GEO-261：研究來源與提案承接

> **狀態：P0 提案，尚未批准／採納，尚未實作。** 本檔只記研究來源與本次內部審查。

此表是 P0 的研究處置索引，不是實作或驗收完成表。R18 的版本各依原留言；本提案重新對照 main `1c80751150d0767ba52509537caf8d5542769ccb`。已讀全部第 1–16 段、第二段附錄與接手留言；後續主線或研究新增內容仍須增量核對。

| 研究來源 | 本提案如何承接 |
|---|---|
| [第 1 段：20 類概念／常數](https://github.com/ZhiQiYang/geometry-axiom/issues/248#issuecomment-6179221443) | PROPOSAL §2–3：K/W/H 責任及幾何↔木工對照；固定政策、尺寸種子、幾何常數分開 |
| [第 2 段：條文／白話／範圍](https://github.com/ZhiQiYang/geometry-axiom/issues/248#issuecomment-6180054709)、[204 條附錄](https://github.com/ZhiQiYang/geometry-axiom/issues/248#issuecomment-6180106385) | clause-map.json 全條號及非條文範圍；AXIOM-PROPOSAL 逐字差異。研究標籤不直接當採納結果 |
| [第 3 段：18 個跨層接點／文案](https://github.com/ZhiQiYang/geometry-axiom/issues/248#issuecomment-6180560741) | §4 的共用實作與 typed source；§5 保留 wire 診斷；§6 移除顯示字串反解身分 |
| [第 4 段：保存／來源／能力](https://github.com/ZhiQiYang/geometry-axiom/issues/248#issuecomment-6180994017) | §5 的 dump/hash/包/版本契約及所有舊入口能力矩陣；來源不可攤平 |
| [第 5 段：Python modeling／CLI](https://github.com/ZhiQiYang/geometry-axiom/issues/248#issuecomment-6181563209) | §4.3：真幾何移 K，編譯與 legacy reader 移 H，領域來源移 W；舊 facade 明列 H |
| [第 6 段：三個工作區](https://github.com/ZhiQiYang/geometry-axiom/issues/248#issuecomment-6182042374) | §6：按入口提供原預填、規格與有限配方；空白不補值；DOM 與草稿責任不改 |
| [第 7 段：文件／模型／方案](https://github.com/ZhiQiYang/geometry-axiom/issues/248#issuecomment-6182351456) | §5：完整 Project、歷史 owner、保存模型葉節點；過濾／展示不刪定義 |
| [第 8 段：網格／空間／試擺](https://github.com/ZhiQiYang/geometry-axiom/issues/248#issuecomment-6182798025) | §3、§5.2、§6：signed/exact 幾何、分型別檢查域、未定位及紅色試排保持；不擴大碰撞 |
| [第 9 段：正式入口／共用工作區](https://github.com/ZhiQiYang/geometry-axiom/issues/248#issuecomment-6184167807) | §5.1、§6：唯一應用裝配、project/history/context 與明示資產 allowlist |
| [第 10 段：工程轉接／規則案例／模型更新](https://github.com/ZhiQiYang/geometry-axiom/issues/248#issuecomment-6184545724) | §4.3、§5–6：舊 kind/source/capability 由外層還原；模型結果、來源快照及 producer 範圍不擴張 |
| [第 11 段：rule_cases Python](https://github.com/ZhiQiYang/geometry-axiom/issues/248#issuecomment-6184900654) | §5.1、§6：同一模板 evaluator；catalog/adapter 參與 validatorVersion；歷史收據不冒充目前驗證 |
| [第 12 段：原生診斷／來源圖](https://github.com/ZhiQiYang/geometry-axiom/issues/248#issuecomment-6185296226) | §4.1–4.2：完整隱含來源閉包、同候選 typed provider；保留失敗診斷與 canonical dump 字節 |
| [第 13 段：試排／碰撞／配號](https://github.com/ZhiQiYang/geometry-axiom/issues/248#issuecomment-6197016333) | §4.2 三種復原狀態、§5.2 型別與檢查域矩陣；未實作 K1/K3 不藉此新增 |
| [第 14 段：參數保存／交換閉包](https://github.com/ZhiQiYang/geometry-axiom/issues/248#issuecomment-6197860344) | §4.1 精確參數與具身分欄位、§5 原子載入及舊 syntax；#253 合流後核對，不搶先改語義 |
| [第 15 段：參數引用至正式放置](https://github.com/ZhiQiYang/geometry-axiom/issues/248#issuecomment-6198587788) | §4.1 分開程式依賴與資料圖；§5–6 保留錨定、來源與角色預設；typed 值先於呈現字串 |
| [第 16 段：相位差漏存／恢復與附件](https://github.com/ZhiQiYang/geometry-axiom/issues/248#issuecomment-6199191496) | §6.1 明列既有更名缺陷及獨立待批准修正；原生省略＝清除保持，恢復／附件／歷史／lost 契約留 H，不用研究探針冒充產品驗收 |
| [2026-10-16 接手記錄](https://github.com/ZhiQiYang/geometry-axiom/issues/248#issuecomment-6199027870) | §9–11：Astra 提案／實作，Claude 最後審查；逐條公理批准仍須本對話明示 |

## 尚待實作驗證的重點

- `World`／`references.inc` 不只是直接引用：較早放置構件可能成擋面，必須保留隱含來源與重建順序。
- 原生幾何抽取涵蓋 frame、凹環／孔、區間、exact lattice、投影、斷面矩形差集、PF 輪廓裁切；不能把整個舊演算法留 W，只給 K 少數 helper。
- `eng_definition_hash` 依 canonical dump；模型包的舊 revision+SHA 為精確配對，不能放寬成兩個獨立允許集合。
- C/Python/JS/HTML 的來源清冊、實際 include/import/load 閉包，以及共用算法負控制，仍是實作片必交證據。
- 本文件引用的研究探針與原測試數不能當成本次執行收據。P0 基線與候選命令另有明確紀錄。

## 內部架構對抗審查

2026-10-16 對 `PROPOSAL.md` 的三輪獨立對抗審查，依次指出並補上：K/W 聯合候選、資料圖跨層引用、全部舊入口、三種復原域、型別碰撞域、全來源清冊的 JS/HTML、巢狀 include 突變遷移。

第三輪檢查的 PROPOSAL SHA-256：`b71330022a1f518b35ab7927c315f55037198c59afc23a698ba205cefee377a4`；結論為「架構提案層面的已知阻擋已解除」，逐條條文仍待另審。本記錄是本次子代理審查，不是 Claude 最終品質審查，也不表示任何產品能力已實作或驗收通過。

其後逐條審查已讀完全部 95 條 M 的新增核心段、全部 K 條（其中 8 條直接改寫）、分層前言、§四與 §6.1，提出並關閉兩項阻擋：D19 的單軸等分數不得誤限為至少 2（現明列 1…65、至少一軸大於 1）；R44 的不可另存副本禁令必須限於活引用衍生物，不能禁止既有普通 D29 值快照及其編輯。另將 6 條校準／草稿／附件宿主流程保留原文、歸 H，避免把它們塞進 K。

最後回讀結論：「提案語義審查通過；此結論不代表產品實作或執行期驗收完成。」其後只移除審閱 Markdown 檔尾一個空白行以通過 `git diff --check`，逐條 payload 不變且 29 項契約測試再通過。凍結版本的 LF 正規化 SHA-256：

- `AXIOM-PROPOSAL.md`：`905e49111b5bb8c4fadecb46c89c0d9ff59deb7d3064b602ae23bfc72ca6b609`
- `clause-map.json`：`51841370641ea38d45d4d46a1767f8c4fd4b4fb4c47c0deb4ce82d0476fa5ca4`

最終清冊為 204 條、103 條逐字差異、101 條原文保留；K 29／M 95／W 30／H 50。真正公理、白話與正典尚未採納本提案。
