# PR #202：三分量拆分修正與收據

回應 ChatGPT `6112860483` 的新 B1。產品提交
`118c7db`，56 筆帳本提交 `299709e09974babff113718bfc3e32b853e09f4c`。
實際受測 head、工作樹、argv、直接 returncode 及二進位身分以各收據為準；
交付文件提交不是最終整合 SHA 的正式七 job。

## 反例與最小修正

原三行輸入保存在 `_ax_r8_three_residual_components.scene`：輪廓面積 700 mm²、
裁切矩形交集 400 mm²，差集是三個 10×10 分量、共 300 mm²。
`comparison/before.json` 原 ed877f5 產品錯誤成功，兩片為 300＋100＝400 mm²，
仍含應刪的 (15,15)；redo、存檔重開都保留污染。精確 base 635dd86 拒絕且完整 dump 相等。
這是 fc4859 已引入的產品路徑缺陷，沒有歸因前次 f32 的孤立線／點修正。

`proj_split_loop` 原以 `pc ^= 1` 在兩個緩衝區間循環；第三段覆蓋弧會把新的
殘留分量接回第一片。新增 4 行 C（計數、兩行註解及拒絕 guard），在第三段弧
寫入兩片表示之前拒絕，沿既有 apply-proj 單一交易完整回滾。
依 R3／R4／R7／R8 保留精確差集及 dump/replay 語意；沒有擴充成三片成功路徑。
分類函式仍回精確矩形接觸；修正消費該分類的共用拆片 helper，柱與 cut-strip 都受保護。
現有兩片表示、原 id 給面積最大片、孔分配、參照重綁及後續世界重驗保持原流程。
原任務的幾何 helper 範圍擴充到 `proj_split_loop`，只有上述 4 行產品改動，
原因與測試／M66 同列；未改公理、閱讀器、白話、BACKLOG、決策佇列或產品 JS。

三代比較各跑柱／cut-strip、單項／先套合法孔洞共四種交易，保存全部 fixture、
query、協定 result、前後完整 dump、undo/redo、存檔重開與 binary/source binding。
`comparison/after.json` 四種均拒絕、完整 dump 相等，前項孔洞亦回滾。
私有比較 exe 不版本化；base binary 對照舊版 source/compile binding 的 SHA-256，
不是使用當前 source 冒認 base。
`world-cmp/` 另以原生 interactive parser 核對四種交易的整份 2,904,880-byte World；
精確 ed877f5 與 299709e C 各以原 -O2／16 MiB stack 編譯，依未變的 include 閉包執行。
未修版四種皆成功且 World bytes 改變、probe exit 1；修正版四種皆拒絕且逐 byte
相等、probe exit 0。這是獨立補證，不取代註冊的回歸與原完整 runner。

## 測試先行、完整幾何及突變

`before/`：原產品加新裁判，native 272/304（32 個新斷言紅）、reference 50 tests／
4 個三分量子案例失敗、scene 153/155（兩個新場景紅）；三支程序各直接 exit 1。
`after/`：native 304/304、reference 50/50、scene 155/155，各直接 exit 0。
每批 source、三支二進位與 sidecar 前後 hash 都記錄，不以空的 binaries 當執行身分。
工作樹先紅／先綠階段有新增測試或產品改動，並未冒稱這兩批 checkout 乾淨。

原生測試以 1 mm 格枚舉完整整數正交夾具的差集，驗聯集、不重疊、面積及應刪點；
涵蓋反向環、換軸、負座標、環起點跨尾，並保留合法兩分量對照。
bridge 正例驗全部保存輪廓的完整差集聯集、面積及移除格，undo/redo、reset 後重開
再驗同一集合，補足只查 boundary 2 的缺口。拒絕案例另驗全 dump／refs／history／replay。
這些有限夾具不是所有多邊形的形式證明。
`scene-comparison.json` 核原 ed877f5 的全部 153 規格與精確 base 的 143 規格均不變，
原接受／拒絕變動 0。

`mutations/` 56 筆＝48 killed＋1 crashed＋4 equivalent＋3 retired；53 個非 retired
全部重新編譯執行，3 個只驗退休依據，五支 worker returncode 均 0。
M66 拿掉第三段 guard，兩個具名三分量場景真正誤收並被殺死；未把編譯失敗當 killed。
全量 baseline 155/155，原 freshness --check 直接 exit 0，
survived／invalid／stale／blocked＝0。原 M61–M65 保留；舊 55 筆及首輪 M61 存活收據仍在歷史目錄。

## 原完整裁判及未解條件

原完整 `python3 tests/run_all.py --build --update-expected`：83 suite 全部執行，2863 個有計數項＝2856 pass／6 fail／1 個具名允許 Windows GDI skip，直接 returncode 1、636.15 秒。reader 35/41、6 fail；完整原 Node 的結果見原 log，沒有用插樁探針拼接本次全量。原 5 秒 timeout／斷言／concurrency 不變。

原 Node 全 36 檔在本次完整批次為 651/651、0 fail／cancelled／skip；四個歷史
timeout 案例本次約 772.61／944.02／1265.65／2529.33 ms，沒有載入 preload。
這只表示本次未重現，不判歷史根因或 flaky 豁免。

`aggregate/` 前後受測 HEAD 均為帳本提交 299709e；原 runner 執行全部 83 suite，
--update-expected 是在本次完整執行後更新發現數，不刪斷言或改成允許失敗。
只增加 native 176→304、scene 153→155、reference 48→50。
source／五支 native binary／sidecar 的原始前後身分、Popen 退出碼、秒數與完整 log 均保存。
快取日誌目錄依原狀保留；`aggregate/log-index.json` 區分本次更新的結果檔與舊未使用
cache 檔，不把後者冒稱新執行結果。
程序抽樣為一秒 PID／PPID／comm 觀察，會漏短程序，沒有強制隔離或正式 WSL 宣稱。

正典原 41 tests 最新為 35/41、6 fail，包含新 R4 燈號導致的 color-contract 冪等斷言。
新增回歸／M66 讓追溯涉及 R3／R4／R7／R8／R12／R14／R15，相對精確 base 差 1,104 字元；
先前 753 字元是前版診斷。`reader-diagnostic/` 僅在記憶體重建，五道 assert／獨立 SSOT
驗證通過、重建冪等、批註／document 身分保留；正典 bytes 未改、未產出第二份 HTML。
相對 base 的非 trace-details 區也有 R4 追溯燈號 partial→ok 差異，
不能沿用前版「非追溯區完全相同」宣稱；原 source 條文並未改。
這不是正典落檔或 reader 41/41 通過。

唯一同步 owner 仍沿 #192 原 writer，在最終整合 head 原位 sync → check → 原 41 tests，
需涵蓋本版全部新增追溯及 R4 燈號；不能複製只含 #192 舊來源的 HTML。
四個歷史 Node 5 秒 timeout 的根因仍未定，沒有 main 同案例豁免；探針擾動時序及
binaries={} 限制見 `review-timeouts/README.md`。舊 2721／9／1、space 13/2 與 BrokenPipe
均完整保留，不以新局部結果改寫。原 BrokenPipe 根因仍未定位。
正式同一最終 SHA 七 job、Windows GDI 與全程強制隔離仍缺，維持 draft。
CI 受帳號計費阻擋;正式合併裁判由本機 WSL 收據提供。無新 UI 入口。
