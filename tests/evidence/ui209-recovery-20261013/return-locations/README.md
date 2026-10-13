# #210 M1：原碼 return 位點校正

依 [審查 6132737897](https://github.com/ZhiQiYang/geometry-axiom/pull/210#issuecomment-6132737897) 與 [原 owner 接續留言](https://github.com/ZhiQiYang/geometry-axiom/pull/210#issuecomment-6132900252)，修正診斷標籤並補舊資料校正。這次只有靜態文字轉換及檔案核驗，沒有執行產品、browser、server、bridge 或 WSL。

原插樁先展開 13 個 await，再用展開後的 return offset 查原 source 行號，33 個 return 中有 27 個錯置。現在先從同一份未修改片段收集全部位點，再由後往前替換；13 個 await 與 33 個 return 的數量不符時拒絕插樁。固定來源的 served 內容除 return 行號外逐字相同，return 值與 await 標籤保持相同。

## 來源身分與舊資料用法

八輪 P70／P88 的 `geometry-web/grid-system-workspace.js` bytes 相同，來源 SHA-256：
`ce0c48d2d2c3d0102f05a45c58ac1568da991c28cc55e2461c1a4644f2e7cf01`。

原 served SHA-256：`19b834a3f5b4c40e1f7a69a63b9ffca31d3fdb07c77ab54b0a5213a6c0be29f4`。
修正後純文字轉換的 served SHA-256：`f7bcf745cae7b14ed1f14cc02c0729c58fea5b198638fb448e4373469048f10e`；這份新 served **未送入瀏覽器**。

[corrections.json](corrections.json) 包含：

- 33 個靜態位點的 ordinal、原記行號、正確行／欄與原碼全文；欄為 1 起算 Unicode code point。
- 八輪 42 筆實際 `open.return` 的 browser.jsonl 行、open 代次、原時間戳與位點對應。
- 原 summary 的六個 JSON pointer 更正，並附對應 raw 行。這是附加校正表，不覆寫原 summary。
- 原 archive／manifest／summary SHA，以及各 run 的來源、served、原插樁、browser.jsonl SHA；328 個成員的實際 bytes/hash 已核對。

| 實際紀錄 | 原標籤 → 正確 source 行 | 依據 |
|---|---|---|
| abort18-01／-02 的 open 3，objects 回應非 ok | 964 → 963 | 位點 7，欄 118；分別 browser.jsonl:496／495 |
| 其餘 40 筆成功返回，含 baseline／hold3／P88 | 1024 → 1015 | 位點 33，欄 91；每筆 raw 行及代次見 JSON |
| 六份 P70 target 摘要 | abort18 兩處為 963；baseline／hold3 四處為 1015 | `summaryPatches` 列精確 pointer；P88 沒有此 target 摘要欄 |

例如 963 行同時有 `ownsEntry` 失效及 objects 拒絕兩個 return，不能只憑正確行號把兩者混同。舊紀錄的 964／undefined 唯一對應位點 7；此次 42 筆都能唯一對應。未實際觀測的位點只提供靜態表，不宣稱曾執行；遇到重複舊標籤且無法區分時，校正工具會拒絕推測。

原 `raw.tar.xz` 保持 2865276 bytes／SHA-256 `89a7ea908a7fb3d0957d1103d45f00b11c5de55d2a305b589b5a5bfcf7d6f5ba`；summary 保持 SHA-256 `4750214a24efd8daf4fd58dc10bdb599370e2f694ee10d38206153150f586d29`。原 manifest、verification、80 段傳輸與 P78 證據不變。原回應、state、期限、時間差、首紅與恢復界線全部保留；這項修正沒有新增歷史 WSL 根因證據。

## 驗證及重做命令

從 repo root 執行，無額外套件：

```sh
node --test-reporter=tap tests/diagnostics/ui209_instrument_test.cjs
python3 tests/diagnostics/ui209_correct_returns.py > /tmp/ui209-return-corrections.json
cmp tests/evidence/ui209-recovery-20261013/return-locations/corrections.json /tmp/ui209-return-corrections.json
git show ecb8a371649e721ae6bd620bec66482666c39d1d:tests/diagnostics/ui209_instrument.cjs > /tmp/ui209-old-instrument.cjs
UI209_INSTRUMENT=/tmp/ui209-old-instrument.cjs node --test-reporter=tap tests/diagnostics/ui209_instrument_test.cjs
```

最後一條預期 exit 1。四項測試使用獨立釘定的原碼行號／return 值，涵蓋全部位點、Unicode／新增前置行、形狀變更拒絕；只 parse 產物，不 evaluate 產品。

| 同一份最終測試 | 結果 | 原始輸出 |
|---|---|---|
| 修前原工具 | exit 1；1 pass／3 fail | [before.tap.json](before.tap.json) |
| 修後工具 | exit 0；4 pass／0 fail | [after.tap](after.tap) |
| 載入原工具，移除修正 | exit 1；1 pass／3 fail | [removed-fix.tap.json](removed-fix.tap.json) |
| 校正工具載入舊插樁 | exit 1，拒絕錯誤位點 | [old-map.stderr](old-map.stderr) |

這是**診斷 metadata 的修前／修後／撤修**，不是產品恢復驗收。校正表重新產生兩次逐字相同；Node／Python 語法與 `git diff --check` 通過。[validation.json](validation.json) 保存命令、exit、工具 hash、Node／Python 實際 binary 身分及輸出 hash。最初兩次 `node --test` wrapper 只回報檔級失敗，原輸出與當時測試 source 另留存；正式三輪使用上面的 direct Node 命令，能看到各斷言結果。

Node 失敗輸出含只有空白的行，首次 staged whitespace check 因此拒絕。兩份 `.tap.json` 以 `lines` 保留每行含原換行；`''.join(lines).encode('utf-8')` 可重建原 TAP bytes，並以內附 `rawBytes`／`rawSha256` 核對。沒有修剪原輸出或更動 repo 設定。

校正工具僅執行目前的文字 transformer；原 source／served 與封存工具／binary 都只讀。它先驗原 archive 與 manifest 及全部成員，按原碼順序配對 return，驗證 served 除行號外相同，再依舊行號及 return 值唯一解析實際事件。`ui209_summarize.py` 仍原樣重現舊 summary；讀舊 return 行號時必須同時套用本附表。
