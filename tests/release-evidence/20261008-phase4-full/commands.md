# 命令

工作目錄 `D:\geometry-axiom-inspector-draft`。先另開 8916，沒有使用 8915。沒有 `GEOMETRY_*_ONLY`，也沒有 `GEOMETRY_CDP_UPDATE_GOLDEN`。

```
$env:GEOMETRY_TEST_URL='http://127.0.0.1:8916/'
$env:GEOMETRY_FEEDBACK_DIR='<local-user>\AppData\Local\Temp\geometry-inspector-draft-20261008\feedback-phase4'
$env:GEOMETRY_CHROME='C:\Program Files\Google\Chrome\Application\chrome.exe'
$env:GEOMETRY_CHROME_PROFILE='<local-user>\AppData\Local\Temp\geometry-inspector-draft-20261008\phase4-chrome'
$env:GEOMETRY_CDP_PORT='9518'
node geometry-web/cdp_test.js
```

服務 banner 的 runtime 前綴是 `f2804c806880`。探針：

```
{"schema":"geometry-runtime/1","version":"f2804c8068805409ccc06cddea3fac6219f768706f9276e981948f1142a286b2","fresh":true,"root":"D:\\geometry-axiom-inspector-draft","pid":31516,"session":"ba75fc92a0794359b9126079015c9949"}
```

```
NODE_EXIT 1
```

外層 PowerShell 結束碼 0。歷時約 2069 秒。
