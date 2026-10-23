# binaries.OUT_DIR 衍生路徑窄靜審

固定來源 S=`3b0b634feb54266700cc61f26c34d7aeac4c0314`。只讀 source／AST，未 import 產品測試、編譯或建立 checkout。

`tests/binaries.py` 的 `OUT_DIR` 在 module import 時有預設值，但 `Binary` 在 REGISTRY 建立時只存 binary 名稱及編譯參數；沒有把當時 OUT_DIR 合成固定 path。`Binary.path`（:71–72）與 `Binary.sidecar`（:75–76）都是 `@property`，在使用時讀當前 OUT_DIR。

其餘衍生輸出位置均在呼叫時取值：`ProcessLock.__init__`（:146）、generated source（:471）、object/build script（:480/:489）、smoke（:517）、pending sidecar（:561）、build/CLI（:594/:686）。`Info` 會快取傳入或當下 binary.path，但沒有在 import-time 建立的 Info 實例；run_all 在 binding 之後才 build／inspect，故無舊目錄 Info。

一個需精確區分的 import-time cached constant 是 **`tests/run_all.py:42` 的 `LOG_DIR = binaries.OUT_DIR / 'run_all-logs'`**。v2 wrapper 已刻意依序 `import binaries; binaries.OUT_DIR=專有路徑; import run_all; run_all.main(...)`，所以此 cached constant 首次建立時也已是專有路徑。不能改成先 import run_all 再設 OUT_DIR；該順序已保存在完整 argv／binding 字串。

原 `_unittest_runner.py` 以另一程序啟動：原 `run_all.child_env` 傳入只含 fresh registry binary 的 `GEOMETRY_TEST_BRIDGE`；子程序 `_bridge._lookup` 先取此 explicit bridge，`binaries.inspect_one(..., path=value)` 對它的真 bytes／sidecar／source fingerprint 驗 fresh。子程序不需靠預設 `/tmp/geometry-tests` 找到本輪 bridge。若它不 fresh，原行為是 skip／環境紅，不會靜默採另一支舊 bridge。

W/H 的 `NativeBuild` 使用 `tempfile`，v2 的專有 TMPDIR 在 subprocess import tempfile 前已設定，故其隔離 kernel/wood/host copies 與 harness 在本輪 tmp。原 mutation runner 自己的 `_registry` 則在每次載入時先綁其傳入的 baseline／mutant／restored out，再 build/inspect；外部 `MUTATE_CACHE` 不共用 #323 的 cache。

結論限此已凍結 wrapper 順序：沒有已發現的舊 OUT_DIR 衍生 binary 路徑；run_all.LOG_DIR 的 import-time 特性已明確處理。正式執行仍需從原 stdout 的輸出目錄、原 source fingerprint、顯式 Node bridge 路徑與前後身份核實，這份靜審不能取代實證。
