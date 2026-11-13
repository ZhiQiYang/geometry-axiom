# 本次執行結果

所有數字都是測試斷言，不能相加當作使用者流程數。失敗／中斷的嘗試保留在表中。

| 執行 | 範圍 | 完成 | 通過 | 失敗 |
|---|---|---:|---:|---:|
| [cdp-native.log](cdp-native.log) | full | 是 | 2207 | 0 |
| [cdp-wsl.log](cdp-wsl.log) | full | **否** | 19 | 7 |
| [cdp.log](cdp.log) | full | **否** | 49 | 1 |
| [infinite-face.log](infinite-face.log) | GEOMETRY_INFINITE_FACE_ONLY | 是 | 9 | 0 |
| [space-async.log](space-async.log) | GEOMETRY_ASYNC_REPLY_ONLY | 是 | 12 | 0 |
| [space-history.log](space-history.log) | GEOMETRY_TIMBER_GUARDS_ONLY, GEOMETRY_TIMBER_HISTORY_ONLY | 是 | 9 | 0 |
| [space-save-native.log](space-save-native.log) | GEOMETRY_SAVE_REOPEN_ONLY | **否** | 7 | 2 |
| [space-save.log](space-save.log) | GEOMETRY_SAVE_REOPEN_ONLY | **否** | 7 | 2 |
| [space-timber.log](space-timber.log) | GEOMETRY_TIMBER_ONLY | 是 | 79 | 0 |
| [space.log](space.log) | full-space-suite | 是 | 242 | 0 |
| [section.log](section.log) | 斷面桌面＋手機完整驗收 | **否** | 22 | 1 |
| [section-retry.log](section-retry.log) | 斷面桌面＋手機完整驗收 | **否** | 22 | 1 |
| [section-diagnostic.log](section-diagnostic.log) | 斷面桌面＋手機完整驗收 | **否** | 22 | 1 |

## 解讀界限

- `cdp.log`：Windows＋WSL bridge 的固定等待在六面建立尚未完成時取樣；不以此判定六面功能失敗。
- `cdp-wsl.log`：WSL 服務多次 API 逾時，未完成；不作全套通過證據。
- `cdp-native.log`：本機 MSVC 新編 bridge／model-base；各 section 收據見下。
- 主回歸收據的 1 筆瀏覽器例外是 P38 刻意觸發的 `fb-auto-probe`；log 標為 EXPECTED EXCEPTION，並通過自動回報驗收。
- 空間 full suite 與角材、歷史、延遲回應專項為不同 scope，部分 setup／字級檢查重複。
- `infinite-face.log` 的 9 項也包含於主回歸 P71（網格套件間接呼叫）；獨立重跑屬重複驗證，不另算新增覆蓋。
- 保存重開兩次在找子線時中斷，沒有完成保存重開階段，不能解讀成資料丟失。
- 斷面完整驗收在桌面歷史後的更新 3D 中斷；後續手機與完整 .gcanvas 驗收未執行。
- 斷面測試使用實際下載 fallback，原生 OS 保存對話框被測試明確停用；不構成原生檔案視窗驗收。
- Native build 成功，見 [native-build.log](native-build.log)；不是沿用舊二進位。
- 人工 `.scene` 下載與當下 dump 逐字一致，見 [manual-export-check.json](manual-export-check.json)。

## 全套 CDP 的 section 收據

| Section | 通過 | 失敗 |
|---|---:|---:|
| 1 | 14 | 0 |
| 2 | 3 | 0 |
| 3 | 1 | 0 |
| 4 | 1 | 0 |
| 5 | 1 | 0 |
| 6 | 1 | 0 |
| 7 | 1 | 0 |
| 8 | 0 | 0 |
| 9 | 12 | 0 |
| 10 | 0 | 0 |
| Setup | 0 | 0 |
| P3 | 14 | 0 |
| P4 | 11 | 0 |
| P5 | 2 | 0 |
| P6 | 4 | 0 |
| P7 | 54 | 0 |
| P8 | 116 | 0 |
| P9 | 9 | 0 |
| P10 | 9 | 0 |
| P11 | 12 | 0 |
| P12 | 8 | 0 |
| P13 | 4 | 0 |
| P14 | 16 | 0 |
| P15 | 6 | 0 |
| P16 | 10 | 0 |
| P17 | 11 | 0 |
| P18 | 20 | 0 |
| P19 | 17 | 0 |
| BF2 | 5 | 0 |
| BF3 | 1 | 0 |
| BF4 | 9 | 0 |
| P20 | 10 | 0 |
| P21 | 4 | 0 |
| P22 | 45 | 0 |
| P32 | 34 | 0 |
| P33 | 9 | 0 |
| P34 | 7 | 0 |
| P35 | 14 | 0 |
| P36 | 2 | 0 |
| P37 | 19 | 0 |
| P38 | 13 | 0 |
| P39 | 8 | 0 |
| P40 | 4 | 0 |
| P41 | 3 | 0 |
| P42 | 12 | 0 |
| P43 | 12 | 0 |
| P44 | 19 | 0 |
| P45 | 2 | 0 |
| P46 | 7 | 0 |
| P47 | 9 | 0 |
| P48 | 14 | 0 |
| P49 | 17 | 0 |
| P50 | 33 | 0 |
| P51 | 13 | 0 |
| P52 | 43 | 0 |
| P53 | 28 | 0 |
| P57 | 56 | 0 |
| P62 | 38 | 0 |
| P63 | 18 | 0 |
| P64 | 24 | 0 |
| P65 | 5 | 0 |
| P66 | 4 | 0 |
| P68 | 36 | 0 |
| P69 | 160 | 0 |
| P67 | 96 | 0 |
| P70 | 117 | 0 |
| P71 | 9 | 0 |
| P78 | 23 | 0 |
| P87 | 60 | 0 |
| P88 | 137 | 0 |
| P72 | 52 | 0 |
| P73 | 69 | 0 |
| P74 | 52 | 0 |
| P75 | 37 | 0 |
| P76 | 87 | 0 |
| P77 | 134 | 0 |
| P82 | 16 | 0 |
| P80 | 23 | 0 |
| P81 | 14 | 0 |
| P85 | 31 | 0 |
| P79 | 87 | 0 |
| P84 | 33 | 0 |
| P83 | 16 | 0 |
| P86 | 20 | 0 |

```json
"matched"
```

完整機器收據：[receipts.json](receipts.json)。
