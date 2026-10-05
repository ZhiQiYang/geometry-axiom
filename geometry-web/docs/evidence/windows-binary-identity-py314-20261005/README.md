# Windows／Python 3.14 二進位身分核對

產品來源仍是 `d6b4b450d741fcbbfd75c51631915d3082926990`。這次只改 `tests/binaries.py` 的檔案身分比對、對應的中性檔測試，以及 `py:test_binaries` 的預期數 27→30。沒有手寫 sidecar，沒有放寬 fresh：sidecar 仍要來源指紋、大小、mtime 與原始 bytes SHA-256 相符，而且只有啟動成功才會發布。沒有改 Windows 安全設定，也沒有把 exe 拷到舊路徑。

PR #134 沒有測。整套 `tests/run_all.py` 沒有跑。

## 身分核對

Windows 上 CPython 3.14.4 的 `stat().st_ctime` 是建立時間，`fstat().st_ctime` 不是同一個時鐘。`st_birthtime_ns` 兩邊都是建立時間。修前的簽名把這兩個 `st_ctime` 放在一起比，所以建立時間與寫入時間不同的穩定檔案會在讀取前記成 `binary changed before hashing`。

修法只在 Windows 把最後一個欄位改成 `st_birthtime_ns`（沒有這個欄位才退回 `st_ctime`）。裝置、inode、大小、mtime 都還在。其他平台仍用 `st_ctime`。

### 修前（未改的 `tests/binaries.py`）

中性檔先寫入，再用 `os.utime` 把 mtime 往後移 2 秒。

```text
ctime_equal False
birth_equal True
mtime_equal True
STABLE_ERROR binary changed before hashing
```

同一個未改函式在修改 mtime 之前就已經拒絕，所以那次沒有走到「雜湊期間」的判斷。開啟中的檔案做 `os.replace` 得到 WinError 5，檔案內容不變。

先前同一 SHA 編出的 `gdi-contract.exe`（722432 bytes，SHA-256 `a92e8d86d36e93f5de48f5eb8005efcf1ff717c213f7aa98b36339277387b0c9`）也是在這個檢查停止，sidecar 沒寫成。

### 修後

同一種中性檔：

```text
ctime_equal False
birth_equal True
mtime_equal True
STABLE_SHA 84e038a2b010ae3850c352d264b884d8d9862074781a68ee097af7d9170bf939
STABLE_MATCH True
STABLE_SIZE 15 True
MUTATE_ERROR binary changed during hashing
REPLACE_ERROR binary replaced during hashing
REPLACE_BYTES b'replacement-content'
REPLACE_OTHER_EXISTS False
```

`python tests/test_binaries.py`：30 個測試，退出碼 0。穩定檔通過；雜湊期間改 mtime 或追加 bytes 會 `binary changed during hashing`；雜湊結束前換成另一個檔會 `binary replaced during hashing`。Windows 上對仍開著的檔案做 `os.replace` 由系統拒絕（WinError 5），函式不回傳身分。

只讀、不啟動那支先前被擋住的 exe，修好的核對現在能算出與檔案 bytes 相同的 SHA-256 `a92e8d86d36e93f5de48f5eb8005efcf1ff717c213f7aa98b36339277387b0c9`。

## GDI 執行（另一件事）

這次在新的暫存目錄執行 `python tests/binaries.py build gdi`。身分核對通過之後，工具自己的啟動也通過，退出碼 0，並寫出 sidecar。新 exe 是 722432 bytes、SHA-256 `de7dec1737e2d658dff1a7dcc7b8c2246254b586efd2efa816be07d4cf869676`，與上一支被 WinError 4551 擋住的 exe 不是同一個 bytes。沒有改安全設定，也沒有沿用那支被擋的檔案來冒充 fresh。

接著只跑 `python tests/test_gdi_contract.py`，退出碼 0：

```text
.
----------------------------------------------------------------------
Ran 1 test in 0.515s

OK
```

harness 本身退出碼 0，stdout 含 11 行 `PASS bench injected-failure`（皆 `hits=1`）、2 行 `PASS bench success`、1 行 `PASS bench no-op`、`PASS actual Windows GDI count unchanged` 與 `PASS SVG ferror/fclose partial cleanup`。工作目錄留下 `complete.svg`（5280 bytes）。stderr 是注入失敗時 harness 自己印的資源取得失敗與釋放訊息，合約測試要求的是退出碼 0 與那些 PASS 行。

這次啟動沒有被應用程式控制原則擋住。上一份基準裡的 WinError 4551 仍是當時那支 exe 的紀錄，不能被這次結果改寫。真實視窗、`geometry-web` 與整套驗收沒有跑。
