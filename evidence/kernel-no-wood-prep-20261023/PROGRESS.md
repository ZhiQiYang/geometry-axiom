# 不帶木工模板：準備進度

狀態：**只有準備證據，產品測試檔尚未修改，正式驗收尚未跑**。這是子代理專有分支；本提交只在 evidence 增加文件，沒有建立 checkout、編譯、開 Chrome、跑 benchmark 或重產帳本。

- 固定產品底本：13d02c1db7022145a52ee063286a558e595eb212。準備分支建於當時整合 evidence head 22ad28f30c5b7c43cb004b95037583bc7b902f3c，不把 evidence SHA 冒稱測試來源 SHA。
- 現有真隔離建置已只取 K＋矩形格網模板＋測試共 11 檔。補缺候選只在既有測試檔加明確 geometry_woodworking blocker 及 K→W 引用守門，原 11 項保留，候選共 13 項。
- 兩種 guard 各自撤回／還原的原始 0/1/0 driver 已備，尚未執行。W include 使用已安裝且可編譯的真標頭，編譯錯誤、缺標頭或 crash 不能冒作分層抓到。
- 已由 #318 owner 做靜態對抗審，沒有找到確立 blocker；這不能代替正式動態驗收。原指定 #314 reviewer 恢復後仍須審正式成果。
- #288 space 原收據只讀核到 full-space-suite 242/0/completed；明列沒有 timber 兩群組，沒有重跑綠項。
- 對 #318 的權威文字／候選／W 與 oracle 草稿另有獨立靜審，實作與掃描尚未完成。

下一步：等 root 安排專有 sparse worktree 與重工作槽，正式套自己的測試葉檔並 commit/push，綁可解析 SHA 跑完整 13 項與兩種 0/1/0。共用檔順序 #323→#314→combined→#318→本子項，#318 正式推穩才普通 merge 前棒並改 registry count；全域帳本只由 root 在共同最終 SHA 整份產一次。未 force push、未合併 PR、未改決策佇列或公理層。


## 測試葉檔已落實，動態仍待排程

已建立專有 tiny sparse worktree，只取 K＋矩形格網模板＋測試 11 檔與本地規則，並將已靜態互審的候選安裝到 `tests/test_rectangular_template.py`。新增精確 `geometry_woodworking` 匯入阻擋與可取得 sentinel 自證；K 引用可取得 W 標頭的 source gate 及三態反證也已入檔。原 11 項保留，現在來源為 13 項。

本階段只做 AST／Git diff 檢查；沒有編譯、執行測試或 0/1/0。`tests/run_all.expected.json` 仍是前棒的 11 項，依 #323→#314→combined→#318→本子項順序後再改為 13，不能以此 source commit 宣稱完整 native 綠。沒有修改共用 registry、產品 C、SSOT 或帳本。

下一步：取得 #314 owner 的正式葉檔靜審，持續對抗審 #318；等 root 放行重工作槽後，以此已推送 source SHA 跑原始完整 13 項及兩種 guard 的 0/1/0，再在 #318 正式合流後重綁最終 SHA。


## 對抗審查的 angle include 繞路已修，動態未跑

第一版測試來源 `af76f9d7c393c441b8244e1ddd40bf72d796cc07` 已推，但 #314 owner 的靜態對抗審指出只抓 quoted include 會漏掉 `#include <rectangular_grid.h>`。尚未動態確證，不將靜態推論冒作原始紅燈。

本修正同時辨識 literal quoted／angle include；angle 無專案標頭候選才視為系統標頭，能解析到隔離 source closure 的標頭同樣檢查 K 邊界。原 quoted 控制、全部斷言與原 11 項保留，仍總共 13 項。兩種 include 各有真編譯／連結／exact-cells 成功後的原 source gate 0/1/0；正式執行仍待 root 排程。

`revision-2/` 凍結新候選、全 patch、driver、AST-only 0 與指出繞路的原靜審。driver 嚴核七 phase 原始 `0/1/0/1/0/1/0`：新增只撤 angle parser 回原 quoted parser的單獨反證；撤 K guard 要求兩個正常 subTest failures，撤 parser 要求一個正常 failure。不是接受 compile error／crash／watchdog。

原 prefix 的 MANIFEST 是準備 commit `07b7df9b` 的歷史 snapshot，PROGRESS 持續追加；新 revision 的 MANIFEST 只綁其凍結檔案。共用 expected count 仍等 #318 正式交棒，不因本修正先動；全帳本未重產。尚未有任何動態通過宣告。

## R2 獨立靜態對抗審已完成

測試來源已推 `21957a45142dadc0787e8970da976ab249b4b6d1`，遠端 exact SHA 相同，worktree 乾淨。#314 owner 再讀葉檔 SHA-256 `e948fb78e81a075875a45041009fb379e58d783c8d6b579cd9fa2f81cd40910e` 與 collector `48e0badb3e09cb16603af11ad04fe8d79a75055009868beabd02acf64b2ce6bc`，未見確立新靜態阻擋；原補審完整 bytes 保存為 `revision-2/REVIEW_LITERAL_R2.md`，SHA-256 `889ae644d8a581dcf768f829c0e7e7dab5aeb127d7faae6604ff9ea0addf7fbc`。

此段只補靜審證據，不改測試來源。沒有 compiler／13 項測試／七 phase 三態收據，沒有原始 gate exit 可報為綠。共用 count 仍 11、全帳本未重產。root #288 的三次 canvas 正獨占 heavy，因此繼續只做 #318 來源對抗審；等 root 排程與正式前棒後再跑。
