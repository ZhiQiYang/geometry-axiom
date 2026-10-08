# 命令

工作目錄都是 `D:\geometry-axiom-inspector-draft`。

```
$env:GEOMETRY_BRIDGE_EXECUTABLE = '<local-user>\AppData\Local\Temp\geometry-focus390-20261008\geometry-tests\bridge.exe'
node geometry-web/edge_draft_redraw_test.js
```

before 用 PowerShell `2>&1 | Out-File`，結束後讀 `$LASTEXITCODE`，寫入 `NODE_EXIT 1`。
redraw-commit 用 `cmd /c`，`%ERRORLEVEL%` 在同一行就被展開，log 裡的 `NODE_EXIT 0` 不能用。
after 用 PowerShell `*>>`，結束後讀 `$LASTEXITCODE`，寫入 `NODE_EXIT 0`。

三輪的原始 log 分別在 `before/console.log`、`redraw-commit/console.log`、`after/console.log`。
