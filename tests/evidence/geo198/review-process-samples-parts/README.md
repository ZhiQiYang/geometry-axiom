# PR #202：大型程序取樣原件的無損文字分塊

外審 `6114690821` 已讀 271／272 份原 payload；唯一未取得的 `aggregate/process-samples.json` 因傳輸量過大受阻。本補件只提供該檔的無損 gzip＋base64 文字分塊，原 272 份 payload、原清單、產品與裁判保持原 bytes，不新增產品驗收或強制隔離聲明。

原件位於 `tests/evidence/geo198/review-local-corner/aggregate/process-samples.json`，來源 head `45603894d9e0545a7070b93d831a5a43397939ee`，受測 aggregate head `1b5919787df1124c0eb6122a886d4403ada21fd2`。

原 SHA-256：`4ed88f6448a80cadbdc3a97c9204468d7b3a42ecf488e0a8b5da8f19d6676726`。

7,419,548 bytes／392,956 行，gzip 為 82,243 bytes。14 個文字 part 各不超過 8,192 個 base64 字元（另有換行），按 `metadata.json` 的順序串接。它們是同一份完整原檔的可逆編碼，不是抽樣、篩選、重寫 JSON 或移除程序。

執行 `python3 verify.py`：逐 part 核長度與 SHA-256、串接／base64 decode／gzip 解壓，再核原長度與原 SHA-256，最後解析整份 JSON，核對 scope、602 筆樣本與完整 PID／PPID／comm 欄位。標準庫即可，預設只在記憶體解壓；`verification-run.json` 保存實際指令、直接 exit、stdout 與 source binding。`make-parts.py` 是本次實際封裝器；`SHA256SUMS` 核所有補件 payload，不自雜湊。

此原件只有每秒 PID／PPID／comm 觀察，沒有 argv，可能漏掉短行程，沒有強制隔離；不能證明正式 WSL／七 job、排他裁判或歷史 Node timeout 根因。

外審指定幾何 M1 已解除，本補件不重排已完成的 native 432／432、scene 157／157、reference 51／51 或 57 筆突變。原 aggregate 仍為 2994＝2987 pass／6 reader fail／1 允許 Windows GDI skip、直接 exit 1。

B1／B2 仍阻擋：既定唯一同步 owner #192 交付仍是 `e37c06826d3ed5503117a47d6e3699908e2804b6`，41／41 對應較早產品，不能解除本線六紅。按 #192→#193→#196→#202 既定整合路徑，由 owner 在最終產品 head 原位 sync→check→原 41 tests、保存五道 assert／獨立 SSOT／批註身分及唯一正典，再交同一最終 SHA 的正式七 job。文字可合併不代表整合驗收通過。歷史 timeout／space／BrokenPipe、Windows GDI 與隔離界線保留；不寫正典、不合併、維持 draft。
