【dot】

Documents job 的 checkout 會取回它不使用的根 `evidence/` 歷史 payload。本變更只讓 `matrix.suite == 'documents'` 使用 `blob:none` 與 non-cone sparse checkout（`/*`、`!/evidence/`）；其他 browser、native、#366 checkout 與 helper 均維持原樣。

| 身份 | 固定完整 SHA |
|---|---|
| 本 PR source U | `b2432c9ea79a6927675883ddde04f629b159be2d` |
| 本輪真 CI synthetic execution | `310bebb505ea04309634279b7025c1849a35d88d`；tree 與 U 完全相同 |
| 本輪 execution 的 main baseline／U sole parent | `e02057b4c725d6f03ae52c3bc30776bf9442b0cf` |
| 後來的 main（#359 R08） | `fca3f1a80f1dab564f5dd4c01c9e1226eaf09e2d`；未合入 U，也未由本輪執行驗證 |
| 固定證據 E | `59f2cac42862dec39a5d0216b4e1bff0f4b0ccc9` |

唯一 source 變更是 `.github/workflows/integration-tests.yml` 的兩個互斥 checkout step。原 action pin 與兩者 `persist-credentials: false` 保留；documents whole-job 仍為 **10 分鐘**，其他 suite 的時限、原 build／fonts／runtime／browser／upload 命令、matrix、permissions、credentials、assertions、golden、expected 與 skip／freshness policy 全部未改。

`tests/evidence`、`tests/release-evidence`、`geometry-core/domain-decoupling/evidence` 與其他 nested evidence 仍保留。靜態依賴審查涵蓋原47個嚴格 check、55-file local require 保守閉包、740 runtime sources、351 static routes／8 catalog routes，以及三個 native 各195 inputs；未找到本輪固定 documents 流程需要的 root evidence leaf。新 main 的29個 changed leaves 另作有界靜態檢查，未發現新增 root evidence 檔案依賴；這只界定 checkout 輸入保全，不能代替 R08 的 runtime 驗證。

[原 CI run 41447885087／attempt 1](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41447885087) 已 completed success，10／10真 jobs 全綠。固定 E 的 [FINAL_ACCEPTANCE.json](https://github.com/ZhiQiYang/geometry-axiom/blob/59f2cac42862dec39a5d0216b4e1bff0f4b0ccc9/evidence/cloud-resume-20261102/ci-documents-checkout-final-ci/FINAL_ACCEPTANCE.json) 綁定上述 U／execution／baseline：

- [Documents job](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41447885087/job/125285440529)：原47 assertions 通過、0失敗；整 job 為105秒，落在原10分鐘內。舊 generic checkout 確實 skipped，新專用 checkout 確實 success；原 log 證明 `--filter=blob:none` 與 non-cone sparse patterns 實際執行。原 native build、fonts、真 browser 與 screenshot upload 均執行。
- Native 三片各79 suites，聯集精確等完整237-suite registry、無重疊；原完整聚合 CLI exit0，5420 counted passes、1次原 Linux GDI allowlisted skip。未宣稱 Windows GDI 真資源測試已跑。
- Canvas 原 full scope：2286 assertions 通過、0失敗、`skipped: []`，86個 golden sections 全等；原 P38 預期 `fb-auto-probe` 例外1次保留。Assertion 數不等於端到端情境數。
- 12個官方 ZIP、667 members 與10份原 job logs 已保全；1810項接收／完整性 checks 通過、無 failures。這1810項不是產品測試案例數。

固定 E 的 [ARCHIVE.json](https://github.com/ZhiQiYang/geometry-axiom/blob/59f2cac42862dec39a5d0216b4e1bff0f4b0ccc9/evidence/cloud-resume-20261102/ci-documents-checkout-final-ci/ARCHIVE.json) 記錄 [OFFICIAL_ORIGINALS.tar.gz](https://github.com/ZhiQiYang/geometry-axiom/blob/59f2cac42862dec39a5d0216b4e1bff0f4b0ccc9/evidence/cloud-resume-20261102/ci-documents-checkout-final-ci/OFFICIAL_ORIGINALS.tar.gz) 原件3,797,828 bytes，SHA-256 `8483a492f4f8f9b1d458e4217e4315eb89a9a4c5b6eb5567f29c9cafc43e31cb`；逐 member 回讀全等、原bytes未修改。本次正文更新沒有重包原件或重跑 CI。

本地在 U 實跑原 `python3 -B tests/mutate.py --check` exit0（6.880秒）：123 records＝114 killed／1 crashed／5 equivalent／3 retired，stale／blocked／survived／invalid均0。帳本原bytes未改；私有 logical cache 前後不存在，因此這只證明 source／tool／closure 的 logical 核驗，沒有另作 binary／產品執行，也沒有為 timestamp 再產123。YAML、原命令、actual SSOT 三件與 policy 核對保持相同；所有非 workflow 的 Git entries 未變。

[原 #345 首次 documents job](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41437638054/job/125251333430) 在 fetch 約612秒後顯示 `The operation was canceled`，整 job 約617秒，build／browser 尚未執行。原設定是10分鐘 whole-job；未證實 checkout 另有10分鐘命令 timer，精確取消發起者仍未知。原 F `f8f0b433ee01429c2c4d7d5f20a85d3d9a9f1b12` 的 root evidence tree metadata 為17,742 blobs、2,659,549,972 logical bytes；這不是 wire transfer 測量。本輪也不是受控網路倍率／效能試驗，不能用舊 cancelled fetch 與新 successful whole-job 的秒數計算加速比。

[#345 原 F 的既有 attempt2 documents 成功](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41437638054/job/125268717592) 與本 utility 分開；先前403請求沒有建立該 rerun，也不將其成功歸功於本片。首次 cancelled 等原紅件均保留。

PR 維持 draft，請對上述固定 U 與 E 作最新審查。這不是全域 sparse 規則：實際需要 root evidence 的 recovery workflow 與 #366 bridge scratch clone 都未改，不豁免 tool_hash 或任何既有判準。尚未合入後來 main，也不把本輪綠燈移標至它。
