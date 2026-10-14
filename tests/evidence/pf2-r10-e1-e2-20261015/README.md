# PF-2 R10 E1/E2：原生回歸與撤修證據

看板指定任務 15，依 [R10 E1/E2](https://github.com/ZhiQiYang/geometry-axiom/issues/128#issuecomment-6172907846)。base main `79412a858f712981fa0ba15a6b293c3e0bf06f21`；完成日 2026-10-15（Asia/Taipei）。產品／測試修正提交 `e8608b786eb8ebcd3a5eb89057a155794a8556dd`，完整 native 固定受測提交 `730001a53fb69dd1f7e38480d0807c0182a7a844`。

## 問題與修正

I52（`公理層.md:1218–1220`）要求厚度的**十進位值**為正整數 mm。`9.` 後接 61／62／125 個零都是精確 9 mm，字串長度為 63／64／127 bytes。D26 材料發布可完整保存三者，但 PF-2 二次讀取只有 64-byte buffer，後兩者因此被誤報 INVALID／PANEL_FILL_INVALID／I52。

`ENG_THICKNESS_CAPACITY=128` 現由材料發布與 PF 求值共用，包含 NUL；沒有放寬材料發布原來的上限，亦沒有裁短／重寫來源或取整。E2 只把 pending 的衍生宿主歸屬改成 PF-H，並把 unknown-operation 的說明對齊原本已分派的四個 operation。交易分派與拒絕條件不變。

## 首紅、修後、撤修、還原

| 輪次 | 結果 | 真正 OS exit |
|---|---|---:|
| 修改產品前，新增同一具名方法 | 63-byte 過；64／127-byte 各在 PF2_THICKNESS_VALUE_9／I52 斷言紅，errors/skips=0 | 1 |
| 修正版 | 三個子案例都讀回厚度 9，原材料字串及獨立重算 fingerprint 保持不變 | 0 |
| 隔離撤回 consumer 到 64 bytes | 只有 64／127-byte 的兩個具名斷言紅，errors/skips=0 | 1 |
| 再用修正版 | 三個子案例過，無 failure/error/skip | 0 |

新方法先寫、先執行後才修產品。首輪有 1 個方法／2 個失敗子案例，不能誤稱 2 個方法。原 stderr 的尾端空白保留在 [before.stderr.gz](before.stderr.gz) 與 raw archive；[before-identity.json](before-identity.json) 綁原 binary、來源與裁判 hash。後來另一個舊方法新增 12.5 負例；[oracle-binding.json](oracle-binding.json) 證明新方法在首紅／修後逐字相同。首輪完整裁判檔在 raw 以單一已知差異重建，並驗回首紅前已記錄的 SHA，不冒稱當時已備份該檔。

[thickness-mutant.json](thickness-mutant.json) 含 compile argv／實際 exit、來源與 binary hash、三個獨立 test 子程序 PID／OS exit、unittest failure/error/skip 明細。bridge.jsonl 保留真實指令／回覆、PID 與各自 monotonic 時間。變體僅編譯隔離副本，沒有改動工作區產品；`current_geometry.c` 以 bytes 讀取，隔離副本維持 CRLF。

定向套件：PF-2 **18/18**、完成面 **22/22**、工程核心 **18/18**，各自 OS exit 0；缺厚度、9.5、12.5 仍拒絕。

## 標準突變帳本

核心 include 閉包變更後，以原 `tests/mutate.py` 真正重編／執行全部 **45 個可執行變體**，另外保留 **3 個退休紀錄**。先做 M01 與基準，再用 4 個普通子程序分批，各自獨立 results 檔，全部 actual exit 0 後才合併。沒有修改 mutation 定義、工具、oracle 或舊證據，也沒有將舊結果改綁新來源。

結果 **40 killed／1 crashed／4 equivalent／3 retired**，完整 check exit 0，**stale 0／blocked 0**。基準 **139/139**。M20 的 crash 由基準綠與三次同場景 SIGSEGV 識別，與 assertion killed 分列。新增厚度撤修是獨立具名反例，沒有灌入既有 48 筆標準庫計數。新舊帳本、分批 raw、sidecar／compile／binary hashes 均在 archive。

## 完整 native

原命令：`python3 -u tests/run_all.py --build --update-expected`；stack **16 MiB**，使用本分支實際重編的 `MUTATE_CACHE`。Debian/Linux x86_64，GCC 14.2.0，Python 3.12.14，Node 24.19.0。

**88 suites、2779 pass／0 fail／1 個 Windows GDI 允許平台 skip、actual exit 0。** 程序 wall **842.678 秒**，runner 表內 **807.5 秒**；兩者分列，前者包含 build／啟動。Node **704/704**、reader **41/41**、PF-2 **18/18**。這不是 WSL／完整 browser／owner 整合收據；產品 PR 的正式七項由本機列車執行，本輪沒有排 WSL。

[native.json](native.json) 記錄固定 HEAD 前後相同、所有追蹤檔案的前後 SHA（排除明示會生成的 expected）；這是前後核對，不宣稱連續監看。唯一明示生成差異由完整 census 產生：`py:test_panel_fill_layout` **17→18**，其餘整份 suite map 全等。原生成 [expected-after.json](expected-after.json) 留原件；提交只保留同一 JSON 語意並維持 base 排版／順序，差異僅該 count 一行，raw 的 expected-format-proof 記錄 hash 與等值檢查。沒有降低其他期望數。

## 原件索引

- [raw.tar.gz](raw.tar.gz)：**374 檔**，含首紅、三組撤修控制、全部標準突變批次、完整 native 日誌、實際工具與隔離變體來源／binary。標準庫 binary 僅附 hash／sidecar，可依來源重編，不冒稱已獨立重跑他人的裁判。
- [raw-manifest.json](raw-manifest.json)：每個 archive 成員的 bytes／SHA-256，封存後逐檔重讀驗證。
- [raw.tar.gz.sha256](raw.tar.gz.sha256)：`980570b170f6ff57c092db2cc56c3acfd8801e7319ebc739d3ccb17074d25155`。
- [native.stdout](native.stdout)、[native.stderr](native.stderr)、[native.json](native.json)、[summary.json](summary.json)。
- 相關套件 JSON、首紅身份、撤修收據、帳本刷新摘要可直接讀；完整 stdout/stderr、OS exits 與動態 bridge 回覆在 raw。

R10 P1～P5 均未修：大面積 JS number 精度、零片時外層列舉成本、未來 PF UI 的結果回執接線、序列化再次求值失敗契約、舊定向突變工具混有 error 的驗核風險，留後續另議。本輪新反例明確要求 errors/skips=0，不倒改歷史工具或收據。

SSOT、白話、唯一正典、BACKLOG、決策佇列、鎖定內容及 `current_geometry.c` 原位 bytes 均未改。沒有新增 UI 入口；只修 E1/E2。最終其後只提交生成 count、文件與證據，受測產品／測試程式不再改動。
