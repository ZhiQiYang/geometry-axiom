# Frozen Geometry UI / single-room acceptance

Tested product: clean `640a81443b3d070dba3d8a0aa52adb2d64cebe0b`, `<workspace-path>`.
Isolated URL: `http://127.0.0.1:19180/`.
Runtime: `ef68eb1ca2ed0985a83a986da6640e695fdc44c607bdde18aecbe82b8b88fb1e`, PID `92781`, session `0cef2fea942845808a7740e163a375b6`.
Before/after HEAD, clean status, measured source files, native source closure, configured and live executables, runtime/session and runner bytes matched in every receipt. No repository writes were performed by this verifier.

| Independent scope | Actual exit | Passed / failed | Accepted complete | Gate directory |
| --- | --- | --- | --- | --- |
| Formal original six adopted UI groups, including four strengthened header assertions | 0 | 198 / 0 | true | `ui123-640a8144-gate` |
| Formal original single-room direct-row suite, all ten normal scenarios and six negative assertions | 0 | 273 / 0 | true | `room54-640a8144-gate` |
| Explicit scratch supplemental plan, BOM, row-blur, S2 groups | 1 | 108 / 3 | false | `supplement-640a8144-gate` |

All paths above are under `<workspace-path>`. Results are separate executions and must not be added together as a full CDP, full Space, or all-#123 result. `releaseApproved:false` remains unchanged: this is execution evidence, not merge or deployment approval.

## Formal original six

Groups ran in original order: colors 8, headers 35, components 28, v3 54, grid-mobile 4, model 62; preflight 4 and final 3. All groups passed. Desktop and 390px interactions used normal pointer and keyboard input; no force clicks, caller retries, or assertion removal.

Gate receipt SHA256: `9efe8a022de5be3178131653d6cc612fba69daac9a711b9fb14f5e6e4de59099`.
Raw log: `ui123-640a8144-gate/command.log`, 32934 bytes, SHA256 `fcbab6fa164acb71ae61d79cf63a40ab6ce3d2bb0fc633e341f34df9185dfda8`.
Probe: `<isolated-test-directory>`, SHA256 `14b3e65e15374b1ce1585d23afb515f55603a6acf4cc4d31ea798bbf3981fd94`.
Actual Node PID 93624; Chromium PID 93675.

## Full single-room #54 suite

Exact ten completed normal scenarios: pdf-rectangle, pdf-l, pdf-notch, image-rectangle, image-l, image-notch, image-rectangle-box, pdf-l-mobile, image-notch-mobile, pdf-l-transform. All six original negative assertions occurred exactly once and passed. The ninth scenario that failed on f980 was reached and completed on this frozen candidate.

The original six measured cases retain independently checked native geometry, the same complete start state, and the same exact ordered confirmed endpoint. Their actual action counts under `room-direct-row-dimensions/1` are:

| Source | Shape | Candidate | Retained manual route |
| --- | --- | --- | --- |
| PDF | rectangle | 12 | 16 |
| PDF | L | 14 | 20 |
| PDF | notch | 16 | 24 |
| PNG | rectangle | 12 | 16 |
| PNG | L | 14 | 20 |
| PNG | notch | 16 | 24 |

Counts include a genuine dimension correction, every edge dimension input, and relevant navigation. Import/calibration, Save/New/Open and automatic locator scrolling are excluded by the recorded protocol. Import/calibration, native acceptance, all displayed edge oracles, Undo/Redo and actual downloaded Save/New/Open are nevertheless verified separately. Elapsed machine time includes automation settling and is not human operation time. Legacy cost protocols remain attached to their original evidence.

Gate receipt SHA256: `6dda336600f3a543fa9959a2eea556f36a94f66f06507fcabc5f1ccf5a7dcdca`.
Raw log: `room54-640a8144-gate/command.log`, 39877 bytes, SHA256 `1eaa848705d9a893dd4d6f9a63858a4ff2c84fcd06efba01ec8a34b0fa0858d6`.
Probe: `<isolated-test-directory>`, SHA256 `af61f570d299fbf50026fc05c38d6f2d0fbd43ff66f6f4d020699662843285de`.
Actual Node PID 98181; Chromium PID 98210.

## Supplemental failure retained

Actual executed probe was the explicitly approved scratch file `<workspace-path>`, SHA256 `43a3d2b6adf011dec05f85af71c14d0de110e24071b69b5bd636dcf30d0e72ca`. This was not execution of the formal six-group probe. Its canonical `completed:true` means all four groups were attempted; gate acceptance `completed:false` and exit 1 mean the declared scope did not pass.

- Plan: all 16 assertions passed at both 1382px and 390px.
- BOM: 11 positive checks passed at 1382px, followed by one group error. After trusted deletion of timber 3, the actual screenshot shows the existing HTML `reference-impact` dialog with exact `delete timber 3` and Confirm/Cancel controls. The test waited for deletion without confirming the required preview. No actual network request/response trace was captured in this original run; screenshot, source contract and original logs are retained. Last-row cleanup, Undo and 390px were not reached.
- Row-blur: 19 positive checks passed at 1382px, followed by one group error. The test asked Playwright `locator.click` to click an actually disabled `#refRoomConfirm` after invalid raw input `0`; actionability waited until timeout. This is not evidence that the product should enable that button. Disabled-pointer attempt, Cancel/recovery and 390px remained unverified.
- S2: 55 positive checks passed at 1382px, followed by one group error. The delete action was correctly inside its closed disclosure. The shared `click(summary)` helper auto-opened that target's own closed disclosure, then its normal summary click closed it again. The subsequent normal button click timed out on a hidden button. Remaining preview Cancel, owner interruption and 390px were not reached.

Gate receipt SHA256: `a45b547c7f17ec12268b64abcede3c95922ad48b4073b50bf5186546eb22e183`.
Raw log: `supplement-640a8144-gate/command.log`, 43268 bytes, SHA256 `4899949ac78cb4f04878fc2b882d0ec58dd5c855df3de7815975f71414330876`.
Probe: `<isolated-test-directory>`, SHA256 `c9c5f9a8a052272adc4a8a9b597ca299355109688a0d7598ccc3db808cf47432`.
Actual Node PID 109729 and Chromium PID 109761 were both absent after the source's finally block closed its owned browser. This verifier released port 19180's test leg; root owns the service itself. No rerun was attempted.

## Source archive and limits

Each gate has an `executed-sources` archive of all 303 measured repository source files plus the exact v3 wrapper. The supplemental archive separately includes actual scratch override bytes. Every file was checked against the receipt and frozen Git blob before writing the new archive; original receipts/logs were not changed. Archive manifest hashes are `da67c4a2cbcce06c06dfee82bc8d218b1c78493133a333379078020ef8798ef6` (six), `acca0564a94de638368d0fe5d36d6aa95ada45a59b3ea7f8de96b96184fa833c` (#54), and `56d75a27d0baa529398d021a4dddfdd3e855fc426a626351b8eab5c4b096c10e` (supplement).

Every receipt records exact commands, actual exits, Python/Node/Chromium identities and native bridge identity. Actual Node bytes/command/cwd/PID and actual Chromium bytes were compared to configured identities. Chromium was launched with `chromiumSandbox:true` and without sandbox-disabling flags; the operating system's kernel sandbox state was not independently inspected. Original #54 accepts native dialogs without a message-specific allowlist; this execution does not upgrade that original dialog policy.

Full CDP and full Space are independent root-assigned gates. Physical touch/phone/IME, operating-system file pickers, private ZIP/golden pixel comparisons and all 43 checklist items are outside these receipts. Historical 2703 failures, f980 six pass/#54 failure, c0 header failure, and original 43a3 supplemental failure remain unchanged.

Next: root reviews a new scratch supplemental oracle version that preserves original conditions, performs guarded real native-preview confirmation for BOM, uses one trusted pointer attempt at the disabled row Confirm with positive refusal assertions, and handles a target's own summary once. Root then selects a new frozen final candidate for the authorized purposeful supplemental verification. No product change is inferred from these harness failures.
