# #47 F4a：原生兩端支撐身分／局部面唯讀投影

本切片依賴 PR #56 的 schedule／CSV／generation identity，未重做該批。
工作分支 `feat/native-timber-support-projection-20261003`，最終依賴基底
`c1bc56675a329d81210265ade69e148cf8825ea3`（PR #56 head，已含 main 的畫布效能修正）。
初始基底 `b06464689ec2377b165a21aa0e395323baccd4c6`，本分支在交付前只 fast-forward
整合 owner 的新 head，沒有改寫其共用檔。開工唯讀查核 main
`d40dee0cc6015d2d7b11adafe32909fab7a9668a`；兩者的 `current_geometry.c`、
`references.inc`、`assembly_generation.inc` 相同。PR #56 尚未合併，應先整合其依賴。
root／整合 owner 為 thread `01a100b5-800b-75f2-9a02-71ee53e550ba`；本 cloud 的
`collaboration.send_message` 回覆該 agent 不存在，因此以本文件、draft PR 及任務結束回覆交接。

## 已實作

`timber_support_projection.inc` 只讀正式 World，以原生 `collect_stop_faces`／
`pick_stop`／`stop_ref_candidates` 取得可證明的關係；不重算料長、不調用交易、不寫 World。
每支 placed Timber 一筆，保留 typed timber／surface ID（包含 0），並輸出兩個實際端面：

- `start`／`finish` 依角材局部長度方向，不依 UV min/max 或 R21 選擇器陣列順序。
- 自動跨距沿 R6/D11 的全寬、唯一及 shadowing 選擇；`between` 沿 R21 只保留明指的合法候選。
- 外輪廓／孔邊保留 boundary ID、原環 edge／hole index。自帶矩形屬 placement，
  不把其有效輪廓偽造成 boundary 0。
- 角材擋面保留 timber ID、原生局部面名與向外的整數世界法向。
  `StopFace.edge_index` 只是 UV min/max 序號；局部 B0/B1／START/END 由
  `timber_get_face_room` 與真實基底核對，能處理負向長度、負深度與旋轉／立面承載面。
- owned 分件及 owned 支撐保留 instance/member/binding、固定 rule version/fingerprint、
  instance 和 binding fingerprint，與原生 ownership mapping 核對。
- 無唯一證據時 `status:"unknown", relation:null`；不能用端點座標、名稱、mesh 或材料習慣補造關係。

投影為 additive `references.timberSupports`，schema `native-timber-supports/1`：

```json
{
  "schema": "native-timber-supports/1",
  "sourceFingerprint": "<同一 references 回覆的 64 字元定義 SHA-256>",
  "entries": [{
    "id": 3, "surface": 1, "owner": "<原生 owned 來源物件，未取得時 null>",
    "start": {
      "status": "exact", "at": 514, "crossRange": [1487, 1514],
      "relation": {
        "kind": "timber-face", "source": {"kind":"timber","id":1},
        "localFace": "B0", "normalWorld": [1,0,0],
        "owner": "<支撐角材的原生 owned 來源物件，未取得時 null>",
        "surface": 1, "stop": {"axis":"u","at":514,"range":[20,2980],"fixity":"fixed"}
      }
    },
    "finish": "<相同端面結構>"
  }]
}
```

上例是欄位示意；`owner` 及 `finish` 的文字佔位不是傳輸格式。
owner 的實際欄位為 instanceId/memberId/bindingId/ruleId/ruleVersion/
ruleFingerprint/instanceFingerprint/bindingFingerprint。
邊類 relation 使用 `kind:"outline-edge"` 或 `"hole-edge"`、typed source、
edgeIndex/holeIndex，localFace/normalWorld/owner 為 null。

來源版本使用正式定義 fingerprint；不加入會在 reset／load／undo 後不同的服務流水號。
原生 references 的既有 scene round-trip 全等契約保持。canonical 定義相同即同來源版本；
正式定義改變則 fingerprint 改變。畫布位置不決定支撐來源。

`timber-supports.js` 包裝 PR #56 的 `TimberSchedule`，只追加讀投影；原生計量集合、
尺寸、選取、排序、單位與匯出前 freshness guard 仍由既有 schedule 決定。
版本／身分／已知所有權不相符時拒絕導出；缺投影能力或缺某筆證據保持未知。
`sourceText` 在既有可展開尺寸來源段落顯示起末端局部面；CSV 保留全部舊欄位，
追加 support_source_fingerprint/start_support_provenance/finish_support_provenance。
引號、換行、公式樣式防護仍使用原 CSV 實作。

## 整合 owner 的最小接線（尚未寫入共用檔）

本分支只有新檔，沒有修改 app.js、reference-workspace.js、project-store.js、
index.html、reference_bridge.inc、測試總註冊／golden、公理或核心。

1. 在 `reference_bridge.inc` 的 `cmd_references` 前 include 本投影；
   於 timbers 陣列結束、specs 陣列開始前輸出同一回覆的 additive 欄位：

   ```c
   #include "timber_support_projection.inc"
   /* ... cmd_references, after the timber loop ... */
   fputs("],\"timberSupports\":",stdout);
   json_timber_supports(&g_world,fingerprint);
   fputs(",\"specs\":[",stdout);
   ```

2. 在 `index.html` 的 `timber-schedule.js` 之後載入 `timber-supports.js`。
   它包裝原 global API，因此既有 `app.js` 的 `derive/sourceText/csv` 入口即使用新投影。
   沒有新增可見 UI 入口，既有可展開來源段落與 CSV 共用；不新增常駐說明區塊。
3. 在 `tests/run_all.py` 註冊 `test_timber_support_projection`（其 helper 自建隔離 bridge），
   並加入 `tests/test_timber_supports.js`。前者 13 tests，後者 8 tests。
   調整同版 expected counts。這兩個檔目前故意未競寫；現行 registry 會明確列出未註冊，
   不能把完整 run_all 宣稱綠。
4. 於現有 CDP harness 接入 `timber_supports_browser_test.js`，傳既有 send/eval_/sleep/
   click/waitForUI/exceptionCount。另設 TEMP 的 `GEOMETRY_SUPPORT_SCREENSHOT_DIR`，
   本插件新增 10 checks，與既有 P80 的 23 checks 一同保留並重跑全量 golden。
5. 以最後整合 head 重跑必要 native／完整 CDP／space suite；再由 merge owner 決定合併。

`tests/_timber_support_bridge.py` 在 TEMP 的真 bridge build inputs 注入缺少的 native hook；
owner 已正式接線時保留唯一一份輸出，只轉接 projection include 至受測來源。
獨立 review 發現初版會在正式接線後失敗；已修正並加入接線／mutant include regression。
它另有 test-only fault injection，在 heap copy 中拿掉來源或提供歧義／FREE 候選，
確認未知不能假變已知；**這些測試指令不會加入正式 bridge**。
雲端瀏覽器驗證由 Playwright response route 注入 index script tag；服務、原生資料、
既有 UI 操作与真 gcanvas／CSV 是實際執行，接線暫存，不能宣稱已發布到正式 UI。

## 雲端驗證與邊界

- 69/69 native（本批 13 + references 35 + generation 21），0 skip。
  使用 GCC、隔離實際 bridge、64MiB stack。初輪 references round-trip 抓到服務流水號
  導致 13 failures；移除該非 canonical 欄位後全部通過，沒有改既有測試以放行。
- 已套用文件中正式接線的 TEMP reference bridge 另編譯並跑同 69/69，0 skip；
  確認 helper 在 owner 整合後不會重複注入或失效。
- 同 69/69 在 ASan/UBSan 通過；detect_leaks=1、abort_on_error=1、halt_on_error=1，無診斷。
- Node 17/17（新增 adapter 8 + 既有 schedule 9），0 skip。
- TEMP 的 B0/B1 對調 mutant 實際編譯成功，13 個 native tests 出現 7 個 assertion failure、
  exit 1；能抓到局部面錯配，不靠編譯錯誤或 skip 變紅。mutant 沒有進分支或 push。
- 真 Chromium／Playwright：新增 support 10/10 + 既有 P80 23/23；1400×900 和390×844，
  實際點料單／來源、產生 CSV、保存重開、六種遲到／失效 CSV guard、0 console/page errors。
  畫面未空白、來源／選取／保存證據均由現有應用取得；截圖放 TEMP，未提交或覆寫既有截圖。
  最終依賴 head c1bc566 的 native／bridge／schedule 核心與前述受測版相同；其新畫布
  與 runtime/cdp 修正保留，browser 在 fast-forward 後重新驗。
- 暫存驗證資料：`/tmp/geometry47-support-verification/`，native build input 与 screenshots
  不屬交付來源；parent 需以最後整合 SHA 保存／重跑所需證據。

重跑命令：

```sh
ulimit -s 65536
python -m unittest tests.test_timber_support_projection -v
node --test tests/test_timber_supports.js tests/test_timber_schedule.js
```

更廣 native 可先以 helper 在 TEMP 建支援投影 bridge，再以 GEOMETRY_TEST_BRIDGE 和
GEOMETRY_TEST_SUPPORT_BRIDGE 同指該路徑，跑上述三個 suites。
ASan/UBSan build 另設
`GEOMETRY_SUPPORT_CFLAGS='-O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer'`。

本輪沒有實體手機、OS 選檔／下載、Windows/GDI 或 actual platform QA。
沒有部署／合併、付費、帳務或 CI 設定操作；GitHub Actions 已知 included minutes 用盡，
不重跑 CI。完整最終整合與正式接線仍待 owner；#47 的空間模型快照適配及 F4b 保持未完成。
