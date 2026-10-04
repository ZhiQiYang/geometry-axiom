# P76 parameter preview ownership — bounded cloud handoff

Implementation: `d93d6a9c1c4a77a4675efe66ec1aaa3ceca53835`, based on main `4bea91a3ff3af25d1062040b2c2ea776b60a8daf`.
Independent branch: `fix/parameter-preview-ownership-p76-20261004`. Root alone reviews and merges.

## Confirmed cause

Ordinary `ParameterUI.preview()` left `s.preview` and its enabled confirm button alive while awaiting both `engineering-read` and the replacement preview. The native core has one candidate slot. Once it creates replacement token B, token A from the previous preview is correctly rejected. The UI could still submit A during delivery of B. The rejected confirmation leaves the unsaved draft pending; the harness then times out waiting for `!ParameterUI.pending`.

The old P76 `confirm()` helper tested only whether the button was enabled. During this interval it observed the previous candidate, so its wait did not establish completion of the requested replacement. This is both a product ownership race and a weak completion oracle. Removing the token rejection or adding a delay would hide the product defect.

Real Linux Chromium/native receipt reproduction, with only delivery of the genuine replacement JSON held:

| Exact checkout | Native sequence | UI at held replacement receipt | Outcome |
| --- | --- | --- | --- |
| main `4bea91a3ff3af25d1062040b2c2ea776b60a8daf` | preview 1 → preview 2 → confirm 1 | `試算中…`, confirm enabled | TOKEN rejection; pending true; native parameters empty |
| main `861b65e9e2281192dd41a068fdd87866617b638d` | preview 3 → preview 4 → confirm 3 | `試算中…`, confirm enabled | Same rejection and pending state |
| original PR125 `2b53a032947e67866c75351e50c88d970fb4fd02` | preview 3 → preview 4 → confirm 3 | `試算中…`, confirm enabled | Same rejection and pending state |

The three relevant product/harness files plus engineering adapter are byte-identical across those checkouts. Native bridge sources are unchanged between the bases. Fresh isolated runtime probes, request/receipt/delivery `performance.now()` timings, native tokens, and DOM state are preserved in [validation.json](parameter-preview-ownership/validation.json). These are actual native candidates and rejections, not fabricated preview/confirm results.

An unmodified, undelayed main4bea parameter run completed **72/72**, with zero browser exceptions. Thus a Linux pass does not exclude the race. PR125 owner's Windows reports of two 57-assertion partial timeouts and full 1586/0 incomplete are prior owner evidence, not new cloud executions. This worker has not executed Windows or reconstructed the exact historical Windows timing. The controlled native-delivery case establishes the matching TOKEN → pending failure mechanism on all three exact sources.

## State and scope decision

`retirePreview()` clears accepted preview ownership and disables confirmation synchronously before the first await. It sends only the existing token-scoped cancel. Every replacement owns a local `previewRequest`; generation, request serial, editor, and project context must still match when its receipt arrives. A stale receipt is discarded using its own token. Its `finally` cannot clear a newer request.

Preview requests leave inputs editable and may be superseded. `s.busy` remains exclusively the confirmation lock, so a confirmation admits one request and preserves inputs until success/failure resolves. `pending` includes the current preview request; the narrow `previewing` getter lets focused waits distinguish receipt completion from an old enabled button. Failed replacement delivery never restores the old candidate. Discard and definition invalidation use the same retirement path.

Changes are limited to `parameters.js`, the two existing focused parameter harnesses, a focused receipt-ownership module, and the corresponding verified census/evidence. EngineeringAdapter, native core, axioms, project-store/reader (#60), menu/app (#116), room outline (#54), and global result metadata (#118) are unchanged. No user PC, service, deployment, paid permission, or external PR125 branch was modified. No sleep/retry was added.

## Executed gates

- Short normal workflow and race cases: **14/14**, zero page exceptions. Source-read delay, genuine candidate receipt delay, disabled trusted clicks plus direct stale handler, native old-token rejection/dump equality, receipt delivery failure, repeated previews and older completion while a newer receipt is pending, single confirmation under repeated clicks, discard/new-editor late reply, project-switch late reply, normal confirm, atomic undo/redo, and complete-project save/reopen.
- Complete focused P76: **86/86**, zero failures, zero skipped groups, zero browser exceptions. Existing 72 assertions remain; 14 meaningful ownership assertions were added.
- Registered native suites: **41/41**, zero skips (`tests.test_parameters_core`, `tests.test_engineering_core`, `tests.test_assembly_parameter_refs`). Binaries were built and fingerprint-registered with `tests/binaries.py`; an earlier raw-binary attempt skipped and is not counted as a pass.
- Requested parameter-grid picker acceptance passed with zero page exceptions: actual visible create menu → parameter card `(915,1830)` → preview/confirm → create infinite grid with initial u600/v400 → open each real reference select and choose by keyboard → preview/confirm. Both actual option lists contain `直接輸入`, card `#1` width `#1:2` (915 mm), and length `#1:3` (1830 mm). Selected inputs are read-only at 915/1830; native `uDefinition.parameterRefs.step` is `{parameterId:1,fieldId:2}`, v is `{parameterId:1,fieldId:3}`, and effective steps are 915/1830. No grid source file changed. Dropdown/selected/preview/confirmed screenshots are `/tmp/geometry-p76/screens/grid-{u,v}-picker.png` and `grid-parameter-{selected,preview,confirmed}.png`; full read-back is in `validation.json`.
- Full CDP: **running; final actual result will be recorded before publication**. Golden began at total **1973**, P76 **72**, P79 **87**. Any update must come from a completed zero-failure full run; only P76's 14 new checks should increase the census. P79 and all other sections must remain equal.

Commands used isolated `GEOMETRY_TEST_URL` services, dedicated `/tmp/geometry-p76/fb-*` feedback, `/usr/bin/chromium` and `--no-sandbox --disable-dev-shm-usage`. Browser plugin was unavailable; the repository's native CDP harness and installed Playwright ran the actual app. No browser dependency was installed. Trace and screenshot paths are local temporary evidence; structured receipts and results are committed above.

The requested grid selection screenshots are also committed: [u reference choices](parameter-preview-ownership/grid-u-picker.png), [v reference choices](parameter-preview-ownership/grid-v-picker.png), [915/1830 native preview](parameter-preview-ownership/grid-parameter-preview.png). They use synthetic acceptance data.

## Integration and remaining gates

This branch targets current main independently. PR125's external owner is performing its ordinary merge of main4bea; this worker neither altered nor pushed that branch. Root can integrate this narrow fix before or after PR125 because PR125 does not change the parameter files. No menu reimplementation or duplicate reader was created. Preserve PR124's selected-wall failure versus explicit boundary-only path, historical replay, P79=87 and original total1973 coverage.

Windows, physical iOS/IME/OS picker, cross-browser behavior and GitHub-hosted CI are not newly verified here. Exact-source timing reproduction and passing cloud gates do not certify PR125's latest merged head or its separate design/owner acceptance gates. Root owns those final integration decisions.
