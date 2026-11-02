# D 的單次 CI 收件預備；尚未驗收

觀測：2026-11-02T10:16:49.254950+00:00。D = `e5b0bc23b04e872a68b066bd5b51d57e2c104943`。
[Geometry integration41424542378](https://github.com/ZhiQiYang/geometry-axiom/actions/runs/41424542378)，`pull_request`、attempt1；同head只見此run。

run集合回傳`queued`，實際11jobs為 **8 success、2 in_progress、1 queued**；其中10jobs已有真runner與steps。canvas:extensions及space正在原browser步驟，timber尚queued、runner/steps空。這份觀測不再輪詢，也不代表終態。

12個artifact的ID、API digest、size、有效期與head/run綁定在`SUMMARY.json`及原`run-41424542378-artifacts.json`；未下載任何artifact。供phase gap一次原件核收的最小既有集合如下，共 **299544 ZIP bytes**。另必須等待`canvas-shard-extensions`真出現後綁其實際ID/digest；當下未見，不能補造。screens及wait trace列為可選診斷，不作分片聯集的替代。

| 必要原件 | artifact ID | ZIP bytes | API digest |
|---|---:|---:|---|
| native-shard-1 | 13132397128 | 4284 | `sha256:17e77bac687dde18385f09740eb85358e3bfd2f06dfb2f7f54f2534d2ee12c0f` |
| native-shard-2 | 13131074047 | 4314 | `sha256:d1f03577019c68415a38944902c9094f774ff019f22a039c29ad8eb502a65fcd` |
| native-shard-3 | 13131483886 | 4279 | `sha256:84f794261445cec266539c0e8b75219f78d746c8bcc49d26367d88250cb2ec3b` |
| native-logs-1 | 13131749015 | 59135 | `sha256:c3961c8b876a8778dbca97d2e8f90292da2eb76a189e15adf90343cf2a3e2596` |
| native-logs-2 | 13130964353 | 69935 | `sha256:19b4aca61f836a2151c0c88a22fc93539bdb68047434fafd7bec50844ce5ff35` |
| native-logs-3 | 13131049916 | 100181 | `sha256:f1acaf0d993b49939d2072fe59f114175c656cd2053d7b6969688d323c9c691c` |
| native-complete-coverage | 13131554190 | 2872 | `sha256:a0568027871dd618ea95ab11701823ffe5356e26f4bcd1024f6be80cd33457b6` |
| canvas-shard-legacy | 13132043656 | 54544 | `sha256:7d2e5de0b82abaffa97eb9d8bf0a3a3c17b292cf76df3ffed0be9bc01fed0253` |

已另外讀唯一completed小job log：`job-125215581921.log`，25994bytes，SHA256`2fdba1e529933f5b17448b9573d588744bb043d51a5578905ef2a4b47ac000eb`。其原checkout真SHA為 **`ea163769f8f570ac06b56906ceb8cdf7dc220a1a`**（D合入R06 F4），不能寫成D execution。原log報native235 suites／5460counted／5459pass／1allowed skip、聯集無重疊；移除`c:integrity`有具名正常AssertionError及0/1/0。這只是原log核讀，尚未官方ZIP獨立verify。

phase gap依`DOWNLOAD_VERIFY_PLAN.json`順序一次核：終態metadata → 官方原ZIP與API digest/size → 原receipt/raw與真source關係 → 既有原聚合verify及官方aggregate bytes對照。local full reference D與CI合成checkout須各留真身份，原工具若拒絕就保留拒絕，不偽造HEAD或改收據。canvas必須用D現行universe含零keys、精確disjoint union及原golden；不借用舊85段或S1綠燈。

本輪不碰`/tmp/geometry-canvas-shards-20261102`、Chrome、任何heavy/local reference程序；不下載大ZIP、不hash binary、不改branch/base/PR/body、不啟測試或CI，也未重收S1原件。三個未終態jobs、兩片canvas聯集、full-reference比對及artifact bytes全部仍未驗。

原API response bytes/hash/HTTP及時戳保留在`OBSERVATION.json`；metadata檢查退出碼 **0**。
