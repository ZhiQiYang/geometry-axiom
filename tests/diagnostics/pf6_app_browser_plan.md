# PF-6 App C1 v2：真 Chromium 與冷開核對

本稿配套 issue #454 工作包 C、issue #461 R2／issue #128。
本節的 Chrome 項目是待執行清單，不是已通過收據。
`P1286.js` 經 strict module 靜態檢查；本次作者環境未開 Chromium。

## 登錄與執行

新段是 `geometry-web/canvas_sections/P1286.js`，由既有 dispatcher 載入。
不改 `cdp_test.js`、歷史 golden、P2052 的 driver 白名單或 module 語法限制。
候選片段的 `assertions: 0`／`cost: null` 是原 `stage-module` 的輸出；正式守門應拒絕，
不能把下面幾何夾具的 16／12／13／9 寫成段落計數。

在已套 T→P、完成必要原生建置的隔離 checkout，先啟動自己的測試服務：

```sh
python3 -Bu geometry-web/start_local.py --port 18839
```

另個終端保留同一 checkout 和同一 feedback 目錄，再跑：

```sh
python3 geometry-web/runtime_version.py --probe 18839
GEOMETRY_TEST_URL=http://127.0.0.1:18839/ \
GEOMETRY_FEEDBACK_DIR=/tmp/pf6-app-feedback \
GEOMETRY_CHROME=/usr/bin/google-chrome \
GEOMETRY_CHROME_FLAGS=--no-sandbox \
GEOMETRY_CANVAS_MODULE_ONLY=1 GEOMETRY_CANVAS_MODULE=P1286 \
node geometry-web/cdp_test.js
```

服務啟動時也須給相同的 `GEOMETRY_FEEDBACK_DIR=/tmp/pf6-app-feedback`；
上述路徑只供新的測試服務，不沿用或停止使用者服務。若環境不需要 `--no-sandbox`，省略該變數。
這是 partial 診斷，不是兩片完整 acceptance。不要設 `GEOMETRY_CDP_UPDATE_GOLDEN`。

正式收據由 main 上既有 **Canvas section measurement** workflow 產生：ref 選套用分支，
section=`P1286`，保留原 artifact `canvas-section-P1286`。由能下載官方 ZIP 的 grokbot／本機 Claude：

```sh
node geometry-web/canvas_registry.js import-cost --id P1286 \
  --artifact-id ARTIFACT_ID --artifact ORIGINAL.zip
```

工具產生的實測 count/cost 原樣採入。改 `serve.py` 也會改已登錄 P2052 driver 的來源身分；
原 P2052 成本會因新的來源身分而報 `R386_CANVAS_COST_SOURCE`，必須重做 P2052 的正式量測／導入，
不修改其斷言或 pin。作者先在固定 main 上放入同一 P1286 module，以原 stage-module 產生候選，
再將工具原件帶入 T；這不代表 P 的 P2052 舊收據仍有效。
本段保持固定第二片尾 slot，不申請 `unit:auto`，因此不偽造 two-slot proof。
採入後仍須完整 canvas 1/2、2/2、complete coverage、R03/PF4A 及其他原 CI 閘門。

## P1286 的範圍與獨立預期

夾具是 300×300 完成面、100×100 板、3 mm 縫、明示 X=8 mm，進 PF-6 前沒有宿主、主格或角材。
fixture 的既有完成面／鋪排由原生 HTTP 建立；受測 PF-6 動作全部由真 CDP 滑鼠／鍵盤走一般 DOM，
沒有直接呼叫 PF-6 Session／Workspace 的狀態方法。fetch observer 只複製收發內容，不攔截、改寫或重送。

390×844 與 1400×900 各自走：

1. 物件面 → 面內屬性 →「面設定…」→「完成面／骨架…」→「完成面與鋪排」表單 →
   該正式鋪排的「建議角材」。入口是 `data-pf-action="suggest-timbers"`，不是另一個別名。
2. A、B 來源及主支方向初態空白；明選直接值 A=27、B=30，主支沿 U。
   實際 wire 必為 `roles.u=secondary`、`roles.v=primary`，revision／generation 保留字串。
3. 取得 16 個來源建議，初始一個也未勾選；按「全選」後仍須明按預覽。
   本 fixture 同跨距 alias 去重後是 12 支；建議與預覽都不增加正式物件、配號、dirty 或 history。
   suggest 與空選持租約但 token 是 null；非空候選 token 為正 uint32，預覽 idMap 為 null，
   createdDefinitions 的候選暫號有明確標示。正式 typed ID 只由確認回執列出。
4. 取消後逐字比較完整 dump、revision、identity、next IDs、project saved/dirty 與附件，history 物件身分不變。
5. 重開並重新明選，先全選，再取消 seam-primary k=0 的三個來源 alias。
   13 個明選來源重算為 9 支 D7；六個副支來源的最終長度依序為
   `164, 164, 55, 164, 164, 55 mm`，不能仍顯示初次建議的 `61, 76, 55`。
6. 表單逐項人讀長度、來源、門檻與承接結果；390 寬不水平溢出。
   真正點到確認、取消、全選、清空、被取消的三列與其他輸入，檢查 hit test。
7. 確認僅送一個帶原 requestId/session 的命令，增加一筆共享歷史及一次 native revision。
   保存定義含普通 D7、衍生宿主與 from-fill，不含 PF-6 token/setKey/generation 暫態資料。
8. 關閉表單，面內復原一次回到完整基準，重做一次回到完整結果；附件不變。

`P1286` 的 expected count 由正式實跑產生。上述數字是夾具幾何 oracle，不是執行成功聲明。
獨立原生幾何及 R43 掃描另見 `tests/pf6_app_oracle.py` 與 `test_panel_fill_builder_app_view.py`。

## 真 .gcanvas 冷開（獨立於 strict module）

服務層另有自動裁判 `PF6HTTPNative.test_real_http_new_service_reloads_sources_keys_and_r43_exactly`：
真正 HTTP suggest → select → confirm → dump，停止第一個自有服務，再起另一 PID／session，
用 `/upload/prepare` 與 `/upload/confirm` 載入原 scene，核對 dump、typed 定義、派生鍵及 R43。
每個服務的停止、程序群組與原回覆都有診斷欄位；沒觀測到的 child PID 明記 null，不能當作通過。
這個測試不啟動 Chrome、不經 `.gcanvas`，不能替代以下一般 App 開檔。

strict module 的受限閉包不允許 `fs`、child process、啟動另一原生服務或另一 Chrome；
本片不增加未審的 driver 類型，也不把重新整理／無痕分頁當冷開。
此步由雲端 Claude 在一般 App 實走，留原件及下列前後唯讀快照。

兩個尺寸各留一個已確認結果及原 archive；另外覆蓋已有同 fill 宿主／主格，以及含 R03 配方的專案。
一般 App 中完成 PF-6 → 檔案 → 另存新檔，保留真正下載的 `.gcanvas`，記 bytes／SHA-256。
先核 runtime fresh:true，再由下列唯讀 probe 取得基準；probe 不能替代任何產品操作：

```js
(async () => {
  const dump = await apiRequest('dump');
  const panelFill = await apiRequest('panel-fill-read');
  const references = await apiRequest('references');
  const engineering = await apiRequest('engineering-read');
  return {
    world: dump.text,
    state: panelFill.state,
    references,
    engineering: engineering.state,
    attachments: ReferenceWorkspace.context().featureAttachments,
    project: ReferenceWorkspace.getProjectState(),
    history: {undo: ReferenceWorkspace.history.undo.length,
      redo: ReferenceWorkspace.history.redo.length},
    pf6Open: !!document.querySelector('[data-pf6-workspace]'),
    displayed: [...document.querySelectorAll('[data-pf6-member],[data-pf6-support]')]
      .map(element => element.textContent)
  };
})()
```

關閉**自己的測試** Chrome 與測試原生服務，另啟新 port、新 service session、新 Chrome process 與
空白 `--user-data-dir`。保留兩組 PID、profile 路徑、啟動 argv 及 `/runtime` 原件。
由「檔案 → 開啟專案…」載入原 archive；禁止用 bridge `loadfile` 代替產品冷開。

預期：

- fresh runtime 指紋對應同一來源，服務 session 與 Chrome PID／profile 均不同。
- dump 逐字相同；來源定義／材料固定版本／卡片欄位／片鍵／縫鍵／衍生邊鍵／角材／R43 警告逐項相同。
- 保留 R03 配方及附件；PF-6 沒有增設自己的配方或新增 format 欄位。
- 開檔過程沒有 `/panel-fill/builder/suggest`、`/select` 或 `pf6-confirm`，
  也沒有重新明選、生成第二批角材、恢復可確認 token 或增加生成歷史。
- 存檔／開檔後的 history、saved／dirty 按原開檔契約判斷，不把整個專案身分等同舊 session。
- 缺來源、未知能力或篡改 typed 引用的檔，拒絕時現案 world／附件／dirty／保存狀態／history 不變。

## 具名撤回與紀錄

所有撤回只改出貨產品分支，原測試、section module、golden 與 registry 都保持原 bytes。
基準、撤回、復原各自啟動 fresh runtime／Chrome；只算指定斷言的 exit `0/1/0`。
無法啟動 Chrome、來源過期、timeout、crash、import error 或其他斷言不算 killed。

| 名稱 | 產品分支 | P1286 指定殺點 |
|---|---|---|
| `PF6_APP_AUTO_SELECT_ALL` | 建議載入即暗勾 | `PF6_DOM_EXPLICIT_SET` |
| `PF6_APP_USE_SUGGEST_GEOMETRY` | selected 畫面改用舊 suggestions | `PF6_DOM_READABLE_VALUES` |
| `PF6_APP_DROP_ENTRY` | 正式 fill 入口失去 handler | `PF6_DOM_ENTRY`，不能只算 wait timeout |

可執行腳本是 `tests/diagnostics/pf6_app_withdrawals.py`。先核對三個唯一錨點及撤回後語法：

```sh
python -B tests/diagnostics/pf6_app_withdrawals.py --kind browser --preflight
```

雲端在乾淨、已提交的套用分支，以本分支的真 bridge／model-base 及 Chrome 執行：

```sh
GEOMETRY_CHROME=/usr/bin/google-chrome GEOMETRY_CHROME_FLAGS=--no-sandbox \
python -B tests/diagnostics/pf6_app_withdrawals.py --kind browser \
  --bridge /tmp/geometry-tests/bridge --model-base /tmp/geometry-tests/model-base \
  --output /tmp/pf6-browser-withdrawals-UNIQUE
```

輸出目錄必須尚未存在、且在 repo 外。腳本直接沿用原 `browser_mutation_check.py` 的
隔離 process namespace、來源快照、fresh runtime probe、fresh Chrome profile、原 CDP footer
與 transport 判定；每次都設定 `GEOMETRY_CANVAS_MODULE_ONLY=1`、`GEOMETRY_CANVAS_MODULE=P1286`。
它不新增 driver 登錄型別，也不改既有 runner、golden 或官方突變帳本。
各組預期為基準 `0` → 指定 assertion 的完整紅 `1` → 原 bytes 復原 `0`。
結果、runtime 原件、stdout／stderr 及來源雜湊均留在輸出目錄。三組 Chrome 尚待實跑。

本機 Node renderer 撤回另用：

```sh
python -B tests/diagnostics/pf6_app_withdrawals.py --kind node \
  --output /tmp/pf6-node-withdrawals-UNIQUE
```

此模式依腳本的最新具名清單，對正 token、整輪 invalid、候選暫號、正式回執、
R43 實寬、完整能力清單與真正入口等逐項撤回；本機測試數與 `0/1/0` 原件見
issue #128 的 v2 證據總索引，不沿用 v1 的 9 案／5 組數字或 token 0 誤定義。
Node renderer／Session 的具名撤回不是 Chrome 收據；兩者結果分別報。
一次確認只增加一筆歷史由 `PF6_DOM_CONFIRM_ONCE` 與出貨 shared observer 的獨立 host suite
共同保留；本腳本沒有把未定義或未執行的第二筆歷史撤回寫成 killed。

## 尚未驗證

本作者環境：上述真 Chrome、正式 section count/cost、兩片全覆蓋、一般 archive 冷開均未執行。
Windows 原生對話框、實體觸控／IME、輔具及使用者驗收 L5 未核對。
派生宿主的物件畫布、面內畫布及參數使用位置呈現由工作包 A 負責；本片只驗三視圖與本表單，
不得把其餘呈現寫成已完成。三視圖另由實機切換後保留畫面與對照值，不能用本段表單斷言代替。
