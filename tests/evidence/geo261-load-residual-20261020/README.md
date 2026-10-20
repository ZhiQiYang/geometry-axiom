# GEO-261 載入成本驗收證據

基底 `546e2eb2142ebf19859489c5391b57cbb8413d10`；修正產品碼／測試 `2af6323bf62ec38281e0ebad672f218d81f2317f`；main `adbaebf9c73ea6801d7b4d5214e4b846b132923b`。環境及逐檔 SHA-256 見 `environment.json`。

- `verify.py.txt`：暫時檢測建置、A／B／C 比對及交錯效能取樣；複製到 `/tmp` 執行。K seal hook 與五個函式入口計數器只存在暫時來源複本。
- `mini_gen.py.txt`、`scenes/`：使用者產生器與四份逐位元組核對的輸入。
- `stdout/base/`、`stdout/fix/`：175 份輸入各自的原始 stdout 與 stderr，包含拒絕場景。
- `graphs/base/`、`graphs/fix/`：每次 seal 的完整有序快照，gzip 無損壓縮。格式由 `verify.py.txt` 的 `TRACE` 明確定義：8-byte little-endian 整數、長度前置的 key／definition／feature bytes；所有 descriptor、state、status、described、value 存在性與完整幾何內容，最後逐筆寫 consumer／source／kind。借用 view 寫內容，不寫指標、padding 或未使用 union。seal 不修改節點／邊，因此在入口傾印。
- `equivalence.json`：全部指令、結束碼、逐份輸出／圖雜湊、位元組數及五個守門計數；所有 base／fix 成對相同。兩邊共保存 47,295,490 bytes 的未壓縮圖內容。
- `performance.json`、`performance-stdout/`：36 次交錯 `loadfile` 樣本、逐次原始輸出及中位數。
- `gprof-*.stdout`、`profile-counts.json`：完整 gprof 輸出與呼叫數；使用 `-O1 -fno-inline -pg`。
- `checks/`：每項驗收的指令、cwd、stack、結束碼和原始輸出；`native.stdout` 含兩種突變的具名斷言。

重跑指令請見獨立 prbody 分支的 `PR_BODY.md`；不依賴 GitHub Actions。
