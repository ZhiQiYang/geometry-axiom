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

## 審查後的同一分支修正

上面的修前失敗紀錄與當時的 30 項結果保留。這一節只記後續審查要求的兩項。

穩定檔測試不再讀取 `st_birthtime_ns`，也不再要求 `stat` 與 `fstat` 的 `st_ctime` 必須不同。缺這個屬性時，Windows 簽名改回 `st_ctime`；其他平台即使物件帶有 birth time 仍使用 `st_ctime`。這段 fallback 用沒有該屬性的記憶體物件覆蓋，沒有拿舊版 Python 實機跑。

同 inode、同尺寸、改內容、再把 mtime 設回去的中性檔，在只比 birth 的版本上實測如下。開啟當下 `stat().st_ctime` 已與 `fstat().st_ctime` 不同；改寫並還原 mtime 之後，inode、size、mtime、birth、`stat().st_ctime` 都沒變，`fstat().st_ctime` 有變。當時函式回傳改寫前內容的 SHA-256 `9f9f5111f7b27a781f1f1ddde5ebc2dd2b796bfc7365c9c28b548e564176929f`，與新內容不同。

舊的跨 API `st_ctime` 在這個檔案開啟時就已經不相等，所以舊碼到不了雜湊中的檢查，它是在開啟時誤拒，不是靠雜湊中的 change time 抓到這次改寫。birth 跨 API 比對拿掉了 `fstat` 自己那次會移動的 `st_ctime`。後續修正把雜湊中的檢查改成兩次 `fstat` 互比，包含該次的 `st_ctime`。跨 API 仍只比雙方都有的時鐘，避免穩定檔在開啟時被誤拒。

修正後的 `python tests/test_binaries.py`：32 個測試。第一次有 1 個失敗，`test_fresh_reuses_without_compile_smoke_or_metadata_write` 的 `st_atime` 差了 1 秒，mtime、ctime 與 sidecar bytes 沒變；立刻重跑 32 項退出碼 0，耗時 2.773 秒。同尺寸案例在重跑中被拒，訊息是 `binary changed during hashing`，而且拒絕之後跨 API 簽名仍與改寫前相同。

這不表示所有競態保護都與改前完全相同。開啟後的 `fstat` 若看不到 `st_ctime`、mtime、size、inode 或 birth 的差異，雜湊仍可能返回已經讀到的 bytes。這次實測的同尺寸改寫有留下 `fstat().st_ctime` 差異，所以被拒絕。

同一支已建好的 GDI harness（SHA-256 `de7dec1737e2d658dff1a7dcc7b8c2246254b586efd2efa816be07d4cf869676`）再用新核對跑 `python tests/test_gdi_contract.py`，退出碼 0，1 個測試，1.108 秒。沒有重編，也沒有改 Windows 安全設定。整套 `run_all.py`、真實視窗、PR #134，以及沒有 `st_birthtime_ns` 的舊版 Windows Python 都沒有實機跑。

## 雲端接續：兩項測試斷言的可移植性

精確修前 head `d9eea1ca5860bc4d7a06a40b75147024d7f68d4b` 在 Linux／Python 3.12.14 首次跑 `python3 tests/test_binaries.py -v` 是 31 pass／1 fail、exit 1。失敗在同尺寸改寫測試的事後完整 signature 相等斷言：函式已以 `binary changed during hashing` 拒絕，inode／size／mtime 核對也通過；Linux signature 正確包含已改變的 ctime，所以最後相等斷言不成立。這個首次失敗收據保留，沒有用重跑覆寫。

接續修正只改 `tests/test_binaries.py` 的兩項 oracle：同尺寸改寫仍在所有平台檢查拒絕、device／inode／size／restored mtime 與 bytes 確有修改；完整 signature 不變只在 Windows 且實際有整數 `st_birthtime_ns` 時核對。fresh reuse 的快照只排除 OS 讀取可更新的 `st_atime`／`st_atime_ns`，其餘可用的 `st_*` metadata（包括 ns 欄位）仍逐項保存；另外明確核 binary 與 sidecar 原始 bytes，保留 `reused` 與 compile／smoke 各只呼叫一次。沒有修改 `tests/binaries.py` 的 fresh／mtime／ctime／SHA-256 防線，沒有改 OS atime 設定或 Windows 安全策略。

Linux 修後首次 `python3 tests/test_binaries.py -v` 是 32/32、exit 0；`python3 tests/test_mutation_freshness.py -v` 是 24/24、exit 0。原 27 項與預期數 32 都保留，沒有新增或刪除 suite，也沒有 sleep／重試到綠。另以中性 fixture 的真 Linux 讀取更新 atime，修後的同一 reuse 測試仍通過，mtime／ctime／inode／size、sidecar bytes 與 compile／smoke 核對不變。

正式非瀏覽器 aggregate 沿 `ulimit -s 16384` 加 `python3 tests/run_all.py --build` 在凍結提交執行，實際命令／head／exit／逐 suite output 由本輪獨立雲端收據交付。這一節的 Linux 結果不替代 Windows／GDI 實測，也不外推到 PR #134／#137、瀏覽器或真實視窗；上面的作者 Windows 首次失敗與重跑紀錄維持原義。
