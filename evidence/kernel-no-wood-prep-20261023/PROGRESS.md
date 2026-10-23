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
