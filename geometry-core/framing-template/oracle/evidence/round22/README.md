# 第 22 輪原始碼突變收據(綁定 1126991c)

審查 <https://github.com/ZhiQiYang/geometry-axiom/pull/251#issuecomment-6332818768> 要的 159 處原始碼突變收據。來源是本機 `D:\geometry-axiom-work\framing-oracle-gaps\round22\`,本輪核對 blob 後收進來,**沒有重跑**這 159 處。

## 綁定

命令檔 `srcmut-cmd.txt` 寫的 SHA 是 `1126991c9dbd3de92d8cce6eab2419f8f7970e34`。`run10.py` 拷貝的是 `final\tree-1126991c\geometry-core\framing-template\oracle\`。該目錄九個 oracle 檔與 `git cat-file blob 1126991c:<path>` 逐位元組相同(git blob SHA-1):

- `README.md` blob `ebe23fd46e6e8cb68fb16689369d4f3efad3cbd1` bytes 93270
- `framing_oracle.py` blob `47b33182e9ed5a80ddd559dde94a7d8f976aebe9` bytes 132179
- `make_golden.py` blob `8edc3eb16cb06ad33039d9ed251b4d74e57ea32c` bytes 3307
- `oracle-golden.json` blob `3321ed75e0ca79f316d5a6010febe707683ddc12` bytes 355766
- `quote_check.py` blob `a0fa93ea58ec9e397444c45e8b819573b2ff22c0` bytes 25787
- `render.py` blob `bb4a11573a21b7ae09f5e5de88fbd2696cc222fb` bytes 8874
- `rooms.json` blob `7ab8dfa2f35c0b78a1037ecf44c9db8dc3d6e4cf` bytes 699
- `selftest.py` blob `aca8cfc9f6ea5d6d028772e24e52e76cc5b0ccfe` bytes 131054
- `sweep-expected-unbuildable.json` blob `913772d5875526be7c84f9911fd2fe6d175bbd1b` bytes 134591

`9b04a3c8` 那份部分副本的 README 與 `framing_oracle.py` 雜湊不同,而且沒有 `render.py`。它不是這份收據,沒有收進來。

## 命令與結束碼

`srcmut-cmd.txt`:

```
sha 1126991c9dbd3de92d8cce6eab2419f8f7970e34
cmd: python -B run10.py <tree-1126991c 的 oracle 目錄> <final\srcmut>
SHARD 0/1, BelowNormal, sequential
start 2026-10-20T09:55:22Z
end 2026-10-20T12:19:10Z
```

每一處在副本裡要求舊字串出現剛好一次,然後跑 `python -B selftest.py --mutants-only`。日誌沒有「原始碼對不上」。

`run10.py` 印到標準輸出的內容,是這份日誌的 CRLF 版,最後多一行 `exit 0 seconds 8627`。收進 repo 的是驅動器寫下的 LF 日誌 `source-mutants.0of1.txt`(SHA-256 `6ddc819e4c446b44aa41783d43e3d0db1f959c0e38fdfb5290970c90449b8681`,289871 bytes)。

引文突變讀的佇列是當時工作樹的 `決策佇列.md`。`final\srcmut\queue_0of1.md` 與 `1126991c:決策佇列.md` 逐位元組相同(SHA-256 `c3387507597afafbdf1962b5374d5cfd8187165e6638b7b33c92bb3f794d9f72`,220461 bytes),所以不另存一份。

## 原始統計

159 處,標題 159 個、互不重複。結束碼:exit 1 共 156 處,exit 0 共 3 處。逐處結束碼與轉紅行數在 `tally.txt`。

exit 1 且轉紅行數是 0 的只有 `X3_no_wall_on_seam_probe`:日誌寫明是 selftest 當掉(沒有斷言轉紅),不是存活。

## 三處 exit 0 的判讀

原始日誌只記 `exit 0; 轉紅的行 0`,沒有寫判讀。下面是本輪對 `1126991c` 原始碼的判讀,沒有重跑那 159 處。

### T2_check_no_noncandidate

改動:`framing_oracle.py` 的 `if dc not in cset:` 改成 `if False:`。

等價。證明沿用 oracle `README.md` 第 20 輪(第 21 輪寫明這一段沒有再動;1126991c 的 `_p182_audit` 仍是 `dc not in cset` 就回 `C7_P182_NOT_CANDIDATE` 並 return):拿掉這一條之後,若結果縫位 `dc` 不在候選集合,後面仍會報錯。trace 有選中時,`dc` 不等於 chosen、或不在 trace、或 trace 判失敗,報 `C7_P182_CHOSE_FAILED`;否則 `dc` 在 trace 裡,trace 試過的每一個都要屬於候選集合,不屬於就報 `C7_P182_NOT_CANDIDATE`。trace 說都不可行時,`dc` 必須等於原縫位 `d0`,而 `d0` 屬於候選集合,所以 `dc` 不屬於時 `dc != d0`,報 `C7_P182_CHOSE_FAILED`。有沒有問題的判定不變,報出的碼可能不同。

### G2_reflex_wall_line_wrong_side

改動:`into = 0.5 if plus else -0.5` 改成 `into = -0.5 if plus else 0.5`(牆線探測從室內側 0.5 mm 改到另一側)。

本輪另拿 1126991c 的 `framing_oracle.py`,只翻這一處,對 COLSTEP(3000)、COLSTEP(2900)、FZ9、STEP20、FZ145 各 8 個排法比對判定、衝突碼、核心限制 `(code, id, end)` 與角材矩形,40 組全部相同。G1 拿掉整段牆線凹角時,同一批 COLSTEP(3000) 與 FZ9 在原始日誌裡是轉紅的,所以這不是「測試沒跑到這些房間」。

幾何理由:這條分支要補的是料帶越不過、牆線延長之後兩側都還在室內的凹角。例:y=3661 的牆在 x=3000 結束,x=2999.5 上 y=3660.5 與 y=3661.5 都在室內,正負 0.5 mm 都判 inside,符號不改變 `ends`。料帶已經認出的凹角會先放進 `ends`,這一行不被用來決定。

這份判讀沒有對掃描裡的每一間房證明「沒有任何一間只在一側為室內」。那是這裡最弱的地方。原始日誌對這 159 處的 `--mutants-only` 是 exit 0。

### C4_sweep_inconsistent_ignored

改動:`selftest.py` 的 `sweep_family` 裡 `elif v_ != "buildable":` 改成 `elif False:`,不再把 inconsistent 放進問題清單。

這不是語意等價。`--mutants-only` 走到的 `sweep_family` 沒有產生 inconsistent,這條分支是死路,所以 exit 0、轉紅 0。拿掉它只證明這次跑的樣本裡沒有 inconsistent,不證明以後出現 inconsistent 仍會被抓到。本輪沒有另加對照把 C4 殺掉。

## 其他檔

- `run10.py.txt`、`make_run10.py.txt`:突變清單與每一處 `(舊字串, 新字串)`。腳本改存成 `.py.txt`。`make_run10.py` 是從第 21 輪 `run9.py` 產生 `run10.py` 的產生器,不是 1126991c 那次執行本身。
- `expected-spotcheck.txt`:README 說的 8 筆抽查(四族原房與鏡像各一)。SHA-256 `aadcb461b6c5089d1fccae885415e3607b369cd5776e4d35c6aae9fee5e06365`。本輪沒有重算這 8 筆。
- 原生探針與 `core-probe-1126991c` 的輸出沒有收進來。ChatGPT 已在 Linux 跑過,本輪未重跑。
