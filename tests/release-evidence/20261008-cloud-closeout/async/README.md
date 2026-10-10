# #173 / #174：整合候選的獨立失敗再現

這份證據綁定 **`bdd1bf7812ba6126aab9ddffced43cd200ac977e`**，不能改標為後續交付 head。當時兩個 integration probe 尚未追蹤，repository 並非全乾淨；`binding.json` 保留逐輪原始 `git status --short` 與空的 tracked diff。受測 app.js／space-workspace.js 的開始、結束 hash 相同。

結論：#173／#174 在此候選仍有實際產品缺陷，尚未具備合併條件。這是新獨立探針，不是 #173 遺失原探針的復原，也不是修後通過或完整產品驗收。

**#173 覆蓋界線：**下文 `main` 是物件畫布的檢查器，`face` 是面內工作區；兩者都沒有進三視圖。#173 的三視圖直接編輯、edge 請求等待中切入三視圖／返回的晚回覆路徑仍未驗。#174 的三視圖手把再現不能替代這些路徑。成功 native 回覆確實到達，但未送出鄰邊被額外提交，因此成功套用後的 draft 保全驗收沒有通過。

| 檢查 | 1400px／390px 的結果 | 原始資料 |
| --- | --- | --- |
| #174 扣 A 的 proj → B 完成手把 → 釋放 A | B 手把 5→0，tool／B id／token 不變，完整 World 不變 | `browser-handles-3/handles-1400.json`、`browser-handles-mobile-4/handles-390.json` |
| #173 拒絕期間在原 input 再打新值 | main／face 均把新值 5151 清回 model 4000，World 不變 | 各 edge 輪的 `*-same-input-new-value.json` |
| #173 拒絕期間 renderer 換成新 input | main／face 均保留已拒絕的 2000，model 仍 4000，World 不變 | `*-replacement-rejected-value.json` |
| replacement 新值控制 | 5151 留在畫面，但經第二個 trusted change／native command 變成 model 5151 | `*-replacement-new-value.json` |
| 成功套用與未送出鄰邊控制 | 邊0成功成4200，鄰邊未送出的4242也經第二個change成為model4242；沒有只保留草稿 | `*-success-sibling.json` |

原生拒絕来自合法带孔面 731：將外環寬 4000 改為 2000，原孔會落到外環外。探針只扣住實際回覆，不替換 native 結果；輸入使用正常點擊、鍵盤和真 change 事件。`replacement-*` 的重繪是**明示呼叫產品 renderer 的故障注入**，不代表已驗某個特定 UI 動作會觸發這次重繪。`success-sibling` 使用成功產品提交自然到達的重繪。

## 查核方式

- [binding.json](binding.json)：完整 main／PR／受測候選 SHA、runtime／bridge／產品與探針 hash、逐輪 dirty 狀態、原件來源與 digest、私有 trace digest、dump 的 trace callId。
- 各單案 JSON 為原樣複製的結果；相鄰 `*-world-before.scene`／`*-world-after.scene` 從原 trace 原始 evaluate 結果提取，可直接逐字比對。
- 各輪 `executed-browser_probe.py` 是當輪精確脚本，已與當輪 hash 核對。共用 instrumentation 沒有變動。外層同名 `.command.json`／`.stdout`／`.stderr` 保存完整命令及退出碼；各輪退出碼為 1。
- 八張選定 PNG 只顯示本次合成 fixture。結果、scene、script 和圖已檢查，未見私人圖紙或憑證。
- 完整 Playwright trace、未抽取的 runtime 原收據留私有；**本公開包不含 trace，也不提供公開下載位置**。`binding.json` 明列原件 SHA 和省略欄位，不能把公開摘要當成完整原件。
- [REVIEW.md](REVIEW.md) 區分已重現缺陷與尚只有來源依據的 await 風險；[SHA256SUMS.txt](SHA256SUMS.txt) 驗證包內檔案。

保留的前置失敗不算產品失敗：stale runtime 的 HTTP409、三視圖隱藏的抽屜關閉鈕、390px 已 inline 顯示的檢查器。修正探針的是入口／抽屜前置，沒有改行為判定；mobile 只重跑 mobile，失敗原件沒有刪除。

## 重現與解除條件

這份 probe 的 repository 常數為 `/workspace/geometry-axiom`，使用既有核准 `/usr/bin/chromium`，sandbox 開啟。取得**獨占瀏覽器資源與隔離測試服務**後，才在該雲端環境執行；它會 reset 該測試 World：

```sh
python browser_probe.py --url http://127.0.0.1:18971/ --out /tmp/geometry-async-new-handles --only handles
python browser_probe.py --url http://127.0.0.1:18971/ --out /tmp/geometry-async-new-edges --only edges
```

輸出路徑必須尚不存在。原受測候選預期仍會重現本包失敗；修正後另綁新的 full SHA，不覆寫舊輪。

由既有唯一 app.js owner 先交回最新提交／dirty diff，再收斂共同原因：

1. 舊 draw／hit／drag 工作在任何 await 後都不能写入或清除新工作；edit→view→edit 必須辨識不同世代，清理也要遵守歸屬。
2. 拒絕只能撤掉該次提交的 draft 世代；跨 DOM rebuild 仍要辨識新輸入，main／face 共用一致規則。不可只檢查 `isConnected` 或工具名稱。
3. 查清重繪過程第二個 trusted change 的節點、焦點及時序，保證尚未送出的 5151／4242 不因重繪進 World。不要全面停用正常 change 來取得通過。
4. 精確修正候選需通過本包兩尺寸／兩 pane 情境，另補 #173 三視圖直接編輯和 pending edge reply 跨 view 切換。正常入口為 #btnObj／#btnCanvasView；三視圖本身只有 pick 結果與手把，不能硬顯示原本隱藏的 mainEdge 欄位當成驗收。再補 AGENTS 要求的完整 CDP／Space 相關回歸與独立審查。完整手機、IME等外部驗收保持另列；眼前缺陷不是外部-only阻塞。
