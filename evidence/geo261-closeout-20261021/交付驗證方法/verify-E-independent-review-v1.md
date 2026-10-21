# E 驗證器首次獨立只讀審查

已完整讀 `verify_E.py` 280 行、`guard_controls.py` 115 行及 `guard-controls.json` 164 行，並核對三份原件 SHA-256：

- 驗證器：`90bc1d7439e9f412be95e6063a6965b8b4dda3ef164e91b6891a709bba5ec4f2`。
- 純資料控制器：`6cd01265b84e13b7119d8f6b7d3117c2fdad1d9edd288e9632d9fb3c4ee46e68`。
- 控制原輸出：`9818c0c956ebaa9236229afb26d04db873ffaf07018237187dad49b3d003f185`。

本代理只讀檔與固定 L 的 import 來源。沒有執行驗證器、控制器、正式 hash 函式、Git 變更、產品測試或建置；沒有 hash 整包。31 個負控拒絕與前後合法資料通過，來自已保存控制原輸出，不冒稱本代理重跑。讀取／原件 hash 核對的工具結束碼為 0，這不是 E 驗證成功。

## 主線核對

未見以下主線放寬：外部 review bytes 與指定 hash 綁定；L 快照固定 hash；相對路徑、重複欄位、檔案數值與排序檢查；index 精確全集合並排除自身、review 仍包含 index 本身 hash；L→E 總 diff 精確等於新根全部 A 加兩份設定 M；每個中間 commit 亦只能變允許路徑且不准 merge／刪除。設定只能原 bytes 加 root 與兩類 log 精確放行，以及新根 -text -whitespace。工作檔 bytes 經 Git blob oid 與外部 sha 兩層核對，來源聯集及正式 closure／oracle／tool 另核固定 L。

`require` 是普通例外函式，不依賴可被 Python -O 移除的 assert；檔案／Git 模式及父層 symlink 都有檢查。未見驗證器呼叫編譯、測試、帳本寫回或 repository 修改。Git 命令以 GIT_OPTIONAL_LOCKS=0 且關閉 fsmonitor，正式來源 hash 呼叫與 mutable main 分開。

## 需處理或明列限制一：二進位類型判讀不足

`verify_E.py:23–25` 的禁止副檔名比既有初步封裝器少 `.wasm`、`.pyw`、`.pyo`、`.zsh`、`.fish`、`.com`、`.dylib`、`.a`、`.lib`、`.jar`、`.class`、`.bin` 等；`:181–200` 只核一般 blob／無執行權限與 bytes/hash，沒有 binary magic 檢查。誤放入初始 review 的無執行 bit WebAssembly，或改名 `.txt` 的 ELF／PE，仍可能通過型態守門。

外部 review hash 可防事後換包，不能自行證明初始 review 只含證據／文字原件。建議恢復適用的禁止類型，並以純資料函式拒絕明確 ELF／PE／WebAssembly 等二進位格式。文本原碼的 `.txt` 歷史原件可能以 shebang 起頭，不能單憑文字前綴把它冒稱已帶執行權限；應保持文字原件與二進位判讀分明。

這是守門覆蓋缺口，不是已在目前封包發現二進位；本代理未執行反例。

## 需處理或明列限制二：import 可能讀既存 bytecode

`:13` 的 `sys.dont_write_bytecode=True` 只禁止寫 pyc，不禁止載入既存、時間戳有效的 `__pycache__`。`:239–243` import mutate／mutation_bridge 後查 `__file__`，仍可得到已核的 `.py` 路徑，不能由此證明實際執行的 hash 函式來自本次核對的 source bytes。

固定 L 的 `tests/mutate.py:78–79` 還會直接 import binaries 與 run_tests。若交付收據要聲稱正式 hash 函式由已核原碼執行，建議這四個模組採強制 source compile 載入或等價明確避開既存 bytecode 的受控機制；僅再加 `-B` 不解決讀快取問題。source bytes 核對應維持在載入前。

本次沒有讀到或證明現有 pyc 異常，也沒有執行快取反例；這是執行程式與受驗原碼之間的證據界線。

## 精確範圍

`:153–158` 的 exact set 是 E Git tree 的新根檔案集合；它不枚舉新根內所有被忽略的未追蹤檔案。若最終聲稱只針對已提交交付，這個範圍可以明說；不能擴張成全工作目錄沒有額外檔案。工作樹的一般 status 檢查同樣不涵蓋 ignored 檔案。

本輪結論是主線來源／索引綁定清楚，但上述兩點尚需處理或明確縮限保證；此檔不宣告 E 可提交、E 已驗證成功或 PR 可合併。後續修正版應另存新 hash 與對應控制，保留這份首次只讀發現，不回寫成首次已通過。
