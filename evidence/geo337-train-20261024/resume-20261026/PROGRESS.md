# #338 current-state：固定 F 的 documents 正式通過，card 原程序已綠待交付

2026-10-27 UTC。候選產品 F=`cbf0fb621888596aa14ad5f2349b503e23b1b72d`；本次證據提交的父 E=`2d576269ab85ef64a921bc4b15d013ca2ef5b4fb`。本提交只封存已完成原件並更新此進度，不改產品、測試、公理或原列車，尚未 READY-TO-MERGE。

documents 封包已先凍結；其中 `CURRENT_PROGRESS.md` 是凍結當時的歷史快照（card 仍執行中），本 repository `PROGRESS.md` 才是以下更新後現況。僅更新這份小文件與發布 manifest，沒有重包或重跑。

## 唯一 current-state 矩陣

| Gate | 真實執行來源與結果 | 現況 |
|---|---|---|
| 全 123 帳本 | S10 `82c922a3941525d3a094ac0158bdc7dea57ea360` exit 0；114 killed、5 equivalent、M20 crashed、3 retired | 已逐 byte 採入 F；120 execution heads 原值保留，不重跑 |
| mutation check | F exit 0，123/123 | 已有效，不重測 |
| 架構三條 | F 0/0/0；798 edges、205 generic、18 product，0 skip | 已有效，不重測；不自動沿用到原列車的新 head |
| reader generate/check/unit | F inner/outer 均 0/0/0；51 tests、0 skip | 已交付 Edf848909；173 ResourceWarning 保留，不重測 |
| §7 axiom | **F 正式 primary/reaper/outer 0**；44 baseline，五組撤回 red 1／恢復 0，全部 killed；11 個 subprocess 合計 269 tests、0 skip | 已交付 E2d576269 原件；不是準備工具或靜態審查代替正式執行 |
| §7 card | F 原 runner／reaper／outer **0**；53 actual mutants killed／restored 0 | root 01:51:47Z 觀測 session 34127／chunk aeb1c7；完整原件核收與發布待完，未混入本 documents 封包 |
| native | F **UNRUN**；F9 歷史 exit 1，5327 pass／1 fail／1 原 GDI skip | D4 裁判與 D5 queue 有真依賴，不能沿用；真 TMP 啟動空間仍不足 |
| documents | **F 正式 inner／outer 0**；47 assertions pass、0 fail／skip、8 screenshots；70.97391320997849 秒 | 本包完整原件，原 10 分鐘未超；不能自動算 F′ 通過 |
| canvas／assembly／grid／space／timber | F 五項 **UNRUN**；F9 歷史六項 0 | assembly r1 原環境 1 保留；space 原 2、timber 原 5 分組 skip 保留，無新增 skip |
| Q38 | F **UNRUN**；F9 全 44 exit 0，43 killed＋SPM24 equivalent | D4 納入模型副本 digest，須補 F 原件 |
| #323 R8／exact | R8 固定源 `75a1e93811a52b69385cbdaf6a09d773ed9052ad` 36 樣本比例綠，但 outer 1 保留；F9 exact outer/stage/audit 0 | 不重抽、不改標 F、不將三差限定擴至 P-189 |
| P52／P-189／required-eight／PF3／whole-memo／replay／#314／RC／Reading A 其他 | 新 F 尚未閉合；P-189 strict exact 原紅保留 | 完整來源／資源／部分原批准依賴未閉合，不放寬門檻 |

F9=`4f8a794f4167c3562eb182045102e86e9e37cca9`。舊矩陣保留於 Git 歷史；相同產品 bytes、封包核對或資源工具測試均不算新 F 正式通過。

## 已交付 §7 axiom 原件

原指令為 `python3 -B -u geometry-core/card-reference/run_axiom_mutations.py --output <OUT>/subject`，完整 Python 路徑、argv、cwd、環境、來源／fixture 雜湊、stdout/stderr、exit、原始報告與 root 終態觀測全部在 `axiom-F-cbf0fb62-20261027/EVIDENCE.tar.gz`。OUT=`/dev/shm/geometry-axiom-geo337-20261025/axiom-F-cbf0fb62-formal-20261027`，01:11:14.148844Z 開始，01:15:28.734150Z 結束，254.585306 秒；沒有重跑取最好樣本。

五組為 V01-remove-gate、V02-ignore-manifest、V03-ignore-source、V04-exempt-latest-pre-adoption、V05-card-adoption-treated-as-pre；各 red exit 1 為具名測試 assertion，恢復各 44 tests exit 0。原 compiler 60 秒、unittest 180 秒、scene 20 秒、stack 16 MiB 保持；原 runner 沒有外層 timeout，不另聲稱有。

獨立原件審查 exit 0、874 checks：22 份完整 unittest stdout/stderr 與 36 份外層 streams 均核對；262 closure 檔、7 fixtures（含五份受保護 fixture）、HEAD/index/refs 與被突變 target 已恢復。這不代表 3763 檔薄來源等同 native 的 6997 檔完整來源。原 gate 沒有額外獨立攔截內部 compiler/scene 的每次 stream，此限制保留。

封包保留整個 OUT 的 105 regular files、32 directories（含 root 與空目錄），沒有排除檔；另保留執行／審查工具與 root 終態、資源原觀測，以及下面 #347 的已閉合文件原件。INDEX 對不同來源 SHA 分開記載，不把 #347 的文件發布當成 F 的產品驗收。

## 資源規劃更正與仍受阻範圍

原 2 GiB 是 2026-10-25 PLAN 的 `recommended_SHM.root_planning_ceiling_bytes`，不是使用者門檻、平台硬配額、安全設定或產品斷言。協調者於本輪明確撤回其後加的「保持 2 GiB」管理限制；本任務暫用兩 OWN 合計 **4 GiB** 工作規劃。沒有改 mount/quota/權限，沒有增加付費資源；原 64 MiB 發布保留、真 TMP 准入與正式時限均不變。

§7 本輪實際以完整 1536 MiB 增量規劃准入；該值是可逆工作安排，不是已證最大成本或產品輸出限制。41 次非原子取樣的 combined OWN 最大 2,084,065,280 bytes、實體 SHM free 最小 15,787,884,544 bytes；不是精確 peak。終態 OWN=2,080,342,016 bytes，OUT allocated=499,712 bytes。共用 cgroup 的前後 OOM/kill/group delta 均 0，但不是 gate 獨占的記憶體觀測。下一項必須 fresh 核對實體容量與完整執行／保留成本，不能拿本次觀測充當准入。

00:56:48Z 的真 TMP free=108,560,384 bytes，原 native 128 MiB 啟動門檻仍差 25,657,344 bytes；這是帶時間的觀測，不是後續現值。原批准 3156 檔＋108 空目錄已完成，TMP 實測回收 107,233,280 bytes，不再待批或重做。新增固定 168 檔 allocated=23,707,648 bytes 仍**未批准、刪除 0**；未知修改、原件、fixtures、Git objects、F9 ELF 等全數保留。沒有以另一批清理規避未批准範圍。

## #347 C1 文件修正已交付

產品／正式 execution S=`324034812bb6effca68e0413bc0468595337b317`，直接 source parent=`a5f1806fb3cad2dada1a56e79e01d54f9f86700f`；本輪 API 觀測 PR base=`eaf15e239324a6464a04740647afccce3a3c17c7`，它們不可互換。

- 新 evidence head=`8bb0359331365c6f3a96872620427cf7847fcb50`，由 `2e8a6ed20325aa4842dcd0f89eacd598662be598` 普通快進，只修 `evidence/issue128-empty-panel-rows-20261024/PROGRESS.md` 的 C1 身分字句。
- 新正文 D=`066bc6606503f29b57b6ff54d07e1a0d13f1617a`，由 `1801e3fd2222b5d9146f97de2ac53589ae7ee526` 普通快進，只修 `PR_BODY.md`；保留原正式來源與原收據連結。
- 兩次發布 exit 0，均各 11 API／33 streams、full remote bytes/OID 核對通過；內容、工具與實際發布均有另一代理窄審。**B1/B2 仍未解，不標 READY-TO-MERGE**。沒有為修文案合流來源或新增產品變更。

父端 01:25 UTC 已回報從 GitHub API 核對 #347 新 head 與正文均套用；這是父端觀測，本代理沒有再輪詢或發布同版。此前 #343／#348 文案交付與其未驗限制仍保持，完整歷史原件在 `review-docs-20261026/EVIDENCE.tar.gz`。

## 其他執行者與下一步

父端 01:25 UTC 的 GitHub 觀測：原 #338 head 新增為 `a4bd77e8090f5a82f0c8934c30c5335782293922`，parent=`a6f4013364e21bcb7239b5dcc25caac0f6d61f77`，只改 PRODUCT-ARCHITECTURE.md 與 product-architecture-receipt.json；訊息稱由另一 Claude 本機重產。這是父端提供的遠端觀測，尚不是本代理重讀原始 receipt 或批准跨 SHA 沿用。recovery 保持自己的 F/E，不覆寫原 train。

同 head 的 CI run 40431992777 七 jobs failure，但 runner_id=0、steps=[]，沒有實際執行，不能當成產品紅綠。#338 正文 D=`2cce6afaeac87521924bde28660a71e43ad306e5` 仍舊矩陣，待一輪實質 gate 後整合更新，避免每筆觀測重發。

主代理其後實際 fetch handoff 至 `913d6c429dbd0c6fbfcb3cf700133881c3149ee6`：`handoff/pr-reviews/338.md` 新增 01:30:50Z 本機 Claude 交接，稱 F′=`a4bd77e8090f5a82f0c8934c30c5335782293922`、evidence head=`2d7a635ec6408f7fda80db13992d08feb4727e4b`，要求後續七項與 oracle；pr-status 也記 #347 D066 已套用。這是 repository 交接轉述，其中帳戶與使用者選項引述其後已由原 API 核實（見下）；Claude 整理不自動擴大授權，帳本 stale 豁免不自動採用。**本包正式 axiom 來源是 F，不是 F′；沒有宣稱 F′ 已驗通過，#338 仍 draft。** 新來源切換須先確認 closure 與原件，避免重複或競寫。

下一步完成已退出 card 的原件核收與一次發布；接著以 F′ 的獨立新來源跑該來源必跑 gate。F 的 documents 不自動移標為 F′ 通過；來源差異與可沿用範圍另保留精確閉包證明。所有既有失敗與原取樣保留。未合併 main／PR、部署、付費、改安全設定或新增公理。

## 本次 documents 正式原件

固定執行 F=`cbf0fb621888596aa14ad5f2349b503e23b1b72d`，原 driver 01:40:33.210738Z 至 01:41:44.184650Z，70.97391320997849 秒；原 CI 時限 10 分鐘保持。root launch session 97232／chunk 658686 的 outer exit 0 是主代理工具觀測，獨立核收不是再次 poll 或執行。原 workflow 47 assertions pass、0 fail／skip，完整八張桌面／手機 screenshots 保留。

環境原件：Google Chrome 156.0.8078.47、Node v24.19.0、Python 3.12.14、GCC 14.2.0、fonts-noto-cjk `1:20240730+repack1-1` 已安裝。依原 workflow 跑 build／runtime probe／文件瀏覽；來源 checkout、埠與暫存獨立，source guard 3759 葉前後一致，原 source index 雜湊保全。GitHub checkout/upload 分別以精確乾淨 checkout／本地 artifact 留存表示，apt 步驟確認已安裝；沒有宣稱 Actions runner 真執行。

`documents-F-cbf0fb62-20261027/EVIDENCE.tar.gz` 依獨立核收的固定 SELECTION 收錄 810 regular files、62,855,047 logical bytes、207 directories；五個 nonregular（四 symlink、一 socket）只留 lstat／link-target metadata，不跟隨。完整 control／seed-copy／plan／source guard／private Git index／launcher／sampler／workflow／runtime／screenshots／測試 fixture／衍生 cache 原件皆保留。三個原碼 namespace（seed/source、seed/verified-readonly-pool、source-layout）和外部 Git object provider 不重複封包，但原件仍在，完整 3759 葉 manifest、精確來源與 guard 在包內；未刪任何資料。

獨立 ACTUAL_PEER exit 0、2470 checks。76 次 nominal 1 秒非原子取樣，最大間隔 1.007987943 秒；全 SHM mount 最小 free=15,579,451,392 bytes，combined OWN endpoint 2,283,098,112→2,292,428,800 bytes。共用 cgroup OOM／kill／group 皆 0，但 memory max events 298165→300640，沒有隱去；這些不是精確峰值，也不拿來外推 R8 或 P-189 效能樣本。

封包採新的 SHM delivery sibling：以未壓縮原件與完整留證成本先規劃，再以實際 packet P 檢查原 `3P+L*65536+M*8+67108864`；64 MiB 保留和兩 OWN 4 GiB 規劃不變。TMP 容量沒有用 SHM 抵算，native 真 TMP 原門檻保持。完整 namespace 與逐檔雜湊在 INDEX/SELECTION；不包未完成 card 原件，也不重跑已有效驗收。

## 原始批准來源核對的邊界

本包另收 `geo338-source-approval-read-20261027` 的兩次帳戶／評論唯讀 API 完整 stdout/stderr、指令與 exit（皆 0），以及其後僅列出 F′ 本機 WSL 證據目錄的唯讀 listing（不代表已核收內部驗收原件），以及已交付 axiom E2d576269 的實際發布核收。01:37 UTC 的 `gh api user` 與 #338 評論作者帳戶 id 均為 59477728（ZhiQiYang）；這比只看 handoff 作者字串多了 API 身分證據。

原留言 permalink：https://github.com/ZhiQiYang/geometry-axiom/pull/338#issuecomment-6396611849 ，created 2026-10-25T10:39:52Z。留言明確區分「使用者選項原文」與「本機 Claude 整理，非原話」：前者逐字為「讓 Codex 繼續做到審查通過」、「A 接受這 3 筆 (Recommended)」、「延伸到所有 PR (Recommended)」、「先合併，帳本留下次 (Recommended)」；後者是 #323 精確三差白名單、七項加專項替代 CI、mutation stale 合併例外等解釋。本包保存全文，不把帳戶核實等同批准解釋的任何擴張；不據此自動新增 P-189 例外、接受 survived／invalid／blocked，或將 F 結果沿用到 F′。本任務仍不合併 PR／main。
