# #348 完整 census 原輪超時，未產生有效 expected 更新

固定 execution **L `7c8e9cee4ed5b3706ee919e2831a1dac0aa55ea5`**。來源目錄 `/dev/shm/pr348-probe-source-7a0e6dd8`；執行前後 HEAD 相同且工作樹乾淨，產品／測試／帳本未改。

原命令：

```sh
ulimit -s 16384
python3 tests/run_all.py --build --update-expected
```

實際由已審 `native_recorder.py`（SHA256 `e1c1fd63bc58f8b7af1b6be28913b86e287101fc1cd3a8908f251bb33bb39445`）執行，原總守門 **2100 秒**。完整工具與引數見 `LAUNCHER.json`；沒有篩選套件、改時限、降低斷言或重跑取最好樣本。

## 真實終態

- 原程序 UTC **2026-10-29 16:54:59.491547–17:29:59.567513**；臺北時間 **2026-10-30 00:54:59–01:29:59**。
- 原程序 **returncode -9**；守門／recorder **exit 124**，`timed_out:true`。
- 原程序耗時 **2100.075953891 秒**；含自己的子程序清理 **2100.117344149 秒**，`cleanup_complete:true`。
- 最後啟動 **[107/243] `py:test_geo261_timber_capacity_host`**；原 unittest 部分日誌為七個 `.`，沒有完整 H7 JSON。後續 **136 套未開始**。
- 原完整 census 總結沒有產生。已完成的 **102 份 Python JSON**合計 **1523 passed／0 failed／1 skipped**，不是全 registry 總數；另四個非 Python suite 原 log 保存但不混入這個 Python 小計。唯一 skip 是原 Windows GDI harness 的 `test_confirmed_failures_release_real_resources`。
- `expected-before.json` 與 `expected-after.json` **逐 byte 相同**，SHA256 `e88f97a2c13e4ab561c071855ebf68f58bef5cec5d05ba20f453d58a23cf4209`。**沒有可採入的 expected diff**，不能手填未跑套件數。
- 原帳本前後 SHA256 都是 `812956bf480e74eda9e838e29f40f83a9cdd1f317e16e0432aaf539f33fcc569`。

本次是 **census 未完成／原總時間門檻紅**，不是完整 native 綠。先前獨立 H7 的綠燈仍保留其原 execution SHA，沒有移標到本次，也沒有拿它略過原 registry。

## 排程限制與可確定的時間事實

原 census 內 H7 `_unittest_runner` 的 `/proc` 起始時間約為 17:13:22.550 UTC；在它之前已用掉約 **1103.06 秒**，原總守門剩約 **996.94 秒**，且其後仍有 136 套。這說明必須處理整輪成本，不能只由獨立 H7 在 1200 秒內通過推論完整 native 35 分鐘可過。

父代理回報 R07 局部 browser 在 17:14:04.935–17:14:15.134 UTC 有約 **10.199 秒**與 census 內 H7 重疊，之後沒有再開重測。這項協調來源與限制保存在 `SCHEDULING-NOTE.json`。本輪 **不是獨占效能樣本**；也沒有證據把整個超時原因全推給這十秒。原獨占 H7 收據不變。

## 原件與保存

- 原 stdout／stderr 逐新增 bytes 即時複寫、fsync 到本 `/tmp` 目錄；終態與 SHM 原件逐 byte 相同，hash 見 `PROCESS.json`。
- `PROCESS.json`、`RESULT.json`、`process-events.jsonl`、前後 expected、binary metadata 與原工具均為原 bytes 副本。
- `prior-run-all-logs.tar`：102,400 bytes，SHA256 `af068459b83ed9acb9ec70d364faff8cc108e569b1d63e3bf65a33c638690173`。
- `actual-binaries-sidecars-logs.tar`：5,867,520 bytes，SHA256 `45d8650021db66415bf876ef4a1725ee3c2be5a1b0e67bd0d587b507e83070df`。包含實際六支 Linux binary、sidecar 與原 logs，連同原先留存的尚未覆寫 log 也保留，未將它們當成本輪新執行。每個檔案的 mtime／hash 見原 archive manifest。
- SHM 原件仍在 `/dev/shm/pr348-census-L7c8e9cee-20261029`；沒有刪除或重建原 archive。兩份 archive 已額外 copy2 到本目錄並核 hash，不是重新打包。
- `COMPLETED_PYTHON_RESULTS.json` 是依本輪起始時間選取的 102 份完整 JSON 內容及原檔 hash；完整原件同時在 archive。

結束後 heavy lock 已釋放；本代理沒有 push、修改 expected、啟動第二輪 census 或正式 native。下一步由 root 在保留本輪紅燈的前提下診斷整輪成本，再安排受影響修復與正式驗收。
