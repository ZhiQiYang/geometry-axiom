# 命令

探針腳本路徑：`<local-user>\AppData\Local\Temp\geometry-aux-20261008\focus390-repro.js`。複製進本包的是 verify-4 執行時的內容，檔名 `probe/focus390-verify.js`。

共用：

```text
FOCUS_HELPERS=D:\geometry-axiom-focus390\geometry-web\cdp_helpers.js
FOCUS_URL=http://127.0.0.1:8907/
GEOMETRY_CDP_PORT=9507
node <local-user>\AppData\Local\Temp\geometry-aux-20261008\focus390-repro.js
```

再現輪另加 `FOCUS_MODE=repro`、`FOCUS_OUT=...\focus390-repro`、profile `chrome-profile-5`。探針結束碼 0。

verify-3 另加 `FOCUS_MODE=verify`、`FOCUS_OUT=...\focus390-verify-3`、profile `chrome-profile-verify-3`。探針結束碼 1。

verify-4 另加 `FOCUS_MODE=verify`、`FOCUS_OUT=...\focus390-verify-4`、profile `chrome-profile-verify-4`。探針結束碼 0。

服務都是隔離工作樹 `D:\geometry-axiom-focus390\geometry-web` 的 `python serve.py <port>`，`GEOMETRY_BRIDGE_EXECUTABLE` 指向上面的 bridge.exe，`GEOMETRY_FEEDBACK_DIR` 在私人 TEMP。8907 各輪在驗證後停止。

乾淨限定流程（`runs/grid-system-170`，結束碼 0）：

```text
cwd=D:\geometry-axiom-focus390
GEOMETRY_TEST_URL=http://127.0.0.1:8911/
GEOMETRY_CDP_PORT=9511
GEOMETRY_GRID_SYSTEM_ONLY=1
GEOMETRY_FEEDBACK_DIR=<local-user>\AppData\Local\Temp\geometry-focus390-20261008\feedback-p88
GEOMETRY_CHROME_PROFILE=<local-user>\AppData\Local\Temp\geometry-focus390-20261008\chrome-profile-p88
GEOMETRY_GRID_SCREENSHOT_DIR=<local-user>\AppData\Local\Temp\geometry-aux-20261008\grid-system-170-shots
node geometry-web/cdp_test.js
```

開始時 `git status --short` 是空的，HEAD 是 `3574b47bd02e2c2f2b77bf5fe6d67ff328bfaa72`。`cdp_helpers.js` 的 `waitCardCanvasPos` 用的是這棵樹既有的嚴格版，沒有再套 #168。

焦點回歸第一輪（`runs/grid-system-170-regress-1`，結束碼 1）：

```text
GEOMETRY_TEST_URL=http://127.0.0.1:8912/
GEOMETRY_CDP_PORT=9512
GEOMETRY_GRID_SYSTEM_ONLY=1
GEOMETRY_FEEDBACK_DIR=<local-user>\AppData\Local\Temp\geometry-focus390-20261008\feedback-p88-regress
GEOMETRY_CHROME_PROFILE=<local-user>\AppData\Local\Temp\geometry-focus390-20261008\chrome-profile-p88-regress
node geometry-web/cdp_test.js
```

當時 runtime 是 `dcc5ee0b4c9164f9eb8a7e6d66f507c88ccd969463e24dcacd74c77f5a476b4c`，`fresh:true`。fatal：`Rule line control unreachable #btnNewProject`。

焦點回歸第二輪（`runs/grid-system-170-regress-2`，結束碼 0）：

```text
GEOMETRY_TEST_URL=http://127.0.0.1:8912/
GEOMETRY_CDP_PORT=9512
GEOMETRY_GRID_SYSTEM_ONLY=1
GEOMETRY_FEEDBACK_DIR=<local-user>\AppData\Local\Temp\geometry-focus390-20261008\feedback-p88-regress-2
GEOMETRY_CHROME_PROFILE=<local-user>\AppData\Local\Temp\geometry-focus390-20261008\chrome-profile-p88-regress-2
GEOMETRY_GRID_SYSTEM_SCREENSHOT_DIR=<local-user>\AppData\Local\Temp\geometry-aux-20261008\grid-system-170-regress-2-shots
GEOMETRY_GRID_RULE_SCREENSHOT_DIR=<local-user>\AppData\Local\Temp\geometry-aux-20261008\grid-system-170-regress-2-shots
node geometry-web/cdp_test.js
```

當時 runtime 是 `09fb8f1c4ebdd411a165677d73fbe22c977967e3692b80c98c74c7425aca5fdb`，`fresh:true`。bridge 仍是 SHA-256 `aa2cc6ae4fd47277c4620bf08bbc99ccae0ee48757c0728785528cfd1357736d`。
