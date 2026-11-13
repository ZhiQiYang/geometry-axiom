# P1 targeted evidence index

Recorded 2026-10-16. These are fixed-source targeted receipts, not the full P1 acceptance suite or the formal seven-job browser/native train. No full `run_all`, expected-count update, full native mutation regeneration, or browser test has been executed by these receipts.

| Receipt | Source | Actual outcome |
|---|---|---|
| `baseline-adapters-a898ad6e` | main `a898ad6e12707104568679591fe1b21804bfc3df` | `tests/binaries.py build model-base bridge` and `status` both exit 0; both adapters fresh. 15,784 tracked source files and HEAD unchanged. Original producer v3 built/verified all five packages and recorded the subdivision rejection, then failed serializing historical tuples as JSON. Combined stage exit 1 is preserved. |
| `producer-retry-v2` and `compatibility-baseline-v2` | same exact main | producer v4 exit 0; fresh adapters before/after, source unchanged. All 11 earlier JSON outputs are byte-identical (five input/package pairs plus subdivision rejection). Full historical versions, model contract and producer receipt now present. |
| `grid-rename-native-v1` | `2f015dfd62779baba066f503f21422f8472a0ae8` using fresh main bridge | 28 tests executed. The 25 existing infinite-grid tests and two new tests pass. The six-shape test records six subtest failures in its whole-reference-response comparison at line 103, whose reported difference begins with a changed fingerprint, followed by `UnboundLocalError` at line 118. Exit 1; not labeled a product failure before contract review. HEAD and source hashes unchanged. |
| `native-kernel-ab90a56d-v1` | archive `ab90a56df488b0cd38d5e6f9df1ed5597a8e126e` | 13 tests, zero failures/errors/skips; exit 0. Includes standalone copied K source, shared real-bridge objects and negative controls. Fourteen compiler/linker command records and 27 artifact hashes retained. All 15,852 source files unchanged. |
| `native-geometry-51e9045b-v1` | archive `51e9045b43078a77383afdaf5db379117ffc8871` | Completed 01:48:45 UTC: 20 tests, zero failures/errors/skips, exit 0. Twenty compiler/linker records and 37 artifact hashes retained; all 15,857 source files unchanged. Original unittest reports 9.083 seconds; archive preparation is included separately in the stage wall time. |
| `grid-rename-native-v2` | clean private checkout `0e7c38bb8bf719f0084d24ce73ef65f016d6ddde` using fresh main bridge | Completed 01:54:43 UTC: 28 methods, 27 pass; the six-shape method has six subtest failures at line 125 because `undo` returns `ok: false`. The preceding exact objects/dump/name-derived fingerprints/full references/segments comparisons passed. No errors/skips. Exit 1; mutation probes were not executed. All 15,789 tracked source files and HEAD unchanged; bridge fresh before/after. |
| `region-edges-old-51e9045b-v1` | product `51e9045b`, four added judge files from `be9ed3e7` | Six positive tests: four assertion failures, two passes, zero errors/skips. The original declaration required five failures, so receipt exit 1 is preserved. Unit-hole actual-product rejection already passed because an independent boundary-role guard rejected it. All original product files and the post-overlay source manifest unchanged. |
| `region-edges-new-be9ed3e7-v1` | `be9ed3e7886f951918a8e02e678e0284f0d34079` | Eight tests: seven pass, one assertion failure, zero errors/skips. Removing the hole-center guard did not make the actual bridge accept the fixture because `V_BOUNDARY_ROLE` still rejected it. Seventeen build commands and 26 artifact hashes retained; source unchanged. This is not a green removal control. |
| `native-grid-49f03842-v1` | `49f03842cca4f70e0e38a82d120c06edd1b16189` | Completed 02:09:56 UTC: 28 tests, zero failures/errors/skips, exit 0. Twenty-six compiler/linker commands and 47 artifact hashes retained; all 15,861 source files unchanged. |
| `native-parameters-4aabd21c-v1` | `4aabd21cf82d495f5ab4902bedc9330ca5ed4e3b` | Completed 02:12:30 UTC: 35 tests, 29 pass and six assertion failures, zero errors/skips. All six fail compiling the actual product bridge: `section_profile_validation.inc` still refers to removed `ParameterEval` and `parameter_eval_field`. Source unchanged; these are code compilation failures, not successful negative controls. |
| `parameters-legacy-4aabd21c-v1` | same exact `4aabd21c` | Completed 02:12:47 UTC: same-source registry build and freshness check both exit 1. The 20 legacy tests were not executed. Bridge has the parameter compile defect above; model-base additionally references removed `TIMBER_FACE_WALK`. Source unchanged. |
| `native-annotation-b370f753-v1` | `b370f753f22d0d119835c59d23b0a78344f8ee55` | Completed 02:22:32 UTC: zero tests, one `setUpClass` error compiling the original harness on the same removed parameter type/function. Four intended tests did not execute. Ten build commands and 24 artifact hashes retained; all 15,869 source files unchanged. |
| `native-datums-c28ea963-v1` | `c28ea9639b79881f30995cd79ce843346373c31e` | Completed 02:26:35 UTC: 13 tests, eight pass and five assertion failures, zero errors/skips. All five fail compiling the real bridge at the same stale profile parameter consumer. Twenty-one build commands and 41 artifact hashes retained; all 15,881 source files unchanged. |
| `rectangular-template-c6599522-v1` | `c65995221cf016cb02533a6cb0952f19c22bfeb9` | Registered partial `--only rectangular_template`: 11/11 pass, zero failures/errors/skips. Twenty-one native command records include the required rounded-fraction mutant assertion and missing-grid-object link failure. All 15,910 source files unchanged. No product binary or browser executed. |

`stage-results.json` and `launcher-exit.txt` retain the first three-stage run's combined exit 1. The successful producer retry is separate; it does not rewrite the first run. All failures and partial original fixture bytes remain available.

Important original logs:

- Original producer failure: `baseline-adapters-a898ad6e/producer.log`, SHA-256 `ffe042de01d514f1ee62488516db56525751a4ae53b376ba81b41893857be151`.
- Corrected producer: `producer-retry-v2/producer.log`, SHA-256 `d374318e8e5a896d79fd2794bcc6ac0b2a116eb557d74a84a1f70eff5248ab52`.
- Full corrected producer receipt: `compatibility-baseline-v2/producer-receipt.json`, SHA-256 `4660414637141df3cfa8da3c392bb17ae33b7c96ff1c35eb8b86827d0eb707e1`.
- Rename failure: `grid-rename-native-v1/unittest.log`, SHA-256 `7c8813f5e8129a7b6e74efaef10c482f011dbc5e3798d6026fd53dbd93ebbe3b`.
- N1a success: `native-kernel-ab90a56d-v1/unittest.log`, SHA-256 `35dcd42906639c41ce30cb4ec4d0dde01746e27802b8ad7af32a87e07dc52533`. Original compiler output is in `native-build-inputs/build-log.json`; complete artifact hashes are in `native-build-artifacts.json`.
- Rename v2 failure: `grid-rename-native-v2/unittest.log`, SHA-256 `2fca6eb5ebbb065318fba1b23b7177a877220037524a6a47ebeb9741a3fcaeb0`; summary SHA-256 `68c97b0dca7ec37284d86afa03d21c0677955f9c14ae75d483840ab56ed1721e`.

The fixed main adapters persist at `/var/tmp/geo261-baseline-a898ad6e/.git/geo261-environment/tmp/geometry-tests/{model-base,bridge}` with their registry fingerprint sidecars. Shared host `/tmp/geometry-tests` is not their storage. The private namespace binds this persistent directory under its own `/tmp`; reuse must still go through the existing shared lock and verify freshness.

## N1b first queue attempt — interrupted before execution

N1b source `51e9045b43078a77383afdaf5db379117ffc8871` was queued through the same wrapper while another train held it (`train-20261016-18-r1`, PID 11437, acquired 00:37:21 UTC). `shared-lock-native-geometry.log` preserves that waiting-only evidence. Session `91983` disappeared after its agent turn ended. A later read-only inspection found no matching Windows or WSL process, no launcher completion file, and no N1b summary or archive. The first queue attempt therefore did not execute and must not be described as a running background job or a test result. A new attempt will use a separate launcher log and remain active through completion. Only actual completion receipts establish pass/fail; N1a evidence remains separate.

## Continuation — complete, aggregate failed

One replacement launcher, `shared-lock-continuation-v2.log`, acquired the original shared lock at 01:45:11 UTC (holder PID 16082) and completed all nine stages at 02:29:38 UTC. Its combined exit is 1, preserving the failed stages above. All 42 external top-level `.py`/`.sh` runner hashes are identical before and after. The lock was released after completion. No failed stage was rewritten or counted as a pass.

| Stage | Fixed source | Intended assertions |
|---|---|---|
| N1b — complete | `51e9045b43078a77383afdaf5db379117ffc8871` | 20/20 pass, zero fail/error/skip; see completed receipt above |
| Compact-grid rename v2 — complete, failed | `0e7c38bb8bf719f0084d24ce73ef65f016d6ddde` | 28 methods, six Undo subtest failures; mutations not executed; see actual receipt above |
| Region edges — complete, failed | old `51e9045b43078a77383afdaf5db379117ffc8871`, judge/new `be9ed3e7886f951918a8e02e678e0284f0d34079` | Original old-red expectation not met (four failures, expected five); new has one failing removal control. See actual receipts above. |
| N1c — complete | `49f03842cca4f70e0e38a82d120c06edd1b16189` | 28/28 pass, zero failures/errors/skips |
| N2a native — complete, failed | `4aabd21cf82d495f5ab4902bedc9330ca5ed4e3b` | 35 methods, six product-bridge compilation failures |
| N2a legacy — build failed | same `4aabd21c` | Same-source adapters failed compilation; 20 tests not run |
| Draw annotation — setup failed | `b370f753f22d0d119835c59d23b0a78344f8ee55` | Zero tests, one harness compilation setup error; four assertions not exercised |
| N2c linear/datum — complete, failed | `c28ea9639b79881f30995cd79ce843346373c31e` | 13 tests, eight pass/five actual-product compile failures; zero errors/skips |
| Rectangular template — complete | `c65995221cf016cb02533a6cb0952f19c22bfeb9` | Registered partial aggregate: 11/11 pass; native command receipt and both negative controls |

The prepared `6985cbd4`, `27552287`, `1e55c9b9`, and rectangular `a52b0d32` revisions were superseded before execution. No result is attributed to them. Full P1/native aggregate and browser acceptance remain outside this continuation.

## Corrected second batch — stages complete, aggregate failed

The new launcher `shared-lock-next-batch-v1.log` acquired the same lock at 02:39:56 UTC. Its four stages completed at 02:59:04 UTC, with independent exit codes `[1, 0, 0, 0]`; the launcher completed with exit 1 and released the lock. All 13 selected runner hashes are unchanged (both manifest SHA-256 values are `1b613f9ac6cc4ce5dbc7d59dee20be4b3e872b28cd856dca857eec549f813c5b`). It fixes the corrected native source to `db65132a41c4b4c815b6814784651e3980bf4f63`, then runs its separate registry legacy tests, rename `73aca666`, and region differential using judge/new `a88d3c57`. The datum diagnostic assertion remains red; earlier red receipts remain unchanged.

| Receipt | Actual outcome |
|---|---|
| `native-corrected-db65132a-v1` | Completed 02:44:34 UTC: original 76 tests, 75 pass and one assertion failure, zero errors/skips. Three CLI/model-base/bridge entrypoints and the previously compile-blocked controls now execute successfully. Sole failure is the malformed datum diagnostic: expected `parameter 99`, observed `parameter 99 field 1`. No expected value was changed. Seventy-seven compiler commands and 137 artifact hashes retained; all 15,894 source files and external runners unchanged. |
| `parameters-legacy-db65132a-v1` | Completed 02:45:44 UTC: same-source registry build, freshness checks before/after and original 20/20 parameter tests all exit 0, zero skips. Includes the actual model-package path. All 15,894 source files unchanged. Model-base SHA-256 `dbed1dbcced5847144879117c5940611004cbe77e4b921000039f3c96075fd39`, bridge `94ec4a7d6cb55d844beb98836f5963a0a82d994edce3d4a45654190f401f659f`. |
| `grid-rename-native-v3` | Fixed `73aca666e779527bd096e7f09a9bc12cdc38d051`, completed 02:49:04 UTC: original 28/28 methods pass, zero skips. Mutation receipt records baseline/restored VM 9/9 and native 3/3 green; both `omit-stagger` and `freeze-stagger-reference` fail as expected in VM and native. All eight outcome checks pass. All 15,789 source files and HEAD unchanged; baseline bridge fresh before/after. |
| `region-edges-old-51e9045b-v2` | Old product `51e9045b` with four judge-only added files from `a88d3c57`: six methods produce exactly the five named assertion failures, zero errors/skips. Both invalid real-product loads are wrongly accepted on the old product, while three geometry assertions also fail. This is the required old-red witness; the raw unittest exit 1 is preserved. All original product bytes and 15,861 post-overlay source files unchanged. |
| `region-edges-new-a88d3c57-v2` | Fixed `a88d3c57917d22aa28e3357b2c22e08c586a9f71`, completed 02:58:03 UTC: 8/8 methods pass, zero failures/errors/skips. Both removal controls compile and change the actual bridge's behavior to wrongly accept the corresponding invalid load and mutate the world; restoring the original again rejects atomically. Seventeen compiler commands and 26 artifact hashes retained; all 15,862 source files unchanged. |

## Original datum diagnostic witness — complete

`datum-baseline-a898-v1` runs the exact scene and two expressions extracted from the unchanged `db65132a` test against original main `a898ad6e12707104568679591fe1b21804bfc3df`. The original bridge is fresh before and after; its SHA-256 is `8e4088762c377ce6cbd023b0aee7d2484bd1c3c1267bb9008461ae50cbbc3d3f`. Both previews actually report `datum 9: I38 MISSING: parameter 99 field 1`, clause `D6c/I7a`, with the original expected description `axis X/Y/Z and exact spec-only expression within D1`. Both are invalid previews and leave the complete dump unchanged. All 15,784 source files, original inputs and runner hashes remain unchanged.

This receipt records observed behavior and asserts no expected diagnostic string. It does not edit the test oracle or make the earlier 75/76 result green. The witness and launcher exit 0; summary SHA-256 is `b56f5df5bf4752214550f9037a28a4989f3689aceabd632ff4ae8a484ebb5c79`, raw stdout `266666bee39414cec43f8b8a83fed67810ab90415e631d18c0b6d47e935d5fc9`. Original scene, commands, stdout and stderr remain in the receipt directory.

## Approved native groups — complete, one surviving control

Frozen source `99eeabe11875f4d18b1bc35607cd3601a0ac3b4b` ran 54 original methods in eight modules. It acquired the same shared lock at 03:06:11 UTC and completed at 03:08:29 UTC; launcher exit 1. Runtime discovery exactly matched each module and group. Results: actual CLI/model-base/bridge entrypoints **3/3 pass**; source/support **24/25 pass**; regions/contact **26/26 pass**. There are zero errors/skips. Supports includes 41 passing guard subtests and contacts includes 17.

The sole failure is `WoodSupportsProduct.test_stop_identity_guard_changes_kernel_client_and_real_between_placement` at the original test's line 59. The mutated standalone reference client returns 1 as required, but the actual mutated bridge still accepts the scene (`ok: true`) where that control expects rejection. This is a surviving actual-product control, not a compiler failure. The original assertions and failure trace are preserved; no expected outcome was changed.

All 15,929 source files and all four selected runner/recipe hashes remain unchanged. Source manifest SHA-256 before/after is `1071150302cd3ea607f9b6032d8b319f94b62bfd7739df38c28a68a9ee63070b`. The receipt retains 173 compiler commands and 292 artifact hashes. Raw unittest log SHA-256 is `3dad6c6a0b23f84dd01d8868d272dfe28f8461f5896c4c090bc991b3c6c431f7`.

G1/history modules were excluded. The earlier `322b837d` request is covered by this newer source and received no separate compile. This is a targeted native result, not a full aggregate or browser result.

## Native closure a3 — complete, grid control assertion failed

Frozen `a3aeef41adb1bc3bb5d0da0b941342387373a238` ran all 98 original methods: **97 pass, one assertion failure, zero errors/skips**. Actual entrypoints passed 3/3, guides 15/15, grid store 22/23, history 13/13, engineering 12/12, panel native 10/10, and source/support/datum/annotation regressions 22/22. The corrected support stop control and datum diagnostic both pass here; the earlier red receipts remain unchanged.

The only failure is `GridStoreProduct.test_zero_stagger_negative_control_reaches_real_parameter_rebuild` at original line 148. Its mutated bridge reports `ok: false` with I8a impact preview required, a valid preview and token 2. The original test asserted immediate acceptance before confirming that preview. This is an actual test assertion/flow failure, not a compilation failure or an executed passing control. The original response includes the previewed zero stagger. The test's expected value and helper were not edited during this run.

All 15,947 source files and all four selected runner/recipe hashes remain unchanged. Source manifest SHA-256 before/after is `a0eea0b5dd80e7387215d3a344097d6757b793b3428f350abc4b0a34eed809ec`. The receipt preserves 174 compiler commands and 303 artifact hashes. Raw unittest log SHA-256 is `b9fd81952f96767865b753d0817df2d33fc057a88f751319b8fd65989796b23e`. The original full trace is retained in `native-closure-a3aeef41-v1/`; launcher exit is 1.

## Original PF-3 registry prerequisite — complete, compilation failed

`pf3-regressions-a3aeef41-v1` reused the exact unchanged a3 archive and attempted the original registry command `python3 -u tests/binaries.py build bridge pf3-algorithm`. The bridge built successfully, but `pf3-algorithm` failed compilation: `tests/pf3_algorithm.c:40` passes an `int` as argument four to `pf_support_evaluate`, which now requires `GeoQuantity`. Build, before-status and after-status each exit 1. The original 50 layout/host tests and PF-3 mutation driver were **not executed**, so none of the 19 mutation outcomes has a result in this receipt.

The process completed at 03:39:41 UTC with receipt and launcher exit 1. All 15,947 source files and the three selected runner/recipe hashes remain unchanged. The source manifest matches the a3 native receipt exactly. The successfully built bridge is retained externally with SHA-256 `50cd223854d18f7089128ecb3576b1eacdcf7c07f96c6187ac56ff4d2000d73a` and its original registry sidecar; there is no successful PF-3 algorithm binary. The registry's original reported compiler output is preserved in `build.log`, SHA-256 `0c7695001454d67fdd037df3dc6a0d72a42fd3b5b457123280ba5a1f32f78307`. This is a code compilation defect, not an environmental block or a killed mutation.

## Corrected original grid product referee — complete

Frozen `b21334a2f5b912a876e0cf98b3cca8ae11065037` ran the original five grid product methods: **5/5 pass, zero failures/errors/skips**. The corrected zero-stagger control now checks the unchanged dump at a valid implicit preview, confirms the actual preview token, requires successful acceptance and asserts the actual committed mutant's zero stagger. The baseline rejection and mutation controls remain original assertions from that commit. This separate passing receipt does not rewrite the a3 failure.

Execution completed at 03:48:22 UTC with receipt and launcher exit 0. All 15,956 source files and all four selected runner/recipe hashes remain unchanged. The source manifest SHA-256 before/after is `6b27a9dd962ebae276020023ab700bb50d0abee8adc2c4304acbde7bfdbd14c2`. The receipt retains 36 compiler commands and 91 artifact hashes; raw unittest log SHA-256 is `22160f7bb2b9753c5b63d3f846e049c4e9620c0a11ce9e5df3b73799a9acd17c`. No full aggregate, PF-3 mutation driver, or browser result is implied.
