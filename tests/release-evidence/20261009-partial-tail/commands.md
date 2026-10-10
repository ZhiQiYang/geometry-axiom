# 命令

工作樹 `D:\geometry-axiom-inspector-draft`。四輪啟動前狀態都是空的，HEAD 都是 `7dfda00df6da60baae4e9a5c846e8feae3b2885c`。

四份原始 log 留在本機：

- parameters.log SHA-256 `c2fb94375b1b4fda4bf882408147cdb642e7e659a50b65e70a47a007874ef4a1`，7543 bytes
- assembly.log SHA-256 `b17543138abe298cc9cc203c85453659870591404bc162cdd01790bc0dedfb82`，10864 bytes
- timber.log SHA-256 `d4cbb525c2614ac5bc9553450ac8a74179e6dad7469fdde436671a118ad2b53b`，7427 bytes
- room.log SHA-256 `47cee9bed95f60cc1172fa7c47eb9f6ed0a3a881d6e77dab5886b27d58ad4c0f`，13595 bytes

每一輪都是：

```
GEOMETRY_BRIDGE_EXECUTABLE=<既有 bridge.exe>
GEOMETRY_MODEL_BASE=<私有 fresh model-base.exe>
GEOMETRY_<ONE>_ONLY=1
GEOMETRY_TEST_URL=http://127.0.0.1:<port>/
GEOMETRY_CDP_PORT=<cdp>
python serve.py <port>
node geometry-web/cdp_test.js
```

沒有同時設兩個 ONLY flag，也沒有 `GEOMETRY_CDP_UPDATE_GOLDEN`。上一輪服務先停，才開下一輪。沒有停 pid 30184。外層四輪都結束後的結束碼是 0。
