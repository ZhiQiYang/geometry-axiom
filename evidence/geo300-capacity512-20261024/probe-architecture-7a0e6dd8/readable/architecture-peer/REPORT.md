# #348 架構正式原件核收

**核收通過，未發現阻擋採入四份架構產物的原件／綁定缺口。** 本輪是對既有原始檔案的獨立一致性核對，沒有重跑 scanner、generic、product、native 或帳本，沒有啟動 Git/API、編譯或修改來源。

真執行來源保持 **M=`7a0e6dd81c54066995981393925fa46a815de2f8`**，來源 checkout `/dev/shm/pr348-probe-source-7a0e6dd8`；原工具 `/workspace/geo323-architecture-tools/run.py`，2026-10-29 **03:50:27.516–03:50:48.849 UTC**，outer／inner／subreaper primary 皆真 exit0、無signal/error。這不是 ledger 正在使用的 checkout；原件記錄 second-heavy lock，沒有把其結果冒全專案動態驗收。

| 原命令 | 原件結果 |
|---|---|
| `python -B tests/architecture_contract.py --root . --manifest geometry-core/domain-decoupling/product-architecture.json` | exit0；604 executable inputs、334 owned、270 excluded、798 edges、0 diagnostics |
| `python -B tests/test_architecture_contract.py` | exit0；205 tests，205 pass、0 skip |
| `python -B tests/test_product_architecture.py` | exit0；18 tests，18 pass、0 skip |

三條 actual argv 的 Python 均為本環境完整 `/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3`；本表是可讀縮寫。29個原命令的實際argv/cwd/source、退出碼、完整stdout/stderr大小及raw/LF hash均核對原流；三條測試的計數及OK來自原stderr，而非只採外層passed摘要。

## 四檔與 closure

四份產物均位於原件 `refresh/new/`：

| 產物 | bytes | SHA-256（本輪raw＝LF） |
|---|---:|---|
| `product-architecture.json` | 221591 | `80f44b8c870e097413e395d30ba029199ba66b7302985c0f325d4f446d0ce525` |
| `product-architecture-scan.json` | 132560 | `94981f75c95517a76f1a619972b433e8e644c6efc81cf38b48a628faa38ebdc0` |
| `PRODUCT-ARCHITECTURE.md` | 44196 | `2c26464a718e21a944d78c9845bee7a8f4e4e14bb35261885071fe8f73d13a4f` |
| `product-architecture-receipt.json` | 134264 | `1ea699d3f6d1b5a56ae1297d3a47ae36cbbcd8c1154fa1bb1696c565e4da45d0` |

receipt schema為 `geometry-product-architecture-receipt/1`；scan逐bytes等原scanner stdout。receipt內manifest／scan／report hashes與實體產物相符，receipt不自hash。manifest逐bytes等舊manifest，policy/classification delta全空，沒有自動增列exclusion或改policy。

獨立解析原 `git cat-file --batch` 的20,758,793 bytes stdout與604個固定M:path stdin，逐blob驗Git SHA1、對照source-inputs記錄及目前probe checkout的raw/LF bytes。604葉唯一、path排序、與manifest owned＋excluded聯集、原固定M `ls-tree` 的全部執行性suffix集合相同。未新增Git查詢或借另一來源。

- LF closure：`0c738c2c8b39b8cc4904bd39121f8ec9412f072cb2be6351b55e5b9f49f6fad0`
- raw closure：`75cfa56dc6695d519c751358c62e2f89237218b0ce5d0d279b1460dec79dd3bb`

兩者皆由原path-sorted `{path,sha256}`清單依原UTF-8／ensure_ascii=false／compact separators重算，與receipt前後值一致。三份裁判原bytes也等固定M原Git stdout及前後hash。原head/status檢查全部固定M且乾淨；目前probe detached HEAD仍M。

## SSOT與限制

公理層、決策佇列原Git stdout、保全before bytes、目前probe實體及receipt before/after完全相同；它們另行綁定，沒有假稱包含在604 executable closure內。

- `公理層.md`：`c66c48e50e0caceef42721c79700365f090f5c48d297abba41993eeb40dba9b7`
- `決策佇列.md`：`cfad2b7ad5181a97a0d87e0791f96548cb0838f6222a01fabdf06d987b5211e0`

僅四份非執行性衍生產物被排除以避免遞迴自hash。工具run/core/reaper快照逐bytes等原工具並符合外層收據hash。原Git的既有alternate警告保留在原stderr；退出皆0、指定blob與完整輸入確實齊，不把警告刪成乾淨輸出。

保留原限制：未執行舊Windows額外probes、未代替native/browser/專項、沒有此刻的遠端發布證明。後續採入產物或帳本時仍保M為真execution；如新來源／裁判改變，須按實際closure處理，不能把本輪收據改標成新F。這些限制不構成此次四檔本身的新缺件。

核對器與結果：`verify_receipts.py`、`RESULT.json`，本輪唯讀核對命令exit0。
