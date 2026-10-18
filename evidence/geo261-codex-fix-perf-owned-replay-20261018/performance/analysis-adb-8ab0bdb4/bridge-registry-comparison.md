# A/D+B 正式 registry bridge 比較

固定 main `e980cb0dbf39beb40f6f3002a9ffbc43ee38c425` 與 A/D+B `8ab0bdb467ba6e6d22f7c5652f221cffab4934b6`。兩輪完整 **24/24、零 fail／skip／blocked／extra error**，但 unittest 總時間倍率 **86.818 ÷ 36.493 = 2.37903159510043**，**≤2 倍驗收未通過**。這是每版各一輪，尚非交錯重複統計。

| 正式輪次 | unittest 秒 | suite JSON 秒 | runner 秒 | 外層秒（含建置） | exit／timeout |
|---|---:|---:|---:|---:|---|
| main | 36.493 | 36.56 | 36.7 | 57.251352479 | 0／false |
| A/D+B | 86.818 | 86.95 | 87.1 | 112.511273206 | 0／false |

兩輪 argv 均為 `python3 -B -u tests/run_all.py --build --only py:test_bridge_integrity`，工作目錄 `/workspace/geometry-axiom`，原 timeout 900 秒。上表倍率只取 unittest 原 footer；外層包含建置，不能作性能比。原文：[main unittest](../bridge-integrity-adb-main-registry/suite-logs/py_test_bridge_integrity.unittest.log)、[candidate unittest](../bridge-integrity-adb-candidate-registry/suite-logs/py_test_bridge_integrity.unittest.log)、[main receipt](../bridge-integrity-adb-main-registry/receipt.json)、[candidate receipt](../bridge-integrity-adb-candidate-registry/receipt.json)。

main UTC 14:11:16.927619–14:12:14.178963；candidate UTC 14:12:37.781217–14:14:30.292491，均為 2026-10-18。來源 SHA、source bytes、status／diff 在各輪前後一致。主代理確認本次兩正式輪無其他正式計時工作並行；收據本身未聲稱自動證明全機 CPU 排他。

## 來源與實際 registry binary

| 身分 | main | A/D+B |
|---|---|---|
| 執行路徑 | `/tmp/geometry-tests/bridge` | `/tmp/geometry-tests/bridge` |
| 當輪 after 檢查 | fresh | fresh |
| binary bytes | 660440 | 1079056 |
| binary SHA-256 | `ba9496d9e054d917c0d9a3a67f7a23c56374da6194d0b215c4babf422753fbe0` | `4f3613cfefda15a1c46b7a254eab4d947d038be632ab0305ff8191458c63be1e` |
| sidecar SHA-256 | `e4a6b9ead3cbe32b9a5178b0e530ff8c1e1ae7ae249424f7da3f4a97dfbae668` | `218efaff16836361e768173a5c4187ec0383e2690c8e0c97481f7b136295fcf4` |
| sidecar 來源數 | 52 | 192 |

兩份 sidecar 的 binary bytes／mtime／SHA 與當輪 `after.binaries.json` 相合；52＋192 個來源的 CRLF→LF 正常化 SHA 均對固定 Git blob 及當輪 raw source snapshot 核對，並獨立重算 fingerprint。command string 均為 `cc -std=c11 -O2 geometry-web/web_bridge.c -lm -> bridge`。完整 registry 原件也列 core／model-base stale，這兩個不是本 suite 的需求，不把它們當已驗 binary。

**registry ELF 未另行封存**；上述 binary 身分是當時 recorder 真正讀取的記錄，sidecar 原檔仍保留，沒有用現在的 `/tmp` 檔或性能 archive ELF 冒充。既有 archive normal／gprof binary 是另一組建置，不能替代本表。

## 共同輸入與框架差異

65 份既有 `.scene`、`tests/test_bridge_integrity.py`、`tests/_bridge.py`、`tests/run_tests.py` 共 **68 份**，已逐項核對兩輪 before／after source snapshots（272 次身份）及兩個固定 Git 版本（136 次 bytes／SHA）。四份正式 snapshot 的 68 份內容全等；暫存路徑由測試各輪產生，不宣稱動態路徑同字串。

兩版 `tests/_unittest_runner.py` 亦相同；`tests/run_all.py`、`tests/binaries.py`、`tests/run_all.expected.json` 不同，不能說整個框架 bytes 相同。`run_all.py` 差異為 suite 登錄；此 suite 的 `['bridge']` 需求不變。`binaries.py` 的 source scanner 由 core／web 擴成 core／web／app／templates；fingerprint 演算法相同。各版 registry 在自己的來源規則下 fresh，已把實際兩份 scanner 身分列入 [機器可讀審核](bridge-registry-verification.json)。測例內原有 freshness 檢查照常執行，scanner 掃描集合差異也可能影響 suite 總時間；本次未將該部分與產品工作拆開計時。外層建置時間則另列。

三輪含無效試跑的 93 個 receipt-listed 原件 hash 已重核；兩正式 suite 的三份封存 log 均為該輪 stdout 宣告、copied=true 且內容 hash 相符。兩正式 source 清單分別 3155／4408 個條目，輪內 bytes／SHA 穩定；這不是宣稱兩版本全 source 相同。

## 無效首次 archive 試跑

[`bridge-integrity-adb-main`](../bridge-integrity-adb-main/receipt.json) 曾從 8ab checkout 透過 `GEOMETRY_TEST_BRIDGE` 指向 archive main bridge。該 ELF 沒有 `binaries.py` sidecar，原 stderr 明示 `explicit bridge 不是 fresh：stale（沒有 sidecar…）`，footer 是：

```text
Ran 24 tests in 8.167s

OK (skipped=149)
```

**149 是原 skip 事件數，不能改寫成 149 個方法，更不能當 24 項通過。** 此次 exit 0 只代表 unittest 接受 skip，無性能／功能通過效力，完全排除倍率。保留 [原 stderr](../bridge-integrity-adb-main/command.stderr)、[原 command](../bridge-integrity-adb-main/command.process.json)。舊 `bridge-integrity-adb-inputs.before.json` 僅用其 68 個 input path／bytes 選取再核正式原件；其中 `binaries`、`runtime_fixture_policy` 屬此無效 archive 試跑，**未挪用為正式 registry 證據**。

環境：Linux 6.18.55 x86_64／glibc 2.41、GCC Debian 14.2.0-19、Python 3.12.14、Node v24.19.0、Google Chrome 155.0.8059.84（另有 Chromium 154.0.8037.57）。版本原 stdout 存在兩輪目錄；本 suite 不啟動瀏覽器。

本次只讀原件／Git 並整理外部報告，未執行 build、產品、測試或更改 checkout。完整驗證數據見 [bridge-registry-verification.json](bridge-registry-verification.json)。
