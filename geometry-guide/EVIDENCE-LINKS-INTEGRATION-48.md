# #48 EvidenceLink independent slice / shared-owner handoff

Based on main `067cbdc` (PR100 adopted scope, then PR101/105). This slice supplies independent modules and tests. It does **not** register an attachment kind, allocate a project format, modify native World, or edit `project-store.js`, `reference-workspace.js`, `ContextHistory`, `app.js`, `index.html`, or #77's module. Shared reader/save integration belongs to the `01a100b5…` owner. No private PDF fixture is included.

## Candidate registration (coordinate with the shared owner)

- Candidate kind: `evidence-links`; feature schema: `geometry-evidence-links/1`.
- `EvidenceLinks.validate(value)` throws on unsupported schema, extra fields, invalid typed refs, malformed page/region/hash, executable/exotic data, duplicates, or bounds; returns `true` on success.
- Bounds: 256 links, 2 MiB encoded JSON; manual raw text/note 2000 characters, raw value 256 characters. This is an engineering bound, not a new geometry rule.
- `EvidenceLinks.references(value)` returns `{sources: sourceHashes[], targets: [{kind:'parameter-field',projectScope,parameterId,fieldId}]}`. Repeated evidence for one field remains independent. Formal model values are never saved inside the annotation.
- Attachment read/write injection uses `readFeatureAttachment(kind)` and `setFeatureAttachment(kind,value,expectedContextToken)` only. Shared owner must register validator/schema/capability and the current project format; this worker has not claimed `/10` or any other format number. Unknown kind/schema/capability must reject before live state replacement.
- The attachment setter is a **synchronous local history commit**. It must finish validation, token/history/busy checks and the entire mutation in one JavaScript turn. It cannot be an async function or return a Promise/thenable; remote save acknowledgments use the separate archive owner. The controller rejects async setters and has no await between its final guard and this local mutation.

## Source closure and coordinates

`documentFromReference(p)` snapshots only existing reference identity, source hash, page, scale-1 full-page dimensions, crop and rotation markers. PDF coordinates are the existing `page.getViewport({scale:1})` top-left, Y-down coordinates, **including intrinsic PDF rotation**. `rotationBasis` records the additional existing underlay `p.rot` at selection; it does not cause a second rotation. `cropBasis` is a marker, not a new coordinate origin. Region is `[x,y,width,height]` in the full page. There is no second calibration: `mmPerPx`, `x`, `y`, calibration points and world geometry stay exclusively in the reference owner. Rendering scale, zoom, DPR, crop and subsequent underlay rotations do not rewrite the evidence rectangle.

Pass the existing `feUlMmToImg` / `feUlImgToMm` as `canvas.toPage` / `canvas.fromPage`. Existing `fePoint(event)` supplies face millimetres. An evidence selection intercepts existing canvas input only during its explicit selection operation; cancellation removes its overlay and permits ordinary canvas input again. It never invokes OCR, source extraction, native preview, or a geometry confirm.

Complete project export must union `references(value).sources` into the original-source closure. Currently `ReferenceWorkspace.manifest()` collects sources from face pages only; evidence-only sources would otherwise fall out after removal of a reference page/boundary. Keep exact original bytes keyed by SHA256, never rendered PNG, blob/cache URL, filename, or filesystem search. `validateSourceClosure(value,{readSource,hashBytes,readPage})` checks source metadata/type/byte length/hash, page existence and original viewport dimensions before the shared owner commits a prepared project. It snapshots the candidate and source bytes for asynchronous validation, and rejects candidate edits during validation. The shared owner must atomically commit the same immutable prepared attachment/source snapshot that was validated; a boolean validation result is not a lease for a subsequently modified candidate. `readSource(hash)` returns `{meta:{id,hash,type,size},bytes:Uint8Array}`; `readPage(source,page)` returns `{width,height}` from the existing PDF API. Target refs must be checked against the prepared final native state. A matching field fingerprint is content evidence, not an incarnation proof.

## Controller injection and identity

```text
EvidenceLinks.createController({
  readFeatureAttachment, setFeatureAttachment,
  getStamp, readCurrent, locateDocument, uuid?, now?
})

getStamp() -> {projectScope,contextToken,revision,nativeRevision,...history stamp?}
readCurrent(document,target) -> {document: currentDescriptor|null,
  target: currentTypedTarget|null, modelValue: {num,den,unit}|null,nativeRevision}
locateDocument(document,region,{isCurrent}) -> existing reference navigation
```

`getStamp()` must return a deterministic plain snapshot, using the shared project ID/context token, project revision/history frame where relevant, and the latest native revision. It must be refreshed when native state changes; cached revisions cannot prove continuity. `readCurrent` must return a native target from the current snapshot; use `SourceInspector.index(await apiRequest('source-inspect'))`, `SourceInspector.key('parameter-field',parameterId,0,fieldId)` and `EvidenceLinks.targetFromNode(projectScope,node)`. Get the exact model value from current `engineering-read.state.parameters[].fields[].value`; it is read-only and can remain fractional. Return the actual `source-inspect.revision` as `nativeRevision`, requiring the engineering read and source graph to agree. The controller rejects a current read whose native revision differs from its stamp. Native ID0/field0 are legal. Do not use names, array indexes or nearby geometry as identity. The shared setter must reject stale context/history/busy writes atomically, including late replies; the controller's before/after guards complement that guarantee.

Resolve `readCurrent`'s recorded document argument independently of the active page: find its recorded reference page, hash and original page in the shared reader snapshot/source pool. Merely selecting another page or face is not source replacement. If the reference linkage was removed but original bytes remain, the source-only locator can still validate and display the original page; this does not assert native target continuity.

Native target validation must retain historical missing/uncertain targets as unresolved annotations. Legal parameter deletion must not make the whole project unsaveable: verify present targets by exact typed IDs and pins, derive `target-missing` or `needs-reassociation` for absent/unknown ones, preserve the observations and historical confirmation, and require explicit rebind. This does not relax the strict annotation schema or mandatory original PDF byte closure.

Controller methods: `add({document,region,target,observations})`, `readView() -> {stamp,links}`, `setReviewed(evidenceId,boolean)`, `rebind(evidenceId,explicitTarget)`, `locate(evidenceId)`, `cancel()`. `readView.links[]` includes saved link fields plus derived `status`, `canConfirm`, and current `modelValue`. Drawing and measurement each retain `{rawText,rawValue:string|null,unit:mm|cm|null,note}`, including conflicting or fractional text. Checking writes a human annotation only. No value adoption API exists here.

Only an explicit `add` or `rebind` grants a runtime association lease, bound to the exact context token, native revision and target pin. Any changed native revision or reopened controller makes identity unknown, even if typed IDs, names and fingerprints match. The historical confirmation record remains, but derived status becomes `needs-reassociation` and checking is blocked until manual field selection. This conservative behavior avoids a persistent incarnation ledger. Source hash/page/dimensions or locator replacement derives `source-changed`; absent bytes/page derives `source-missing`; absent field derives `target-missing`. Presentation-only crop/rotation changes retain the same original evidence region.

## UI adapter handoff

`evidence-links-ui.js` mounts into a child of existing `#refRecordDetails`, merging evidence into existing source records. The shared owner alone adds this small host and script wiring, destroys/remounts on inspector repaint, and exposes target-to-evidence listing through the existing parameter source disclosure. No new PDF application or persistent manager is created by this slice.

The adapter receives `controller`, `getStamp`, guarded `readSelection() -> {stamp,document,targets:[{target,label,modelValue}]}`, and the existing canvas functions. `locateDocument` must use `isCurrent()` through all asynchronous page loads/navigation before painting, and display the recorded full-page region. A source-only locator can show the original PDF even when its former face linkage is gone; do not silently substitute a new reference by filename. For reverse listing, filter the same link bundle by its typed target or source hash/page; do not maintain a second lookup truth.

Mount signature: `EvidenceLinksUI.mount(host,{controller,readSelection,getStamp,canvas})`; `canvas` supplies `{svg,layer(),eventPoint(event),toPage(point),fromPage(point),pageIdentity()}`. Returned methods are `refresh`, `cancel`, `destroy`, `redraw`, `snapshot`. The evidence polygon is a child of the existing transformed canvas layer with a fixed screen stroke; existing pan/zoom applies naturally. The shared owner calls `redraw()` after `drawFaceEditor`/`feApplyZoom` rebuilds the layer, and destroys/remounts after the inspector host is rebuilt. It does not need a second transform, calibration, or pixel-to-page formula. `pageIdentity` should include reference page ID/hash/page and current basis markers; guarded selection rejects stale reads before writing.

## Validation and remaining integration gate

Focused Node tests, actual native bridge tests, and an isolated Chromium adapter check cover strict data, conflicting exact observations, parameter0/field0, source closure, four rotations/crop/zoom/DPR, annotation-only review, recreated IDs, cancellation/late/context replies and responsive safe text. Browser tests inject the new scripts and a bounded in-memory attachment adapter into the real existing app; this proves the independent slice, **not** complete project archive persistence.

Complete true ZIP save/reopen (including evidence-only original bytes), history/dirty/undo/redo, prepared import atomicity, unknown project capability and A/B attachment closure remain mandatory at the shared-owner integration stage. Their implementation is intentionally absent from this branch. Physical iOS/OS picker/keyboard checks are unverified. Hand off as a draft PR for root's independent review; do not merge or deploy from this worker.
