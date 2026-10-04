# #44 F1b ordinary single-plan integration contract

User accepted item 3 of the eight decisions: explicitly select current sources,
review an isolated candidate, replace the same model's complete record with one
undo. This supersedes Q32's earlier pending status only for that finite scope.
No durable incarnation ledger, new axiom, automatic update or version upgrade is
introduced. F1a is already delivered and is not repeated here.

## Ownership

Implementation branch: `feat/issue-44-f1b-controlled-update-20261004`, initially
based on main `1c83b5e76cb0226bfd9c6c92289c8ab0760413e4`.

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
The original height, bottom, floor/ceiling/holes purpose and thickness are
preserved; only the explicit new source references and edges change.

The old result must replay exactly with the actual native adapter. The whole
current source is parsed in fresh native processes. The producer reuses
`space_modeling.preview` and its package verification, with no second geometry
solver. Typed fixed material/method/rule tuples and fingerprints in the selected
closure, including inactive overridden definitions, must match. A changed
fixed-version closure fails with `UPDATE_FIXED_VERSION`. Unrelated versions do
not affect the selected closure. Faces, assembly-owned/assembly-capability
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
picker starts blank. The wiring patch merges the existing model-edit action
into one chooser for height editing or current-source updating, preserving one
top-level edit action. Integration owner should record this reduction in the
existing BACKLOG #44 entry while adopting the patch. No new permanent global
help area is added.

Dedicated tests are directly runnable before registry integration:

```sh
GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge python3 -m unittest tests.test_model_update
GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge node --test tests/test_model_update.js
```

The final evidence packet records actual commands, counts, exit codes and
remaining limits. Production integration requires the shared owner to apply
the wiring patch. This draft does not merge, deploy, close #44 or claim the
whole proposal delivered. Physical phone/OS file picker acceptance is separate.
