# #58/#59 native source subdivision — validation and handoff

This is execution evidence and an ownership handoff, not another geometry specification. The accepted item 7 contains six explicitly written behaviors. Formal geometry remains [公理層.md](../公理層.md) D19a/I25a and related clauses; the [native contract](GRID-SUBDIVISION-NATIVE-CONTRACT.md) defines transport. Q36 and the older proposal do not authorize additional behavior.

Merged base: main `d1a161f6b1ed50d100d316a0b90be9d7d34451f6`. Frozen native implementation: `f0a185df8a8a5e15d792fad7f35fcd1a68d38478`; later changes are tests, reader synchronization, shared registry, real execution receipts and documentation. C/header/include files remain byte-identical to that frozen implementation. `current_geometry.c` retains 13,036 CRLF lines and zero bare LF.

Formal adoption correction: `73b9ba1d417c1b6c9885951b24139b67f8550312`; normalized axiom SHA-256: `d4bd69cd3dcbcef10802dd401a66b293afdaa09abccc6853d7a39f478cefe29a`. New rules accept only two nonstagger REPEAT axes, following merged PR100's implementation queue. Divisible REPEAT_PANEL axes refuse new or retained source rules; ordinary existing panel sources, bindings and grids retain their original behavior. Earlier broader panel-rule evidence is superseded.

## Accepted behavior and independent regression

| Accepted behavior | Formal/API boundary | Regression evidence |
| --- | --- | --- |
| One source-owned layer, all-cells or one signed cell, inherited by every configuration | D19a/I25a; GridSystem rules, decimal-string cell coordinates; no expanded World grids | Literal repeat/signed vectors; differently anchored configurations; invisible source cells |
| Two nonstagger REPEAT axes; divisions 1..65; one axis above 1; exact integer millimetres | Full pitch must divide exactly; no rounding or automatic conversion | Type/division/source/cell negatives, 65-way boundary, both-axis panel refusals and ordinary panel controls |
| Stable source/rule/cell/inner-line refs; cancel consumes no committed key; complete undo | Existing candidate World/revision/preview/history; source-local uint32 key/highwater | Cancel/create/undo/redo/exhaustion, wrong source/key/index, pending confirmation after queries and failed loads |
| Referenced divisions/selector/delete refuse; overlap and manual conflict refuse | Formal guide/compound/direct use locks structural edits; rename preserves identity | Both manual-conflict creation orders and two-source/same-key controls |
| All affected configurations/components validate atomically; sublines supply no support | Existing full candidate rebuild and D11/R6 support; direct footprint stays in parent cell | Failure in the second actual component; real-support refusal; guide/direct distinction; state/revision preservation |
| Save complete rules/refs/allocator/capability; unsupported input refuses | Native `requires grid-subdivision-rules/1`, replay-only highwater, lexical syntax capability guard | Fresh roundtrip, unknown/stripped markers, default-only allocator input, missing/wrong references and incomplete closure |

The independently authored [16 literal vectors](../tests/fixtures/grid_subdivision_vectors.json) and [40-test oracle](../tests/test_grid_subdivision_oracle.py) are observations and regressions, not a second production evaluator. Native reuses existing cell geometry and the shared clipper. The same three new regressions fail semantically against the saved pre-fix binary, with zero infrastructure errors; its SHA-256 is `7046f429486793a61789c23823540e0834393d670fa5dd2136dd2d9c035c8c71`.

Engineering budgets remain 32 rules/source, 1024 returned cells and 4096 emitted query segments. Exact mode refuses excess. Sample mode returns whole cells with a stated row-major stride and unchanged identities, validating only returned cells. The independent eight-hole comb gives `64*65 + 72 = 4232` segments in one cell. Cell/exact/sample and a two-cell sample return `QUERY_CAPACITY` with requiredCells 1/2 and requiredSegments 4232. The stride is bounded by requiredCells and terminates at the first-whole-cell selection; no inner line is thinned. Pending confirmation, World and undo remain intact.

## Actual execution

- Default 8 MiB stack: fresh original scene baseline 139/139 and owned subdivision oracle 40/40, no failures or skips.
- Complete official census `python tests/run_all.py --build --update-expected`: 63 suites, 1915 counted items, 1914 passed, zero failed, one existing named Windows-GDI platform exemption, exit 0. The only count change after the owner registry increment is the owned subdivision floor 37→40; all other values and ordering are preserved.
- Final normal strict `python tests/run_all.py --build`, default 8 MiB: all 63 registered suites ran, 1915 counted items, 1914 passed, zero failed, one existing named Windows-GDI exemption; exit 0. No expected mismatch, unregistered file, stale binary, environment block or avoidable skip remains. Formal owner/browser integration is separately required and is not counted as passed.
- Actual fresh mutation executions against frozen f0: all three disjoint partitions compile and run the unchanged tool, baseline 139/139, ordinary 8 MiB stack. Genuine merged `python tests/mutate.py --check` exits 0: 48 definitions, 40 killed, one crashed, four equivalent, three retired; zero survived/invalid/stale/blocked. M20 repeats the actual SIGSEGV three times and remains a crash, not an assertion kill. Retired definitions are not claimed as active executions. [Tracked receipts](../tests/mutants_results.json) retain actual f0 Git identity, binary identity and exits.
- Source-wide execution closure: `252befe533dd26cdede2735ec1c596cfb19787efabf487ad6a572f5522452351` (23 files); unchanged scene-oracle hash: `eb5a850003998f3e2a5ca67dbbe56dc3d15038c0f19205bba36311c92fad3f63`.
- ASan/UBSan: 152/152, exit 0, no skips, with `-O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -fno-pie -no-pie -fstack-usage`, leak detection and halt-on-error. This instrumented process uses a disclosed 64 MiB stack; release checks use 8 MiB. Instrumented fingerprint `027919a1b9276c581c8eff9dc3d706ae5f077be4f08bdae1591d7304a1e74834`, binary SHA-256 `db3d66a1aea3473243db5c5938eff80299d8ce2056648e2e231af67ff25b66ae`.
- Fresh standard bridge fingerprint `2dac9dc80ab3adeb11a56557fafa49c242c1a9ff32cb7b683fac3f6d1cf17eb2`, binary SHA-256 `7a1510af11f1a9142fb2024cb33f657d1a3f31e3ff6cbf3df13f246eaac73205`. The official registry verifies source closure and executable bytes.

The canonical reader is synchronized at r22: 120 clauses, 598 blocks, 31 witnesses and 63 examples. Reader 41/41, witness marks 6/6 and witness diagnostics 2/2 pass; fresh f0 core checks all 31 existing witness outputs unchanged. D19a has no existing visual witness and I25a remains computed partial; tests are not promoted into completed traceability. No second geometric truth or invented source-rule witness is added.

## Shared clipping and stack

The legal five-hole comb still returns exactly 41 visible segments; the old helper omitted nine after its 32-entry truncation. The shared helper's conservative temporary capacity is `32*(8+1)=288`; a 32-vertex polygon has at most 16 intervals, giving a tighter theoretical bound of 144. This covers all allowed holes without growing World/history. Query segment capacity remains 4096.

Fresh independent O2 `-fstack-usage` builds of frozen f0 core/bridge and an include-size probe confirm: shared clipper 19,584 bytes, source visitor 11,216, bridge query 23,600; World 2,029,080 bytes, GuideLine 544 and ReferenceGrid 1496. Temporary GridQueryAxis is 757,296 bytes and production allocations are on the heap. Existing `apply_subgrid_line` is 4,060,048 bytes; standard tests pass at 8 MiB. Actual fresh artifacts are `/tmp/subdivision-f0-stack-bridge-web_bridge.su`, `/tmp/subdivision-f0-stack-core-current_geometry.su` and `/tmp/subdivision-f0-size-probe.c`.

## Independent review and integration boundary

The new [independent read-only review](NATIVE-SUBDIVISION-REVIEW-20261004.md) returns PASS for frozen f0, superseding the prior broader panel-rule scope. Its actual 8 MiB microchecks confirm panel guard/legacy controls, atomic source edits, lexical capability encounter/reset/deleted-source lifecycle, bounded one/two-cell sampling counts, and preserved confirmation/undo. Its fresh mutation B check and a separate C receipt audit pass. No native defect or further user decision remains.

Typed diagnostic dependency: [draft PR103](https://github.com/ZhiQiYang/geometry-axiom/pull/103), production `74469be` cherry-picked as `81c95bb`, adds exact existing D33/D32 refusal evidence without acceptance or World changes. The #49 owner's tests-only patch `b65857b` is retained. Isolated diagnostics: 94/94, six true CLI cases passed (four accepted/two precisely rejected), 35 assertions, six distinct cleaned processes; historical generic evidence remains blocked/stale.

PR103 final head: `7706ad6ed3c3217a32efa3b7b6f7371fcabc9c58`. Its catalog explicitly declares the fresh bridge. The integration owner's exact six-file commit `6ea92728e1e7fa94f7bf92a898a24c60a63168f9` is applied to both draft branches, without importing project-store/schema/app product changes. It preserves prior floors and the original five owner test bodies/21 assertions; node 294→374 and model-update Python 22 are actual added tests. PR103 normal full non-browser strict exits 0: 62 suites, 1875 counted, 1874 passed, zero failed, one named Windows-GDI exemption, no registry blocker. Its unchanged diagnostic baseline uses a disclosed 16 MiB stack. All six true CLI cases were rerun at this exact head and passed with 35 assertions, six distinct cleaned processes and unchanged negative World/revision/dump (`/tmp/diagnostic-shared-registry-six-cli-summary.json`).

The [required integration gate registry](../tests/INTEGRATION-GATES.md) preserves five formal #77 owner tests as a separate required entry. With no implemented adapter, actual output is exit 3, pending_implementation, required 5/executed 0/passed 0; a configured invalid adapter actually fails exit 1. Neither is a pass or environment skip. Four real browser entries remain required and unexecuted here. Complete non-browser strict does not certify these product integrations.

Native owns World, native serializer and web_bridge changes. Integration owner `01a100b5-800b-75f2-9a02-71ee53e550ba` owns project-store/schema/capability/app/ContextHistory: save the native dump plus actual capabilities, infer new syntax even if manifests are stripped, retain raw unsubmitted draft separately, and group confirmation/attachments in one context transaction. Native assigns no project format number. Cancel reserves no formal key; undo restores the complete prior context, including key/highwater. No cross-project or abandoned-branch permanent identity guarantee is added.

A native scene roundtrip does not certify a full `.gcanvas` draft flow. #61 UI, physical Windows/iOS acceptance, #44/#77 product integration and #54 automation remain separate owners' scope. This slice adds no nested subdivision, arbitrary region, per-face override or automatic component generation. Handoff is a draft PR; no merge/deployment was performed.

## Retained execution artifacts

Cloud logs remain under `/tmp`: `subdivision-repeat-only-baseline139-valid.log`, `subdivision-oracle-40-fresh.log`, `subdivision-new-tests-old-control.log`, `subdivision-repeat-only-recorded-floor-census.log`, `subdivision-repeat-only-final-strict.log`, `subdivision-repeat-only-sanitizers-valid.log`, `subdivision-repeat-only-mutation-check.log`, the three `subdivision-repeat-only-mutations-{a,b,c}.json/.log` outputs, `subdivision-repeat-only-mutations-c-independent-audit.log`, and `subdivision-repeat-only-review-microchecks.log`. Tracked mutation receipts retain per-executable provenance; hashes below identify the final complete logs.

| Artifact | SHA-256 |
| --- | --- |
| `/tmp/subdivision-repeat-only-recorded-floor-census.log` | `d549c12bbf5cd61761f52d2cf00ecdfcec2b7e70293ec0aa8ed794a47599b1cf` |
| `/tmp/subdivision-repeat-only-final-strict.log` | `f16440bb67c11518cc5e84de084e52ecdedd7736a7c206f71ade565be14f0f72` |
| `/tmp/subdivision-repeat-only-sanitizers-valid.log` | `00766856e9148ff432cf7826e4b9958f29c48d30f1cd9b7aad3a38b54bf0c430` |
| `/tmp/subdivision-repeat-only-mutation-check.log` | `6923de5f59e78393c16847136953df8b2014871ce64d0aa59b50b7e7924b3212` |
| `/tmp/subdivision-repeat-only-independent-review.md` | `bc861f16c68f0c56b29f54c4d128375304ca7449482eb30ca348ea064afcd069` |
| `/tmp/subdivision-repeat-only-mutations-c-independent-audit.log` | `19feb42bbc81ae83383c410ed28d17020f1011dfcdff3d502d806f816cfeba86` |
| `/tmp/subdivision-oracle-40-fresh.log` | `0d284160c38b33cf9392acb64f39cb96202b3a832fe9e8a4343fef817c51feae` |
| `/tmp/subdivision-new-tests-old-control.log` | `3f5d917b30b2d353ae2023f86ec19d17e7efd393477f41682215256622b9e3c9` |
| `/tmp/diagnostic-shared-registry-final-strict.log` | `7766e32634d9683b8234baac9e98a773883dd005a0e350785a72dedf274bbab7` |
| `/tmp/diagnostic-shared-registry-six-cli-summary.json` | `e9def73c1d2b825b52da24f6c7081d3cc917e8d77039ac74287d258ea39a5183` |
