# U476 真 native 研究夾具來源

固定來源基底：`19c00180228f6dfdff65684b47160736d2fae7e9`；本次觀察 HEAD：`19c00180228f6dfdff65684b47160736d2fae7e9`。

夾具：`r05_takeoff_native.json`；185969 bytes；SHA-256 `5f9c5d5bfbd9de1e168acdb7780f8c36e83d2665f023501190f614ee0071dba3`。

此八例由新編 bridge/model-base、真 space_modeling.preview、每包 verify_package、整筆 replay_stored、input/result 雙端 source-inspect-file、既有普通模型 pack/unpack 產生。沒有手寫模型成功結果，沒有改 source-inspector.js。

每次重播由宿主新配隨機 epoch，故 incarnation 和夾具 bytes 可改；模型 pins 來自原 live graph，不取去身分 candidate 的記號。

owner/project/scenario 是明示離線研究條件，不是正式 owner service；僅 literal A/B 普通已放置 D7 正例。新附件與 /2 未接線；既有 /1 的 saved-model/union 仍回 WORLD_KIND。

## 從 repository 根重播

```sh
python geometry-core/timber-takeoff/research/native_reproduce.py --repo . --out /tmp/u476-native-fresh --candidate geometry-core/timber-takeoff/research/candidate.cjs --fixture tests/fixtures/r05_takeoff_native.json
python geometry-core/timber-takeoff/research/native_root_withdrawal.py --native-artifacts /tmp/u476-native-fresh --out /tmp/u476-raw-root-withdrawal
```

sourceInputs 包含原 binary registry 的 C 閉包與 producer/host JS/Python 保守閉包，全部取自固定基底已有檔案；新增研究檔不免除任何既有來源變更。sourceInputNormalization 明示跨平台行尾處理，不能只核對 fixture 自己的 JSON。

BASE 物件必須可讀。套用研究 T/P 後 HEAD 可以前進，但 pinned BASE inventory 中每個既有檔案仍須完全通過 git diff BASE；再核 binary fingerprint 與 source byte pins。若 #472 改變任何既有來源，重播即拒絕，不得只刷新 pin 續綠。

## 本次原始命令與輸出

### build

```text
["/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python", "/tmp/u-native-new/native_reproduce.py", "--repo", "/workspace/scratch/9ce1d6e6119e/u-repo", "--out", "/tmp/u-native-476/run-final", "--stage", "build"]
exit=0; timeout=240 seconds; timedOut=False
  bridge：建置（找不到 /tmp/u-native-476/run-final/binaries/bridge）…
  model-base：建置（找不到 /tmp/u-native-476/run-final/binaries/model-base）…
{"stage": "build", "ok": true, "binaries": ["bridge", "model-base"]}
```

### native-run

```text
["/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python", "/tmp/u-native-new/native_reproduce.py", "--repo", "/workspace/scratch/9ce1d6e6119e/u-repo", "--out", "/tmp/u-native-476/run-final", "--stage", "native"]
exit=0; timeout=240 seconds; timedOut=False
{"scenario": "single", "producer": "space_modeling.preview", "replay": "equal", "native_readonly": true, "selected": [0]}
{"scenario": "independent-control", "producer": "space_modeling.preview", "replay": "equal", "native_readonly": true, "selected": [0, 4]}
```

### consume

```text
["node", "/tmp/u-native-new/native_consume.cjs", "/workspace/scratch/9ce1d6e6119e/u-repo", "/tmp/u-native-476/run-final"]
exit=0; timeout=90 seconds; timedOut=False
{"ok":true,"live_rows":1,"saved_rows":1,"continuity":"proved","independent_rows":2,"k1_single_new_stock":1,"k1_independent_new_stock":2,"cross_world_saved_status":"UNSUPPORTED","cross_world_union_status":"UNSUPPORTED"}
```

### projection

```text
["/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python", "/tmp/u-native-new/native_projection.py", "--native-artifacts", "/tmp/u-native-476/run-final", "--out", "/tmp/u-native-476/run-final/facts"]
exit=0; timeout=90 seconds; timedOut=False
{"researchOnly": true, "studySchema": "U476-facts/1", "cases": [{"name": "single-unresolved", "representations": 2, "physicalSources": 1, "expectedStatus": "INCOMPLETE", "inputSha256": "e5345d7ef413cb179dc173384f562eb65c36858826ed347c6234f0ee591d8147"}, {"name": "single-explicit", "representations": 2, "physicalSources": 1, "expectedStatus": "COMPLETE", "inputSha256": "98e13753a59d01456687113e526fe73dc06ee32d7f17ba1c4577cb23d2873419"}, {"name": "single-exclude-model", "representations": 2, "physicalSources": 1, "expectedStatus": "COMPLETE", "inputSha256": "06fb856d7cd30486bfd549649442b0f37dba4739230bbadaa6e0782a0d5a7c4d"}, {"name": "single-revoked", "representations": 2, "physicalSources": 1, "expectedStatus": "INCOMPLETE", "inputSha256": "e5345d7ef413cb179dc173384f562eb65c36858826ed347c6234f0ee591d8147"}, {"name": "independent-control-unresolved", "representations": 4, "physicalSources": 2, "expectedStatus": "INCOMPLETE", "inputSha256": "b19eb9165b7e26e5c9cd7a01dc4c84ee0426b36b49ca5736107e68e541ec5f05"}, {"name": "independent-control-explicit", "representations": 4, "physicalSources": 2, "expectedStatus": "COMPLETE", "inputSha256": "83c3fec251baf3b7b1d4c1ad7c18e76960c845e172336209a0145487a527c204"}, {"name": "independent-control-exclude-model", "representations": 4, "physicalSources": 2, "expectedStatus": "COMPLETE", "inputSha256": "5f9394404136ae5d38a8201fbb60fc2bdf73776eabb46235449fc0d1621cfc27"}, {"name": "independent-control-revoked", "representations": 4, "physicalSources": 2, "expectedStatus": "INCOMPLETE", "inputSha256": "b19eb9165b7e26e5c9cd7a01dc4c84ee0426b36b49ca5736107e68e541ec5f05"}]}
```

### native-root-probe

```text
["/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python", "/tmp/u-native-new/native_root_probe.py", "--native-artifacts", "/tmp/u-native-476/run-final"]
exit=0; timeout=90 seconds; timedOut=False
{"ok": true, "researchOnly": true, "realBaselineScenarios": 2, "negativeCounterfactuals": 48, "expectedFailure": "typed root guard, not downstream content mismatch"}
```
