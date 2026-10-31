# 不帶木工模板：候選對抗式靜態審查

本次只讀 `/workspace/kernel-no-wood-prep/candidate/test_rectangular_template.py.patch`、其完整候選檔，以及 `/workspace/kernel-no-wood-prep/run_proof.py`。未編譯、未執行測試、未取資源鎖，未修改對方檔案。候選尚未提交為最終產品 SHA，這不是正式驗收結論。

目前沒有找到可確立的阻擋缺陷。特別檢查下列可能假陽性：

- import 負控有建立真可匯入 sentinel package，且先要求不在 `sys.modules`；撤回精確 `geometry_woodworking` 阻擋後會讓該項正常 `assertRaises` 失敗，其餘名稱仍受原 blocker 保護，不靠套件不存在冒紅。
- K→W 負控引用隔離來源中真存在的 rectangular-template header，先編譯、連結並執行 exact-cells 成功，才跑原 source-isolation 裁判。這驗證的是 K 不得依賴任何 W template；不把缺 header／編譯失敗算成分層抓到。
- source gate 對相同實際 include 候選加 K 路徑閉包條件。嵌套命令固定只選一條原 source-isolation test，保存三態原輸出；修改發生在隔離安裝樹，`finally` 恢復原 bytes。
- 外層 driver 分開撤 import guard 與 layer guard，只接受正常 exit 1、`Ran 1 test`、`FAILED (failures=1)` 與對應正常 AssertionError 文字；拒絕 timeout、其他 returncode、unittest error、ImportError、SyntaxError。baseline 要求完整 13 tests 且無 skip。
- baseline 與 K-layer restored 再核對嵌套 source gate 的 0/1/0 及 mutant binary 真執行 exit 0，沒有只把外層 driver 自己成功當 mutation 被殺。
- driver 綁完整可解析 commit、逐檔 Git bytes/hash、工具 hash、環境與堆疊；每 phase 獨立來源樹，結束逐原輸入 bytes 核對，沒有產全域 mutation ledger。外部 override 明標 preflight，不冒 final-SHA 測試。

正式交付仍須取得不可變的產品提交、實際原始 streams／exit／hash 與兩種 guard 的 0/1/0，並核對更改後 registry 計數及 root 最終架構／帳本。尚未有這些原收據前，只能說候選靜態審查未發現 blocker。
