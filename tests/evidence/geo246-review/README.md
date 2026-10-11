本目錄是 PR #196 回應【dot】的修正收據，與首輪 `geo246-weak-pins/` 歷史資料分開。

產品修正在 `fe7da3dac977265305b1948a104a78c55fb67220`：panel 長度不足、gap 關鍵字、from 關鍵字及數值欄位分開診斷，原條件及解析順序不變，新增 7 筆回歸輸入。原 32 筆表見 `32-pins.md`；補充 7 筆見 `7-panel-pins.md`。三個契約 suite 維持 13／25／31 項，共 69/69。

成功的訊息退化驗證在乾淨 checkout `/tmp/geo246-review-audit` 的 `9456bebe1c7009672073b4d3b8d5f197aea50d35`／tree `8b866b9ac9a024eefebcb6f2851dd346af42158f` 執行。`audit/` 保存原 32 筆及新增 7 筆的 baseline／generic／restored 原始紀錄；病因失敗分別為 0/32/0 與 0/7/0，輸入與 expected 完全一致。泛稱造成的失敗仍是真正 unittest failure，訊息列出指令及缺少的具體病因。四份 archive 來源在執行 generic binary 前逐位元組還原，原 checkout 前後身分相同。編譯 argv/cwd、archive paths/head/tree/SHA、patch SHA、binary SHA 與 fingerprint 都可核查。

`commands/message-v2` 是本工單中止的大型媒體封存作業；`message-v3` 是缺少 bridge include 的編譯失敗；`message-v4` 是 checkout setup 失敗。這三次不是通過收據。成功重跑是 `commands/message-v5`，實際執行入口已版本化於 `tests/geo246/`。`interrupted-audit/` 保留失敗嘗試的 compile receipt，不混入成功 audit。

原生變異使用原 `tests/mutate.py`，分批只為避免結果檔互撞。`mutants/` 是 50 筆原始紀錄與各批 raw log：47 筆實際執行、3 筆原 retired 定義。結果 killed 42、crashed 1（M20 同一夾具 SIGSEGV 三次，基準線已過）、equivalent 4、retired 3；stale／blocked／survived／invalid／unrun 皆 0。已回存 `tests/mutants_results.json`，WSL 與 Windows 的原 `--check` 都為 stale=0。

`parent-reader/` 重新擷取親代 `7b603b4dc34bbbf41731f0e7845d0519dd876c71`／tree `5e89cef213923b3c7bb5c6a97a1473457b6e2a3b` 的乾淨 checkout，執行前後身分相同。reader-only suite 41 項中 5 fail，failure names 與首輪 head 相同；此 suite 不消耗 native binary，`required_binaries: []`。不宣稱 HTML 逐位元組相同，也不是完整 base/head 產品對照。

`windows/`：六支皆已編譯，五支 fresh；integrity 的 SAC WinError 4551 在初次及後續重試後仍受阻，未寫 fresh sidecar。GDI 1/1 通過。沒有變更安全設定或停止使用者服務。

所有 `.log.gz` 的解壓長度及 SHA-256 見 `log-archives.json`。來源身分區分 raw checkout／Git blob／CRLF→LF 正規化，詳見 audit identity 與首輪的 `legacy-newline-identity.json`。`current_geometry.c` 維持全部 CRLF。

本目錄是提交前的局部驗證；final-head 七個 workflow job 的收據另外綁定最後 HEAD/tree，於 PR【Codex】留言提供，不以本目錄冒充 final-head 全綠或另一位 agent 的【WSL 裁判】批准。正式獨立裁判仍待提供，#193 retired 取消 preview 的跨 DSL 污染仍是獨立阻擋。維持 stack／draft、不合併。

CI 受帳號計費阻擋;正式合併裁判由本機 WSL 收據提供

無新 UI 入口
