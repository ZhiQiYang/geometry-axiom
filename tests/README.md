# 核心與保存完整性測試

`run_tests.py` 驗證既有場景的接受／拒絕、尺寸與文字輸出。
`test_core_integrity.c` 驗證承載面重綁後的世界座標、Space 範圍、交易回滾及 undo/redo。
`test_bridge_integrity.py` 使用獨立 bridge 程序，驗證不完整指令、存檔重載、auto 支撐義務及所有接受型場景的幾何往返。

以下輸出目錄須先建立；執行測試時可在專案外工作，避免 SVG 測試產物覆寫工作中的圖。

Unix（gcc）：

```sh
mkdir -p /tmp/geometry-tests
gcc -std=c11 -O2 current_geometry.c -lm -o /tmp/geometry-tests/core
gcc -std=c11 -O2 geometry-web/web_bridge.c -lm -o /tmp/geometry-tests/bridge
gcc -std=c11 -O2 tests/test_core_integrity.c -lm -o /tmp/geometry-tests/integrity
/tmp/geometry-tests/integrity
python3 tests/run_tests.py /tmp/geometry-tests/core
GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge python3 tests/test_bridge_integrity.py
```

Windows（本工作樹；MSBuild `cl`）：

```bat
mkdir %TEMP%\geometry-tests
tests\_clw.bat current_geometry.c %TEMP%\geometry-tests\core.exe
tests\_clw.bat tests\test_core_integrity.c %TEMP%\geometry-tests\integrity.exe
cd geometry-web
build.bat
cd ..
%TEMP%\geometry-tests\integrity.exe
python tests\run_tests.py %TEMP%\geometry-tests\core.exe
set GEOMETRY_TEST_BRIDGE=%CD%\geometry-web\web_bridge.exe
python tests\test_bridge_integrity.py
```

記憶體／未定義行為驗證：將編譯選項換成
`-O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer`，重跑同一組測試。

Windows 可用現有 `tests/_clw.bat` 編譯 C 測試；bridge 依 `geometry-web/build.bat` 使用 `/U_WIN32`。
以環境變數 `GEOMETRY_TEST_BRIDGE` 指定剛編譯的 bridge，避免測到過時的 exe。

## 新公理與保存格式

2026-09-18 的 D6–D7 / I12–I13 已廢除自由座標、明寫角材長度與凍結保存。
`test_reference_contract.py` 驗證具名規格、有理引用、依賴重算、I8a 預覽／確認／取消、
過期預覽、奇數板縫、交易群組與引用往返。執行：

```sh
GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge python3 tests/test_reference_contract.py
```

新版 dump 只保存引用式與 `at-line` / `at-face`，並依依賴順序重放。
舊 `at` / `at-guides` / `at-grid` / `at-edge`、明寫 L、`grid-ref`、`span-auto` 都拒絕；
不能從已丟失來源的裸座標反推引用。專案內示例已改成新規格，故意測拒絕的夾具保留舊輸入。
完整語法與核對紀錄見 [公理實作核對](../geometry-core/README.md)。

## 其餘缺陷的回歸

bridge 測試另涵蓋 32 組樑中線／奇偶寬度的三次重載、面分類保存、失敗放置的草稿與 redo、拖曳群組及取消，以及數值上限。
幾何定義座標／尺寸限於 ±100,000,000 mm；ID 仍可用完整 uint32 範圍。
`geometry-web/cdp_test.js` 的 P24–P30 會實際點擊樑的套用、拖曳並復原／重做，以及在兩種視窗寬度開啟檔案選單並載入範例；也檢查外框／孔四種方向組合的淨面積。
可用 `GEOMETRY_REPAIR_SCREENSHOT_DIR` 指定這組互動的額外截圖目錄。
