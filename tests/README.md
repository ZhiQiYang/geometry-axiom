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

## 保存格式相容性

非網格錨定的 auto 角材匯出為已凍結的尺寸及位置，全部 `place` 之後另有 `span-auto 角材id`。
此標記只恢復兩端仍須有合法支撐的義務，不重新計算尺寸或錨點。網格角材的 `grid-ref` 已保存這項義務。

新版繼續接受既有 DSL 語法（數值須符合下方支援範圍）；舊版程式無法讀取新增加的 `span-auto` 指令。
舊版曾匯出且已遺失 auto 模式的檔案，無法僅從明寫長度可靠推回原本的模式；須從原始 auto 場景重新匯出。

## 其餘缺陷的回歸

bridge 測試另涵蓋 32 組樑中線／奇偶寬度的三次重載、面分類保存、失敗放置的草稿與 redo、拖曳群組及取消，以及數值上限。
幾何定義座標／尺寸限於 ±100,000,000 mm；ID 仍可用完整 uint32 範圍。
`geometry-web/cdp_test.js` 的 P24–P30 會實際點擊樑的套用、拖曳並復原／重做，以及在兩種視窗寬度開啟檔案選單並載入範例；也檢查外框／孔四種方向組合的淨面積。
可用 `GEOMETRY_REPAIR_SCREENSHOT_DIR` 指定這組互動的額外截圖目錄。
