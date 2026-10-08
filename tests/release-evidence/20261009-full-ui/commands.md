# 命令

工作樹 `D:\geometry-axiom-inspector-draft`。啟動前 `git status --porcelain` 是空的，HEAD 是 `ce74dc949168b597e33ec00110ce57f26ae51ff8`。

私有 TEMP 目錄只放這輪的 log、feedback 與 Chrome profile，沒有提交。原始 log SHA-256 `9de6d1d5858a37154ed99bd9a8a6763786720b372188a254b419ebcd0910bcf7`，534908 bytes。log 留在本機，不進 git。

```
GEOMETRY_BRIDGE_EXECUTABLE=<既有 bridge.exe>
GEOMETRY_MODEL_BASE=<既有 model-base.exe>
GEOMETRY_TEST_URL=http://127.0.0.1:8931/
GEOMETRY_CDP_PORT=9532
python serve.py 8931
node geometry-web/cdp_test.js
```

`node` 的輸出追加到同一份 log，接著寫入 `NODE_EXIT` 與 `$LASTEXITCODE`。沒有用 `Tee-Object`。服務結束時只停這輪 pid 40308 的子行程，沒有停 pid 30184。

bridge 沒有重編。model-base 沒有重編。沒有 `GEOMETRY_CDP_UPDATE_GOLDEN`。
