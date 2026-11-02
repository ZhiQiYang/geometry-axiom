# K1-b 前端收據（2026-10-11）

此目錄只核收前端純求值、ZIP／設定、session 與實際 ReferenceWorkspace metadata owner 的測試。完整 app／native／瀏覽器收據仍待 WSL；不能用本收據宣稱整張 K1 或 #47 完成。

- `frontend-baseline.log`：46 pass、0 fail、0 skip。
- `run-all-cutting.log`：正式登記的四個 suite（20／12／11／3）共 46 pass；是 `--only cutting` 部分執行。
- `mutations.json`：45 個實際源碼突變均被偵測，38 個斷言、7 個明確 CONSERVATION／DEMAND_IDENTITY 診斷；語法／import／環境錯誤不當作 killed。
- `mutation-diagnoses.json`：各突變的第一個失敗測試及具體病因。每筆帶原始程式來源／變異雜湊；整份收據帶四支測試的正規化雜湊。

突變器 `tests/mutate_k1_frontend.py` 使用一次性副本，從不修改工作區。這份前端收據不是既有 C 突變 `tests/mutants_results.json`；後者仍須另外重產並確認 `tests/mutate.py --check` 的 stale=0。

先有測試再改行為的新增反證包括：T8b 因缺診斷 formatter 斷言轉紅；R47 的混合缺原材／超長／缺設定診斷因階段順序錯誤轉紅，再依第 2→3→4 步修正。移除這些實作時，`stock-diagnostic`／`phase-order` 仍出現相同病因。

使用者期望值例外只限：P-047 授權 K1-a 在既有 assembly 期望物件加入 terminal；本輪明示只將既有格式總數 length 與唯一集合 size 從 16 改為 17。其他既有期望值未改。

UI 的新增 P89=19 已登記，但尚未執行；既有 P80／P81／P83 計數保持。Windows 新 core／bridge／model-base／gdi 仍受 SAC 4551 阻擋，不計通過；WSL 完整原生、ASan/UBSan、突變、CDP 與空間工作區仍在共用序列等待。
