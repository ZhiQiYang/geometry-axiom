【dot】

Documents job 的 checkout 會取回它不使用的根 `evidence/` 歷史 payload。這個變更只讓 `matrix.suite == 'documents'` 使用 `blob:none`＋non-cone sparse checkout，排除根 `/evidence/`；其餘 browser、native、#366 checkout 全部維持原樣。

| 項目 | 固定來源與結果 |
|---|---|
| Utility head | `b2432c9ea79a6927675883ddde04f629b159be2d`；sole parent main `e02057b4c725d6f03ae52c3bc30776bf9442b0cf` |
| 唯一變更 | `.github/workflows/integration-tests.yml`；兩個互斥的 `matrix.suite` checkout，pin 不變，兩者仍 `persist-credentials: false` |
| 保留輸入 | `/*`、`!/evidence/`；仍保留 `tests/evidence`、`tests/release-evidence`、`geometry-core/domain-decoupling/evidence` 及所有其他 nested evidence |
| 原 guard | documents whole-job 仍 **10 分鐘**；native 三片35分鐘、其他browser時限、原 build/fonts/runtime/browser/upload 命令、matrix、permissions、credentials、assertions、golden、expected／skip／freshness policy 均未改 |
| 本地驗證 | YAML／原命令／完整diff靜態核對通過；actual file／936-byte canonical patch 精確等預審candidate；所有其他Git entries（含SSOT三件、架構policy、mutation helper/workflow及237-suite expected）相同 |
| 原 freshness 命令 | 在此head實跑 `python3 -B tests/mutate.py --check` exit0，6.880秒；123＝114 killed／1 crashed／5 equivalent／3 retired，stale／blocked／survived／invalid均0。帳本原bytes未改、私有logical cache前後不存在；這是logical source/tool/closure核驗，未重跑產品或為timestamp重產123 |
| 新CI gate | Draft；此utility尚未取得新的真UI47或完整required CI通過。必須用原命令完成documents47與完整required CI，保留原10分鐘時限後才驗收 |

[原F首次documents job](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41437638054/job/125251333430) 在 fetch 約612秒後顯示 `The operation was canceled`；整job約617秒，build／browser尚未執行。原workflow對documents配置的是10分鐘whole-job預算，並未證實checkout另有10分鐘命令timer，精確取消發起者仍未知。Pinned checkout source 的10000ms delay是process退出後等stdio關閉的10秒。

Root `/evidence/` 的Git trees API metadata（未截斷）列出17,742 blobs、2,659,549,972 logical bytes；這不是wire transfer或效能測量。靜態依賴審查保全原47個嚴格check、55-file local require保守閉包、740 runtime sources、351 static routes／8 catalog routes，以及三個native各195 inputs；沒有找到這個固定documents47流程需要的root evidence leaf。PDF、Markdown、notes與case assets均為原程式在TEMP／瀏覽器生成；沒有本地執行Chrome／build／新UI驗收。

[#345既有attempt2 documents成功](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41437638054/job/125268717592) 屬原F `f8f0b433ee01429c2c4d7d5f20a85d3d9a9f1b12`，與本utility分開；原403請求沒有建立該rerun，這裡不移標或歸功。首次cancelled與其他原件均保留。

這不是全域sparse規則：PR338 recovery實際讀root evidence，#366 bridge scratch clone也有自己的patterns；本片不改這些workflow/helper，不豁免tool_hash或任何原判準。不合main、rebase、force或approve。
