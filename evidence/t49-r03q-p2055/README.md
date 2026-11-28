# T49：P2055 在建立舊骨架時遭工作階段拒絕

**處置：不採入工作包 Q 第一片。** 任務 #455 留言 7230501730 第 5 點要求 P 後不綠就退片。這份說明是給下一版補丁的重現紀錄，不是 `/4` 實作、正式量測或可合併的證據。分支不含候選的 T、P 或任何登錄變動。

## 在哪裡停住

在 `48d5f3887e8cb8d222307db62dbdea287fda8442` 重現，原件為 #205 留言 7229966888 的 T（SHA-256 `9422db8c303b9dfd5d2c20967ecc245f876100a3c7c8c513874cfc95dfb9222e`）與 P（`7631cca69f564d4529adf3da5e9df9afb8ca1c89dafdff4efe2c31b82641675b`）。套用後 28 檔逐一與交付 manifest 相同。

非 root、真 Chrome 158.0.8127.36、本次建置的服務 `fresh:true`。以下為在原樣 T+P 上的重現方式；使用專屬測試服務，不連使用中的專案：

```sh
ulimit -s 16384
npm run build
export GEOMETRY_TEST_URL=http://127.0.0.1:18839/
export GEOMETRY_FEEDBACK_DIR="$(node -p 'require("node:os").tmpdir()')/t49-fb-q"
export GEOMETRY_CHROME=/usr/bin/google-chrome GEOMETRY_CHROME_FLAGS=--no-sandbox
export PYTHONDONTWRITEBYTECODE=1
python3 -u geometry-web/start_local.py --port 18839 >/tmp/t49-p2055-server.log 2>&1 &
server=$!; trap 'kill "$server" 2>/dev/null || :' EXIT
for n in $(seq 1 30); do
  kill -0 "$server" || exit 2
  if python3 -B geometry-web/runtime_version.py --probe 18839 >/dev/null 2>&1; then break; fi
  sleep 1
done
python3 -B geometry-web/runtime_version.py --probe 18839 || exit 2
GEOMETRY_CANVAS_MODULE_ONLY=1 GEOMETRY_CANVAS_MODULE=P2055 node geometry-web/cdp_test.js
```

最後一條 exit **1**。關鍵輸出原文：

```text
FATAL: Browser evaluation failed: Error: {"ok":false,"error":"角材候選或工作世代已失效，請重新預覽。"}
FATAL_NETWORK: {"failures":[],"pendingAssets":[]}
```

`CDP_RESULT`：`"completed":false,"passedAssertions":0,"failedAssertions":0`。頁面連線已就緒；`newid 1`、建立第一片無孔面均成功。失敗在 T 的 `geometry-web/canvas_sections/P2055.js:72`：為建立 53 支的 v2 種子，先直接 fetch `/framing-template/preview`，再由 App 的 `apiRequest` 確認。後者在 `geometry-web/app.js:741` 檢查 `assertTimberPreviewToken`；前者沒走 `framing-template-session.js` 正常預覽時的 `beginTimberPreview` 與 `bindTimberPreview`。原生預覽結果不等於工作區已持有可確認的候選。沒有到達下一段的 1400／390 px 迴圈；**不是 `/4` 幾何斷言失敗，也不是兩寬通過**。

重出時需讓種子經同一工作階段預覽與確認，再以 `newid` 建後續的面。不能略過 v2 種子、放寬 owner 檢查或填入推估成本。

## 已區分的對照

| 裁判 | 本次在候選上的實得結果 |
|---|---|
| 原生與 HTTP（同一 T） | T：16 個方法、37 個失敗、exit 1；P：16 個方法、OK、exit 0 |
| Node 工作階段 | T：7 項中 6 個斷言紅、exit 1；P 含既有回歸：38/38、exit 0 |
| G 與產品逐支對照 | 308 案，274 接受、34 拒絕、差異 0。瀏覽器三個 fixture 重生為 53／53／58 支，bytes 與 T 相同 |
| 隔離撤回 | W 8、native/API 10、Node 9；各項實跑退出碼皆為 0／1／0 |
| 既有對照 | 原生模板 22 項 OK；同一 P 上獨立跑 P205（25 斷言）與 P2052（28 斷言），兩段均 exit 0 |

只有 P2055 是新段。上述局部結果不能用來導入它的成本，不能替代正式 CI，也不證明普通孔已在 App 可用。
