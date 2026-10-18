# GEO-261 六個瀏覽器 job 基準報告

測試來源固定為 `e64aa6359d600f43313ec9d7ba1112c465b6a40c`。報告產生時間：2026-10-18T12:04:15.141411+00:00。
本報告只適用於這個測試 SHA；報告分支或之後的 integration head 不等於已驗來源。

六個 job 已有終止收據。
可由完整證據確認通過：2/6。狀態計數：`{"failed": 4, "passed": 2}`。

| job | 工作時限 | 狀態 | harness exit | 工作秒數／含封存秒數 | 通過／失敗斷言 | harness 完整 | 原始 log |
|---|---:|---|---:|---:|---:|---|---|
| canvas | 35 分鐘 | 失敗 | 1 | 1839.618 / 1842.06 | 1593 / 1 | 否／未取得 | [canvas/test.log](canvas/test.log) |
| assembly | 15 分鐘 | 失敗 | 1 | 309.483 / 311.804 | 115 / 1 | 否／未取得 | [assembly/test.log](assembly/test.log) |
| documents | 10 分鐘 | 通過 | 0 | 90.117 / 92.344 | 47 / 0 | 是 | [documents/test.log](documents/test.log) |
| grid | 15 分鐘 | 通過 | 0 | 639.684 / 642.101 | 350 / 0 | 是 | [grid/test.log](grid/test.log) |
| space | 15 分鐘 | 失敗 | 1 | 472.037 / 474.37 | 127 / 2 | 否／未取得 | [space/test.log](space/test.log) |
| timber | 20 分鐘 | 失敗 | 1 | 254.365 / 256.757 | 24 / 2 | 否／未取得 | [timber/test.log](timber/test.log) |

斷言數不是端到端情境數。逾時或 fatal 前的已執行斷言，不能代表未執行範圍通過。

## 環境與執行差異

Debian GNU/Linux 13.6、Linux 6.18.55 x86_64；GCC 14.2.0、Python 3.12.14、Node 24.19.0；真正 Google Chrome 155.0.8059.84；Noto Sans CJK TC；stack 16 MiB。完整原始版本見 [environment.json](environment.json)。
Chrome 位於 `/workspace/geo261-tools/google-chrome-155.0.8059.84/opt/google/chrome/google-chrome`，由官方 HTTPS／簽章／套件 SHA-256 驗證後解壓。CI 路徑為 `/usr/bin/google-chrome`；本次沒有使用 Chromium 冒稱 Chrome。
各 job 預定流程依序為 `npm run build`、獨立 Linux `start_local.py --port 18839`、fresh runtime probe、原 harness；實際執行到哪一步以該 job 收據為準。CI 時限數值維持 35／15／10／15／15／20 分鐘；本機時限涵蓋 build、服務啟動、probe 與 harness，清理／封存另計。CI 的 checkout、字型安裝與 artifact upload 邊界不同，故不宣稱整個 CI wall-clock 完全相同。
已開始的 job 使用短 `/tmp` 與獨立 XDG/profile、feedback、screenshots、downloads；完成後把實際證據另封存至該 job `artifacts/`，保留來源路徑與 SHA-256 manifest。只清理本 runner 擁有的 process group。所有繼承 GEOMETRY 旗標先清除，不更新 golden，也沒有放寬斷言。

## 每個 job 的命令與證據

### canvas

Harness：`node geometry-web/cdp_test.js`；scope 旗標：`(無)`。

consoleAPICalled 僅列印 [console]，未保留類型，也沒有獨立 console.error gate。非預期例外會增加 failedAssertions；僅 full canvas 的 P38 刻意注入 fb-auto-probe，仍會計入 uncaughtBrowserExceptions，因此該欄不等於非預期例外數。

起迄：2026-10-18T11:03:30.993615+00:00 → 2026-10-18T11:34:13.053406+00:00；測試來源與收據：[result.json](canvas/result.json)。
Runtime：fresh 與自建服務 PID 均有收據。兩次 probe 均在 harness 啟動前，未宣稱另做執行後 probe。
原始命令、各步起迄／timeout／底層 exit、server 清理與環境全部保留在 [browser-stage-results.json](browser-stage-results.json) 的此 job row。
Golden：`not compared (run did not complete)`。

原始 fatal：

```text
Unexpected native dialog at === P72B. 更名保留相位差及來源 ===: confirm 建立一份空白新專案，切換為新的專案識別及「未命名專案」。目前尚未保存的變更不會自動寫入檔案。本次切換可一步復原；僅保存在本頁的形狀特徵參數不會恢復。確定繼續嗎？
```

原始檔案：
- [canvas/archive-wait-trace.log](canvas/archive-wait-trace.log)：343 bytes；SHA-256 `78d9b5e359a2b72ddc26e381bac928ec662da513143b1f19ccc34c48c0f14b2a`。
- [canvas/build.log](canvas/build.log)：1361 bytes；SHA-256 `1534d9b2aa635dfb1294fa815b24d200860255b116425ececdc48eea832013ad`。
- [canvas/runtime-final-probe.log](canvas/runtime-final-probe.log)：225 bytes；SHA-256 `876e540cb11e356a76655578c1f672b169f510b76c8958397161b3255f7d9ec0`。
- [canvas/runtime-probe.log](canvas/runtime-probe.log)：299 bytes；SHA-256 `c410b938e6e3cfa07deb20bd03a219eea28c46b7fad6f4c6ca5e3499cb011b98`。
- [canvas/server.log](canvas/server.log)：176011 bytes；SHA-256 `75b1390917ea4f93f764ce89163a90b08706654589802f2ab6dd03a2dc597097`。
- [canvas/test.log](canvas/test.log)：187657 bytes；SHA-256 `f78f81c88ee64c7604b75cd6fd88aeb2907ae877304a7d51c5ed494abb65dd1d`。
- [canvas/result.json](canvas/result.json)：11608 bytes；SHA-256 `98613774d1a5fa9f328945af72406cae3a5c99da0615417c88e6e8c71a053ed9`。
- [canvas/artifact-manifest.json](canvas/artifact-manifest.json)：106044 bytes；SHA-256 `407e9699e2de0ba532adeb82090bb3ed9556339ed09ed1a8abea9646af067770`。

### assembly

Harness：`node geometry-web/cdp_test.js`；scope 旗標：`GEOMETRY_ASSEMBLY_ONLY`。

consoleAPICalled 僅列印 [console]，未保留類型，也沒有獨立 console.error gate。非預期例外會增加 failedAssertions；僅 full canvas 的 P38 刻意注入 fb-auto-probe，仍會計入 uncaughtBrowserExceptions，因此該欄不等於非預期例外數。

起迄：2026-10-18T11:34:13.055642+00:00 → 2026-10-18T11:39:24.859222+00:00；測試來源與收據：[result.json](assembly/result.json)。
Runtime：fresh 與自建服務 PID 均有收據。兩次 probe 均在 harness 啟動前，未宣稱另做執行後 probe。
原始命令、各步起迄／timeout／底層 exit、server 清理與環境全部保留在 [browser-stage-results.json](browser-stage-results.json) 的此 job row。
Golden：`not compared (run did not complete)`。

原始 fatal：

```text
P77 assertion failed: G07 未完成實例草稿保存第8版 false
```

原始檔案：
- [assembly/build.log](assembly/build.log)：1381 bytes；SHA-256 `9eeb7f0aa42ae60ddfba1b868911cbfd7f4cb9cde4b5fe71ee556b83d47f43f3`。
- [assembly/runtime-final-probe.log](assembly/runtime-final-probe.log)：225 bytes；SHA-256 `f4614d2faa5cafab8830da8d0236c95379995e65d282d78344067db6074dbcf5`。
- [assembly/runtime-probe.log](assembly/runtime-probe.log)：299 bytes；SHA-256 `253921d282000958c5cb9cc5745fe5e3e3776b3780e4db0428f78d467e5e1753`。
- [assembly/server.log](assembly/server.log)：3386 bytes；SHA-256 `b05e56ea31b4529ad87065c9430585298735a473d772f3dca979c4f5e98894f2`。
- [assembly/test.log](assembly/test.log)：18965 bytes；SHA-256 `0346520c9b6a1050a360ccb1247523a75a0d35c383e339d1040912661c21b849`。
- [assembly/result.json](assembly/result.json)：10729 bytes；SHA-256 `38f778e616b4830492370547ac6bf86a35ff5e0f2eaf7a53f9165d561bd6250c`。
- [assembly/artifact-manifest.json](assembly/artifact-manifest.json)：88074 bytes；SHA-256 `06277830fcc173dad16e9c8f2c98de0be0d627e3a3b8307b3dfd42a425cc0f0f`。

### documents

Harness：`node geometry-web/documents_browser_test.js`；scope 旗標：`(無)`。

未監聽 consoleAPICalled，不能宣稱 console 無錯；只檢查 Runtime 例外、HTTP >=400 與外部請求，未監聽 Network.loadingFailed。成功 footer 沒有 schema、scope 或 completed，完整性依成功專用 footer、零失敗與正常退出判讀。

起迄：2026-10-18T11:39:24.862159+00:00 → 2026-10-18T11:40:57.205718+00:00；測試來源與收據：[result.json](documents/result.json)。
Runtime：fresh 與自建服務 PID 均有收據。兩次 probe 均在 harness 啟動前，未宣稱另做執行後 probe。
原始命令、各步起迄／timeout／底層 exit、server 清理與環境全部保留在 [browser-stage-results.json](browser-stage-results.json) 的此 job row。

原始檔案：
- [documents/build.log](documents/build.log)：1391 bytes；SHA-256 `6fad07c25ed473101e12ecb7e056cc60cbc0b18f573f8169ab2ae1f7ccf3394a`。
- [documents/runtime-final-probe.log](documents/runtime-final-probe.log)：225 bytes；SHA-256 `8d8a73edffad41c9ac8344ad629919888776291a7670a68a2e852751762391ac`。
- [documents/runtime-probe.log](documents/runtime-probe.log)：299 bytes；SHA-256 `c80e19532c3000fe533cd16c02d6bc2a702d0d6c3d57e76b1791892a70d9ef57`。
- [documents/server.log](documents/server.log)：917 bytes；SHA-256 `3ae70df27ae033b575df76fe0992113f1ddc2ccf1c16e86d9aacf5f2cbb7be96`。
- [documents/test.log](documents/test.log)：2404 bytes；SHA-256 `8000c00782e42cb2d748b761c8ef513ac25f4383a9423a182c1f0a6179978f11`。
- [documents/result.json](documents/result.json)：10764 bytes；SHA-256 `2ba4520239d35b2d096b4d39cb71e5d002ef0edbfc403ed718ed893e145bc5e2`。
- [documents/artifact-manifest.json](documents/artifact-manifest.json)：88425 bytes；SHA-256 `a8d280edf1616825f6b610479c80a021196bf7eb2bc8848a3de2c6f7e29b9315`。

### grid

Harness：`node geometry-web/cdp_test.js`；scope 旗標：`GEOMETRY_GRID_SYSTEM_ONLY`。

consoleAPICalled 僅列印 [console]，未保留類型，也沒有獨立 console.error gate。非預期例外會增加 failedAssertions；僅 full canvas 的 P38 刻意注入 fb-auto-probe，仍會計入 uncaughtBrowserExceptions，因此該欄不等於非預期例外數。

起迄：2026-10-18T11:40:57.208012+00:00 → 2026-10-18T11:51:39.309284+00:00；測試來源與收據：[result.json](grid/result.json)。
Runtime：fresh 與自建服務 PID 均有收據。兩次 probe 均在 harness 啟動前，未宣稱另做執行後 probe。
原始命令、各步起迄／timeout／底層 exit、server 清理與環境全部保留在 [browser-stage-results.json](browser-stage-results.json) 的此 job row。
Golden：`not compared (partial mode)`。

原始檔案：
- [grid/build.log](grid/build.log)：1341 bytes；SHA-256 `35035eed7ec5b3b0026e3dc2ffd64551adf1ef537682a786b82ab3b643a642f0`。
- [grid/runtime-final-probe.log](grid/runtime-final-probe.log)：225 bytes；SHA-256 `255489364c820f200e118758a18105df74017b742e9a4e5ac552d57d8d9b3e09`。
- [grid/runtime-probe.log](grid/runtime-probe.log)：299 bytes；SHA-256 `8e8c6a0a13378c402a174bb1639ad12fded35fb1cb26e71a51ce72a4268d92fd`。
- [grid/server.log](grid/server.log)：147275 bytes；SHA-256 `dd6cc0816f2acd9799ac3e8084aac2d7f9b7535e84f0502f0074f200708cc84e`。
- [grid/test.log](grid/test.log)：42390 bytes；SHA-256 `67b099b5ee83517fe71d94588f5935b8a392a347ddd44eaae46481a230652a98`。
- [grid/result.json](grid/result.json)：10568 bytes；SHA-256 `98d7fabd5a05d79eb1ff65a3049f710b46d04b3243cb0b078aa7a36c84c41946`。
- [grid/artifact-manifest.json](grid/artifact-manifest.json)：92450 bytes；SHA-256 `c561c212fef3dcade8452106db105b2e54dbf95dee8280b2a01675647c4579b6`。

### space

Harness：`node geometry-web/space_model_test.js`；scope 旗標：`(無)`。

原 browser-health 群組要求未捕捉例外及 console.error 都為零；另以固定群組斷言 census 核對完整性。timber 的限定範圍仍會跑 browser-health。

起迄：2026-10-18T11:51:39.314157+00:00 → 2026-10-18T11:59:33.684496+00:00；測試來源與收據：[result.json](space/result.json)。
Runtime：fresh 與自建服務 PID 均有收據。兩次 probe 均在 harness 啟動前，未宣稱另做執行後 probe。
原始命令、各步起迄／timeout／底層 exit、server 清理與環境全部保留在 [browser-stage-results.json](browser-stage-results.json) 的此 job row。

完整性問題原文：

```json
[
  "Space run did not finish",
  "Group space-height-library did not complete",
  "Group space-height-library: expected 112 passed assertions, got 93 passed / 0 failed",
  "Group projection-placement did not complete",
  "Group projection-placement: expected 36 passed assertions, got 0 passed / 0 failed",
  "Group font-layout did not complete",
  "Group font-layout: expected 19 passed assertions, got 0 passed / 0 failed",
  "Group space-flow did not complete",
  "Group space-flow: expected 39 passed assertions, got 0 passed / 0 failed",
  "Group browser-health did not complete",
  "Group browser-health: expected 2 passed assertions, got 0 passed / 0 failed"
]
```

原始檔案：
- [space/build.log](space/build.log)：1351 bytes；SHA-256 `834eed717e173a0a2441b4bb90e2341978389db6e8a042e243ce5b69160e0bb2`。
- [space/runtime-final-probe.log](space/runtime-final-probe.log)：226 bytes；SHA-256 `90a8b751c0b33d6942d30612c08d0474289d747b55b5dbb95740c8b35862347e`。
- [space/runtime-probe.log](space/runtime-probe.log)：300 bytes；SHA-256 `eee406d13ad1d36a6db341019fa40ad99c7e54f7cd764fe461e5833914a8c830`。
- [space/server.log](space/server.log)：6102 bytes；SHA-256 `76f7e89bf1b1ec22f96ffb15efac7285d8b67b2681fdcbf1dc4e449c502fe421`。
- [space/test.log](space/test.log)：12344 bytes；SHA-256 `8a53863e9af67bad8b75fe77a46f94f891dbe46fd9650f3de6df7d1af10d0aa6`。
- [space/result.json](space/result.json)：10616 bytes；SHA-256 `37a2152aa38cb23bc760b54d2afdc4e372f584442ec93ca2cbc56e6fe04d5fbd`。
- [space/artifact-manifest.json](space/artifact-manifest.json)：89529 bytes；SHA-256 `e1d37a75a0c2b44ff7858640a9c055fcdbf7801d8d80d7afc16732f4dbe41197`。
- [space/artifacts/space-results/result.json](space/artifacts/space-results/result.json)：22995 bytes；SHA-256 `a737dd4fe0df84cb7a7d7bc4b899e5a107645727516ee9c1141da46744856f6e`。

### timber

Harness：`node geometry-web/space_model_test.js`；scope 旗標：`GEOMETRY_TIMBER_ONLY`。

原 browser-health 群組要求未捕捉例外及 console.error 都為零；另以固定群組斷言 census 核對完整性。timber 的限定範圍仍會跑 browser-health。

起迄：2026-10-18T11:59:33.688636+00:00 → 2026-10-18T12:03:50.445277+00:00；測試來源與收據：[result.json](timber/result.json)。
Runtime：fresh 與自建服務 PID 均有收據。兩次 probe 均在 harness 啟動前，未宣稱另做執行後 probe。
原始命令、各步起迄／timeout／底層 exit、server 清理與環境全部保留在 [browser-stage-results.json](browser-stage-results.json) 的此 job row。

完整性問題原文：

```json
[
  "Space run did not finish",
  "Group timber-material did not complete",
  "Group timber-material: expected 48 passed assertions, got 22 passed / 0 failed",
  "Group timber-source-guards did not complete",
  "Group timber-source-guards: expected 8 passed assertions, got 0 passed / 0 failed",
  "Group font-layout did not complete",
  "Group font-layout: expected 19 passed assertions, got 0 passed / 0 failed",
  "Group browser-health did not complete",
  "Group browser-health: expected 2 passed assertions, got 0 passed / 0 failed"
]
```

原始檔案：
- [timber/build.log](timber/build.log)：1361 bytes；SHA-256 `6891778370dd46529379362174fe15f217038487bc24411454fa481ac920fffd`。
- [timber/runtime-final-probe.log](timber/runtime-final-probe.log)：226 bytes；SHA-256 `8b0dd16d1c0af63a5332df8f239353ef0c0fc6de17d73f6270296dc02bb18df3`。
- [timber/runtime-probe.log](timber/runtime-probe.log)：300 bytes；SHA-256 `97f3f6abf60d1f9598495f4d5c25aa0c9adf4734b850fc5391efd53895562ec9`。
- [timber/server.log](timber/server.log)：3078 bytes；SHA-256 `e439af3df54fb8e9aa393ffb207371ae1fab749a92c3b5b48a492486ded96868`。
- [timber/test.log](timber/test.log)：6309 bytes；SHA-256 `2a0ac2bae463b7e4849b6d3f76478a4c04f26583693ecb6215d5a007bac44981`。
- [timber/result.json](timber/result.json)：10694 bytes；SHA-256 `55cb5dc042eea52e8a4c3d671774b5d20377788196f2563754ce4add6197c9b5`。
- [timber/artifact-manifest.json](timber/artifact-manifest.json)：86657 bytes；SHA-256 `d3c3d26e36b0bab5574cd214db8a8c5aed04c5e1f364f776a634acdea4e20ba2`。
- [timber/artifacts/space-results/result.json](timber/artifacts/space-results/result.json)：8359 bytes；SHA-256 `b4df15a915b0244bd4992b3d4345f3bb8b0abeca713984548a9071eb1381a0e7`。

## 未驗與修正狀態

尚未完成：無。
已取得終止收據者中，失敗／收據不足且須逐項分析：canvas、assembly、space、timber。
本輪為原始基準測試；未套用 proposed-fixes，未在此階段建立修正分支。修正後重跑與撤除修正轉紅的突變證據，須另輪記錄。
canvas／assembly／grid／documents 沒有完整 console.error gate，不能由通過推論 console 無錯。space 與 timber 只按其原 scope 及 census 報告。
已取得的原始 footer 與 byte/hash 收據見 [browser-stage-results.json](browser-stage-results.json)；本報告的完整性核對是證據判讀，沒有修改 CI 測試判準。
