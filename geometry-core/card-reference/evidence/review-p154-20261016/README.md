# P-154：診斷、追溯與網頁模型載入核對

完整受測 head：`300cb953d84b37f542cbad2b4940417ab4cf7629`；雲端 native,非正式 WSL 收據。後續交付提交只補文件、expected、官方帳本及本證據，產品與測試保持受測 bytes。

M1 把 struct 的 I74 註解移入 grid_card_mark，標準同步後不再錯連 guide_line_get_local_segments；I74 仍 partial，統計與全部 reader state 不變。M2 格式錯誤使用 D29 GRID_DEFINITION 並指名網格；真正卡片映射仍是 I74 COMPLETE_MAPPING，原軸模式診斷保持。helper 對同一則診斷與完整 id token 比對；舊版本案例從驗證器共用允收集合減現行版本推導。

測試先行：最終新案例對舊產品／舊 helper 為 2 方法、7 個失敗子案例、0 errors／skips；修正後整卡 36 與相容性 36 共 72 方法全綠。完整 native 99 suites、3033 計數／3032 pass／0 fail／1 既有 GDI skip；reader 41/41。唯一新增 expected 是整卡 34→36，未降低門檻或新增 skip。

本來源 53 筆反證為 50 原生產品碼 + 3 helper 負對照，均具名轉紅／逐 byte 還原重編回綠；另四筆版本防線、六筆保存端變異及一筆註解追溯負對照。註解對照撤回 M1 後讓原 reader 冪等斷言轉紅，不冒稱原生語意 mutant。

MODEL-ADMISSION-AUDIT.md 列出正式開啟／本機恢復／續接／方案及子快照共用的 readProjectContext → verifyStoredModel → /model/verify → verify_package 路徑。真私有服務與真客戶端 VM 探針，對結構合法但舊版號帶整卡能力的模型包，只送一次 /model/verify 就得到 AXIOM_VERSION，context/history/models/dump 不變；VM 內撤除一般驗證呼叫後，具名斷言轉紅並觀察到 upload/prepare、upload/confirm；還原探針回綠。沒有在產品檔撤掉驗證，也沒有新增網頁版本表。

ZIP 收 1156 份原件及逐檔 SHA-256，沒有編譯執行檔或 HTML 副本。早期未採認嘗試亦保留並在 summary.json 標明，不以它們充當有效反證。完整 stdout/stderr、每筆 patch、編譯／測試 receipts 及官方 check 見 ZIP；B2/S1、正式 WSL 七項與身分帳／UI 邊界仍未驗。
