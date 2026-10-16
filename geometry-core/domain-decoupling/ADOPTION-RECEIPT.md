# GEO-261：207 條正式採納與相容性收據

本片實際寫入 `公理層.md`，LF SHA-256 為 `18a9a75bcf4a5d5fed28c6c5f5cb9702d173198d7d0cd198ffad9936a4b94fa5`。這是規範、白話、唯一閱讀器與版本識別的採納，不代表 C 核心解耦、來源圖完整覆蓋、產品接線或整合列車已完成。精確寫入提交 A、版本配對提交及逐項執行結果由同目錄 `ADOPTION-RECEIPT.json` 固定。

寫入提交 A 為 `e744f5316fd7c896275bdee4c34ad22ae97d9d8e`；後續提交只把執行器 revision 指向 A 並附本次收據。[機器收據](ADOPTION-RECEIPT.json) 與 [原始證據](evidence/adoption-20261016/) 保存實際結果及逐檔雜湊。最終閱讀器 51/51、提案 29/29、採納 15/15、純 Python 相容 4/4 均通過；原生相容 10 項仍為 UNRUN。獨立只讀複核曾指出 D11 白話把「接觸邊」誤寫成「平面」，已修正並複驗；r42 同步及這裡的最終 51 項結果都在修正後執行。

## 批准與獨立來源

- 原 103 條完整差異、前言與 §四：`17a25e92c75e8c89063e36ca329729980d8ea6a9`，使用者原話「批准此版本的逐條提案」。獨立更名缺陷另答「批准此更名缺陷修正」，不與本片規範驗收混算。
- 最小追加案：`c8ce964be623084af957dc2ff662abfdaf670c87`，使用者於 `2026-10-16T15:23:52.328994Z`（台北 23:23:52）原話「批准此追加分層提案」。清冊 204→207；D64／I74 歸 K、R60 歸 H，三條正文與功能原樣保留。
- 原提案及追加案 Markdown／JSON 保持審閱時的原 bytes 與歷史 `proposed-not-approved` 狀態；批准記在 `APPROVAL.json` 與 `決策佇列.md`，沒有回寫歷史提案。
- 獨立舊來源為 `tests/fixtures/geo261-axiom-base.txt`；上游為 `a898ad6e12707104568679591fe1b21804bfc3df` 的 `tests/fixtures/geo261-axiom-train17.txt`，LF SHA-256 `e5e43ec5da2030669c9ecd7a67f8b250cfb7290cf663365b2b66c51814bb77b9`。

批准 103 條中 96 條原樣採用批准 after；與 train17 重疊的 7 條（D9、D29、D31、I8a、I37、R32、R33）保留批准 K 前綴及完整上游適用正文。全部 95 條 M 均逐字驗證完整上游正文；D25／I38／I39 保留新上游內容；D64／I74／R60 正文不改，GEO-262 前言也保留。作用域總數為 K 31、M 95、W 30、H 51。SSOT 保持 Windows CRLF；同一性只忽略 CRLF→LF。

## 閱讀器與旁白

只由 `geometry-guide/sync_axiom_reader.py` 原位重建 `geometry-guide/公理層-閱讀器.html`。全文 207 條、1258 blocks、文字 r42、5 筆原批註保留；90 個補丁標記、五道 assert 及獨立 SSOT 比對通過。前言與 §四的來源原文、雜湊及靜態 DOM 一併保存，19 列作用域與 19 項排除限制均保留。既有兩個說明位置承載完整來源，重複來源說明合併為一條，不新增閱讀器或操作入口。

白話同步解釋責任分層，保留既有用途與未完成功能的說明；D64／I74／R60 另補批准的作用域。既有匯出文字包加入完整前言與 §四，匯出時核對兩區塊來源雜湊。CLI 與實際瀏覽器驗證分別記錄：Chrome 155.0.8059.80 在 1440×1000 與 390×844 檢查顯示與無水平溢位，停用 JavaScript 及列印媒體均保有全文；實際點既有按鈕下載 `.md`，逐字包含兩個完整來源區塊；沒有外部 HTTP 請求或 page error。系統淺色偏好與深色偏好、手動切換維持既有行為。390px 是桌面模擬，沒有宣稱實體 iOS 驗收。

## 舊檔相容與驗收界線

`PRE_DECOUPLING_AXIOM_VERSIONS` 只新增採納前 main 已宣告的一對 `(b3c79615d0cde89bbdca72c1223d214324bc5f8f, e5e43ec5da2030669c9ecd7a67f8b250cfb7290cf663365b2b66c51814bb77b9)`。原有每代 allowlist、六道能力年代閘門、schema、generator 與 capabilities 不改。先 commit A 寫入條文，後把 `AXIOM_REVISION` 指到 A；過渡版本不交付，也不加入歷史 allowlist。

`tests/fixtures/domain-decoupling-main-a898ad6e/` 是舊 main 實際 producer 輸出，不以新 writer 重做或塗改 manifest。producer receipt、腳本與 13 份 fixture 都核對原始 bytes；`.gitattributes` 固定這些 bytes。14 個 compatibility 方法包含完整幾何／參考構件、有限與無限網格、相位差、參數引用、既有子規則拒絕、所有歷史版本、六道能力年代拒絕、交叉版本拒絕，以及重新雜湊仍不能接受假幾何／來源的重建控制。

其中 4 個方法不依賴原生 adapter；其餘 10 個依賴原生重建，本片因尚無對應來源的 verified adapter **UNRUN**，不使用任意舊 exe 代替，也不冒稱 14/14 綠燈。本片未編譯 C、未跑 WSL、未切換預設執行器、未啟停使用者服務。完整 `.gcanvas` 與 native source-graph 的產品整合仍由主整合驗收，不能以這些模型包 fixture 代替。

採納測試為 15 項（含實際批准與實際 SSOT 正例），原提案測試 29 項，閱讀器測試 51 項。五組刪除真守門條件的負控制都必須在各自具名案例失敗、0 errors、正式輸入不變；此分支保留 `--skip-registration` 的 **preflight** 身分，因 aggregate registry 由整合分支擁有，不能把局部結果冒充正式整合通過。整合需更新閱讀器 41→51、採納 13→15，並登記新 compatibility 14；本片未自行修改 registry／expected manifest。
