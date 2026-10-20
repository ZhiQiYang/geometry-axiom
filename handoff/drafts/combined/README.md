# #299 + #316 合併版補丁

`patch.diff` = `../issue299/patch.diff` 與 `../issue316/patch.diff` 的合併（17 個檔案），基底 `09ab5f79`。
這兩個單獨補丁**不能先後套用**（`contact_world.h`、`run_tests.py`、`test_geo261_mutation_migration.py`、`test_geo261_wood_contact_world.py` 四個檔案互相擋，暫時索引實測）；要兩個都要，就只套這一份。兩個單獨補丁各自單套都可以。

為什麼合在一起：兩邊都動到 `current_geometry.c` 的 include 閉包與 `tests/run_tests.py`／`tests/mutate.py`，整份突變帳本（約 2 小時）和讀者追溯區塊都要重產，一次做完最省。

## 合併版驗證（靜態，沒有建置）

- 暫時索引 `git read-tree 09ab5f79` + `git apply --check --cached patch.diff`：通過；真套後 17 個 blob 與預期逐位元相同。
- 合併後的互相一致處已逐項核對：突變 88 個編號（50 + 38）、`TESTS` 166 = `run_all.expected.json`、`test_geo261_wood_contact_world.py` 測試方法 9 = 期望值、控制項 18／23／12。
- 其他草稿（`../issue300`、`../issue314`）先套再套本檔：`git apply --check` 通過（沒看語意衝突）。

## 重新產生／重驗

`../_gen/` 放了產生器與檢查腳本：`fetch_base.sh` 取基底檔案、`build.py` 重新產生三份補丁（#299、#316、合併）、`checks.py` 做靜態一致性檢查、`reader_impact.py` 算讀者追溯變動、`verify_all.sh` 全跑一遍。GEO-261 合入 main 後基底變了，改 `BASE_REV` 重跑即可；錨點對不上時 `build.py` 會直接報是哪個檔案哪一段。
