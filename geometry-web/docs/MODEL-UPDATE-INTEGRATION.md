# #44 F1b ordinary single-plan integration contract

User accepted item 3 of the eight decisions: explicitly select current sources,
review an isolated candidate, replace the same model's complete record with one
undo. This supersedes Q32's earlier pending status only for that finite scope.
No durable incarnation ledger, new axiom, automatic update or version upgrade is
introduced. F1a is already delivered and is not repeated here.

## Ownership

Implementation branch: `feat/issue-44-f1b-controlled-update-20261004`, initially
based on main `1c83b5e76cb0226bfd9c6c92289c8ab0760413e4`.
Rebased onto main `1075058be37d37b98a2a910f4f67b87583be85b3` after the existing
#85 owner's merge; this branch makes no changes to that work.
Then incorporated main `8d08f1aceda7f26b6f05c64010f4b47a41df9c31` (#24's
tests/evidence-only merge), rerunning its strengthened 35-test assembly suite.

This branch owns new files only: `model_update.py`, `model-update.js`,
`model-update-app.js`, `model-update.css`, their dedicated acceptance tests and
this handoff. Shared format/schema/project-store/ContextHistory and
`reference-workspace.js` remain exclusively owned by integration thread
`01a100b5-800b-75f2-9a02-71ee53e550ba`. No #45/#77/#54/#85 work is included.
The companion `MODEL-UPDATE-INTEGRATION.patch` is reviewable wiring for that
owner; it is not applied to shared files on this producer branch.

## Producer boundary

`model_update.prepare_update(data, *, base_executable=None,
bridge_executable=None, max_cells=200000)` accepts exactly:

```text
{record: completeSavedModel, current_scene: completeCurrentDump,
 selection: {placement_id, boundary_id, edges, obstacles, timbers, projection}}
```

Every selection field is required. Placement IDs may be zero. Edge indexes are
explicit picks on the new outline, never a mapping inferred from old indexes.
Timbers and obstacles are typed, explicitly selected lists including empty
lists. Projection is the selected source's existing typed projection or null.
Models containing timbers require a positive, matching named boundary under
the existing strict saved-model schema. Embedded rectangles (`boundary_id:0`)
remain selectable only without timbers; the UI explains that limit and exposes
no timber choices. Both invalid old timber metadata (`null`/`0`) and current
embedded-rectangle timber selection fail with `UPDATE_TIMBER_BOUNDARY` before
candidate creation. No shared schema is relaxed.
The original height, bottom, floor/ceiling/holes purpose and thickness are
preserved; only the explicit new source references and edges change.

The old result must replay exactly with the actual native adapter. The whole
current source is parsed in fresh native processes. The producer reuses
`space_modeling.preview` and its package verification, with no second geometry
solver. Typed fixed material/method/rule tuples and fingerprints in the selected
closure, including inactive overridden definitions, must match. A changed
fixed-version closure fails with `UPDATE_FIXED_VERSION`. Unrelated versions do
not affect the selected closure. The guard also compares fixed fields and
explicit root associations, preventing A/B or two-root version swaps with an
unchanged global set. Endpoint support comes only from the existing native
exact support projection. Unknown support or a different protected root
without explicit correspondence is unsupported. Faces, assembly-owned/assembly-capability
sources, unknown capabilities, incomplete graphs, missing binaries and failed
native execution remain unsupported.

The receipt is transient `geometry-model-update-candidate/1`:

```text
{ok:true, schema, identity:'unknown', old_record_sha256,
 current_scene_sha256, selection, record:completeReplacement, diff,
 runtime:{base_binary_sha256,bridge_binary_sha256,producer_sha256,axiom_sha256}}
diff = {source,input,settings,summary: {before,after},
 packages:[{kind,before,after} /* exactly space/volume/clearance/walls/timbers */]}
```

Each package pin is SHA-256 of canonical JSON of its whole manifest, or null
when absent. Raw current source bytes, canonical full record, native graph node
fingerprints, package source/geometry hashes and actual binary hashes have
separate domains. The receipt never enters the saved strict record.

### Mapping to the shared-owner draft

Compared directly with PR100's
`geometry-guide/IMPLEMENTATION-QUEUE-20261004.md` at
`0230e436870ec3ba06fcb0735ffabc3b7427979d`; that draft is not treated as main.
The shared owner's accepted candidate envelope maps without a schema change:

```text
modelId           = receipt.record.id
previousSignature = receipt.old_record_sha256
record            = receipt.record
diff              = receipt.diff
sourcePins        = {current_scene_sha256: receipt.current_scene_sha256,
                     runtime: receipt.runtime}
```

`previousSignature` is SHA-256 of canonical JSON of the entire previous strict
record, not the source scene hash or the model ID. The controller independently
checks that hash and also compares the complete current record with its captured
canonical value. Native revision, context/frame identity, history entry references,
project revision and cancellation generation remain transient host/controller
guards; they do not become model fields or feature attachments. The integration
owner supplies those host callbacks and the synchronous replacement callback.
This #44 slice needs neither `manifest.featureAttachments` nor its new format.

## Controller and atomic commit

`ModelUpdate.create(host)` needs `getState`, `getRecord`, `readSource`, `produce`,
`validateRecord`, `sha` and synchronous `commit` callbacks.

`getState()` returns actual context/frame objects, contextToken, project revision,
undo/redo top-entry references, history group and blocked boolean. Blocked must
cover project editing lease, scene load, active UI/native mutations and
disconnection. `readSource({signal})` atomically brackets the native revision and
dump and returns exactly `{scene,revision}`. `produce(data,{signal})` calls the
isolated producer. `commit(id,record)` calls the existing
`ReferenceWorkspace.updateSpaceModel` synchronously.

Flow: `begin(modelId)` → `prepare(explicitSelection)` → `getReview()` → explicit
`confirm(reviewId)`. `cancel()` aborts and invalidates all late replies. The
review contains complete before/after records and all diff domains. Confirm
rechecks the complete record/context/history guards, reads current source,
reruns the true producer, compares the entire receipt/runtime, reads source
again, and commits synchronously without an intervening await. Duplicate
confirm, cancel, failures, stale context/source, model deletion and same-ID
record replacement perform zero writes. Existing updateSpaceModel performs one
complete replacement and one ContextHistory local undo.

Existing pack/unpack and import's true producer replay provide saved-model
verification on reopen; no new project format or persistent receipt is needed.
The UI never guesses identity continuity; even identical content stays unknown
and requires explicit selection.

## UI wiring and verification

The new adapter exports `ModelUpdateApp.open(modelId)` and `close()`; its source
picker starts blank. The wiring patch uses the existing model-edit action for
height editing or current-source updating, preserving one top-level edit
action. Its height editor summary and separate help paragraph become one
paragraph. The patch records this reduction in BACKLOG for the integration
owner. No new permanent global help area is added.

The browser harness distinguishes direct module acceptance (injects missing
modules and opens directly) from `GEOMETRY_MODEL_UPDATE_ENTRY=owner` acceptance
(requires real index wiring, never injects, and enters every update via the
existing model edit action and `smCurrentSourceUpdate`). Direct module scope
alone does not prove the owner entry. The owner patch registers 22 Python
tests and 39 controller tests, so the combined existing Node registry count is
333. Additional review cases cover actual nonempty column/beam selections,
true-native confirmation hash-await races and strict-store rectangle limits.
The support-unknown negative case is explicitly a compiled test-local C read
projection fault: real placed timber, real native parser/endpoint function and
true producer rejection; it is not claimed to be a naturally legal ambiguous
placement. No live World, stored record or history is changed.

Dedicated tests are directly runnable before registry integration:

```sh
GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge python3 -m unittest tests.test_model_update
GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge node --test tests/test_model_update.js
```

The final evidence packet records actual commands, counts, exit codes and
remaining limits. Production integration requires the shared owner to apply
the wiring patch. This draft does not merge, deploy, close #44 or claim the
whole proposal delivered. Physical phone/OS file picker acceptance is separate.
