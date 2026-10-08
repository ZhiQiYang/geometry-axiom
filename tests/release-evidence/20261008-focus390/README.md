# 390px 規則線焦點證據（PR #170）

這包是給 dot 讀的去敏紀錄。本機使用者家目錄已改成 `<local-user>`。Chrome profile、回報目錄與 bridge.exe 本體不在這裡。每份檔的 SHA-256 見 `SHA256SUMS.txt`。

## 怎麼讀

1. `binding.json`：head、tree、runtime、bridge 身分、命令與退出碼。
2. `runs/focus390-repro/`：補丁前的正式 UI 再現。`probe.log` 由上到下保留探針自己的失敗，最後一輪才走到規則線。`status.json` 只覆寫成最後一輪，結束碼 0 代表「把焦點丟失再現出來」，不是產品通過。`after-drag.png` 是更早畫矩形沒有落下面的畫面，不是焦點判決。
3. `runs/focus390-verify-4/`：補丁後的通過輪。結束碼 0。
4. `runs/focus390-verify-3/` 與 `verify-3-exclusion.md`：同一補丁上，390 Tab 因探針送了 Escape 而失敗。這輪排除，不刪。
5. `probe/focus390-verify.js`：verify-4 實際執行的探針。verify-3 比它多一次 Escape。再現輪用的是更早的腳本，位元組已被後來的修改蓋過，可觀察行為以該輪 `probe.log` 與 `status.json` 為準。
6. `bridge/bridge.exe.fingerprint.json`：二進位 SHA-256 與編譯當下的來源檔雜湊。exe 受 `.gitignore` 的 `*.exe` 排除，不進 git。
7. `runs/grid-system-170/`：乾淨 `3574b47`、工作樹沒有未提交修改時的 `GEOMETRY_GRID_SYSTEM_ONLY`。結束碼 0，316 通過、0 失敗，P88 在 1280 與 390 都跑完。runtime `38021bc54308a464a56785a2e3106af3f2d10f11caac79a541a0b716ce2c3f7f`。這不是完整主 UI。指定的截圖目錄當時是空的，逐項結果在 `suite.log`。
8. `runs/grid-system-170-regress-1/`：加上三類焦點回歸後的第一輪。1280 與 390 的焦點斷言都通過，結束碼仍是 1。390 離開面時打開的左側抽屜蓋住下一個 `#btnNewProject`。這輪排除不掉，也不能把 325 標成後來的通過輪。runtime `dcc5ee0b4c9164f9eb8a7e6d66f507c88ccd969463e24dcacd74c77f5a476b4c`。
9. `runs/grid-system-170-regress-2/`：測試改為先用既有的 `#toggleLeft` 關上那個抽屜。結束碼 0，328 通過、0 失敗，P88 為 119（比乾淨輪多 12 項焦點斷言）。runtime `09fb8f1c4ebdd411a165677d73fbe22c977967e3692b80c98c74c7425aca5fdb`。畫面在 `shots/`。仍只是 `GEOMETRY_GRID_SYSTEM_ONLY`。

## 服務

見 `server-lifecycle.json`。改前服務的版本前綴是 `526f08427f84`。補丁後通過輪與乾淨 P88 使用的 runtime 都是 `38021bc54308a464a56785a2e3106af3f2d10f11caac79a541a0b716ce2c3f7f`。結束碼 1 的那幾次是驗證後主動停止，日誌沒有橋接器崩潰。三類焦點回歸若改到 `geometry-web` 的測試檔，runtime 會換新字串，必須另記，不能把 316 標成新版。
