【WSL 裁判(代理)】head 90659e6190b592feeb06fab263a16175538eb64a

第9班 `train/20261014-9-pr201`，實測base main `23ca8961d87a8b76591afebb403164e4c62c339f`，只一般merge #201 `3f1664fb5c43ad49f76ee97853d8d5923197f7c3`。K2a集合草稿的孤兒ZIP冷讀案例已依P-095量測後配置具名預算；本班將該已審修正合入main，驗證完整流程。審查[6149716938](https://github.com/ZhiQiYang/geometry-axiom/pull/201#issuecomment-6149716938)及看板02:00為上車依據。

七項原判定 `red: native, canvas`，七項合格=`False`，完整canvas gate=`False`，開draft條件=`False`。CI／WSL／實際工具 exit=1／1／1，原件收集exit0。原命令 `WSL_CI_LABEL=train-20261014-9-pr201-r1 wsl_locked3.sh ci 90659e6190b592feeb06fab263a16175538eb64a all`。

| job | 原判定 | job exit | pass／fail／skip | 首跑／總秒數 | 原CI秒數 | 超原CI |
|---|---|---|---|---|---|---|
| native | red | 1 | 2751／3／1 | 2094.4／2575.2 | 900 | 是 |
| assembly | green | 0 | 150／0／未統計 | 369.0／369.1 | 900 | 否 |
| documents | green | 0 | 47／0／未統計 | 137.1／137.4 | 600 | 否 |
| grid | green | 0 | 346／0／未統計 | 915.8／915.9 | 900 | 是 |
| canvas | red | 1 | 707／1／未統計 | 1071.7／1073.8 | 2100 | 否 |
| space | green | 0 | 242／0／未統計 | 387.2／387.2 | 900 | 否 |
| timber | green | 0 | 79／0／未統計 | 216.7／216.7 | 1200 | 否 |

native expected比對：`{"available": true, "expected_suites": 87, "expected_items": 2755, "ran_suites": 87, "mismatches": [], "missing_in_log": [], "extra_in_log": [], "equal": true}`；原reader：`[{"suite": "py:test_axiom_reader", "total": "41", "passed": "41", "failed": "0", "skipped": "0", "seconds": "307.9", "note": ""}]`；原Node：`[{"suite": "node:tests-js", "total": "703", "passed": "700", "failed": "3", "skipped": "0", "seconds": "301.3", "note": "日誌 /tmp/geometry-tests/run_all-logs/node_tests-js.log"}]`，期望703、計數符合=True。原生HTTP首跑通過=True；原Rule2=`{"rerun_max": 2, "baseline_sources": ["/mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/5cc1ffa1-attempt3-red-1-flaky-test", "/mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/5cc1ffa1"], "suites": [{"suite": "node:tests-js", "failed_ids": ["node:tests-js::*"], "eligible_by_baseline": false, "first_run": {"failed": "3", "total": "703", "note": "日誌 /tmp/geometry-tests/run_all-logs/node_tests-js.log", "tests": []}, "baseline": {"node:tests-js::*": null}, "reruns": [{"attempt": 1, "passed": false, "exit_code": 1, "seconds": 288.5, "why": ["re-run exit 1 (run_all: 有 fail／預期數不符／未登記檔)", "suite row not clean: failed=3 note=日誌 /tmp/geometry-tests/run_all-logs/node_tests-js.log"], "log": "/mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/90659e61-train-20261014-9-pr201-r1/native/reruns/node_tests-js.attempt1.log", "row": {"total": "703", "passed": "700", "failed": "3", "skipped": "0"}}, {"attempt": 2, "passed": false, "exit_code": 1, "seconds": 179.0, "why": ["re-run exit 1 (run_all: 有 fail／預期數不符／未登記檔)", "suite row not clean: failed=2 note=日誌 /tmp/geometry-tests/run_all-logs/node_tests-js.log"], "log": "/mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/90659e61-train-20261014-9-pr201-r1/native/reruns/node_tests-js.attempt2.log", "row": {"total": "703", "passed": "701", "failed": "2", "skipped": "0"}}], "excused": false, "rerun_passed": false, "why_not_excused": "failed test(s) NOT failing in any main baseline receipt: ['node:tests-js::*']"}], "qualifies": false, "reasons": ["not excused: ['node:tests-js']"], "other_problems": [], "totals_consistent": true}`。

瀏覽器範圍：
```text
assembly: scope=partial, completed=True, golden=not compared (partial mode), skipped_groups=[], uncaught=None
documents: scope=None, completed=True, golden=None, skipped_groups=None, uncaught=None
grid: scope=partial, completed=True, golden=not compared (partial mode), skipped_groups=[], uncaught=None
canvas: scope=full, completed=False, golden=not compared (run did not complete), skipped_groups=[], uncaught=None
space: scope=full-space-suite, completed=True, golden=None, skipped_groups=['timber-material', 'timber-source-guards'], uncaught=None
timber: scope=partial, completed=True, golden=None, skipped_groups=['space-height-library', 'projection-lifecycle', 'projection-placement', 'space-flow', 'projection-close'], uncaught=None
```
完整canvas原CDP_RESULT：
```json
[
  {
    "line": 785,
    "value": {
      "schema": "geometry-cdp-result/1",
      "scope": {
        "mode": "full",
        "filters": [],
        "modifiers": [],
        "url": "http://127.0.0.1:18844/",
        "feedbackDirectory": "/tmp/ga-ci/90659e61-20261014-020838/canvas/geometry-integration-feedback",
        "browserProfile": "/tmp/ga-ci/90659e61-20261014-020838/canvas/geometry-cdp-p9GuuE",
        "cdpPort": 9333,
        "browserPid": 1161
      },
      "completed": false,
      "passedAssertions": 707,
      "failedAssertions": 1,
      "fatal": "P52-3 H(長度軸u) at-line guide 2 A28 -u-n setup 失敗: [{\"line\":\"reset\",\"ok\":false,\"error\":\"服務未在 15 秒內回應，請稍後重試。\",\"preview\":false}]",
      "skipped": [],
      "sections": {
        "1": 14,
        "2": 3,
        "3": 1,
        "4": 1,
        "5": 1,
        "6": 1,
        "7": 1,
        "8": 0,
        "9": 12,
        "10": 0,
        "Setup": 0,
        "P3": 14,
        "P4": 11,
        "P5": 2,
        "P6": 4,
        "P7": 54,
        "P8": 116,
        "P9": 9,
        "P10": 9,
        "P11": 12,
        "P12": 8,
        "P13": 4,
        "P14": 16,
        "P15": 6,
        "P16": 10,
        "P17": 11,
        "P18": 20,
        "P19": 17,
        "BF2": 5,
        "BF3": 1,
        "BF4": 9,
        "P20": 10,
        "P21": 4,
        "P22": 45,
        "P32": 34,
        "P33": 9,
        "P34": 7,
        "P35": 14,
        "P36": 2,
        "P37": 19,
        "P38": 13,
        "P39": 8,
        "P40": 4,
        "P41": 3,
        "P42": 12,
        "P43": 12,
        "P44": 19,
        "P45": 2,
        "P46": 7,
        "P47": 9,
        "P48": 14,
        "P49": 17,
        "P50": 33,
        "P51": 13,
        "P52": 25
      },
      "sectionsFailed": {
        "P52": 1
      },
      "currentSection": "P52",
      "goldenCompare": "not compared (run did not complete)"
    }
  }
]
```

P-095前第6班f0d的native首紅與兩補跑、六browser綠仍保留原身分，不拼到本班。舊雲端native2754/0/1受測ade6d7f、3f1664fb只增證據，亦不是本班收據。上車由02:00看板明示；M2歷史5878.7ms「最慢」標示問題保留，沒有改原owner的測試預算或斷言。

四共享runner與1531份來源啟動前凍結。七clone的精確head／tracked diff／來源核符，22份實際step、23支唯一binary、1083個metadata來源引用均重算。binary與steps在同一WSL父程序結束前取回；sidecar metadata嵌入identity，沒有冒稱每份sidecar另存獨立檔。

另存3個原Git commit、1857個tree objects，重算Git SHA-1到根tree `7443629aaff25de7fe237a109bf1c8efbc80e63e`、13857個追蹤路徑與上述來源blob。Git物件在列車排隊後唯讀擷取，未宣稱保存所有追蹤blob內容。

foreign 190次取樣，原清單 `{}`；不冒稱連續全機監控。原CI秒數、三倍watchdog、具名skip、各job範圍與清理例外均保留。原diff-check exit2，6595處既有空白警告，清單在state與原輸出；原件沒有正規化。另有兩個owner原樣測試EOF空行，最初準備檢查中止後已逐blob核對再續接同一merge，原失敗保留。四保護檔均等於當時main；本輪native驗原41，未另宣稱重跑同步器。GEO-219整合無新可見UI入口。

唯讀合流預檢：當時main `caf49852a4b40d4e61bdf76480c79b43bb5a3676`，merge-tree exit1，合成tree `None`，不是本輪實測tree，不移用本輪結果；實際整合由Claude／dot裁決。

首紅定位：

````text
native/job.log
L246:     - ✖ K2a P064 ordinary discard preserves large normal singleton ZIP raw and local UndoRedo 130956-byte boundary (5851.71168ms)
L247:     - ✖ K2a P064 ordinary discard preserves large normal singleton ZIP raw and local UndoRedo 131072-byte boundary (8789.908087ms)
L248:     - ✖ K2a B1 collection two drafts orphan remove other manifest ZIP cold read preserves 130955-byte boundary (12359.045071ms)
L249:     - ✖ failing tests:
L250:     - ✖ K2a P064 ordinary discard preserves large normal singleton ZIP raw and local UndoRedo 130956-byte boundary (5851.71168ms)
L251:     - ✖ K2a P064 ordinary discard preserves large normal singleton ZIP raw and local UndoRedo 131072-byte boundary (8789.908087ms)
L252:     - ✖ K2a B1 collection two drafts orphan remove other manifest ZIP cold read preserves 130955-byte boundary (12359.045071ms)
L254: exit 1：有 fail／逾時／預期數不符／未登記檔
{"why": ["exit code 1", "rule 2 (flaky re-run) did not excuse: not excused: ['node:tests-js']"], "completed": null, "scope": null, "golden": null, "fatal": null, "failure_details": ["  node:tests-js", "    - ✖ K2a P064 ordinary discard preserves large normal singleton ZIP raw and local UndoRedo 130956-byte boundary (5851.71168ms)", "    - ✖ K2a P064 ordinary discard preserves large normal singleton ZIP raw and local UndoRedo 131072-byte boundary (8789.908087ms)", "    - ✖ K2a B1 collection two drafts orphan remove other manifest ZIP cold read preserves 130955-byte boundary (12359.045071ms)", "    - ✖ failing tests:", "    - ✖ K2a P064 ordinary discard preserves large normal singleton ZIP raw and local UndoRedo 130956-byte boundary (5851.71168ms)", "    - ✖ K2a P064 ordinary discard preserves large normal singleton ZIP raw and local UndoRedo 131072-byte boundary (8789.908087ms)", "    - ✖ K2a B1 collection two drafts orphan remove other manifest ZIP cold read preserves 130955-byte boundary (12359.045071ms)"], "flaky": {"rerun_max": 2, "baseline_sources": ["/mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/5cc1ffa1-attempt3-red-1-flaky-test", "/mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/5cc1ffa1"], "suites": [{"suite": "node:tests-js", "failed_ids": ["node:tests-js::*"], "eligible_by_baseline": false, "first_run": {"failed": "3", "total": "703", "note": "日誌 /tmp/geometry-tests/run_all-logs/node_tests-js.log", "tests": []}, "baseline": {"node:tests-js::*": null}, "reruns": [{"attempt": 1, "passed": false, "exit_code": 1, "seconds": 288.5, "why": ["re-run exit 1 (run_all: 有 fail／預期數不符／未登記檔)", "suite row not clean: failed=3 note=日誌 /tmp/geometry-tests/run_all-logs/node_tests-js.log"], "log": "/mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/90659e61-train-20261014-9-pr201-r1/native/reruns/node_tests-js.attempt1.log", "row": {"total": "703", "passed": "700", "failed": "3", "skipped": "0"}}, {"attempt": 2, "passed": false, "exit_code": 1, "seconds": 179.0, "why": ["re-run exit 1 (run_all: 有 fail／預期數不符／未登記檔)", "suite row not clean: failed=2 note=日誌 /tmp/geometry-tests/run_all-logs/node_tests-js.log"], "log": "/mnt/c/Users/Yang/AppData/Local/Temp/claude/D--geometry-axiom/f46787ac-6918-4891-81a1-b3d8a9aa653c/scratchpad/wsl-ci/90659e61-train-20261014-9-pr201-r1/native/reruns/node_tests-js.attempt2.log", "row": {"total": "703", "passed": "701", "failed": "2", "skipped": "0"}}], "excused": false, "rerun_passed": false, "why_not_excused": "failed test(s) NOT failing in any main baseline receipt: ['node:tests-js::*']"}], "qualifies": false, "reasons": ["not excused: ['node:tests-js']"], "other_problems": [], "totals_consistent": true}}
````

````text
canvas/job.log
L781: P52-3 H(長度軸u) at-line guide 2 A28 -u+n ✗ {"band":{"hoverNull":true},"expCross":[1986,2014],"sent":[],"rng":null,"expLen":[27,3973],"expZ":[2500,2533]}
L782: FATAL: P52-3 H(長度軸u) at-line guide 2 A28 -u-n setup 失敗: [{"line":"reset","ok":false,"error":"服務未在 15 秒內回應，請稍後重試。","preview":false}]
{"why": ["exit code 1"], "completed": false, "scope": "full", "golden": "not compared (run did not complete)", "fatal": "P52-3 H(長度軸u) at-line guide 2 A28 -u-n setup 失敗: [{\"line\":\"reset\",\"ok\":false,\"error\":\"服務未在 15 秒內回應，請稍後重試。\",\"preview\":false}]", "failure_details": null, "flaky": null}
````

原收據 `C:\Users\Yang\AppData\Local\Temp\claude\D--geometry-axiom\f46787ac-6918-4891-81a1-b3d8a9aa653c\scratchpad\wsl-ci\90659e61-train-20261014-9-pr201-r1\receipt.json`，完整原件隨封包交付，公開後另行GET核回。CI受帳號計費阻擋，以本機WSL收據代替。

內層封包共3782路徑、11077820bytes，SHA-256 `a82f2d4a1e08650ab7499f46f8348daf7ba4613196d5e126d4bed43730170993`；每份原件已核bytes/hash，公開後再獨立GET重建。

本裁判由本機 Codex 代 Claude 執行,Claude 復工後會複核


完整原件 14 個路徑（14 份唯一 bytes）收錄於以下 manifest 與 ZIP。 ZIP 11787610 bytes，SHA-256 `074059a093c1c9e466fc8372e279e79bd7e0602a2bddb9982d233208008752d9`；manifest SHA-256 `770a0376eaaaedbb150ad07741347c0b84819685b107cd75737682b6273607e9`。可按順序串接 base64 後解碼，再依 manifest 逐檔核對；原始失敗與還原紀錄均按其實際結果保留。


<!-- evidence-sha256:c3ea9a2376c83ad6121820576f59a3f3893cd119ef5e6beac64a4436aa966b58 -->

