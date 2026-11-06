# #338 B1 原件回收查核（2026-11-02）

本輪承接 [ChatGPT 10/28 審查 B1](https://github.com/ZhiQiYang/geometry-axiom/pull/338#issuecomment-6479275307)。審查已關閉 B2、B3、P52 與狀態同步缺口；剩餘條件是三支原 R8 ELF 與既定 whole-memo 正式反證。**本目錄的 CI 是原件回收查核，成功只表示查核完整；不表示 B1 通過或解除。** B1 最後解除由審查方判斷。

## 必須交回的原件

實際原 execution F8 固定為 `75a1e93811a52b69385cbdaf6a09d773ed9052ad`，完整 mode 均為 `0100700`（十進位 `33216`）。以下規格來自已核收的固定 STATUS，未更改分母、樣本或裁判。

| 原角色 | bytes | SHA256 |
|---|---:|---|
| `base-pg` | 1039760 | `4231f2559727262562164487f95da8544595561857886ee598ac5b20f9b1e47b` |
| `fix` | 1126456 | `e07c98a5be1f28b151b2abf6b206bb2add438024424d5bb6c6d614428ead7088` |
| `fix-trace` | 1134992 | `fa793dd393932b946bfe521e30c12c3ca8a8096f20b50818a1ce9a50f881a978` |

## CI 會保存什麼

工作流程 `.github/workflows/pr338-b1-recovery-audit.yml` 僅在 #338 修改本查核時啟動。它直接檢出完整 PR head，沒有編譯或執行 ELF，也沒有執行任何產品測試。

- 完整分頁的 GitHub Actions artifact API 原文；逐一下載當時所有未過期 artifact 的 ZIP，核對 GitHub digest，記錄每個 ZIP 成員的 bytes／SHA256／完整 mode。只讀 ZIP，不把其內容執行或抽出到檔案系統。
- F8 的 [run 40170221039](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/40170221039) 原 API 與下載日誌的真返回碼；這一輪原先七個 job 均零 steps、沒有 artifact，不能假定它曾產出 R8 ELF。
- 已知七綠 [run 41203002092](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41203002092) 的完整 head `ad64b7d7a53e0bec5ed94197a2a5c14712e32da3`、各 attempt／job、**attempt 1 與 2 分開的完整原始 log ZIP**及真讀取退出碼。attempt 1 有六 browser 與首次取消的 native；attempt 2 是 native 完成重跑。只抓 run 的預設 logs 會僅得到最新 native，故本查核逐 attempt 保存；該 run 的七綠不代表執行過 whole-memo。
- 已發布 R8 原 tar 本體、全部成員清單與 hash、`EXCLUDED_ELF_PAYLOADS.json`、原 whole-memo 工具與既有 B2 來源／建置／裁判閉包。保留原 R8 overall exit `1`。
- `AUDIT.json` 區分程式真正回傳的 `auditActualExit`、計算出的靜態 `originalPayloadIdentityGate.classificationCode` 與尚未執行的 `formalWholeMemoExit=null`。找不到三支原件時，靜態分類碼為 `2`（**不是 process exit**），正式反證及 baseline／withdrawal／restoration 均為 `UNRUN`。
- `MANIFEST.json` 列出下載物與每份原流的 SHA256；整份 artifact 保留 30 天。若 artifact API 快照在分頁間變化、下載或 digest 出錯，查核本身會以真 exit `1` 失敗。

檢查範圍是查核時 API 仍可列出／下載的 artifacts、其直接 ZIP 成員，以及已發布 R8 tar 的全部 regular-file 成員；不能由此宣稱已找遍遭刪除或不再保留的歷史環境。

## 本機僅做的靜態查找

本輪在隔離 clone 操作；`D:\geometry-axiom` 僅供唯讀 Git 物件查找，沒有在本機／WSL 編譯、執行 ELF 或跑產品測試。針對來源 repo 現有全部 Git 物件，以三個精確 bytes 篩候選，僅出現一支 `1126456` bytes 的 ELF：Git blob `2484073920a54ae844430b4d41c60a327aefd9dc`，位於 `dd2cbf6a558b4af240ab4702cc8402621380881b` 的 `evidence/geo337-q38-20261027/q38/q38-bin/bridge`。其 SHA256 為 `1c8fce07037ac0fbd0429fa504d68a00da7b02a93bb14f54f7aa083c3f9acd6f`，**與原 R8 fix 不同，不能代用**。此物件掃描不代表掃描任意壓縮包內嵌物或所有 D 槽檔案。

## 尚缺的交付

若查核沒有找到原件，仍須由原保存者／環境交回上述三支原 bytes，逐一驗 full mode 與 hash，才可在 GitHub CI 以原 F8 執行既定工具，取得具名撤回紅／恢復綠與隔離 175／350 ABC 的原始 streams／真退出碼。與目前產品的來源閉包須另外列出，不能把 F8 execution 改寫成目前 head。重編 ELF、P-189 新 bridge、合成 metadata `0/1/0` 或本查核綠燈皆不能代替該正式反證。
