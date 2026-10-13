# #134 P88 重跑:FATAL 是否偶發(本機 Windows 11,2026-10-06T17:54Z–18:15Z)

- PR head `77c3847f32b2ba0616bab6c8d0c8370082c4941c`,tree `5660d1ef8836095a96d62d7f3bdcb18a6718cf56`,main `6562fa53d90de22b3e5492f2083199b26377a8c2`
- 隔離 detached worktree `D:\geo-bqa-134r`、port 8874;每輪重啟服務(`../../env/svc.ps1`)、獨立 CDP port(9481/9482/9483)與全新 Chrome profile
- `/runtime`:三輪皆 `fresh:true`、version `a7155144cb7f4463…`、root `D:\geo-bqa-134r`(`runtime-N.json`)
- 指令:`GEOMETRY_GRID_SYSTEM_ONLY=1 node geometry-web/cdp_test.js`(完整環境變數見 `p88rerun.sh`)

## 結果

| 次 | exit | 完成 | 通過/失敗 | P88 | FATAL |
|---|---|---|---|---|---|
| 原始(`../p88_cdp.log`) | 1 | false | 289/0 | 84 | `Rule line control unreachable [data-rule-cell-i]` y=1411.5,hit:false |
| 重跑 1(`p88-run1.log`) | 1 | false | 289/0 | 84 | 同一控制項,y=2021.5,hit:false |
| 重跑 2(`p88-run2.log`) | 0 | true | 310/0 | 105 | — |
| 重跑 3(`p88-run3.log`) | 0 | true | 310/0 | 105 | — |

**判定:間歇性失敗(2/4),不是單次偶發,也不是穩定重現。** 兩次失敗都停在 P88 390 寬度同一步(第 289 項之後),目標控制項 `[data-rule-cell-i]` 在 12 次 `scrollIntoView({block:'center'})` 重試後仍位於 844 視口外(`grid_rule_lines_test.js:9`)。原因未定:可能是 390 抽屜捲動容器的版面時序,也可能是測試等待條件不足;本輪未區分。

## 測試腳本的作廢紀錄(非產品問題)

在這份結果之前有兩次作廢嘗試,輸出已刪除、不計入:
1. 服務啟動輸出接 `tee`,python 繼承 pipe 寫端,腳本卡在啟動步驟約 5 小時,P88 未執行。
2. 停止上述任務後,孤兒腳本恢復執行並與新腳本共用 port/CDP/profile 競跑,產生 `Missing #refGuideCreate`、P70 斷言失敗等**污染結果**,不能當作 #134 的證據。

本版腳本(`p88rerun.sh`)加單例鎖、服務啟動不接 pipe、每輪獨立 CDP port 與 profile。所有本次啟動的程序只依記錄的 PID 停止(見 `summary.txt`)。
