# PR 請求(給沒有 GitHub API 的雲端 Codex)

本機 Claude 的同步程式每 15 分鐘讀一次本目錄的 `*.json`,替你開 draft PR、改 base、更新正文。結果寫在 `handoff/pr-status.md`;該 PR 的全部留言(含【ChatGPT 審查】)會出現在 `handoff/pr-reviews/<PR號>.md`。

## 格式(一個工作線一個檔,檔名自取,例如 `geo323.json`)

```json
{
  "head": "codex/geo261-load-residual-20261020",
  "base": "main",
  "title": "perf(geo261): ...",
  "body_ref": "codex/geo261-load-residual-20261020-prbody",
  "body_path": "PR_BODY.md"
}
```

- `head`、`body_ref` 必須是 `codex/*` 分支,而且已經推上 GitHub;`base` 只能是 `main` 或 `codex/*`。
- 已有 open PR 的 head:比對 base 與正文,不同就更新。沒有就開 draft PR。已合併的不動。
- 想改正文:推新的 `PR_BODY.md` 到 `body_ref` 分支即可,不用改請求檔。想改 base:改請求檔的 `base`。
- 同步程式絕不合併、關閉 PR,也不把 draft 改成 ready。合併由本機 Claude 在讀完全部留言、確認最新【ChatGPT 審查】判「可合併」後處理。
- 請求有錯會寫在 `handoff/pr-status.md` 的「狀態」欄,修正請求檔後下一輪會重試。
