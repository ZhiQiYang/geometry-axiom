# PF-H 最終原生收據：正典同步仍阻擋

記錄時間：2026-10-15 11:13:21 UTC+8。產品程式最後變更 `858515596f21a9329beff339caa83725906b491a`；加入突變收據及證據後，固定完整 native 與負控制 head **`48a0220561cdda9322bde86dbddad7b4b4705764`**。交付 commit 只封存原件／說明，不能把交付 SHA 冒稱為實際受測 SHA。

| 裁判 | 結果 | 實際退出碼 |
| --- | --- | --- |
| `python3 -u tests/run_all.py --build`，89 suites | 2858 題：2851 過／6 失敗／1 允許略過 | 1 |
| 固定 head 宿主基線／還原 | 32／32 → 還原 32／32，無 error／skip | 0／0 |
| 八項領域撤除 | 各自讓一個具名斷言轉紅；含子格第二分量及 render 第二塊 | 每步 1 |
| 子格堆疊撤回 | 具名 S09 紅，原生 exit -11；與斷言型控制分列 | 測試 1 |
| 正式核心突變，新產品來源 | 42 killed／1 crashed／4 equivalent／3 retired，50 筆 | 三個父層各 0 |
| 全新來源突變收據查核 | 47 支實際執行檔＋baseline／sidecar 字節查核，無 stale／survived／blocked／unrun | `--check --killers` 0 |
| 唯一正典目前 `--check` | 五道 assert／獨立 SSOT 通過，patches=0；不驗 rebuild 冪等 | 0 |
| 原同步器記憶體內反事實驗證 | 新來源 14 行追溯差異，原 41／41 綠，無 error／skip；正典未改 | 0 |
| 正式 WSL 七項 | 未執行、未排程 | 未驗 |

完整 native 耗時 **971.474511 秒**。環境：Linux-6.18.44-x86_64-with-glibc2.41；gcc (Debian 14.2.0-19) 14.2.0；Python 3.12.14；Node v24.19.0；stack 16777216 bytes。沒有 `--allow-skip`，沒有 count drift 或未登記測試；唯一略過是 `py:test_gdi_contract` 的 `requires compiled Windows GDI contract harness`（Linux 平台具名允許項）。必要 owner/browser 整合不在這個 aggregate 的 pass/skip 內，不能當成已驗。

本次宿主32／32、原有子格31／31、核心143／143。三份突變 baseline 各143／143。M20 在基準通過後、同一夾具連三次原生 SIGSEGV，記為 crashed，不冒稱斷言 killed。47 支突變＋1支基準的實際 sidecar 封存在 `official-components/executed-sidecars.tar.gz`，48個成員SHA見 `sidecar-manifest.json`；二進位本體沒有進 repo。

6 項失敗全部是 `CanonicalReader` 的既有追溯／同步測試：

- `test_color_contract_allows_unrelated_properties_and_untracked_selectors`
- `test_current_layout_change_does_not_relock_historical_migration_tests`
- `test_legacy_image_handler_retires_without_changing_live_svg_handler`
- `test_rebuild_is_byte_idempotent_and_keeps_reviews`
- `test_retired_color_migrations_allow_format_and_unrelated_layout_changes`
- `test_traceability_lights_and_hub_badges_exist`

R41 實作使燈號／連結及 none 計數變更；既有同步器產生的完整 authored state（條文、blocks、批註、草稿）全等。新補丁 SHA256 `296192fc7f0410bf4836e8fc768b9d812a482222bdf67593c7f1f3b65b69f8e1`，取代歷史 `4a534e4f…`。counterfactual 在相同產品來源 `85851559` 跑41題／345.666327秒；不能代替目前版本化正典的35過／6紅。

現有唯一同步 owner 已查明為 [#207](https://github.com/ZhiQiYang/geometry-axiom/pull/207)，分支 `codex/geo198-reader-sync-20261012`，已查 head `14afc2b6d0c6df6ee68e1128744fb2d4eb81a469`。須由該 owner 在包含 PF-H 新來源的整合候選重建，或由 Claude 明確授權本 PR 套用純生成差異。[具體交接 6183368057](https://github.com/ZhiQiYang/geometry-axiom/pull/227#issuecomment-6183368057) 已附新差異、原件、SHA與看板指示。看板明定碰到閱讀器須標「需 Claude 裁決」；正典未擅改，不宣稱可合併。

`native/native.json` 記錄全部 **14903** 個 tracked 一般檔案前後 hash 相同，未排除任何檔案，head不變，結束工作樹乾淨；`native/tracked-snapshots.tar.gz` 保留兩端映射。這是端點查核，不宣稱連續監視。
本輪 204 個原日誌完整封存；archive SHA256 `1ea21d5e057caaa836a2a7a2f3cb1b21b1a86b9d936e4b857971b909677cdc54`，逐成員 SHA 與 manifest 核對。二進位／sidecar在 `native/binary-final.json`；reader與GDI原JSON亦單列。SSOT／白話／正典／🔒無本輪作者差異，來源核對見 `components-checkpoint/source-audit.json`／`delivery-audit.json`。

第二分量反例和修正、32宿主、31子格見 `component-review/`／`components-checkpoint/`；固定最終head的11步控制見 `controls-verified/`。#221 真宿主 E1/E2/E3、原生板片／D7足跡、source-only dump與新程序重開見 `witness-final/`。獨立測試端R43 consumer得到5／3／3；原純算法3／1／1保留。PF-3產品support/effectiveSeams仍另案，沒有冒稱產品已執行R43。

`native-review-63ed/` 為修正消費端前的2848／6／1；`native-before-subgrid/` 為更早2847／7／1，均保留歷史紅燈。第一次外部補測誤用 explicit、第一次正向執行未設16 MiB、grid timber probe最初誤把+v方向origin當footprint左界，也各保留診斷／更正，不當作產品領域失敗。

同 head 的 [GitHub workflow](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/38673638940) 七個 jobs 均 failure 且 steps=0；native annotation 明示付款失敗／支出上限，工作未啟動。原 JSON 在 native/ci-fixed-head-*.json。這是CI環境阻擋，與本機完整native的6項reader斷言紅分列；沒有修改帳號或repo設定。
