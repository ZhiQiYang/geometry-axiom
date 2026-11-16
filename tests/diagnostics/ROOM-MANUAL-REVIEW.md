# R22 manual correction diagnostic

This adds component/native evidence for issue #54's **existing outer-ring
replacement**. It does not change the product or extend the separate new-room
draft contract. The starting point is main
`fd96b8bf7094bd57e74e3226aeba1f24a73b74fc`, including #405's earlier browser walk.
That walk confirmed an extracted rectangle without entering dimensions or
editing vertices; it remains historical browser evidence.

## Run

Use a clean checkout, the existing Python/Node dependencies and the normal
native registry. The launcher uses `start_local.ensure_stack()` (16 MiB) and
`binaries.require_fresh()`. It does not start a service or a browser.

```sh
python3 geometry-web/start_local.py --build-only --binary-dir /tmp/r22-native
python3 tests/diagnostics/run_room_manual_review.py --bridge /tmp/r22-native/bridge --out /tmp/r22-review-baseline
node --test tests/test_room_outline.js tests/test_room_outline_closeout.js tests/test_room_outline_worker.js
```

Every output directory must be new. A failure writes its receipt and exits 1;
the script never replaces a previous result. `result.json` records UTC, HEAD,
file hashes, binary build receipt, every assertion and each native child exit.
`native-transcript.json` contains commands and unedited bridge replies. Six real
`.gcanvas` ZIPs and their scene files are produced on a complete successful run.
The Python launch command and shell exit should also be retained by the caller.

## What executes

The production room extractor, worker message handler, workspace's actual bound
input handlers, `ReferenceWorkspace`, `ContextHistory`, archive writer/reader,
and the source-verified native bridge execute. The six paths are PDF-like
operator-list input and image pixels, each for rectangle, L and notch fixtures.

After acquisition, each path checks fractional dimension rejection, explicit
edge input, review invalidation, retirement of old dimension markers, all edge
lengths in order, native rejection of a self-crossing ring, candidate cancellation
and impact-preview cancellation. A final explicit vertex correction inserts a
notch, extends an L leg or deepens a notch; **the saved geometry differs from the
extracted geometry**. Every final edge is entered and reviewed. Confirmation,
undo/redo and archive replay compare entire native scene text, ordered vertices,
the retained hole/fixity, source bytes, calibration and the source-bound review.
The cold native bridge is a new process checked blank before replay. Recalibration
invalidates review without scaling the formal geometry.

## Boundaries

This is **not App/browser acceptance**. It uses small DOM event doubles and the
existing `reference_workspace_vm.cjs` fixture. The PDF operator-list provider and
canvas decoder are substituted; PDF parsing/rendering, a real Web Worker, focus,
pointer/keyboard routing, `app.js`, impact dialogs and the Save/Open UI are not
executed. The test adapter explicitly drives native preview/confirm and passes
the native replies to the real history observer. `ReferenceWorkspace.exportBytes`
blocks live candidates and creates the archive; cold replay uses the archive
reader and a new native bridge, not a fresh App tab.

The original synthetic PDF generator supplies portable source bytes, and the
image case generates its own PNG. No private drawing is opened. These results
do not upgrade R22's unverified manual-correction browser slice to L4, nor prove
physical phone/IME/OS-picker behavior or human operation time.

## Named assertion-sensitivity checks

The optional mutations alter exactly one matched production-source anchor **in
VM memory**. They never edit a product file, the original assertions, a golden,
or the repository mutation ledger. Both commands must exit 1 at the named gate:

```sh
python3 tests/diagnostics/run_room_manual_review.py --bridge /tmp/r22-native/bridge --out /tmp/r22-review-no-reset --mutation keep-reviewed-after-edit
python3 tests/diagnostics/run_room_manual_review.py --bridge /tmp/r22-native/bridge --out /tmp/r22-review-unapplied --mutation allow-unapplied-row
```

Expected failures are `applying vertices clears acknowledgement` and
`unapplied invalid row cannot be reviewed`. A mutation that fails to match its
single anchor is an invalid check, not a detected defect. `effectiveWorkspaceSha256`
distinguishes the in-memory mutation from the unchanged on-disk source. Run the
unmodified command again after these checks to establish restoration.

The remaining App evidence requires an environment with an approved functioning
browser sandbox: repeat the same actual edits, edge entry, review, impact
cancel/confirm, Save, blank App Open and source/projection continuation through
the formal UI. Keep the existing browser assertions and baselines unchanged.
