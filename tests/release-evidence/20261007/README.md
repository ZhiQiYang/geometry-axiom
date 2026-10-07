# Geometry Axiom 交付證據

主要本地回歸已有通過收據；整體候選驗收尚未完成，仍待補齊下列模型庫證據。遠端 CI 另見 PR，平台驗證另列，不代表 merge、deploy 或全平台批准。

- 候選狀態：`acceptance-incomplete`；候選受測 source head：`66a4c89d985e5e7a34f602ff1d085c7a9943c883`。
- 9712006 是先前受測版本；完整 CDP 第四輪為 `command-failed`。
- 每個 scope 的原始 head、runtime、結果、限制與失敗前序均保留，沒有把舊結果重標為新 head。
- 精確來源、每檔大小與 SHA256 見 [manifest.json](manifest.json)；原始資料見 [evidence.tar.gz](evidence.tar.gz)。

## 本地結果

| 範圍 | 實際受測 head | 結果 |
| --- | --- | --- |
| 完整 CDP 第七輪 | `66a4c89` | 2175 pass / 0 fail / 0 skip；golden 84 段逐段相符；0 unexpected exceptions，1 次預期 P38 probe |
| Strict 非瀏覽器登錄（6b，16 MiB stack） | `f6672d8` | 80 suites：79 success + 1 允許的 Windows GDI skip，0 failure；混合計數 2508/2507/0/1（total/pass/fail/skip） |
| Space / timber / #123 | `f6672d8` | 228 / 79 / 138，各 scope 全通過 |
| Raw provenance | `f6672d8` | 207 pass / 0 fail |
| P76 新 profile / seen combo | `f6672d8` | 正式 87 pass；TEMP 組合診斷 156 pass |
| Storage / blank entry / lesson Save/Open | `f6672d8` | 35 / 2 / 8，各 scope 全通過 |
| Fresh checkout + cold restart | `f6672d8` | 32 pass；官方 npm build 驗證 receipt-backed 未變原生快取 |

完整 CDP 使用新候選；其餘列保留 f6672d8 的實際受測結果。1771 個 tracked files 與 403 個 runtime source 的逐項比較證明兩版僅 P14 fixture 三行不同；`reviews/source-equivalence-f6672d8-to-66a4c89.json` 保留完整比較，不宣稱舊測試曾在新 head 重跑。

seen combo 是 TEMP 組合診斷，與正式新 profile P76 分開。舊 9712006／e3af640／f6672d8 的 failed、partial 與已通過範圍均保留原始 head。P38 預期故障探針的 1 次例外也保留，並未改寫成總例外數 0。

## 解壓與驗證

壓縮包 SHA256：`e06116c9c536e083256cb869c811c8bfbfa849841d4ed52177f52a57befc695e`，大小 3381155 bytes。

```sh
printf '%s  %s\n' 'e06116c9c536e083256cb869c811c8bfbfa849841d4ed52177f52a57befc695e' evidence.tar.gz | sha256sum -c -
mkdir -p evidence-unpacked
tar -xzf evidence.tar.gz -C evidence-unpacked
(cd evidence-unpacked/geometry-release-evidence && sha256sum -c SHA256SUMS)
```

解壓後的 `MANIFEST.md` 提供 scope 對照，`MANIFEST.json` 提供逐檔原始來源與雜湊。資料已實際納入壓縮包，TEMP 路徑只作 provenance。

## 限制與待補

1. PR161 模型庫十項 browser guards 的既有腳本、逐例原始結果及來源／終態收據尚未收錄，包含 pending native Undo 重入、Save／remove 拒絕、close／reopen／context／session 遲到回覆及真 readonly lease。
2. `historical/model-a49d/ui-settled-v2/ui` 的 155 項通過紀錄保留原受測版本；其 `browser_ui.py`、完整 oracle 結果及 initial-world 失敗→fixture settling 修正前序尚未收錄。

以上優先取回既有紀錄；Space 228 的一般模型庫檢查與 #123 的 138 項 Create／grid 流程不能代替這些缺口。若原紀錄已不可取得，只補缺少的有界 browser cases，不重跑已通過的全庫。

`manifest.json` 與壓縮包內的 `local-candidate-acceptance-complete` 是收集時作者記錄，保留原 bytes 作歷史來源，不作目前驗收完成結論。[限定獨立審查](https://github.com/ZhiQiYang/geometry-axiom/pull/162#issuecomment-6040383490) 明列上述缺口。

既有 Windows QA 的 390px 規則線控制項間歇不可達另列診斷；本包 Linux 窄 viewport 的通過不代表該平台問題已解除。

不包含 Chrome profiles/cache、原生執行檔或使用者收件匣。窄視窗／模擬觸控不代表實體手機或 IME；Linux 測試不代表 Windows、GDI/SAC 或原生 Save picker。混合 assertions、native cycles、component 和真使用者流程的計數不合併成單一驗收數。

本包已收集其配置範圍內的終態檔；整體驗收仍待上述缺件與相應驗證完成。
