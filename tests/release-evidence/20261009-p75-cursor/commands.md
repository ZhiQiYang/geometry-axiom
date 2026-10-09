# 命令

工作樹 `D:\geometry-axiom-inspector-draft`。啟動前狀態是空的，HEAD 是 `1101e730b1b120c9d65b8a33329bb6698e529c0e`。

原始 log SHA-256 `d6cf4bd6000ec090d1813b7e49997a11beffb0bb9516d22aae799fa72610689f`，3936 bytes。log 留在本機。

```
GEOMETRY_BRIDGE_EXECUTABLE=<既有 bridge.exe>
GEOMETRY_MODEL_BASE=<私有 fresh model-base.exe>
GEOMETRY_SELECTION_CURSOR_ONLY=1
GEOMETRY_TEST_URL=http://127.0.0.1:8942/
GEOMETRY_CDP_PORT=9542
python serve.py 8942
node geometry-web/cdp_test.js
```

沒有 `GEOMETRY_CDP_UPDATE_GOLDEN`。`NODE_EXIT` 是 `$LASTEXITCODE`。沒有停 pid 30184。
