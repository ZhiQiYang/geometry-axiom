# Topic 14：G07 原件診斷，最新組合未重現

受測 `89c269bf68724f9a8b003ac792875f96414d9c3d`（整合基底 `e9c1509cf89e6f35d298743ec5e3368370316cf7` 加唯一診斷 hunk）的 assembly job 完整結束：**150 個斷言通過、0 失敗、0 略過**，P77=134、P82=16。G07 的原複合斷言完全保留且通過；本提交沒有產品修改，不是已找到並修復 e64 根因的聲明。

分支為 `codex/geo261-fix-assembly-g07-20261018`。此資料夾是待發布證據；實際發布狀態與報告提交由 PR #288 留言另記。受測 SHA 與後續加入本報告的 commit 分開記錄。

| 範圍 | 原始結果 | 耗時 |
|---|---|---:|
| `npm run build` | exit 0 | 75.660 秒 |
| `GEOMETRY_ASSEMBLY_ONLY=1 node geometry-web/cdp_test.js` | exit 0；completed=true；150/0/0 | 197.752 秒 |
| assembly 整個 job（含建置、啟動、清理、封存） | passed；無外層 timeout | 277.583 秒 |

UTC 起迄為 2026-10-18 14:35:38.022107 至 14:40:15.605490；原 CI 15 分鐘上限不變。原件：[test.log](assembly/test.log)、[result.json](assembly/result.json)、[summary.json](summary.json)、[build.log](assembly/build.log)、[server.log](assembly/server.log)。精確建置／server／probe／harness 命令與每步退出碼均在 result；最外層 shell argv 沒有另存。以下為同一固定契約的重現入口，須使用全新 output，入口會先預檢再執行固定 assembly job：

```sh
python3 -u /workspace/geo261-validation-20261018/run_topic14_diagnostic.py \
  --expected-sha 89c269bf68724f9a8b003ac792875f96414d9c3d \
  --contract /workspace/geo261-validation-20261018/browser-contract-topic14-diagnostic-v1.json \
  --contract-sha256 59c0cb5ce333c63b2fa508406c3d10d19ad5dd434aa37fe0a1ad404e18bd866f \
  --output /workspace/geo261-validation-20261018/topic14-e9-diagnostic-rerun
```

## 原件核對與分類

直接用 Python 標準函式庫讀 ZIP，不呼叫產品 pack/unpack、不重打包：

| 核對項目 | 觀測 |
|---|---|
| [原 `.gcanvas`](assembly/artifacts/geometry-tests/assembly-generation-g07-before.gcanvas) | 5,200 bytes；SHA-256 `2984678981fbe9705a40f37464507eb0ec3bb5b5908769b2b931302929688930` |
| [同次診斷 JSON](assembly/artifacts/geometry-tests/assembly-generation-g07-before.json) | 1,874 bytes；SHA-256 `0baa4160853a1a85154eff968ca5690e640cc07503d7c02d2882db5a4edb1006` |
| ZIP entry | 僅 `world.scene`、`manifest.json`；名稱唯一、無路徑穿越；CRC 可讀 |
| G07 條件 A | `format === 'geometry-canvas/8'` 為真 |
| G07 條件 B | 唯一 `instance` 草稿首個 member 的 `guideId` 為數字 `0`，為真 |
| JSON 對 manifest | `format` 與完整 `assemblyDrafts.records` 完全相同 |
| `world.scene` | 3,740 bytes；SHA-256 `c153068b840159f9b3af64c1c581b822da780dc83ad7e6e6ddffdcdeef5d8d27`，等於 `sceneHash` |
| 能力 | 僅 `assembly-rule-authoring/1`、`assembly-timber-generation/1`；沒有 section/grid 集合能力 |
| 來源資產 | `sources=[]`；ZIP 實體集合與清單一致 |

場景內三筆 assembly record 的原 base64 payload 長度及 SHA-256 均與各自 header 相符。已提交 instance 的 member 1 仍引用 guide 1；未完成草稿的 member 1 為 guide 0，兩者有意分開保存。後續原測例「保存重開原生來源映射幾何精確一致」也通過。完整機器判讀與原件身份見 [results.json](results.json)。

**分類：最新組合未重現；e64 歷史失敗仍待定位。** e64 baseline 的原 G07 只有合併後 false，未封存當時 saved bytes；不能由本次 /8 反推當時格式，也不能判定原紅是格式預期過時、草稿遺失或某一個上游修正所致。本次沒有產品修正、修後／撤回變紅三證據，也不把診斷 patch 的新增 I/O 視為已排除所有時序影響。

## 保存契約與診斷範圍

固定受測源碼 `project-store.js:663` 在 pack 時以 `normalizedManifest(manifest, scene)` 選擇最終格式；`:174–183` 按所需能力選擇較新格式，instance 草稿本身加入 generation 能力。`:730–747` 的 unpack 不改 format。本次真場景只有兩種 assembly 能力，因此保存 /8 與既有契約一致。`ASSEMBLY-GENERATION.md:26` 說明 /8 必須宣告 generation 能力；I32 是能力／版本守門。較新 section／grid collection 另有格式契約，但本次原件沒有使用它們，不能拿這些候選理由修改原 G07 預期。

[唯一診斷 patch](diagnostic-only.patch) 只把同一份 `window.__generationBytes` 與 saved JSON 寫出，並讓原 check 第三參數輸出 saved；原 AND、斷言數、timeout、golden 都未改。[原預檢](preflight.json) 綁定 clean 受測 SHA，56 個來源 pin 中僅批准該測試 JS 的精確新 hash，其餘 55 個、workflow 與 golden 相同；[固定契約](contract.json) 保留唯一允許差異。

`partial` 是 CI assembly 分流的既有模式；原 harness 不對整份 canvas golden 比較。本報告另核 footer 精確 P77=134、P82=16、總數 150、completed=true，不能擴大成六個瀏覽器 job 或完整 canvas 通過。footer 的 `uncaughtBrowserExceptions=0` 不是一般 console.error 全域守門；`firstTransportFailure` 是原測例刻意注入的 `Injected lost success response`，後續回執恢復斷言通過，`firstNetworkFailure=null`。

## 環境、收據與未驗項

[environment.json](environment.json)：Debian GNU/Linux 13.6、Linux 6.18.55、gcc 14.2.0、Python 3.12.14、Node 24.19.0、真正 Google Chrome 155.0.8059.84、16 MiB stack。Chrome 使用 checkout 外已驗官方套件路徑，CI 路徑為 `/usr/bin/google-chrome`；實際版本／路徑差異保留。Noto Sans CJK 已存在。

啟動前兩次 port 18839 觀測均無 listener；runtime fresh=true、root 相符且 PID=自建 server 175401。兩個成功 probe 都在 harness 前，沒有宣稱 harness 後再 probe。第一次 readiness probe 因啟動競態 exit 1，後續兩次 exit 0。前後 SHA 完全相同且 checkout clean；只清理 runner 擁有的 process groups，server 收 SIGTERM 後的 -15 為清理結果，不是產品 job 失敗。

[artifact-manifest.json](assembly/artifact-manifest.json) 的全部 466 個實體、4,843,985 bytes 均逐一核對原 bytes/hash，封存 errors=[]。公開集合保留所有資料型原件、screenshots、runtime 指紋與 smoke 場景；ELF、node cache、鎖只在 [inventory.json](inventory.json) 留身份及排除理由。runner 原先省略的 Chrome profile、cache、socket 仍照原 manifest 記錄，沒有假稱已逐檔 hash。未收整包工作區、憑證、repo `.codex/` 或使用者 `feedback/`。

尚未完成：e64+同診斷的原紅重現／根因、產品修正三證據、其餘五個 browser job 在此 SHA 的重驗、完整 canvas golden、Windows／實體裝置。這些都不由本次 150 個斷言推定通過。
