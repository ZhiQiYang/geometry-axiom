# 過期投影回覆不得清掉較新的編輯手把

這是草稿 PR #174 的接續紀錄。產品父提交是 `b0ef9bcfb6133e6463c859952270231f8e740363`。工作樹是 `D:\geometry-axiom-async-qa`。沒有改 `main`，沒有合併，沒有部署。

## 修正前

`app.js` 尚未改。`drawEditHandles` 在 `uvMap` 的 `proj` 回來後，只要代號或工具已不是這一次編輯，就呼叫 `previewClear()`。

測試握住第一次由 `drawEditHandles` 發出的 `proj`，再按檢視、再按編輯，讓較新的編輯畫完手把，然後釋放舊回覆。

- 桌面 1400：釋放前 `handles` 5、`editLoops` 1、工具是 edit；釋放後 `handles` 0，工具與 `editLoops` 仍在。
- 390：同樣是 5 變 0。
- 既有 6 條晚回覆斷言仍通過。群組預期 8，通過 6、失敗 2。另有一條完整性失敗。
- `NODE_EXIT 1`。`completed: false`。passed 10，failed 3。
- runtime `6c320952b78b69fd6297e752937e68655d6b85f0a7ef2920f80df1682a2d2e03`，fresh true，pid 2572，session `52946a2dd38349f4b82b8be718b2f773`，port 8924，CDP 9348。
- `async_reply_ui_test.js` SHA-256 `152c23ab908bc4c205a22d1fb2064536e3af121d4bcd2dbc7e1edad60f3553aa`。
- 當時 `app.js` SHA-256 `c6cfc99e54a9daf05dad7ee442cbbd1203dd730736834d4f84a60b7d5bbbf4c8`。
- `space_test_floor.js` SHA-256 `ae43121580fcf6a1b8cd9c7baa98751991e4f9ce31881553cbe57cb6780d084f`。

`before/final-state.png` 是整輪結束時的畫面，不是失敗當下的單獨截圖。

## 修正後

過期代號或已離開編輯工具時直接返回，不呼叫 `previewClear()`。同一次編輯若自己的 `editLoops` 已空，仍清除自己的預覽。

同一支測試再跑：`NODE_EXIT 0`，passed 12，failed 0，`completed: true`。async-reply-ui 預期 8、通過 8、失敗 0。1400 與 390 的新手把都保留。

- runtime `497e9cc85a60dd9a738eb8e9ef8ff49c555ad34255afa3615c6fd4e9586287bb`，fresh true，pid 7536，session `e7db6a8a56c34dffaac51835123ea99f`，port 8924，CDP 9348。
- 修正後 `app.js` SHA-256 `e6ab3b4e24d93b45e8d68b6e799879637750a08764df31ae0a0855a4fe7932a9`。測試腳本雜湊與修正前相同。

## 沒有重跑

`b0ef9bc` 的合成格網保存重開 24／0、`8982605` 的 GRID 346／0、以及 #173 的完整主 UI 都沒有重跑。這次只跑變更後的 `GEOMETRY_ASYNC_REPLY_ONLY`。狀態文字與 `navigationSequence` 沒有新斷言。實體手機、人工 IME、作業系統存檔對話框未驗。

橋接器沿用既有二進位，SHA-256 `aa2cc6ae4fd47277c4620bf08bbc99ccae0ee48757c0728785528cfd1357736d`，沒有重編。model-base SHA-256 `03a487c77ee20adcc73624adc947027019c071cff9025d1c7ba8cc5a81c8476f`，沒有重編。port 8915 沒有停止。
