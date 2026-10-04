# #77 formal owner checkpoint — unfinished

This draft preserves the shared owner's work after the cloud execution
environment disconnected at 2026-10-04 09:13 UTC. It is not a merge-ready or
completed #77 implementation. Root owns merge and further contract decisions.

Base: PR113 `b72044d0ca6705086c24bb583fa6a30de751de3c` (tree
`3d7053c2193a8d7b0ab55e2dd08c2612d9a69cc1`); current main is
`f1b9f9df905b5e7d3f60077d6d2c005c01154a36`. Once root merges PR113, review
the remaining #77 diff against the resulting main. Do not reset main to this
branch or discard PR106/110 registry entries.

## Work preserved

- Existing v10 envelope gains the finite `source-rooms` kind with the existing
  `source-rooms/1` payload and frontend `source-room-collection/1` capability.
  One grid record and one room record maximum; duplicate/unknown kinds reject.
  Grid retains its original 128KB/128-array/4096-node limits, including the
  single-grid envelope overhead. Room traversal separately bounds 8MB,
  10000-array/600000-node/depth12, while the room validator retains its existing
  256 planes/collections and 10000 rooms limits. This is a finite dispatch,
  not a dynamic registry or native capability extension.
- Actual ProjectStore pack/unpack validates room source metadata closure and
  frontend capability; candidate object validation requires detached native
  boundary fingerprints before publication. `boundaryFingerprints` is the
  requested interface name, still awaiting the sole native writer's contract.
- Actual ContextHistory snapshots legacy groups and attachment values; tracked
  native delete retires room association, same-ID recreation cannot revive it,
  unknown history marks associations unknown and preserves referenced PDF
  runtime/bytes. No second polygon or durable incarnation ledger.
- ReferenceWorkspace owns a frozen opaque room transaction lease with
  context/frame/session/editor/confirmation guards. Grouped metadata writes
  require the exact owned dirty native group and do not add a second undo.
  Ordinary attachment writes retain local history and context checks.
- `getRoomIntegration()` maps existing module callbacks. Explicit legacy
  adoption revalidates the native pin and source/page/stamp, snapshots before
  the final synchronous write, removes only the chosen legacy basis page and
  preserves other pages. Selected pages with records or reconstruction receipts
  currently reject before changing data because the existing room schema has no
  lossless home for them; this is a real remaining requirement.
- SourcePlane is loaded before FeatureAttachments; existing room modules are
  loaded/configured. Only the reviewed app.js portion of the handoff UI patch
  passed apply-check and was applied. The old index/ReferenceWorkspace patch
  was not blindly pasted. ReferenceWorkspace still needs its remaining UI
  routing/guards, listed below.

## Actual validation and interruption

After the environment restarted, fresh shell commands succeeded; all changed
JavaScript passed syntax checks and `git diff --check`. The actual existing
`node --test tests/test_project_store.js` ran 10/10, zero skip, exit0 again.
These are working-tree checkpoint checks, not formal #77 acceptance.

PR113 same-head terminal results received before the disconnect were owner
browser28, space183, timber79, strict66 suites2042 pass/0 fail/1 named Windows
GDI, all exit0. Their exact hashes are preserved in PR113's body/comments.
PR113 full CDP had reached P79 but no terminal/exit result was received:
**full CDP remains pending** and must be rerun in a fresh isolated service.
Its old service18987 now refuses connections; the previous `/tmp` evidence,
binaries, review packets and Chrome profiles disappeared. Workspace/git/frozen
heads survive. Never relabel the interrupted CDP as success.

## Required continuation

1. Finish/verify ReferenceWorkspace shared basis routing (calibration/changed),
   page-add/remove/select/import guards and summary lookup. Review the app
   recovery handler's room-lease abort/settlement against existing grid and
   assembly guards. Prevent zero-point room intent from disappearing through
   project switching, and provide the existing source overview/reassociation
   path after all rooms unlink or retire. Do not create placeholder boundaries.
2. Root must coordinate native candidate summaries before import publication.
   Do not query live boundaries for an unpublished candidate or confirm first.
3. Decide the minimal lossless selected-page records/receipt migration contract.
   Proposed finite plane records reuse existing id/label/location/datum/unit/
   value validation and contain no old basis shadow; no new schema or axioms
   have been implemented here. Until a reviewed contract exists, refusal is
   mandatory and this requirement remains incomplete.
4. Fix the newly reproduced create-only ID race in RoomCollection.Controller:
   after readBoundary reports absent, another native writer may occupy the ID
   before preview. Require this owned candidate's matching boundary row to
   have `before === null`; cancel the owned token and reject otherwise. Preserve
   edit's existing same-pin guard. Baseline b720 true-native TEMP probe actually
   overwrote geometry and failed the independent prohibition assertion (exit1),
   with the bridge itself exiting0. See the frontend review handoff; it is not
   a browser or formal owner pass. This fix is still pending in this checkpoint.
5. Supply the test-only adapter that delegates exclusively to actual owner
   code, then run all five required gates in
   `tests/integration/issue77_attachment_owner.js`, all four real browser gates,
   selected legacy records/receipt preservation, receipt loss recovery,
   same-ID/unknown history, native candidate pins and fresh-context true ZIP.
   Missing owner gates remain exit3/pending, never skip/pass. Run relevant
   space/timber and full strict/CDP on the final fixed head, then root review.

No native source, SSOT, deployment, paid service, safety policy or private
drawing changed. User service8765 was never used.
