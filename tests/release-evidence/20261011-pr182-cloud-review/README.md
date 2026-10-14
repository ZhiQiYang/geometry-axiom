# #182 雲端審查修正收據

本輪修正版本說明及 SPM41 故障注入；未修改產品 C、原生／模型測試、公理、白話、正典、runner、expected 或核心帳本。原 canvas `Rule line control unreachable #igNewBinding` 首紅與 WSL 6/7 結果仍有效；未排七 job 或宣稱可合併。

## 實跑版本與故障因果

`before/receipt.json` 在乾淨 `aa4067b3a4343329a5fba261453c9032bb60290a` 執行。`after/receipt.json` 與 `gate-cli/receipt.json` 在同 HEAD 加本輪未提交修改執行，不能稱乾淨新提交測試；收據綁定實際 gate／測試／C 閉包與 binary SHA-256，可對最終提交逐檔核對。執行器、來源雜湊、完整編譯及測試命令、直接 exit 與 stdout/stderr 均保留；所有十二次 probe 編譯 exit 0。temporary source／binary 路徑只是執行位置，未當成長期產品或閱讀器提交。

原始 `pr182` 來源為該 HEAD。`shared-predicate-192` **只在拋棄式 C 複本**以 #192 `e37c06826d3ed5503117a47d6e3699908e2804b6` 的 `poly_rect_center_inside`／`poly_contains_rect` 函式 bytes 替換對應函式；它是共享判定相容性探針，不是 #192／#202 完整整合樹或正式 head 收據。兩種來源各有完整 C 輸入閉包雜湊。

| SPM41 定義 | 原 #182：基準／突變／還原 exit | 共享判定覆疊：基準／突變／還原 exit |
|---|---|---|
| 舊：改回 `poly_contains_rect` | 0／1／0（killed） | 0／0／0（survived） |
| 新：`return n;` → `return n>1?n:0;` | 0／1／0（killed） | 0／1／0（killed） |

每次基準跑原 native 類別的 25 個 gate 方法、零 skip；來源圖／建置收據方法仍依原 gate 排除。突變與還原跑原具名 `test_concave_not_four_corners_and_winding`，不改其精確 `outsideRegions`、繞向、貼緣接受及拒絕斷言。新突變丟掉恰一片正面積差集，兩種來源均以 AssertionError／`V_PROFILE_OUTSIDE` 真紅；無編譯／基礎設施錯誤或 skip。每種來源的突變 binary 與基準不同；還原 binary 與基準完全相同。

另直接執行原 gate CLI `--only SPM41 --group native --receipt … --logs …`，基準 exit 0、新 SPM41 killed、整個 gate exit 0。只跑一個案例；`gate-cli/mutations.json` 是本輪新定義的子集帳，不拼入歷史 42 案全綠。`probe.py`、`gate-cli.py` 為完整執行器；`judge-closure.json` 綁定 gate 使用的本 repo Python 測試來源，編譯器版本等見 `environment.json`。

## 文件更正及舊證據

歷史 f0c4c71 的 42 案為 **39 個 FAIL＋SPM38／SPM40 兩個含指定 cause 的 ModelError（ERROR）＋1 equivalent**；只在 native 37 案比較重編 binary，model 5 案變異 Python、使用未變異 adapter。沒有改寫原 ERROR 日誌或 JSON。

`f0c4c71→f752994` 的 docs／docstring 同一性不適用於 aa4067b：後者另有選集守門、九項測試及 runner 登記，清冊 **84 suites／2620 項**。本輪沒有增加測試方法或更改 expected。AC23 仍被 gate 排除，其他提案原數字／完整面材上限移除的缺口仍在；沒有宣稱完整 AC16 完成。

本輪只更新歷史 README 導讀及其 checksum；73 筆清冊全核符，其他歷史 raw／JSON／tgz 相對 aa4067b 逐 byte 不變。更新前 README 與清冊原位元組保存在 `historical-README.md`／`historical-SHA256SUMS.txt`，舊清冊應對舊 README 驗，而不是把它拿來驗修訂後導讀。

## 輕量檢查與限制

原選集守門測試 9/9、exit 0。`mutate.py --check` 首次在共用 `/tmp/geometry-tests/mutants` 快取檢查為 exit 1、45 stale，原因全部為 cached binary 與歷史 executed receipt 不同；保留原 log。其 M01 快取指紋對應 #202 的閉包，見 `cache-binding.json`，不能當成 #182 原執行 binary。

依工具既有 `MUTATE_CACHE` 入口指定未存在的獨立快取路徑（未刪除或改寫共用快取），同一份核心帳本的來源／裁判／執行收據檢查為 **40 killed＋1 crashed＋4 equivalent＋3 retired，stale 0、exit 0**；工具明文允許 clean checkout 缺少 temporary binary。這只驗證保存的執行收據與來源，沒有在本輪重編／重跑 48 個核心條目，也沒有改帳本。

本輪為雲端 Linux，非 WSL。未重跑完整 native、canvas／main 對照、正式七 job、Windows GDI 或強制排他裁判；舊正式 canvas 紅燈與最終新 SHA 待驗均未解除。`sha256.json` 列本目錄所有 payload（不含清冊自身），用 Git LF bytes 驗證。
