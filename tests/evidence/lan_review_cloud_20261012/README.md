# PR #194 M1／M2 雲端複核

受測來源是 `5d7b044beb43f34e01bb56bf3cde70484aee377d` 加兩檔未提交的修正，`source-binding.json` 與各 receipt 綁定实际 bytes／起始 head。後續提交不是先前已執行的 SHA；來源／裁判 bytes 相同才承接這些收據。原 owner 未推的 `73fb6dd` 未取得，不聲稱已交付其原件；本輪從遠端 `5d7b044` 獨立修正並提供完整 Git diff。

## 改動與真 TCP

`tests/test_lan_review.py` 只加 errno import 和普通 `OSError` 的 ENOTCONN 分支（4 行）；既有 BrokenPipeError／ConnectionResetError 分支及排空／bridge 原斷言不變。`tests/run_all.py` 只補三個完整方法名的既有 reason／posix、nt 限制（12 行），分類器、測例數、expected、逾時及既有 allowlist 不變。沒有修改產品、C、SSOT、白話、唯一正典、🔒、安全政策或 UI。

原 registry 的 **M23** 只有 `if self.lan_linger`→`if False`，在私有 source fixture 執行；不是替身 TCP。原 SocketReview 仍實際綁 127.0.0.1 臨時埠並送收 HTTP，產品 handler 真執行；native bridge 依既有測試為 mock，不能據此宣稱真 bridge 多端或 LAN 介面驗收。

| 步驟 | 實際結果 | exit |
|---|---|---|
| 修前判官＋同一 M23，三次真 TCP | 0 fail／3 error，均 shutdown ENOTCONN | 1 |
| 修後判官＋同一 M23，三次真 TCP | 3 指定 AssertionError／0 error／skip | 1 |
| 私有 serve bytes 還原，三次真 TCP | 3 pass／0 fail、error、skip | 0 |
| 原 LAN 30＋review 21＋serve 50 | 101 pass／0 fail、error、skip | 0 |

指定失敗原文均為 `refused late body was not drained after the response`。修前 OSError 不是 killed，修後三次 FAIL 才提供原 M23 被這個判官抓到的證據。三次重複是同一個突變，不是三個新 inventory 項。原 `serve.py` SHA256 `8bdc8c18b21cbc4a93cc1edae48de35c36a79712216cd2b1f9cf897beeaacec9`，私有 M23 為 `551552e4b07e3eee17422648c7ba61e184541cc369f39ae1214b314e515e49d0`；還原 SHA 精確回原值。repo 產品 bytes 全程未被突變改寫。

補充 AST 純例外控制使用實際方法的 try 區段及緊接的原排空斷言：sendall／shutdown 各八例，共16例，ENOTCONN 修前保留 OSError、修後到原 AssertionError；EBADF／ETIMEDOUT／ENETUNREACH／無 errno／PermissionError 保持同一例外物件拋出，兩種舊例外仍到斷言。此純控制沒有 socket，不能替代上表真 TCP。

## 真無 cryptography 與精確 skip

`python -S tests/_unittest_runner.py tests/test_lan_review.py ...` 前後皆實際 21＝14 pass＋7 skip、0 fail／error、runner exit 0；原分類器對該結果為4允許／3未允許，修後7／0，沒有偽造 skip events。刪任一新具名條目，各於 posix／nt 的原分類器參數控制降至6／1，還原7／0；不把六個控制格說成新增產品幾何 mutant。未知方法／reason／scope／suite／平台及重複 event 的負控制保留。nt僅分類器參數控制，沒有聲稱 Windows socket 實跑。

再用 `/tmp/geometry-tests/pr194-no-crypto` 的無 pip、無系統套件 venv，parent 與 child 共用真正無 cryptography 的 interpreter，執行原 `run_all.py --only lan_review`：

- 原 allowlist（測試已含 M1 修正）：14 pass／7 skip，4 允許、3 未允許，exit **3**。
- 還原新 allowlist：同樣14 pass／7 skip，全部具名允許，exit **0**；沒有 `--allow-skip`。

這是原 aggregate 的**局部選定範圍**，不是完整 native／正式七 job。臨時還原原 allowlist 後以 finally 精確恢復新 bytes。首次用 parent `-S` 的 partial 執行，child 未繼承 `-S` 而有套件、21全過／exit0；已交付的只是該子程序 stdout／stderr、receipt 與 suite logs。當時外層 driver 的原 stdout／stderr、實際退出碼及原文未附，無法獨立核其歷史紅燈；不能拿後續 venv driver 或重跑代替，也不把首次執行稱作無套件證據。

## 原件、環境與仍待事項

原私有 mutant 驅動有兩次載入錯誤（缺 helper、缺 RuntimeSnapshot source layout），各三個 ERROR／exit1；沒有算 killed。修正為原 runtime_catalog 的436個來源／靜態檔案閉包，逐檔 hash 在 `M23-source-closure.json`，只變更私有 serve 的登記 patch。canonical reader 僅指向 repo 唯一原件的 read-only symlink，未另建或修改 HTML，沒有提供使用者預覽。

本輪沒有觸碰使用者憑證／信任庫／NetworkCategory、沒有啟動 LAN 介面服務，測試使用暫存合成材料；沒有真原生執行器、實機 iOS、完整安全批准、排他環境或正式 WSL 七 job 收據。**B1 根信任／CN fallback／iOS 指定 IP 隔離、完整 handoff／使用者安全批准仍未結案；B2 正式七 job／真 bridge 多端仍待既定 owner 排程。** 原177原件、前輪101與49指定突變僅保留既有審查已核範圍，本輪只重驗上述受影響判官，不重稱全49重跑。

所有 stdout／stderr／log 無損存為 `*.raw.json`：原檔名、bytes、SHA256及UTF-8 raw 字串可逆還原，包含空檔與行尾空白。`package.py --decode /tmp/geometry-tests/pr194-decoded` 可解碼；manifest綁全部payload，`product-test.diff.json`保存兩檔原 patch bytes。腳本保留本輪 `/workspace`、`/tmp` 執行位置，重現時需對應checkout。所有測試 listener／bridge reader 均由原 cleanup 結束；不停止使用者服務。
