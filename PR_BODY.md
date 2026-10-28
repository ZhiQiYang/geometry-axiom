R02 UI-1 把既有完成面／鋪排原生能力接到 App 的面內屬性檢查器：以「面設定…」整合投影與「完成面與鋪排…」，保留依平面建立空間；表單只組定義，幾何由原生推導。採用 [#128 介面 A](https://github.com/ZhiQiYang/geometry-axiom/issues/128#issuecomment-6436162095) 與[完整契約](https://github.com/ZhiQiYang/geometry-axiom/issues/128#issuecomment-6435620807)。

**Draft／未達合併條件。** #343 → #346 → #347 尚未同源閉合，UI15 未跑；本 PR 不宣稱 PF-6／PF-4／PF-5 或整體 R02 已完成，`complete:false` 保持不變。

## 唯一 current-state 矩陣（持續驗收中）

- 目前 head：`0ee42a58953292523894740a6cb3b22cb6a5c47b`。
- 基底：`405f8c5e1a637a16cbe47470faf5ae1fa02b8676`。
- 原生初輪執行 SHA：`1b63a0498bf941da5b83866d7234afb25d7aefb4`；不是上述 head 的完整驗收。
- 純保存候選執行 SHA：`037bda6abb2dba1c91388c1ae6eb03f675ac1aab`。
- 進度：[PROGRESS.md](evidence/r02-ui1-20261028/PROGRESS.md)。

| 案例 | 實際狀態 |
|---|---|
| UI01 入口／減項 | 接線已實作；真 UI 尚未完成 |
| UI02 明選來源 | 表單已實作；真 UI 尚未完成 |
| UI03 精確值 | 初輪 native 契約 8 項 exit 0；新增 X 有理數與真 UI 待驗 |
| UI04 結果誠實 | 原生既有四套 92 項 exit 0；真 UI 待驗 |
| UI05 生命週期 | 共用回執與 generation 已接；真 UI 待驗 |
| UI06 no-op／原子性 | 保存單元已跑；真 UI 待驗 |
| UI11 保存重開 | scoped definition reader 與 /19 已接；fresh profile 待驗 |
| UI12 390／720／1280、焦點／Esc／IME | 未完成；不以 CDP 冒稱實體 IME／觸控 |
| UI13 真入口及三項撤線 | 測試工具已實作；尚未跑到三項反證 |
| UI14 分片能力 | 有限 supportedActions 已接；真 UI 待驗 |
| UI15 同源整合 | 未跑，#343 → #346 → #347 尚未閉合 |

已執行命令（16 MiB stack；完整原件會隨後續 evidence 提交）：

- `python3 tests/binaries.py build bridge core model-base`：exit 0。
- `GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge python3 -B tests/test_panel_fill_ui_contract.py`：初輪 8 項、0 fail／0 skip，exit 0。
- `GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge python3 -B -m unittest tests.test_panel_fill_finish_surface tests.test_panel_fill_layout tests.test_panel_fill_host tests.test_panel_fill_support`：92 項、0 fail／0 skip，exit 0。
- 保存候選的 9 套單元／相容回歸：105 pass、0 fail、24 個缺 native fixture 的原有 skip，exit 0；不能當原生或真 UI 通過。四個保存守門撤回各 exit 1，恢復 exit 0。
- `python3 -B tests/mutate.py --check`：exit 1，75 stale／3 retired；帳本尚待最終來源重產。
- `GEOMETRY_PANEL_FILL_ONLY=1 node geometry-web/cdp_test.js`：第一輪 Chrome 啟動環境失敗，exit 1、0 斷言；保留原紅燈，正在修復執行環境，不能稱產品通過。

CI 曾受帳號計費阻擋；本 PR 的遠端 CI 目前未取得可核實執行結果，不以無 runner／steps 的 failure 判產品紅綠。本機 Claude 的 WSL native、canvas、grid、space 等相關 job 亦尚未收到，不列已過。

本片未改公理、正典閱讀器或決策佇列；三份允許文件只增設計擬補文字。PF-bearing scenario leaf 仍 fail closed，尚不宣稱該組合可用。未修改 #352／#353／#354 分支，不合併 main。
