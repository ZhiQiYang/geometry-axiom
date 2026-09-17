# 公理層閱讀器 · 第 3 版設計

依照選定的深色三欄設計製作的本機互動原型。

## 直接離線開啟

離線檔是建置產物，不入 git。在本資料夾執行 `npm run build:offline`，會寫出 **公理層閱讀器-離線版.html**（約 9 MB）。之後在檔案總管雙擊該檔，以 Edge 或 Chrome 開啟：程式、字體、條文、白話與所有圖例都內嵌，不需要網路、開發伺服器或旁邊的資料夾，可以單獨複製到其他位置。

此命令使用現有依賴，不更動一般 Vite / Sites 建置。檔案的內容安全政策會封鎖網路連線。交付時把建出來的 HTML 當 release 資產，不要把生成物提交進版本庫。

打包腳本會檢查資產內嵌與 HTML 標籤形態。Codex 內建瀏覽器的 URL 安全政策禁止 `file://` 頁面，因此未在工具中實測直接開啟離線檔案；原本的本機網頁版操作驗證記錄仍見 `design-qa.md`。不得把網頁版的操作驗證宣稱為離線檔案驗證。

- 條文導覽與搜尋：63 條（19 定義、23 不變量、21 推演規則）。
- 白話與完整原文分開，引用可固定於右側。
- 從引用前往全文後，可保留原文展開狀態並返回原捲動位置。
- 141 個既有範例記錄，保留接受／拒絕、DSL 和三視圖切換。
- 窄螢幕改為導覽抽屜與參照面板。

## 來源

`scripts/sync-content.py` 只讀取上層 `公理層.md`、`公理層-白話.md`、`公理層-閱讀器.html`，產生本資料夾的 `src/content.json` 與 `public/assets/diagrams/`。原文包含本次同步時專案既有的未提交變更。圖例是原閱讀器已產生的記錄；此原型沒有重新執行幾何引擎或驗證案例。

R21 預設的摘要與 R6(d) 短白話來自選定設計，明標「非條文」；R21 的白話全文及所有原文可展開閱讀。原始工程圖僅調整配色；首頁概覽另裁切並調整標籤位置，幾何座標未更動。

## 開發

```powershell
npm install --prefer-offline --no-audit --no-fund
python scripts/sync-content.py
npm run dev -- --host 127.0.0.1 --port 18773 --strictPort
npm run build
```

可用 Ctrl+K 搜尋，方向鍵與 Enter 選取結果，Escape 關閉搜尋或手機參照。瀏覽器上一頁／下一頁可切換條文。

視覺與操作驗收：`design-qa.md`；證據：`qa/`。

字體：[Noto Sans TC](https://github.com/google/fonts/tree/main/ofl/notosanstc)；圖示：[Phosphor](https://github.com/phosphor-icons/react)，由 npm 安裝並在本機提供。
