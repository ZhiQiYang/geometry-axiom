# #299＋#316 正式雲端驗收

固定受驗 F：`5bfadf187e615ba0fb8466753b63ce3044ef7d1c`。每項原命令與完整輸出、環境及來源狀態已分項封存；後續 E 只保存證據。

| 原 workflow job | 原退出碼 | 原秒數 | 原 CI 分鐘 | 超時 | 證據推送退出碼 |
|---|---:|---:|---:|---|---:|
| native | 0 | 1812.307123 | 35 | False | 0 |
| canvas | 0 | 1665.084770 | 35 | False | 0 |
| assembly | 0 | 186.209069 | 15 | False | 0 |
| documents | 0 | 60.458381 | 10 | False | 0 |
| grid | 0 | 439.853007 | 15 | False | 0 |
| space | 0 | 207.312252 | 15 | False | 0 |
| timber | 0 | 119.906185 | 20 | False | 0 |

原 native 合計：224 個連續 suite，5,185 計數＝5,184 passed、0 failed、1 原允許 GDI skip。`mutation:check` 原退出 0。三條原架構裁判退出 0／0／0，inner／outer 均退出 0，來源前後為乾淨 F。

原 canvas 的 P73 模組中，「空空間不畫假邊界，提供加入成員入口」與該模組「整輪沒有未處理瀏覽器例外」均具名通過。canvas 原 footer 的 uncaughtBrowserExceptions=1 原值保留：原 P38 以 fb-auto-probe 預期注入單次例外，並有具名成功斷言；不宣稱全 canvas 的例外計數為零。P52-5 原同步等待為 197ms、core 足跡同預示；這是本輪正常 browser 步驟，不當作 main/fix 三方專項。

七項通過依據是各原裁判退出碼、原收據與原 CI 時限。FORMAL_METRICS.json 是純讀摘要（not_acceptance_gate），不新增裁判或數值門檻。assembly／grid／timber 原 footer 的 scope:partial、golden 未比較與 omitted groups，及 space 的 full-space-suite／omitted groups 均保留。各原分組的 included／omitted 與計數見 BROWSER_SCOPE_FACTS.json；只宣告原 workflow 各 job 範圍。

原整份帳本退出 2 的容量失敗、同 S 的 18 bridge 環境重試 0／strict check 0、各外部收集器原 1、Linux 架構 r1／r2 與原完整 streams 限制，均保留在 SOURCE_HANDOFF.json 與已公開的帳本／架構封包。沒有改寫失敗或把 M20 crash 算 killed。

Windows GDI／MSVC 未在此 Linux 執行。這個分支獨立基於 #288 整合來源，未與 #314／#323 疊合驗收；沒有合併或 force push。
