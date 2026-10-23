# GEO-300 前置進度

基底：`a048530c18f5df43a921e6b06bb3e4aa2192684e`。獨立分支：`codex/geo300-prerequisites-20261024`。

- 已 fresh fetch main／train／handoff，保存原 Git 指令、退出碼、完整 stdout/stderr 與權威文件 hash。handoff 沒有 `pr-reviews/300.md`，原 Git exit 128 保留，不聲稱已讀到不存在的審查。
- 已讀決策佇列指定日期、公理、FIELD-RULES 與舊 issue300 草稿。現行 train 權威與先前已讀的整份文件逐位元組相同；舊草稿不是新規格。
- 已把現有 order/source 索引、五個各自為 64 的容量常數、cut-list 平方儲存與剩餘 sort/dedup 成本分開。
- 已備小範圍 active-set／單次 stable compact 設計及正反例，保留超標準 caller buffer 的原算法後備。
- 已備三個產品／測試 leaf 候選及五個新具名 control；所有原方法和原 ASSERT 靜態保留。候選 v1 的 108 個靜態項目有一項基底既存失敗：原 `free-end` anchor 在 Reading A 合流後命中三次；原失敗與候選全部凍結保留，沒有宣稱靜核全過。
- 該 anchor 的單行維護補丁另交主代理，不混入本次候選掩蓋基底；目前仍未執行原套件。`UNIQUE_ID_FOLLOWUP.md` 另列更大區間索引方向與證明邊界，未實作。

產品候選、原套件、新反證、差分量測、架構與帳本目前均未取得本分支動態驗收。主代理正在 R3 執行原完整帳本，本代理沒有啟動編譯、測試、效能量測或另一份帳本。

下一步：只在本分支備候選碼與新具名反證，交另一代理做對抗靜審；主代理給時槽後才跑正式原裁判。未取得全綠前不稱完成 GEO-300。
