# 命令

工作目錄 `D:\geometry-axiom-async-qa`。私有 TEMP 與回報目錄都在本機暫存，不進提交。服務從 `geometry-web` 啟動：

```
python serve.py 8924
```

環境：`GEOMETRY_BRIDGE_EXECUTABLE` 指向上一段既有 bridge.exe，`GEOMETRY_MODEL_BASE` 指向上一段既有 model-base.exe。修正前回報目錄是 `feedback-before`，修正後是 `feedback-after`。

測試：

```
GEOMETRY_TEST_URL=http://127.0.0.1:8924/ GEOMETRY_ASYNC_REPLY_ONLY=1 GEOMETRY_CDP_PORT=9348 node geometry-web/space_model_test.js
```

修正前 `GEOMETRY_SPACE_TEST_DIR` 是 `space-before`，`NODE_EXIT 1`。改 `app.js` 後重開 8924，再以 `space-after` 跑同一命令，`NODE_EXIT 0`。

單元測試：

```
node --test tests/test_space_test_floor.js
```

結束碼 0，10 passed / 0 failed。這次在瀏覽器失敗輪之前已跑過；census 數字其後沒有再改。
