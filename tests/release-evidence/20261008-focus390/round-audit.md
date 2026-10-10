# 316／0 與 328／0 的身分，以及其後兩輪

每一輪只代表當時的 HEAD、工作樹與 runtime。後一次提交沒有把前一輪改標成自己。

harness 指 `geometry-web/grid_rule_lines_test.js` 的 SHA-256。`cdp_helpers.js` 與 `cdp_test.js` 在 `3574b47` 與 `9b97a39` 是同一份：`46d1a55c082f6a10571721370a709cfbf8aebb9df5661c04f51d18238d8befff`、`59804f52ae7df139352afa4899014596f14effea86c0839cdc8bfd020f672af1`。`app.js` 也同一份：`0eb8373cd7fdda7fd328312f8690d87ffc7804fbaa5b3c1d6b15d8263a1193c9`。bridge 來源與二進位在這幾輪沒有重編，SHA-256 `aa2cc6ae4fd47277c4620bf08bbc99ccae0ee48757c0728785528cfd1357736d`，`python tests/binaries.py status bridge` 對 `8982605` 仍是 fresh。

| 輪次 | git HEAD | 未提交差異 | harness SHA-256 | runtime | 結束碼 | 斷言 |
|---|---|---|---|---|---|---|
| 乾淨格線 | `3574b47bd02e2c2f2b77bf5fe6d67ff328bfaa72` | 無 | `6aca5014d3b8ff199a849a960959859e0798e6910578305b50ad945c5c2191a7` | `38021bc54308a464a56785a2e3106af3f2d10f11caac79a541a0b716ce2c3f7f`，開始時 fresh | 0 | 316／0，P88 107 |
| 400ms 焦點回歸 | `3574b47bd02e2c2f2b77bf5fe6d67ff328bfaa72` | `grid_rule_lines_test.js` 已改、證據目錄未追蹤 | `cee523ccc5ff4ca902dde5b52c7cdc336f9be2c478cd5b5d8b62139d9afd5b89` | `09fb8f1c4ebdd411a165677d73fbe22c977967e3692b80c98c74c7425aca5fdb`，fresh | 0 | 328／0，P88 119 |
| 可觀測等待，參數路徑要求重建 | `163c575756dedf31efff7842cdeb2f9de9726ba2` | 無 | `04ba411d82881d6e94ae58b133c286d581856d1c1b70d4a8184dd3eb731c4684` | `1d1fc4931086a75c3f728de9bab88b6dd90dcba9671e80916fa24412ea18baa5`，fresh | 1 | 266 通過後逾時，0 失敗斷言，未完成 |
| 參數路徑改等處理結束 | `8982605c83d0f27cec27790c0b407d946b0093fe` | 無 | `bf7b648d6d367446b9bf12f7b08e9c9957d4c0d0913e357d0c9684d594ded9b3` | `168bfaecbe12bf0adbf8def1ca67834fc1177305c76a72cd75045b36794388a6`，fresh | 0 | 346／0，P88 137 |

316 與 328 之間還有焦點回歸第一輪：HEAD 同為 `3574b47`，測試檔未提交，結束碼 1，325 通過、0 失敗，未完成。見 README 第 8 項與 `runs/grid-system-170-regress-1/`。那輪不是 328。

`09fb8f1c…` 與後來乾淨的 `9b97a39` 工作樹算出的 runtime 相同，因為那次未提交的測試檔就是 `9b97a39` 的 blob。執行當下的 HEAD 仍是 `3574b47`，所以 328／0 不是 `9b97a39` 的乾淨跑。

`8982605` 才是凍結提交後跑完的限定 `GEOMETRY_GRID_SYSTEM_ONLY`，不是完整主 UI，也不是完整驗收。1280 與 390 都到 P88。檢查器外在兩種寬度都觀察到釋放後重建（序號 112、212）。390 關閉抽屜也重建了（217）。1280 的參數對話框與兩種寬度的離開面沒有再重建。六條都在該狀態定案後才看焦點，舊回覆沒有回到 `#refGuideExpr`。持有中的完成條件為假。「搶回引用式會被判失敗」是判定式自檢：`stole(id)` 在 id 為 `refGuideExpr` 時為真，並讀到當時 `activeElement` 不是該 id。這不是變異測試，也沒有改產品。產品側的不搶焦點結果仍是其後的「舊查詢不搶回焦點」。

163c575 的失敗留在 `runs/grid-system-163c/`。那輪把參數對話框也要求成「必須再重建」，25 秒後逾時。產品沒有做第二次重建：參數編輯器換掉規則明細後，`paintQuery` 不再呼叫 `renderFaceInspector`。
