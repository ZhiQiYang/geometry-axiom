# K1 對抗審查要點（照錄）與 r1 處理對照

- 審查人：opus 對抗審查
- 判定：「須先改」（無阻擋）
- 下方「照錄」段一字不改，為主迴圈轉來的審查發現與裁決。

## 照錄

K1 提案經 opus 對抗審查判「須先改」(無阻擋),請依下列主迴圈裁決修成 r1(依授權 L,全部標暫定)。

【審查發現 → 裁決】
1. 工程專案整體不能用(唯一工程範例 geometry-web/examples/engineering-spec-v1.gcanvas 的 7 支角材 A/B 全是 {kind:application,...},7/7 會 UNSUPPORTED;UI 面套用流程也產生 application 來源)。→ 採 P14-B 併入首版:原生 `json_engineering_sources` 每筆加唯讀的具型別末端欄位(`eng_effective` 已走完 D28 鏈),前端只讀此欄位,不在前端重做 D28 查找(R31:那是核心的事)。首版因此會動 native,PROPOSAL 的受影響檔案、驗收表、PR 切分要更新;補一個以 engineering-spec-v1 為夾具的驗收例。
2. 被引用的原材種類可改截面/材料鍵 → 溯及改變實物餘料(27×33 被當 30×40 配料,硬失效)。→ 原材種類被餘料或設定引用時,截面與材料鍵不得修改(拒絕並給碼);要改須新建種類。
3. 材料鍵只有 (id,version),沒帶 D26 內容指紋。→ 材料鍵加入內容 fingerprint,比對須三者皆等。
4. 容量規則矛盾(餘料上限 256 vs boundedJSON 陣列上限 128 於 feature-attachments.js:96;原材種類 ≤32 是保存驗證,故 T18「33 種→求方案 CAPACITY」不可能;需求件上限 4096 只出現在 T18)。→ 每個上限只定義一處並寫明拒絕層;餘料上限改 128 對齊既有 boundedJSON;刪改 T18 中不可能的案例。
5. records 上限現況寫錯(程式是 records.length > 3,於 feature-attachments.js:215,3 種 kind)。→ 改為 3→4;並註明多份提案同時增加 kind 時於寫入時統一配。
6. CSV 列序依畫面排序、none 列值與負可用長度未定義(參考實作 T4 輸出 −5;剩料 < t 時可用長度為負)。→ 定一個與畫面排序無關的 CSV 列序(建議:原材種類 key → 原材支序 → 下刀序);剩料為 none 時該欄留空;可用長度定義為 max(0, 剩長 − t),且「可留用」需 ≥ 留用下限。
7. derive 的拋錯無對應狀態(timber-schedule.js:18/35/44 同一種 Error 丟三種錯)。→ 先用 references.timbers 自行驗範圍得 SCOPE_STALE;其餘失敗明定為 INCOMPLETE 並帶細碼;不得靠比對錯誤字串。
8. OVER_LENGTH 判準與求值順序不唯一。→ 判準定為 C > max(S−2e, max U)(U=宣告餘料可用長度);餘料被用完導致放不下另給 INCOMPLETE 細碼;求值順序明定:範圍/輸入有效性 → OVER_LENGTH(不需 k)→ MISSING_SETTING → 排料。
僅記錄(一併修):T3b 變異欄改為「期望值紅」而非「守恆紅」;MATERIAL_MIXED 改歸 INCOMPLETE、OVER_LENGTH 維持 INVALID 但在理由中說明與 D24 的關係;T7 若無法表達跨世界請求就刪或改為 API 層拒絕測試;設了材料鍵時截面與 D26 A/B 不一致要給診斷碼而非靜默 NO_STOCK;Δ7 不要依賴「上一條」相對指涉,改用明確條號/標題錨點;Δ2 補一句「專案層定義」不是 I34 引用、不屬 I36。

## r1 處理對照

| 項 | 處理位置 | 備註 |
|---|---|---|
| 1 | **PROPOSAL** §3（K1-a／K1-b 切分）、§6.1、§9、§8（E1、E2、N1–N5）<br>**AXIOM** D⟨K1-4⟩（材料鍵由核心末端決定）、I⟨K1-2⟩(d)<br>**decisions** P14、P36 | 末端欄位也加在 `assembly.bindings[].effective[]`。理由：owned 角材的材料指紋只能從那裡取得 |
| 2 | **AXIOM** D⟨K1-2⟩ 末句、I⟨K1-1⟩（`STOCK_TYPE_IN_USE`）<br>**PROPOSAL** §4.1、T12b<br>**decisions** P29 | 「被設定引用」：設定中只有宣告餘料會引用原材種類，因此鎖定條件寫為「被任何宣告餘料引用」 |
| 3 | **AXIOM** D⟨K1-2⟩、D⟨K1-4⟩、I⟨K1-2⟩(e)<br>**PROPOSAL** §4.1、T26<br>**decisions** P12 | — |
| 4 | **PROPOSAL** §4.4（唯一的容量表）、T18<br>**AXIOM** D⟨K1-1⟩ 末句、I⟨K1-1⟩、I⟨K1-2⟩(f)<br>**decisions** P30 | 另核對節點上限 4096：32 種原材加 128 段餘料約 1,200 個節點，在上限內 |
| 5 | **PROPOSAL** §6.2、§11-3<br>**AXIOM** 自檢第 8 點 | **基底差異**：main `5cc1ffa` 的 `:215` 是 `> 3`（3 種 kind），即將合入的 a7bff8f 在 `:225` 已是 `> 4`（含 rule-case，共 4 種）。照裁決寫成「3→4」，並註明合入 a7bff8f 後應為「4→5」，寫入時以實際基底加 1 |
| 6 | **AXIOM** D⟨K1-5⟩（`max(0, 剩料 − t)`）、R⟨K1-4⟩（固定列序、留空）<br>**PROPOSAL** §4.3、§4.5、T4、T15b、T25<br>**decisions** P31、P32 | — |
| 7 | **AXIOM** I⟨K1-2⟩(b)(c)<br>**PROPOSAL** §5 第 1、2 步、§6.2（`timber-schedule.js` 各拋錯點加 `code`：:11/18/26/28/30/35/39/44）、T21<br>**decisions** P34 | 補一點：讀取結果沒有承載面清單，被刪的面只會表現為零件，所以新增 `SCOPE_EMPTY`（P35） |
| 8 | **AXIOM** I⟨K1-4⟩（M 判準、REMNANT_EXHAUSTED、a 未設定時以 L 判）、R⟨K1-1⟩（0–5 步）、R⟨K1-2⟩(4)<br>**PROPOSAL** §5、T23、T23b、T28<br>**decisions** P33 | OVER_LENGTH 需要 C = L + a，所以 a 未設定時以 L 判。因 a ≥ 0，這樣判定只會漏判、不會誤判 |
| 僅記錄：T3b | **PROPOSAL** T3b | 改為「期望值紅」 |
| 僅記錄：MIXED／OVER_LENGTH | **AXIOM** I⟨K1-2⟩(d)、I⟨K1-5⟩ 理由句<br>**decisions** P15、P20 | — |
| 僅記錄：T7 | **PROPOSAL** T7 | 改為 API 層拒絕；另加 `WORLD_KIND` |
| 僅記錄：截面與 D26 不一致 | **AXIOM** I⟨K1-2⟩(e)（`STOCK_SECTION_MISMATCH`、`MATERIAL_FINGERPRINT_MISMATCH`）<br>**PROPOSAL** T26、T27 | 只有當計量世界中有該材料的件時才會診斷；設定驗證讀不到 World（自檢第 6 點） |
| 僅記錄：Δ7 | **AXIOM** Δ7 | 改以「D35–D40、I43–I51、R36–R40」加上「§四 以『斷面拉伸第一版明確不做』開頭的條目」作錨點 |
| 僅記錄：Δ2 | **AXIOM** Δ2 | 補上「不是 I34 的引用，不在 I36 範圍」 |
