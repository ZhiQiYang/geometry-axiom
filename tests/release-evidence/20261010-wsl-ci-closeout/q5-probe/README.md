# Q5 CDP 探針 — Issue #123 空間卡片第二下點擊被 #btnZoom 接走

## 這是什麼

整合鏈阻塞項 ⑤（Issue #123）的獨立 CDP 探針。原始重現依據：

- `tests/evidence/cloud-takeover-20261009/known-races/README.md`：beam/slots × 1400/390，基底 3 過 / 1 敗。
- `tests/evidence/.../ui-single-room-243-public-v2/rounds/card-243-scoped/`，原始入口是
  `script.py --width 390 --only slots`（Playwright `dblclick` on
  `.ocard[data-kind="space"][data-id="1"] .ocard-frame`）。

情境：API fixture 建立 `space 1` 卡片後，用真實輸入做雙擊。缺陷版本上第一下
pointer-up 選取空間 → 手機版 inspector 佔入版面 → 按鈕列上移 → 同座標的第二下
pointerdown 落到 `#btnZoom`，空間工作區打不開。

前一版探針（run1/run2/run3-header-* 目錄是它的歷史收據）測的是物件畫布裡的
boundary 卡 731，在 main 上也通過，所以沒有牙齒。本版 `q5_card_second_click.js`
改為忠實移植原始 script.py：空間卡 `data-id="1"`、slots/beam 兩種 fixture、
1400×1000 / 390×844、真實 `Input.dispatchMouseEvent` 雙擊（第二下 clickCount=2，
瀏覽器自然合成 dblclick，與 Playwright `locator.dblclick()` 相同）。

## 執行方式

```sh
wsl -d Ubuntu-24.04 -- bash \
  /mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/q5-probe/run_q5.sh
```

無參數時依序跑 main `5cc1ffa1`、鏈頂 `72a3cbf4`、以及
`fix/closeout-wsl-red-20261010` 分支 head（本次為 `6615db6`）。也可帶 SHA 指定。

每個 SHA：在 `/root/q5-clones/<sha>` 建 clean detached clone → `npm run build` →
起 serve/start_local → 等 runtime probe 驗 fresh 指紋 → 跑
`q5_card_second_click.js`（2 case × 2 width = 4 cell）。收據寫進
`<sha8>/{runner.log,identity.txt,build.log,server.log,runtime.json,probe.log,probe.json,*.png}`。

輸入只有 `Input.dispatchMouseEvent` / `Input.dispatchKeyEvent`：無 DOM
`.click()`、無 programmatic focus、無 force click、落空不重試。斷言包含兩下
trusted pointerdown、第一下落空間卡 1、第二下不得落 `#btnZoom`、雙擊窗口與座標
漂移、以及 `oc.focus.t==='space'` + `#spaceWorkspaceLayout` 可見。

## 結果（2026-10-10，WSL Chrome 153）

| SHA | slots-1400 | slots-390 | beam-1400 | beam-390 |
|---|---|---|---|---|
| main `5cc1ffa1` | ✓ | **✗ 第二下落在 `#btnZoom`** | ✓ | ✓ |
| 鏈頂 `72a3cbf4` | ✓ | ✓ | ✓ | ✓ |
| 新 head `6615db61` | ✓ | ✓ | ✓ | ✓ |

牙齒成立：main 在 390 失敗且失敗訊息指名 `#btnZoom`——第二次
`pointerdown`/`click`/`dblclick` 的 `buttonId:"btnZoom"`、tag `BUTTON`，
`x=192.15,y=476.10` 在 `#btnZoom` rect `{x:193,y:441,w:44,h:44}` 上；
`oc.focus` 沒有進入 space workspace。失敗圖樣與原始證據「4 cell 中恰 1 敗
（slots-390）」一致。

`run_q5.sh` 整體 exit code 1（main 那一格失敗），屬預期；probe 本身在
`6615db61`/`72a3cbf4` 都 exit 0。

## 對應關係

| 原始 script.py | 本探針 |
|---|---|
| `--only slots` / `--only beam` | `FIXTURES.slots` / `FIXTURES.beam`（逐行移植 api line） |
| `--width 390` / 1400 | `Emulation.setDeviceMetricsOverride` 390×844 / 1400×1000 |
| 工具課程關閉 + `f` fit | `dismissLessons()` 真實點擊 `[data-guidance-dismiss]` + `Input.dispatchKeyEvent` KeyF |
| `locator('.ocard[data-kind="space"][data-id="1"] .ocard-frame').dblclick()` | frame 中心兩次 mousePressed/Released（clickCount 1、2） |
| 斷言 workspace 開啟 | `oc.focus.t==='space' && oc.focus.id===1 && !#spaceWorkspaceLayout.hidden` |

## 檔案

- `q5_card_second_click.js` — 探針本體
- `run_q5.sh` — 三 SHA 執行器（clone/build/serve/probe/收據）
- `5cc1ffa1/`、`72a3cbf4/`、`6615db61/` — 本次有效收據
- `run1-*`、`run2-*`、`run3-header-*`、`f147d945/`、`fix-same-as-tip/` — 前一版無牙齒探針的歷史收據，僅存檔

本目錄全部在 scratchpad，不進 repo、不 commit。
