# GEO-261 來源圖索引驗收（2026-10-20）

量測與測試的產品 commit：`0636a0867556cf5ade397e995b5a93f53fba7a4b`。
後續 commit 只收錄本目錄的驗收證據；產品碼與已測版本相同。

- base：`3e600772076465fc65a26ac09055028301c0fb0b`
- main：`adbaebf9c73ea6801d7b4d5214e4b846b132923b`
- 環境：Linux x86_64，Intel Xeon Platinum 8573C，GCC 14.2.0，stack 16 MiB。
- 時間採 `perf_counter`，包含 bridge 行程啟停及 `loadfile`；效能樣本不含 `dump`，每次新建 bridge 行程。
- 量測時沒有並行執行測試或其他建置；三版本每輪輪換順序，各取三次中位數，所有樣本均保留。

詳細語意說明、A–D 的指令／結束碼／輸出摘要、效能表、突變結果與最不確定處，見 [PR 正文](PR.md)。

| 證據 | 內容 |
|---|---|
| [measure.py](measure.py)、[mini_gen.py](mini_gen.py) | 可重跑的 A／B 腳本與任務提供的產生器 |
| [measurements.json](measurements.json) | 三版本編譯指令／SHA、八次等價性 stdout 指紋、36 次原始效能樣本、各次結束碼與輸出 |
| [measure.log](measure.log) | A／B 執行輸出；整支腳本結束碼 0 |
| [commands.json](commands.json) | 其餘驗收命令、工作目錄、結束碼與耗時；執行前設定 stack 16 MiB |
| [required.log](required.log) | 指定 7 個 suite：655／655 通過，結束碼 0 |
| [source-index.log](source-index.log) | 新測試 7／7 通過；包含兩個結束碼 1 的重複斷言突變 |
| `sanitizer-*.log` | ASan／UBSan 編譯與五組案例，全部結束碼 0，沒有 sanitizer 診斷 |
| [architecture-base.log](architecture-base.log)、[architecture-fix.log](architecture-fix.log) | 皆結束碼 1；`cmp` 結束碼 0、輸出空，只有同一個既有未登記來源診斷 |
| [gprof-summary.log](gprof-summary.log)、[profile-load.log](profile-load.log) | 新版 N=48 profile；編譯、載入、gprof 結束碼皆 0 |
| [full.log](full.log) | 完整非瀏覽器 suite 輸出；結果與限制見 PR 正文 |
| [mutation-base.log](mutation-base.log)、[mutation-fix.log](mutation-fix.log) | 只讀帳本檢查皆結束碼 1；base 18 筆 stale、fix 75 筆 stale，未重產帳本 |

重跑 A／B（請在沒有其他測試或建置執行時量測）：

```sh
git worktree add --detach /tmp/geo261-source-base 3e600772076465fc65a26ac09055028301c0fb0b
git worktree add --detach /tmp/geo261-source-main adbaebf9c73ea6801d7b4d5214e4b846b132923b
python3 -u tests/evidence/geo261-source-index-20261020/measure.py \
  /tmp/geo261-source-base "$PWD" /tmp/geo261-source-main /tmp/geo261-source-measure
```

重跑 sanitizer：

```sh
mkdir -p /tmp/geo261-source-checks
gcc -std=c11 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -I geometry-core/kernel tests/geo261_source_index_harness.c \
  -o /tmp/geo261-source-checks/source-index-sanitized
for case in nodes edges allocation growth statuses; do
  ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 \
    /tmp/geo261-source-checks/source-index-sanitized "$case"
done
```

建立指定 base 的 draft PR（需可用的 GitHub API 連線與認證）：

```sh
gh pr create --draft --repo ZhiQiYang/geometry-axiom \
  --base architecture/geo261-integration-20261016 \
  --head codex/geo261-source-index-20261020 \
  --title '修正 GEO-261 來源圖線性搜尋造成的場景載入退化' \
  --body-file tests/evidence/geo261-source-index-20261020/PR.md
```
