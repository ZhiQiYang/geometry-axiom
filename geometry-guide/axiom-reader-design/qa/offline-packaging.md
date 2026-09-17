# 單一 HTML 離線版

2026-09-17；產物：`../公理層閱讀器-離線版.html`。

## 已驗證（打包腳本／靜態檢查，不是 file:// 實開）

- `npm run build:offline` 成功；產出約 9 MB 單一 HTML。
- 63 條條文、141 個範例記錄。
- 127 個不同的 SVG 圖片來源全部轉為內嵌 data URL。
- CSS 的字體 URL 全部內嵌。
- JavaScript 輸出為單一 IIFE classic script；零靜態或動態 module imports。
- HTML 沒有外部 script src、stylesheet link 或 type=module。
- 內容安全政策 `connect-src 'none'` 且其他資源僅允許內嵌內容，阻止連線依賴。

`qa/offline-check.json` 若存在，只是某次打包的人工紀錄，不是 `build:offline` 寫出的牙齒。

## 驗證限制

Browser Use 的 URL 安全政策拒絕開啟這個 `file://` 檔案。沒有改用其他瀏覽器、自動化通道、HTTP 重掛或間接方式繞過。直接開檔的執行、互動與畫面驗證尚未完成；不得把舊有本機網頁版的操作驗證宣稱為離線檔案驗證。

使用者可在一般桌面瀏覽器直接開啟此 HTML；不需要執行開發伺服器。
