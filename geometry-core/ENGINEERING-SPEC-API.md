# Engineering specification API / 1

Implementation contract for the approved `ENGINEERING-SPEC-PROPOSAL.md` (2026-09-28). This document fixes the transport and storage representation; the proposal and the synchronized axioms govern behavior.

## Authority and transport

The C `World` owns published materials, methods, applications and dimension sources. Evaluated grid/timber dimensions remain caches. Python transports JSON and the browser edits drafts; neither independently evaluates engineering sources. The capability is `engineering-spec/1`.

The bridge exposes `engineering-read`, `engineering-preview <server-owned UTF-8 JSON file>`, `engineering-confirm <token>`, `engineering-cancel <token>` and readonly `engineering-validate <server-owned scene file>`. The service maps these to read/preview/confirm/cancel HTTP operations. Paths are an internal bridge transport, never accepted directly from remote JSON. Preview reads a complete `engineering-transaction/1` request into one candidate World. It does not execute history groups against the live World. Token-scoped cancel cannot discard a newer candidate.

Every response has `ok`; failures include `error` and `code`. A preview additionally returns `preview:{token,valid,revision,before,after,violations}`. `before` and `after` contain engineering definitions and the complete affected grid/guide/timber geometry, including indirectly affected objects. Confirmation requires the same definition revision and candidate; canvas positions may change without invalidation. Confirmation swaps the already validated candidate once and records one native undo step. Cancel, invalid preview and stale confirmation do not change World/history.

## Values

IDs for materials, methods and applications are stable ASCII strings matching `[A-Za-z0-9_-]{1,64}`. Versions are integers `1..4294967295`. Geometry IDs retain their existing uint32 namespaces. All lengths used in geometry are integer mm within D1; JSON booleans/floats are not integers. An omitted optional setting means unset or, in an update operation, preserve existing as specified below. `null` explicitly removes an optional setting.

Material content:

```json
{"id":"panel-uuid","version":1,"kind":"panel","name":"915 panel","width":915,"length":1830,"thickness":"6","brand":null,"model":null,"notes":null}
```

A timber material replaces width/length/thickness with positive integer `A` and `B`. Panel thickness is a positive decimal string or null, preserved exactly; it does not participate in geometry. Name is required. Brand/model/notes are optional strings or null. Publishing returns the content plus `fingerprint` (lowercase SHA-256) and `archived` (initially false). Archived is project state outside immutable content. Same ID/version with different content is rejected; identical content is idempotent. A changed version never changes existing references.

Method content:

```json
{"id":"method-uuid","version":1,"name":"Ceiling","panel":{"id":"panel-uuid","version":1},"roles":{"boundary":null,"primary":null,"secondary":null},"gap":3,"longAxis":"v","mainAlong":"u","notes":null}
```

Panel and each role reference a fixed compatible material version, or null. Gap is nonnegative integer mm or null. `longAxis` is the axis receiving panel length (`u`, `v`, or null); the other receives width. `mainAlong` is `u`, `v`, or null. Missing material slots/settings remain unset; publication may succeed while a later specific application remains incomplete.

Application content:

```json
{"id":"application-uuid","placement_id":1,"method":{"id":"method-uuid","version":1},"longAxis":null,"mainAlong":null,"overrides":{},"anchorOptions":{"u":null,"v":null}}
```

Exactly one application per placement. Application `longAxis`/`mainAlong` explicitly override corresponding method defaults; null inherits. `overrides` allows `gap`, `boundary.A`, `boundary.B`, `primary.A`, `primary.B`, `secondary.A`, `secondary.B`, each a non-application DimensionSource. `anchorOptions` is only a creation preference: each axis is null, `{kind:"coordinate",value:0}`, or `{kind:"edge",side:"min"|"max"}`. Existing effective anchors live only in the grid definition and remain unchanged unless a bind-grid operation explicitly supplies anchors. Read responses add derived `bindings`, without storing another binding list that can drift from sources.

DimensionSource is exactly one of:

```json
{"kind":"literal","value":915}
{"kind":"spec","name":"板寬"}
{"kind":"material","id":"panel-uuid","version":1,"field":"width"}
{"kind":"application","id":"application-uuid","field":"u.panel"}
```

Material fields are width/length for grid panel, and matching A/B for timber A/B. Material is not a gap source. Application fields are `u.panel`, `v.panel`, `u.gap`, `v.gap`, and the six role A/B fields above. Application must belong to the target placement. Role bindings must match an existing placed timber's role; custom is not implicitly bound. The effective path is object override, application override, method setting, then its fixed material version. No fallback to an unrelated material.

A persisted dimension binding is `{target,source,override}`. Target is `{kind:"grid",id:1,axis:"u",field:"panel"|"gap"}` or `{kind:"timber",id:7,field:"A"|"B"}`. Override is null or a non-application DimensionSource. Read responses additionally expose `effective` and the resolved source path. Pure legacy dimensions have no binding and are reported as existing direct input.

## Transaction operations

Request: `{schema:"engineering-transaction/1",expectedRevision:123,operations:[...]}`. The revision comes from read and is checked before evaluating the candidate. Operations are ordered, capacity checked as a whole, and fully rebuilt before a preview can be confirmed. Unknown keys/op/schema reject the complete request.

| op | Fields | Behavior |
|---|---|---|
| `publish-material` | `value`, optional `fingerprint` | Publish immutable content; supplied fingerprint is recomputed and checked. |
| `publish-method` | `value`, optional `fingerprint` | Same; referenced material versions must already exist in candidate. |
| `put-application` | `value` | Create/replace the exact application definition. Existing bindings remain and are re-evaluated. UI preserves overrides/anchorOptions when changing only method. |
| `bind-grid` | `id`, `application`, optional `anchors:{u:integer,v:integer}`, optional `create:boolean` | Explicitly bind both PANEL_LAYOUT axes panel/gap to application. New grid uses explicit anchors, else explicitly stored anchorOptions; missing origin rejects. Existing anchors are preserved unless supplied. Existing mainAlong is preserved; new grid uses application/method default and requires it. Existing object overrides survive rebinding. |
| `bind-timber` | `id`, `application`, `slot` | Bind A/B of an existing placed timber to the named boundary/primary/secondary slot; preserve role, anchor, placement and existing object overrides. |
| `set-source` | `target`, `source` | Set an explicit typed dimension source; preserve an existing override. Existing main grid PANEL_LAYOUT or placed timber required. |
| `set-override` | `target`, `value` | Set non-application DimensionSource override; null removes it and restores inheritance. Target must already have a source binding. |
| `archive` | `kind:"material"|"method"`, `id`, `version`, `value:boolean` | Change archive state without changing immutable fingerprint or breaking references. |

The first implementation does not expose deletion of published versions. Legacy numeric grid/timber edits may not silently overwrite an engineering binding; they must be rejected with an actionable message to edit the engineering source/override instead. Creating unbound legacy objects remains supported.

Deleting a grid or timber removes only its own attached dimension bindings in the same candidate and undo entry. Existing downstream-reference checks still apply; rejection restores both geometry and attached definitions. Deleting a placement after its guides, grids and timbers are removed also removes its attached application. Published material/method versions remain. Reusing a deleted object ID never reattaches a former binding implicitly.

R13 splitting preserves each grid ID, its DimensionSource identities and concrete anchors. The existing parent/child family remains intact on its selected fragment. If every object bound to one application moves to the same fragment, that same application ID follows to the new placement and retains all other fields. If its bindings would span both fragments, the complete split is rejected explicitly; there is no automatic cloning, replacement ID or conversion to evaluated numbers. Direct material/spec sources keep their original references. Named-spec changes that affect an engineering grid use I8a preview even when no timber or subgrid is present.

## Persistent scenes, canonical fingerprints and limits

Engineering scenes start with the non-comment marker `requires engineering-spec/1`; old readers therefore reject rather than silently strip sources. Each engineering record uses `engineering <material|method|application|grid|timber|archive> <base64>` where base64 contains canonical UTF-8 JSON. Material/method records contain immutable `value` and `fingerprint`; archive is separate. Sources are serialized without evaluated cache values. Dump orders material versions, method versions, ordinary geometry dependencies, applications, then bound geometry definitions, preserving I9. All published versions, including unused versions, are included.

A bound main grid record is `{id,placement_id,mainAlong,axes:{u,v}}`. Each axis is null, `{kind:"panel",panel,gap,anchor}`, `{kind:"series",start,step,count}`, or `{kind:"explicit",coords:[...]}`. Panel/gap are either legacy direct integers or `{source:DimensionSource,override:DimensionSource|null}`. A bound timber record is `{id,A,B,role,priority?}`, with A/B using the same integer-or-binding representation. Its separate legacy `place` line preserves the original anchor references. Unbound grids/timbers keep their original DSL. This avoids temporarily replaying an evaluated number before re-attaching its source.

Read returns `{ok,revision,definition_sha256,state:{capabilities,required_capabilities,materials,methods,applications,sources}}`. Material/method entries flatten content fields plus fingerprint and archived. Preview before/after have the same state plus `geometry:{grids,guides,timbers}`, using existing references geometry. `references` also exposes `engineeringSources` via the identical core writer. Validation returns `{ok,capabilities,required_capabilities,definition_sha256}`. Available capability is always engineering-spec/1; required capability is present only when the validated World contains engineering definitions. Confirm returns `history_changed`, `revision`, `before_revision` and `transaction_id`; identical publication confirmation does not add undo history.

Canonical content encoding is `engineering-content/1`: the same strict UTF-8 JSON rules as MODELING-CONTRACT canonical JSON (lexicographically sorted ASCII schema keys, no insignificant whitespace, integer decimal numbers, UTF-8 strings with JSON control-character escaping, no floats/duplicate/unknown keys). SHA-256 hashes the material/method content object, excluding fingerprint and archive state. Decimal thickness remains a string. Import recomputes hashes in C. One implementation supplies read/dump/import/publication; the frontend does not maintain a second fingerprint algorithm.

Limits are explicit capacity errors, never truncation: 64 material versions, 32 method versions, 16 applications (existing placement limit), 192 dimension bindings (4 per grid plus 2 per timber), 1024 UTF-8 bytes per canonical version/application record, 256 operations per transaction, 1 MiB transaction/scene input. Individual stored DSL lines remain within existing SCENE_MAX_LINE. Unknown required capabilities reject before replacing the current project.

`.gcanvas/5` stores complete engineering declarations only in world.scene, advertises requiredCapabilities, and may independently store unpublished engineeringDrafts. Model definitions retain their engineering scene/dependency closure and advertise the capability; model_base must replay sources in C, never flatten to literal values.

## Core integration and ownership

EngineeringState is fixed-capacity POD inside World. C engineering modules own source resolution and fingerprints. `world_revalidate` resolves every engineering dimension before subgrid validation, reference rebuild and existing geometry guards. Legacy commands use the same revalidation, so named-spec and boundary changes cannot leave stale engineering caches. Native history snapshots automatically include all definitions; a separate monotonic definition revision invalidates preview even after an edit/undo ABA. Canvas-only edits preserve the revision.

Implementation owner: height_ui_change for engineering_types.h, engineering.inc, engineering_commands.inc, engineering_bridge.inc, references/transactions hooks, current_geometry.c integration and core tests. Root owns service JSON transport and app entry adapter; space_storage owns .gcanvas/model capability handling; engineering_spec_existing owns workspace UI.
