# SR16 / SR23 browser probe — prepared, not executed

`sr16_sr23_browser.py` is private acceptance tooling. The sole browser owner must execute it against the already isolated, receipt-backed service. This preparation does not establish a product pass. Source review must finish before execution.

## Bounded sequence

At 1400 px, then 390 px, create a new project through File/New. Only boundary geometry, placements, and physical support timbers are seeded through the API. All source, rule, binding, applied-grid, derived guide and direct rule-line timber creation uses normal existing controls, click/keyboard input, and actual completion state.

Create source U=600,V=400, `main-along none`, rule divisions 3,2. Create face 1 binding and its guide/direct timber **before** creating face 2 binding and its references. All references therefore precede the source edit, closing the ordering gap in historical P88. IDs allocated by normal UI are read from native responses and recorded; t3/t23 or grid 10/20 are not presumed.

SR16 edits U to 300, inspects the actual native preview and rendered impact dialog, requires both bindings and only the second physical secondary timber in violations, and requires disabled Confirm. Preview and Cancel must preserve full raw dump/objects/references/assembly-read, including revision, and exact history entry/frame identities.

SR23 edits U=900,V=600 together so both the u0 coordinate guide and v0 direct physical member change. It previews, cancels, previews and confirms, checks one history transaction, exact source-only serialized edit, both faces and all native references, then performs normal Undo/Redo. Formal Save must preserve the complete World/project and produce an independently predicted complete manifest. New must really empty all data. A new Chromium process/profile then opens the saved `.gcanvas` through the formal chooser and proves full restoration; one normal Undo must return to the captured fresh empty context, and Redo must restore the complete reopened World/project.

No API source/rule/binding/reference creation, force click, arbitrary sleep, unlimited retry, internal save/load/history call, browser policy change or full-CDP claim is used. Download fallback is explicit; physical phone, IME and OS-native save-picker behavior remain outside this probe.

## Oracle fixed before execution

Both boundary outlines are (100,200)–(2100,1800). Each binding anchors cell (-2,1), fraction (0,0), to outer vertex 0 at (100,200). Both have boundary supports on e0/e2. Primary supports are x=120/380 on face 1 and x=120/680 on face 2, A=B=20. Direct secondary members lie on rule v0, +u, between the respective physical supports: their spans are [130,370] and [130,670], lengths 240 and 540.

| Value | Before | Valid candidate |
|---|---|---|
| U,V | 600,400 | 900,600 |
| binding translation | 1300,-200 | 1900,-400 |
| exact cell bounds | 100,200,700,600 | 100,200,1000,800 |
| child u coordinates | 300,500 | 400,700 |
| child v coordinate / direct centerline | 400 | 500 |
| guide u0 offset | 300 | 400 |
| coordinate guide visible v extent | 200..1800 | 200..1800 |

U=300 makes cell bounds [100,200,400,600]; only span [130,670] exceeds its cell. A formal guide has coordinate semantics and is clipped against the full face, not the parent cell. Rule query segments themselves are clipped to the parent cell. Segment endpoint order is normalized only for geometric comparison; untouched responses remain in evidence.

## Source basis

- `公理層.md` D19a, D30, I13/R6: shared source identity, exact child geometry, retained cell scope and physical support.
- `tests/test_grid_subdivision_oracle.py:597–639,680–705`: physical support construction, coordinate-only guide versus direct scope, exact SR16 only-second-timber rejection fixture.
- `geometry-web/grid_rule_lines_test.js:6–51,98–111`: actual UI controls, finite select keyboard operation, creating formal references and saving. Its older source edit at 86–90 precedes references, so it does not establish this combination.
- `geometry-web/grid-system-workspace.js:866–875,897–915`: exact source command and actual preview request `line preview grid-system ...`, context-bound confirmation. A preview may legitimately have outer `ok:false`; the fixture helper inspects preview before requiring final `ok:true`.
- `current_geometry.c:1109–1154`: coordinate guide clipping uses boundary outline; the hand oracle therefore expects the full vertical face span.
- `geometry-web/app.js:9833–9883`: native Undo/Redo response, render completion and final success text. Probe waits actual final success text and busy state.
- `geometry-web/project-store.js:139–183,292–308,488–500,624–658`: native subdivision capability implies format /11; a retained raw grid draft schema /2 takes precedence as /13. Before Save, the probe predicts complete archive manifest from preexisting metadata and these narrow supported capabilities, including scene SHA, preserving all existing metadata. Unknown attachment kinds are not silently normalized away. Archive output never chooses the expected format.
- `geometry-web/reference-workspace.js:1233–1237,1257–1274`: in-memory manifest omits archive sceneHash and can omit native-derived version/capabilities; direct equality against this unwrapped manifest would be an invalid test.
- Earlier independently reviewed `ci-source-audit/save-reopen-gate-review/compound_project_probe.py`: isolated service identity, sandboxed fresh profile, real New/Save/Open, complete World/project comparison and owned cleanup pattern.

## Execution and evidence

Parent chooses a fresh `--out` directory; existing evidence is never overwritten. The intended command uses the current reviewed **full** SHA, explicit isolated loopback URL, exact native binaries and installed browser. `preparation.json` records this preparation's source hashes and read-only git command evidence. Before/after runtime binding and `/proc` executable hashes are captured by the executed script, including failure exits where preflight succeeded. The parent driver must separately retain stdout/stderr and actual process exit code. Per-width results, full raw native/API responses, scene files, trusted-input event log, manifest/archive, screenshots and traces are private until reviewed for publication.

Successful World Undo/Redo/reopen comparison excludes only top-level transaction revision in dump and assembly-read. All other fields are compared; cancellation excludes nothing. Full snapshots remain unmodified beside comparisons. First failure stops the width/run and retains its phase and raw evidence; preparation defects must be distinguished from product failures before any retry.
