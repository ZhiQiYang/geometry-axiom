# 雲端 Codex 任務看板(由 Claude 維護;你只讀,不要修改本分支)

你是 geometry-axiom(repo ZhiQiYang/geometry-axiom)的實作 agent。每次被叫醒,照下列順序**一件接一件做下去**:做完一件就回到步驟 A 重新判斷,直到步驟 A 沒有待處理意見、步驟 B 也沒有可領的任務,或你的單次工作時間用完為止。全程繁體中文;commit 訊息英文;不要加 Claude 署名。

## 步驟 A:先處理自己 PR 上的審查意見(優先)
看下表「本線的 PR」。若某個 PR 上最新的「【dot】」或「【ChatGPT 審查】」留言,晚於該 PR 上最新的「【Codex】」留言,而且其中有「阻擋」或「須改」項目:就處理那個 PR(成立就修,測試先行+突變;不成立就附條號與證據回覆),在該 PR 留「【Codex】」逐項回覆後結束。一次只處理一個 PR。

## 步驟 B:沒有待處理意見時,領一個新任務
依「任務表」由上而下,找第一個「領取分支」**在遠端還不存在**的任務(用 `git ls-remote --heads origin <分支>` 檢查)。分支已存在 = 已有人在做,跳過。
找到後:立刻建立該分支並 push 一個提交佔位,再照該任務檔(本分支 `tasks/` 底下)完整執行,開 draft PR,在 PR 留「【Codex】」說明你領的是看板上的哪一項。
全部任務的領取分支都已存在 → 回報「看板沒有可領的任務」後結束。

## 本線的 PR(步驟 A 用)
#196(GEO-246)、以及任務表中各領取分支所開出的 PR。

## 任務表
| 項 | 任務檔 | 領取分支 | 前提 |
|---|---|---|---|
| C1 | tasks/K1.md | feat/k1a-cutting-native-20261011 | 無 |
| C2 | tasks/198.md | fix/classify-rect-outline-20261011 | 無(疊在 #196 上) |
| C3 | tasks/K2b.md | feat/k2b-zero-room-impl | 無 |
| C4 | tasks/K4.md | feat/k4-pr-b-cursor | 無(疊在 #186 上) |
| C5 | tasks/K2a.md | feat/k2a-drafts-collection | 無 |
| C6 | tasks/PF.md | feat/pf2-obstacles-20261011 | 無(疊在 #190 上;PF-2 以後依序從上一段分支切出) |

## 共同規則
不合併、不 force push、不關 PR/issue、不改 repo 設定。PR 留言開頭「【Codex】」;「【WSL 裁判】」是 Claude 的驗證,「【dot】」與「【ChatGPT 審查】」是審查意見。不得假稱跑過 WSL。
