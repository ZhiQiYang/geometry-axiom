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

## Saved-cloud continuation stage 1 (2026-10-04)

The new sole writer recovered the exact PR114 head/tree from origin into
`/workspace/geometry-axiom`; the initial checkout was clean. Remote main remains
`f1b9f9d`, PR113 remains `b72044d`. No existing uncommitted work was replaced.
The prior native repro directory was absent; independently reproduced evidence
is stored at `/workspace/handoffs/geometry-axiom-20261004/77-native-repro-new/`.
Frozen `4cad268` different-geometry and identical-geometry occupancy baselines
both fail prohibition assertions (exit1; bridge exit0). The fixed controller
requires exactly one matching candidate boundary row, `before === null` and
matching `after.id`, otherwise cancels its owned token. Six fresh-native probes
pass, including missing/duplicate/wrong-after candidate rows. This is targeted
native/controller evidence, not product completion.

Owner responsibility fixes now route public shared calibration/alignment through
the canonical attachment, guard legacy page add/remove/select/import, render
shared summaries without a legacy group, reject project/source switching during
zero-point room intent, and validate shared source closure before metadata writes.
Import checks the actual PDF/image page dimensions before native publication.
Current-group rollback restores data in the same frame, allowing the owned lease
to finish; undo/redo still create fresh frames. A transient bounded native preview
summary stores only token/frame/session and changed boundary IDs/retirement flags;
confirmed affected boundaries become review/retired, unknown confirmation retires
associations. Automatic native impact previews may report `ok:false` with a valid
candidate; they still remain uncommitted. No native geometry is copied into it.

Receipt recovery now adopts the exact owned recovered preview token and cancels
it before clearing the draft/releasing its lease; only valid owned cancellation
with no pending receipts is allowed during connection loading. A real browser
preview-loss case was added to the four previous recovery scenarios.

Working-tree focused checks reached 54 pass/0 fail/0 skip. Formal owner gates
first run reached 5/5 (the history gate explicitly uses actual ContextHistory
with synthetic observed receipts; workspace gate uses actual native/browser).
The first no-injection room browser run passed 29 checks, then correctly failed
fresh-context ZIP publication because the native candidate fingerprint interface
is still missing. Logs, exact hashes and scope are in
`/workspace/handoffs/geometry-axiom-20261004/77-formal/`.
These are intermediate trees; final frozen-head reruns remain required.

Still blocked/incomplete: root-coordinated detached candidate fingerprints,
root-reviewed lossless selected-page records/receipt migration, and the shared
source overview/reassociation path after all rooms unlink/retire. The new writer
requested the first two decisions and does not alter native World/bridge or the
payload schema without that coordination. Draft PR114 stays non-merge-ready;
Refs #77, no merge/deploy or #54 work.

## Saved-cloud continuation stage 2 (2026-10-04)

Remote main is now `b972dafbc0b9838ecab13032bbd4ed3b71b63609` after
root merged PR113. Its tree matches the inherited PR113 `b72044d` tree;
the #44 model entry, immutable snapshots and HTTP update-preview are preserved.

The existing project-information popover now exposes shared source collections
even after every room unlinks or retires. Explicit native-boundary association
uses the actual full native pin, preserves stable room identity on reassociation,
and records metadata-only undo. New-room choice uses the empty value outside the
persisted room-ID domain, so a valid imported ID `new` remains independent.
390px controls were rendered and inspected. The real browser removal/overview
gate reached 46 checks, including cold-source late navigation rejection and
one-undo preservation. No placeholder native geometry or new toolbar was added.

Known pre-delivery rejection can leave a native history group or owned candidate
unsettled. The owner now exposes the existing connection recovery and retains
its lease until native rollback/cancellation succeeds. True native history-abort
of an untouched group does not retire the candidate: recovery explicitly cancels
the still-owned candidate before releasing ownership. A central owned-candidate
cancel path handles both ordinary cancel and recovery. The real browser recovery
gate reached 111 checks across five executed-reply losses and real HTTP409 stale
confirm/abort/cancel rejections; old preview tokens cannot apply after recovery.
No pending receipt is invented for a known rejection. Expired service-session
receipts remain blocked and require reopening a saved project; no synthetic
receipt or new-session adoption is permitted.

Stage1 `4076c568` full CDP genuinely failed P69 timber navigation; the isolated
same harness passes on PR113. The shared source await had preceded synchronous
focus identity publication. It now runs after that identity and checks existing
focus/context guards before native reads. Room navigation delegates to that one
preparation path and rejects late continuation before starting an old edit.
Stage1 default-space also failed during source loading; baseline PR113 passes,
but a dialog-open readiness race is not yet excluded. These failures remain
durable evidence, never relabelled as success; stage2 exact-head reruns are needed.

Shared #44 scenario receipt decoding now accepts only the optional complete
`boundaryFingerprints` summary, validating exact fields, typed IDs, uniqueness,
membership and lowercase 64-hex hashes. Existing receipts remain valid; unknown
fields and incomplete summaries still reject. Native output is still missing:
no native writer is assigned, and no native file has been changed here.

A complete non-browser census ran with `--build --update-expected` and exit0.
The only expected-count changes are the added genuine regressions in
`node:tests-js` and `py:test_scenario_verify`; original JSON ordering is preserved.
This is an intermediate-tree census, not the final frozen-head gate.

Required root response is explicit, not just a PR-body note:
1. Assign the sole native owner for candidate hashes from `g_load_after`, using
   existing `boundary_geometry_hash`; no World capacity or axiom change. Minimum
   true-native repro/interface packet lives at
   `/workspace/handoffs/geometry-axiom-20261004/77-native-candidate-contract/README.md`.
2. Decide the finite legacy historical-evidence storage contract. Recommended:
   selected-page records belong to the unique source plane; the original receipt
   belongs to the selected room as read-only history, with existing validation
   and limits. Its old basis/geometry are evidence only, never a second editable
   basis or automatic acceptance of a later shared basis. No such payload fields
   have been added. Selected records/receipt still refuse adoption without loss.

Independent review fixed concrete ID-sentinel, late-navigation and candidate
settlement findings. Latest scoped review proofs are under
`/workspace/handoffs/geometry-axiom-20261004/77-review/`; formal/frozen-head
acceptance remains separate. Full fresh-context room ZIP reopen is still blocked
by missing native candidate pins. This draft remains unfinished and non-merge-ready.
