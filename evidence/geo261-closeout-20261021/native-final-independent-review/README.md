# 正式 L native 獨立審核補充包

來源 SHA `43f85313c32410ac01406ab585846bbacafea278`。本包保存僅讀取原件的獨立接受器、報告與觀察；沒有執行產品、build 或測試，也沒有修改原 `native-final` 凍結包。

最終核對 exit 0：224 suites、5175 pass／0 fail／1 具名允許 GDI skip，188 Python 結果、600 raw／296101 bytes、656 原件索引、18 launcher 副本、12 個初始／最後 binary 與 sidecar，以及 203 個 Git L 來源 blob 一致。原命令是 `timeout 2100 python3 tests/run_all.py --build`，含 build 實耗 1895.301800551 秒，原真退出碼與限制見報告。`mutation:check` 是 78 筆 inventory freshness，不冒稱重新執行 78 個突變；M20 crashed 不計作斷言 killed。

`attempt1/` 保存獨立接受器首次 exit 1，原因是把原 bytes hash 直接比對既有 CRLF→LF 正規化的 sidecar hash。當時曾過早推測 symlink；後續 Git mode 100644 與原 bytes 相同的證據已推翻，`correction.json` 明確更正。正確結論是 `current_geometry.c` 有 10496 處 CRLF，原 bytes 與 Git L 完全相同。最終接受器按正式 `binaries.py` 的正規化及 HARNESS AST literal 契約核對；仍嚴格要求原工作 bytes 等於 Git blob。這些是只讀審核器的診斷，不是正式 native 測試失敗，也沒有重跑 native。

正式 native 自身第一次封裝解析器以 `\s` 跨行誤讀 116 列的另一個失敗，已在原 native 包 `packaging-attempt1` 保存；不要與本包的 hash 審核器誤判混為一輪。本包不改它的任何原件。

`接受器退出觀察.json` 是實際工具 session 回覆已知欄位的事後轉錄，明示證據型態，沒有冒稱先前自動保存的 transport 原件。最終接受器輸出與原碼皆以原 bytes 保存。`原件清單.json` 提供來源、長度與 SHA-256，`SHA256SUMS` 可用 `sha256sum -c SHA256SUMS` 核對。

本包不代替獨立 browser／Q38／§7／P-189 gates；Windows GDI 未在本機執行，未在 GitHub CI、Windows 或 WSL 重跑。最不確定處仍是其他 runner 的 init／subreaper 條件是否一致。
