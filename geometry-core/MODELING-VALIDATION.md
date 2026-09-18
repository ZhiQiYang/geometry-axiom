# GEO-130 實作與驗證紀錄

規範基線：`65156839990f274a6144127bfe55991d6ac5fb84` 的 89 條公理與 `orthogonal-model/1` 契約。未改公理條文或正典閱讀器。

## 已交付與實測

| 項目 | 結果 |
|---|---|
| 新建模驗收 | 36 項通過，包含原 18 組案例 |
| CLI／HTTP 整合 | 2 項通過：真實子程序、OBJ 整數資料、跨生成器匯入、錯誤恢復、舊 World 不變 |
| 既有 HTTP 回歸 | 8 項通過 |
| 正典閱讀器 | 五道 assert 與獨立 SSOT 對照通過；89 條、452 blocks、5 則批註 |
| 建置 | 原 C CLI、原 bridge、新 C adapter 均成功 |
| ASan／UBSan | 新建模 36 項經 sanitizer 編譯的 C adapter 通過，無記憶體存取／未定義行為報告 |
| 來源／檔案檢查 | `git diff --check`；原始公理與閱讀器未改 |

重現：

```sh
npm run build
GEOMETRY_MODEL_BASE=.build/model_base python3 tests/test_modeling_runtime.py
GEOMETRY_MODEL_BASE=.build/model_base python3 tests/test_modeling_transport.py
python3 tests/test_serve.py
python3 geometry-guide/sync_axiom_reader.py --check
```

sanitizer 環境的 LeakSanitizer 受 ptrace 限制而無法執行，第一次因此失敗；後續使用 `ASAN_OPTIONS=detect_leaks=0` 執行 AddressSanitizer／UndefinedBehaviorSanitizer。**不宣稱記憶體洩漏檢查已通過。** 建置仍有既有 C `scene_error` 訊息緩衝區的截斷警告，未因本次修改而變更該核心。

## 驗收內容

測試讀取原向量的輸入和預期值，實際經 C parser → 擴充守門 → 幾何 → 拓撲 → 交換包 → 來源重建。
獨立的網格檢查器不引用引擎的幾何／切分／拓撲 helper，直接以輸出頂點與三角形計算：

- 整數有向體積、外接範圍、閉合邊、頂點鄰接及殼分區。
- 帶孔牆的孔拓撲與穿孔位置；L 形空間的凹口不能被填成盒子。
- KEEP 重疊面保留，UNION 內表面消除，差集內腔、多塊、全空與空結果重用。
- 僅共邊的材料分量不共用拓撲頂點；三面共邊、點捏合與朝內空間殼拒絕。
- 明示障礙只扣空間內交集，未列障礙不扣；開放空間 partial 以根為原子。
- 缺規格、未知欄位／型別、布林混充整數、前向引用及容量限制。
- 來源／幾何摘要、重新計算後的快照竄改拒絕、外部生成器與診斷、省略根診斷要求。
- 規格／frame 變更重算、引用刪除回滾、取消及同候選重開後的過期 token。

C adapter 另以 48 組有號 frame／法向組合、144 個角材核對實際六面朝外，並檢查正典重讀、舊依賴放置順序、guide 引用及 Space 成員。
獨立審查另檢查真實容量超限、Unicode、非流形反例與原始碼守門；修正了完整舊依賴閉包及指數來源／KEEP 展開的容量漏洞。

## 已產生的模型

| 輸出 | 幾何 |
|---|---|
| `examples/wall-with-opening.model.json`／`.obj` | 4000 × 2800 mm 牆截面、120 mm 厚、1200 × 1200 mm 貫穿孔；材料體積 1,171,200,000 mm³ |
| `examples/l-room.model.json`／`.obj` | 六段立面加頂底的 L 形封閉空間，體積 68,040,000,000 mm³；角色為 enclosure，不冒充 RC 材料 |

## 尚未驗證／接入

這是 Python 精確參考執行器加 C 舊場景驗證；新型別未放進舊 C World 或已發布畫布 UI。
本次沒有手機實機、瀏覽器建模操作、Windows 原生或 GLB／SketchUp 適配器驗證。
來源重新計算由本參考執行器完成；獨立網格驗證不等於已完成第二套完整引擎的 M8 跨實作符合性驗收。
