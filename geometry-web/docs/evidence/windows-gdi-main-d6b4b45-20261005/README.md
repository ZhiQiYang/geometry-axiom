# Windows GDI harness 基準（目前 main）

被測完整 commit：`d6b4b450d741fcbbfd75c51631915d3082926990`

這是 2026-10-05 的 `origin/main`，主旨為 Merge pull request #133。本地 `main` 與 `origin/main` 相同。工作樹 `D:\geometry-axiom` 未被更新。

[PR #134](https://github.com/ZhiQiYang/geometry-axiom/pull/134) 仍是開啟中的草稿，head 為 `08b2ef79d060946495dc7bd848157d55af12543a`，`mergedAt` 為空。這份紀錄只對上面的 main SHA 負責。它不能當成 #134 已通過。#134 或任何後續整合版本都要用該次的完整 SHA 再跑同一支程式。

## 隔離

- 測試工作區：`D:\geometry-axiom-win-gdi`，由 `git worktree add --detach` 停在上述 SHA。
- 二進位目錄：`%LOCALAPPDATA%\Temp\geometry-win-gdi-d6b4b45\geometry-tests`。只對這個程序設定 `TEMP` 與 `TMP`。
- 沒有寫入 `D:\geometry-axiom`、`D:\geometry-axiom-qa`、其他 agent 的 worktree，也沒有重啟或改用他們的測試服務、bridge 或瀏覽器資料。
- 共用 `%TEMP%\geometry-tests\gdi-contract.exe`（2026-10-04，旁邊沒有 sidecar）沒有執行，也沒有覆寫。
- 只建置並執行註冊項 `gdi` / `tests/test_gdi_contract.py`。沒有跑 `tests/run_all.py`。

## 環境

| 項目 | 值 |
| --- | --- |
| Windows | NT 10.0.26200.0，顯示版本 25H2，組建 26200.9168 |
| Python | 3.14.4（tags/v3.14.4:23116f9，2026-04-07，MSC v.1944 64 bit AMD64） |
| 編譯器 | Microsoft C/C++ Optimizing Compiler 19.50.35730 for x64 |
| Visual Studio | Build Tools 18.5.11723.231 |
| vcvars | `C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat` |
| Node | 未使用 |

`cl` 不在一般 PATH。`tests/binaries.py` 用上面的 vcvars，沒有另外安裝或改系統設定。

## 實際命令與原始結果

以下命令的工作目錄都是 `D:\geometry-axiom-win-gdi`。`TEMP` 與 `TMP` 都指到 `%LOCALAPPDATA%\Temp\geometry-win-gdi-d6b4b45`。

### 1. 建置前狀態

```text
python tests/binaries.py status gdi
```

退出碼 1。

```text
輸出目錄：%LOCALAPPDATA%\Temp\geometry-win-gdi-d6b4b45\geometry-tests
gdi        MISSING  找不到 %LOCALAPPDATA%\Temp\geometry-win-gdi-d6b4b45\geometry-tests\gdi-contract.exe

1 支不是 fresh；修法：python tests/binaries.py build
```

### 2. 只建置 gdi harness

```text
python tests/binaries.py build gdi
```

退出碼 1。工具標成編譯失敗。

```text
  gdi：建置（找不到 %LOCALAPPDATA%\Temp\geometry-win-gdi-d6b4b45\geometry-tests\gdi-contract.exe）…
gdi        編譯失敗           無法建立可信 binary 記錄：binary changed before hashing
```

連結器已經寫出檔案：

- `%LOCALAPPDATA%\Temp\geometry-win-gdi-d6b4b45\geometry-tests\gdi-contract.exe`
- 大小 722432 bytes
- SHA-256 `a92e8d86d36e93f5de48f5eb8005efcf1ff717c213f7aa98b36339277387b0c9`
- 同目錄有 `obj\gdi\gdi_contract_harness.obj`（766366 bytes）
- 沒有 `gdi-contract.exe.fingerprint.json`，也沒有 pending sidecar

`tests/binaries.py` 的 `_binary_identity` 在雜湊前比較 `os.stat` 與開啟後的 `os.fstat`。兩者的 size、mtime、裝置與 inode 相同，`st_ctime_ns` 不同。對這支 exe 連續三次都是：

- `stat` 的 `st_ctime_ns`：`1791210473481475200`（與 `st_birthtime_ns` 相同，是建立時間）
- `fstat` 的 `st_ctime_ns`：`1791210473822497500`（與 mtime 相同）
- mtime 兩邊都是 `1791210473822497500`

同一個 Python 對一個 2-byte 中性檔（先寫入、等 1.1 秒再追加）也得到 `neutral_ctime_equal False`、`neutral_mtime_equal True`。`stat.st_ctime` 等於 birth time，`fstat.st_ctime` 等於 mtime，`fstat.st_birthtime` 仍是建立時間。因此這次失敗發生在 sidecar 核對，發生點是 `tests/binaries.py` 把這個 `OSError` 收成「編譯失敗」（約第 184–191 行與第 530–536 行）。`cl` 的產出還在。工具沒有走到它自己的 Smart App Control 重試。

### 3. 直接啟動該 exe

工作目錄放在隔離暫存。行程沒有建立，所以沒有程式退出碼。

```text
OSError
winerror 4551
errno 22
message [WinError 4551] 應用程式控制原則已封鎖此檔案。
```

### 4. 註冊的那一個測試程序

```text
$env:GEOMETRY_TEST_GDI_HARNESS = '%LOCALAPPDATA%\Temp\geometry-win-gdi-d6b4b45\geometry-tests\gdi-contract.exe'
python tests/test_gdi_contract.py
```

退出碼 1。

```text
E
======================================================================
ERROR: test_confirmed_failures_release_real_resources (__main__.GdiContract.test_confirmed_failures_release_real_resources)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\geometry-axiom-win-gdi\tests\test_gdi_contract.py", line 28, in test_confirmed_failures_release_real_resources
    harness = binaries.require_fresh('gdi', HARNESS)
  File "D:\geometry-axiom-win-gdi\tests\binaries.py", line 342, in require_fresh
    raise RuntimeError('%s 不是 fresh：%s（%s）' % (path, info.state, info.reason))
RuntimeError: ...\gdi-contract.exe 不是 fresh：stale（沒有 sidecar（這支 exe 不是 binaries.py 建的，來源是否相符無從證明））

----------------------------------------------------------------------
Ran 1 test in 0.383s

FAILED (errors=1)
```

`require_fresh` 在呼叫 harness 之前就中止。11 條注入失敗、GDI 物件計數與 SVG 清理都沒有執行。

## 通過、失敗、未執行

| 項目 | 結果 |
| --- | --- |
| `python tests/binaries.py status gdi` | 退出碼 1，MISSING |
| `python tests/binaries.py build gdi` | 退出碼 1；exe 已寫出；sidecar 沒寫成 |
| 直接啟動 `gdi-contract.exe` | WinError 4551，行程未啟動 |
| `tests/test_gdi_contract.py` | 退出碼 1；1 個 ERROR；0 個斷言失敗；0 個通過 |
| GDI 函式層斷言 | 未執行 |
| `AUDIT_DISABLE_FAILURES` 對照編譯 | 未執行 |
| `tests/run_all.py` 與其餘 suite | 未執行 |
| 真實 GDI 視窗操作 | 未執行 |
| PR #134 head `08b2ef79d060946495dc7bd848157d55af12543a` | 未執行 |

## 這支測試設計上保護的行為

來源是 `tests/gdi_contract_harness.c` 與 `tests/test_gdi_contract.py`。本次執行沒有走到這些斷言，所以下列行為在這個 SHA 上仍未由本機證明。

- `gdi_color`：11 個畸形字串得到 `RGB(0,0,0)`；`#aBcD09` 得到 `RGB(171,205,9)`；每個 `STYLE_SPEC` 的 line、fill、`gdi_fill` 都是 7 字元色碼且與 `gdi_color` 一致。
- `gdi_layout_input_bar`：假客戶區（0×0、1×1、15×5、100×20、175×33、1100×800）各呼叫 5 次 `MoveWindow`，座標與尺寸都不是負數。這裡的 `GetClientRect`、`GetDlgItem`、`MoveWindow` 是測試裡的替身。
- `bench_paint` 使用 `reference_default_world`：螢幕 DC 第 1 次、相容 DC 第 1–3 次、點陣圖第 1–3 次、`SelectObject` 第 1–3 次、`QueryPerformanceFrequency` 第 1 次，共 11 次注入失敗，每次 `hits=1`，結束時螢幕 DC、記憶體 DC、點陣圖計數與刪除失敗都是 0。另有 2 次成功繪製（2 次與 10 次迴圈）與 1 次 0 迴圈 no-op。失敗序列前後的 `GetGuiResources(GR_GDIOBJECTS)` 必須相同。
- `emit_svg_three_views`：強制 `ferror` 與強制 `fclose` 都拒絕寫出並刪除半成品；正常寫出留下根節點為 SVG 的 `complete.svg`；Windows `NUL` 不會被交給 `remove`。

## 這次沒有覆蓋的 Windows 使用流程

- 真實視窗 `gdi_show_three_views`、訊息迴圈、關閉或 Esc。
- 選單、開啟場景對話框（`comdlg32`）、滑鼠按下／移動／放開、編輯模式、狀態列與懸停文字、點選描述。
- 真實視窗的 DPI、多螢幕與互動縮放。版面檢查用的是假客戶區。
- `geometry-web` 與 `web_bridge`。它們以 `/U_WIN32` 編譯，不包含這段 GDI。
- 無視窗 `core.exe` 的命令列流程。
- 使用者在桌面視窗開檔、作圖、復原、存檔。
- 預設世界以外的場景。
- 測試檔頭寫的 `AUDIT_DISABLE_FAILURES` 敏感度對照。
- PR #134 的規則線顯示。

## 最小重現

1. 確認 `git rev-parse origin/main` 是 `d6b4b450d741fcbbfd75c51631915d3082926990`。
2. 在獨立 worktree 把 `TEMP` 與 `TMP` 指到空的私人目錄。
3. 執行 `python tests/binaries.py build gdi`。目前會以退出碼 1 結束，訊息是 `binary changed before hashing`，同時留下沒有 sidecar 的 exe。
4. 啟動該 exe。目前回 `[WinError 4551] 應用程式控制原則已封鎖此檔案。`
5. 把 `GEOMETRY_TEST_GDI_HARNESS` 指到該 exe，執行 `python tests/test_gdi_contract.py`。目前在 `require_fresh` 產生 1 個 ERROR，退出碼 1。

不要手寫 sidecar、不要把新 exe 蓋到舊路徑、不要改測試或降低門檻來得到通過。下一份整合 SHA 要整段重跑。
