# #58/#59 native source subdivision — validation and handoff

This is execution evidence and an ownership handoff, not another geometry specification. The user accepted item 7's six explicitly written behaviors. Geometry remains defined by `../公理層.md`; the transport boundary is [GRID-SUBDIVISION-NATIVE-CONTRACT.md](GRID-SUBDIVISION-NATIVE-CONTRACT.md). No unadopted Q36 alternative is implemented.

Latest merged base: main `d1a161f6b1ed50d100d316a0b90be9d7d34451f6`. The complete initial census and independent review used main `067cbdc08340536eaf1a2ec96cf923e7682a9afe`. The native implementation is frozen at `414c392a504b5f35d5e804dab6bad8784806bc3f`; later commits add tests, documentation and real execution receipts. All C/header/include files remain byte-identical to that implementation. The original `current_geometry.c` retains CRLF throughout.

Formal adoption commit: `12b75b050c3b1aa18a1b66adea79b7f5216e5976`; normalized axiom SHA-256: `ac2b4ede9d6687111e9ef2f4c6194cb3d8f97543b55d41c455ec9db9b01a96b1`. The existing reader was regenerated through its canonical synchronizer. Traceability is not promoted from test success: I25a remains computed partial under the existing matrix rules.

## Approved scope and regression correspondence

| Approved behavior | Formal/API boundary | Independent regression |
| --- | --- | --- |
| Source-owned single layer, all-cells or one signed cell, inherited by every configuration | D19a/I25a; rules are GridSystem data; cell coordinates use decimal strings; no expanded World grids | Literal repeat/panel/signed vectors; two differently anchored configurations; invisible source cells |
| Nonstagger repeat/repeat-panel; divisions 1..65; at least one axis above 1; integer millimetres | Full source pitch must divide exactly; REPEAT_PANEL includes its gap | Exact pitch and negative type/division/source/cell fixtures; 65-way boundary |
| Stable source/rule/cell/inner-line refs; cancel consumes no committed key; complete undo | Existing candidate World, revision, preview token and history; source-local uint32 key/highwater; undo restores allocator too | Cancel/create/undo/redo; exhaustion; deleted-last-rule save; wrong source/key/index; pending confirmation survives queries/load failures |
| Used divisions/selector/delete refuse; overlap and manual conflict refuse | Formal guide/direct timber use locks structural edits; rename preserves key; both conflict creation orders revalidate | Guide and compound refs; direct refs; both manual conflict orders; same-key other-source refusal |
| All affected configurations/components validate atomically; rule lines supply no support | Existing full candidate rebuild and D11/R6 support; direct complete footprint stays in its cell; guide expressions take coordinates | Failure only in the second actual component; real-support refusal; guide/direct distinction; full dump/revision preservation |
| Save rules, refs, allocator and required capability; unsupported input refuses | `requires grid-subdivision-rules/1`; replay-only highwater; inferred syntax cannot hide capability; native scenes preserve complete rule closure | Fresh-process roundtrip; stripped/unknown capability; missing/wrong source/rule/index/highwater; unsupported Python producer explicitly refuses |

The numerical fixture was fixed independently before reading the new production evaluator. It supplies observations and test inputs only: [vectors](../tests/fixtures/grid_subdivision_vectors.json), [37-test oracle](../tests/test_grid_subdivision_oracle.py). Production uses the existing cell geometry and shared guide clipper.

Query budgets are 32 rules per source, 1024 returned cells and 4096 emitted segments. Exact mode refuses excess. Sample mode returns whole cells, stated stride and original identities, and validates only returned cells. No sampled omission is reported as verified. Tests cover 32/33 rules, 1024/over-limit cells and 4096/4224 segments, including unchanged pending previews.

## Actual execution

- Default 8 MiB stack: standalone oracle 37/37 and original scene baseline 139/139. The separate instrumented focused set is described below with its actual stack limit.
- Complete unchanged-source census: `python tests/run_all.py --build`, 62 suites, 1810 counted items, 1809 passed, zero failed, one named platform skip. Its exit 1 was solely six missing new-suite count entries, not a native/test failure. Exact new floors are diagnostics 8, subdivision 37, catalog 14, definition 27, executor 40 and request 5. Existing floors must stay unchanged.
- Official complete recorded-floor census: `python tests/run_all.py --build --update-expected`, 62 suites, 1810 counted items, 1809 passed, zero failed, one named Windows-GDI platform exemption, exit 0. All prior floor values and ordering were retained; only the six exact new entries above were added.
- Final normal full strict after merging latest main `d1a161f`: `python tests/run_all.py --build`, default 8 MiB, all 62 registered suites ran, 1810 counted items, 1809 passed, zero failed, one named platform exemption; no expected mismatch or environment block. **Exit 1 remains** because main's newly merged #44/#77 test files are not registered by the shared runner. This is a genuine latest-main gate blocker, outside the native/four-case-floor ownership; it is not silently excluded.
- Actual mutation reruns: all three disjoint partitions compiled and ran the unchanged mutation tool against `414c392`, using default 8 MiB stack. The merged [tracked receipts](../tests/mutants_results.json) pass genuine `python tests/mutate.py --check`: 48 definitions, 40 killed, one crashed, four equivalent, three retired, zero survived/invalid/stale/blocked. M20 is a repeatable crash in three executions of the same fixture; it is not relabeled as an assertion kill. Retired definitions are not claimed as executed.
- Source-wide execution receipt closure: `ea2ebbfc23618d61dad18bb984f5b2a8b1461f5b26cce88a6b5b74c1224d7cc7`; original scene oracle hash: `eb5a850003998f3e2a5ca67dbbe56dc3d15038c0f19205bba36311c92fad3f63`.

Fresh standard bridge source fingerprint: `ebf8f16a35cf0d6152a93d2cf281bbbc9a93f19226b6805f6a51eed1b50e75a5`; binary SHA-256: `7046f429486793a61789c23823540e0834393d670fa5dd2136dd2d9c035c8c71`. The official binary registry checks source closure and executable bytes; stale binaries were not borrowed.

ASan/UBSan: 149/149, exit 0, no skips, with `-O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -fno-pie -no-pie -fstack-usage`, leak detection and halt-on-error enabled. This instrumented process uses a disclosed 64 MiB stack; standard release checks use 8 MiB. Instrumented source fingerprint `2c555d9982684a46410040e3606e41716893ee3ec3b91adb17f843fb2a16f35a`, binary SHA-256 `f065843d3bfce9f948c8d54b886faaa42a80ccfc00b39a384d2a78fde34d70c3`.

## Clipping completeness and stack evidence

An independently authored legal five-hole comb has 40 removed intervals and exactly 41 visible segments. The old shared helper returned 32 and omitted nine. The fixed original helper returns all 41 through applied-grid/binding queries, exact and sample rectangles, formal guides, pending confirmation, save/reopen and undo.

The conservative temporary storage bound is `32*(8+1)=288`. A 32-vertex loop supplies at most 16 intervals; subtracting each hole interval increases the union size by at most one, giving an actual theoretical upper bound of 144. All shared guide/grid callers use the corresponding complete capacity. Per-loop polygon buffers remain 32, and legacy stagger selection limits stay explicitly 32. The query's 4096-segment budget is unchanged.

Independent O2 stack measurements: shared clipper 19,584 bytes; source visitor 11,216; bridge query command 23,600. World remains 2,029,080 bytes, GuideLine 544 and ReferenceGrid 1496. Enlarged GridQueryAxis is 757,296 bytes and every production allocation is on the heap. Largest existing `apply_subgrid_line` frame remains 4,060,048 bytes; complete standard tests pass at 8 MiB.

## Independent review and dependency boundaries

Independent [read-only review](NATIVE-SUBDIVISION-REVIEW-20261004.md) at `0394cfd53a0f6bb3056de476733010f4c87dd5bd` against main `067cbdc` returned PASS with 53 checked file/line anchors. It confirmed all six adopted behaviors, original shared clipping, allocator/history identity, atomic negative-capability loads, bounded queries and native source equivalence. It reported no native defect or additional user decision.

This branch includes the explicit minimal diagnostic dependency from draft [PR #103](https://github.com/ZhiQiYang/geometry-axiom/pull/103): code `74469be` cherry-picked as `81c95bb`. Its five production files expose exact existing `DIMENSION_TYPE/D33` and `RULE_VERSION_IMMUTABLE/D32` failures without changing acceptance or persistent World data. The #49 owner's test-only correction `b65857b` was applied as `65fd35e`; native ownership does not extend to #49 modules/tests. Independent isolated diagnostics validation reports 94/94 tests, six isolated CLI cases passed with four accepted and two precisely rejected outcomes, 35 assertions, six distinct cleaned processes, and preserved generic historical blocked receipts. The stale four-passed/two-blocked wording in the #49 module README is an external owner documentation follow-up.

Native owns World, native scene serialization and native web bridge changes. The integration owner `01a100b5-800b-75f2-9a02-71ee53e550ba` owns project-store, project schema/capability preflight, app and ContextHistory. Native assigns no project format number. That owner must save native dump plus actual capability requirements, keep raw unsubmitted drafts separate from formal objects, and group confirmation/attachments into the existing context transaction. Cancel creates no formal rule reservation; undo restores the complete prior context.

Native scene roundtrip does not certify a complete `.gcanvas` draft flow. Full #61 UI, physical Windows/iOS acceptance, #44/#77 modules and #54 automation remain outside this native slice. No nested subdivision, arbitrary region, per-face override or new automatic component generation is added. Handoff is a draft PR; no merge or deployment is authorized for this worker.

The latest-main blocker consists of nine files: `tests/test_model_update.py`; `tests/test_model_update.js`; `tests/test_room_collection.js`; `tests/test_issue77_attachment.js`; `tests/test_issue77_workspace.js`; `tests/test_issue77_browser.js`; `tests/test_issue77_exit_browser.js`; `tests/test_issue77_recovery_browser.js`; `tests/test_issue77_remove_browser.js`. The shared owner must register execution/exclusion appropriately and preserve actual counts. Root explicitly delegated only the four #49 floors/registrations to this worker; no #44/#77 test or additional shared floor was edited.

An independent read-only check of the executable new suites at default 8 MiB reports model-update JS 39/39, room-collection JS 31/31, issue77 workspace 6/6 and model-update Python 22/22. Attachment checks report 4 passed and 5 skipped because the formal `GEOMETRY_ISSUE77_ATTACHMENT_TEST_ADAPTER` is absent. Total: 102 passed, 5 explicitly skipped, no executed failure. Those five attachment checks are not claimed as verified; their formal capability/closure/ContextHistory adapter remains the integration owner's scope.

PR103's final head is `b7342cf3d3f78cd7259e044d4e1e106ea3027ab0`, merged with the same latest main. Its exact post-`e8174f4` floor increment is four entries, 20 added lines, no prior value change. It has 61 registered suites, 1773 counted items, 1772 passed, zero failed and one named exemption; its latest normal strict exits 1 for the same nine unregistered files. Its native code remains byte-identical to `74469be` and its genuine mutation check exits 0.

## Retained execution log identities

The selected cloud workspace retains these logs. SHA-256 values identify the actual complete artifacts; the tracked mutation receipts separately retain per-executable compilation, baseline and execution evidence.

| Artifact | SHA-256 |
| --- | --- |
| `/tmp/subdivision-final-strict.log` — official full recorded-floor census | `0e8e97468d1860e9ba7f1053b12f5cb9b3dbcf97b513496d2df3d2e4894b6c69` |
| `/tmp/subdivision-latest-main-strict.log` — latest-main normal gate | `bd595335859f0df24e88a10ef878fdf9251be5c0ace3720ac281ecbd2ec32424` |
| `/tmp/subdivision-clipping-sanitizers.log` — 149 instrumented checks | `634fbe4611d71712f7ace1e4a91004f20b3a2e19bc673377dbd77232f80b13b8` |
| `/tmp/subdivision-final-independent-review.md` — original independent review | `d4b8eecf8b0460d189dde74c089b66ac477e23128dee0a39c44e6e057821aa35` |
| `/tmp/subdivision-latest-owner44-77-readonly.log` — read-only additional suites | `23ff98111f9519cedfef6f8594148a27565ec2d9f37449366707890f5f44714c` |
