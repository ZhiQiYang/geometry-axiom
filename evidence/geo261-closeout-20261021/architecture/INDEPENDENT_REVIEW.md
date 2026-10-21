# 架構收據獨立複核

本文件記錄獨立審查代理對既有產物、Git 物件與原始日誌的只讀核對。沒有重跑架構 gate、原生測試、瀏覽器測試、Q38、§7 或 P-189，也沒有修改 repository。下列 gate 結束碼及計數來自原執行紀錄；複核另以只讀 Python 計算雜湊及比對資料，各輪複核命令均以結束碼 `0` 完成。

## 第一輪：來源 4fe18b8b

- 來源 SHA：`4fe18b8b2afe79c44f8a293dcbeb119c43f0e22c`。
- 證據目錄：`run-4fe18b8b/`。
- 實際架構 CLI 結束碼 `0`：333 個登記來源、796 條邊、0 項診斷。執行 5.587 秒；原始 stdout 與新 scan 逐位元組相同。
- 通用測試 205/205、產品架構測試 18/18，兩者結束碼皆為 `0`，略過皆為 `0`。原始 unittest 摘要與收據一致。
- 29 項負控制完整：2 項既有 digest 撤回，9 個新增工具各有移除登記、破壞 digest、禁止 H 來源依賴三項。全部結束碼 `1`，逐項診斷與目標檔案或完整依賴 chain 一致。
- 已核對四產物、33 份執行紀錄的原始 stdout/stderr 雜湊、610 個來源、3 個裁判、舊四檔備份與當時 HEAD。
- 來源閉包：`60789fecfee767e1954f15ce7450e5d3a23b4966971d57b810675a2405dc01e3`。
- scan 與前版 bytes 相同，仍有上述實際重跑紀錄；未將相同檔案誤稱未執行。

## 第二輪：來源 7afacf65，描述矛盾尚未排除

- 來源 SHA：`7afacf656912edccc7eb84cb9590990bccae1166`；父提交為 `c87c6d90bd06552b7b7b04e0d2aa42fd56f65eb3`。
- 證據目錄：`run-7afacf65/`。此輪保留為中間紀錄，不作最終描述一致性通過聲明。
- 三條 gate 皆結束碼 `0`；通用 205/205、產品 18/18、略過皆為 `0`。實際掃描 5.081 秒，scan bytes 與前版相同。
- 唯一撤回 digest 控制針對 `geometry-core/domain-decoupling/closeout-tools/p72_probe.js`，以正確 `EXCLUSION_DIGEST` 及結束碼 `1` 轉紅。
- 已核對 5 份執行紀錄原始日誌、610 來源與 3 裁判、四產物及舊四檔；舊四檔與 `c87c6d90bd06552b7b7b04e0d2aa42fd56f65eb3` 逐位元組一致。
- 相對前次封存，唯一來源差異為 `p72_probe.js`：`11f85b9f10e296ea4864d7a8d9a8e460a1fe9a2070b6ab5271756b1f13f230ae` → `6884e80a843834630b777d2add24e1c07c12ccc33f075a18f02403256d0dfcbc`。
- 來源閉包：`9723ffce54ba1223948a591cf2fd133abb22ad03e43cefcea8a71e61cd14ab9b`。
- 複核發現當時 manifest 的 `p72_probe.js.reason` 仍寫舊 raw SHA 及已失效的 Document 暫停方式，與新 digest 及本輪 review 矛盾。已要求修正當前 metadata；外部 README 不能取代當前清單的描述修正。此問題屬描述準確性，沒有把通過的靜態 gate 改報為失敗。

## 第三輪：來源 55623598，完成描述修正

- 來源 SHA：`55623598f23e4b630987bb27bbb3f55c10815ea9`；相對 `7afacf65` 只提交 manifest reason 一行修改。
- 證據目錄：`run-55623598/`。
- `p72_probe.js.reason` 已移除舊 hash 及 Document 暫停說法，改述穩定的專用驗收用途；各版控制細節及執行結果交由對應收據記錄。
- 三條 gate 皆結束碼 `0`；通用 205/205、產品 18/18、略過皆為 `0`。實際掃描 5.132 秒；scan 同 bytes 且原始 stdout 完全吻合。
- 唯一撤回 digest 控制仍以目標 `p72_probe.js` 的 `EXCLUSION_DIGEST`、結束碼 `1` 轉紅。
- 已核對 5 份執行紀錄的原始日誌雜湊、610 來源與 3 裁判、四產物，以及與來源 `55623598` 逐位元組相同的舊四檔。僅 manifest、report、receipt 三份 metadata 有 diff。
- 閉包維持 `9723ffce54ba1223948a591cf2fd133abb22ad03e43cefcea8a71e61cd14ab9b`。
- 重新核對 `run-4fe18b8b/`、`run-7afacf65/`：其 final 產物、原始日誌及 previous 備份均仍符合各自收據雜湊，沒有以後輪結果覆寫前輪。

## 最終 metadata 提交 366ef501

- 提交 SHA：`366ef501b78105d1f7242dc1f4f4752cac9086b5`，父提交確為 `55623598f23e4b630987bb27bbb3f55c10815ea9`。
- 此提交僅修改 manifest、report、receipt 三檔；scan 雖已重產，因 bytes 相同沒有 Git diff。複核時工作樹乾淨。
- 全部 610 個 input 的 LF 雜湊同時符合最終收據、工作樹及 `366ef501` Git blobs，閉包仍為 `9723ffce54ba1223948a591cf2fd133abb22ad03e43cefcea8a71e61cd14ab9b`。
- 相對交接基準 `7dae5f21c7ca401e660450d437e60ba566218da8`，333 個 owned 產品來源、`current_geometry.c`、`tests/` 全部 15851 個既有 Git 檔案 blob 均完全相同，`tests/` 沒有新增檔案。新增收尾工具與兩個修改的瀏覽器驗收檔案另以具體 exclusion 登記。

## 複核範圍與限制

以上確認靜態架構證據的來源綁定、原始紀錄完整性、負控制病因及 metadata 描述。沒有由架構掃描推定產品行為、效能、原生或瀏覽器驗收通過，也沒有把第一輪 29 項控制冒稱第三輪重新執行；每輪保留自己的來源、計數與結束碼。

## 最終封裝核對

只讀核對 `metadata-binding-v2.json` 與最終 Git 物件，結束碼 `0`：610 個 input 的 Git blob id、raw SHA-256、LF SHA-256 及整體閉包均一致；345 個 C／header／include 檔案、1471 個遞迴 Python 測試（其中直接位於 `tests/` 的 225 個）均與 `7dae5f21` 相同。舊 binding 所列 184 個本地 quoted-include 閉包檔案也與最終及基準 Git blob 相同；這沿用原收集範圍，沒有新作 preprocessor 求值或將原先 30 筆未解析 include 宣稱已解析。

`final-bundle/architecture/` 的 193 個檔案與來源白名單精確相同，逐檔 bytes 相同。白名單為三個完整 run 目錄，加上 `README.md`、`PORTABILITY.md`、兩份 metadata binding、兩份 Git diff 紀錄、兩份 review、三份 refresh 日誌及本獨立複核文件。

三個 run 的檔數分別為 129、26、26，大小與 binding 各自登記的值一致。封裝沒有額外程式來源、二進位、符號連結、檔案執行權限或 `__pycache__`，也沒有收入外部 `refresh_receipt.py`。本段補記後由封裝代理重新同步本文件；總 bytes 不寫入會計入自身的文件，以免形成遞迴計數。
