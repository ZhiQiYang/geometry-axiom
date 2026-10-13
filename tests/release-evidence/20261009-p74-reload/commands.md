# 命令

工作樹 `D:\geometry-axiom-inspector-draft`。啟動前 `git status --porcelain` 是空的，HEAD 是 `181fc76049b2b2d001957d2ee0008448bbf5b024`。

model-base 只建在私有暫存目錄，指令是 `python tests/binaries.py build model-base`。`TEMP` 指到該私有目錄，所以沒有寫進共用的 `geometry-tests`。建置結束碼 0，inspect 是 fresh。

原始 log SHA-256 `0547cfd639871dfbc71fa3a9c2e084d8d56f8d0133bebe0fc9e2a3850aaa10d6`，7154 bytes。log 留在本機，不進 git。

```
GEOMETRY_BRIDGE_EXECUTABLE=<既有 bridge.exe>
GEOMETRY_MODEL_BASE=<私有 fresh model-base.exe>
GEOMETRY_UX_REFINEMENT_ONLY=1
GEOMETRY_TEST_URL=http://127.0.0.1:8941/
GEOMETRY_CDP_PORT=9541
python serve.py 8941
node geometry-web/cdp_test.js
```

沒有其他 `GEOMETRY_*_ONLY`，也沒有 `GEOMETRY_CDP_UPDATE_GOLDEN`。`node` 的輸出追加到同一份 log，接著寫入 `NODE_EXIT` 與 `$LASTEXITCODE`。服務結束時只停這輪 pid 40864 的子行程，沒有停 pid 30184。
