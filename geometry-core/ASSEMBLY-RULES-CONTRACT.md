# Assembly rules contract (authoring/1)

Refs #19 #20. Capability `assembly-rule-authoring/1` is editing, validation, binding and exchange. It does not generate construction timber (#25).

## Identities

- Rule id + version is the published identity. Name, order and canvas position are not identity.
- `slotId` is a role. `memberId` is an occurrence. Two main members may share a slot and must not share a member id.
- `jointId` is local to the rule. Conflict uses junction scope, not joint id.
- Copy allocates a new rule id and keeps internal slot/member/joint ids. Published versions are immutable.

## Joints

- `end-to-side`: terminated member start/finish contacts target member local side `+u|-u|+v|-v`, with explicit relative direction `u|v`.
- `ortho-split`: one member stays continuous, the other is segmented. No diagram coordinates are stored.
- A rectangular adjacency loop is legal. Nested rule references are rejected; this phase has no rule-nesting feature.

## Binding

Sources are an existing timber material version, a dimension parameter field, or an explicit millimetre literal. Unset source, face or orientation is an incomplete but legal binding. Missing or wrong-type sources are rejected. Bindings do not modify timber.

## API

`assembly-read`, `assembly-preview <file>`, `assembly-confirm <token>`, `assembly-cancel <token>`.
Transaction schema `assembly-transaction/1` with `expectedRevision` and `operations`.
Errors include `I40` conflicts/dangling refs, `TOKEN`, `STALE`, `SCHEMA`, capacity as capacity rather than geometry.

Cross-project definition import is `definition-import/1` (D54, D55). See `geometry-core/DEFINITION-IMPORT-CONTRACT.md`. It is not an assembly-transaction operation. Parameter-pack import reassigns parameter-card ids only; definition import classifies D54 and previews rewritten references before confirm.

### Guarded binding writes (2026-10-03)

The formal workspace uses explicit intent:

```json
{"op":"create-binding","value":{"id":1,"name":"...","rule":{"id":1,"version":1},"slots":[]}}
{"op":"edit-binding","id":1,"expectedFingerprint":"<64 lowercase hex>","value":{"id":1,"name":"...","rule":{"id":1,"version":1},"slots":[]}}
```

The abbreviated `slots` above must be replaced with the complete valid slot definitions.
Create rejects an occupied positive uint32 ID, including identical content. Edit requires the existing ID,
matching value ID and native definition fingerprint returned by `assembly-read`. The fingerprint is SHA-256
of canonical binding JSON, independent of object key order and resolved-value changes.
It is checked against the sequential transaction candidate, together with the existing revision/token guards;
stale edits reject the whole transaction. Missing native fingerprints retain the UI draft and refuse preview.
Legacy `put-binding` remains an upsert for existing callers; it is not the formal UI create/edit path.
This adds no archive capability, high-water allocator or generation behavior; format 7 and free-ID wrap remain.

The finite generation contract and adopted D34/I42/R35 source additions are in
[ASSEMBLY-GENERATION-PROPOSAL.md](ASSEMBLY-GENERATION-PROPOSAL.md).
Reviewed PR #53, including the capability-preflight repair from PR #55, was merged to main
on 2026-10-03 at 68c4ac13ec963dae4c9776fb67dac7eff003be06. This is the finite three-member
generation scope only. The preceding format 7 note describes authoring closeout.

## Scene

Native records use bounded Base64 chunks. This replaces the original draft's unimplemented `assembly-rule` / `assembly-slot` line proposal. Replay is atomic through the existing scene loader; individual `line assembly ...` edits are rejected. Canvas kinds `assembly-rule` and `assembly-binding` are display metadata only.

```
requires assembly-rule-authoring/1
assembly begin
assembly record <base64 of {"kind":"rule","bytes":N,"sha256":"..."}>
assembly data <base64 of at most 768 UTF-8 bytes>
assembly data <next chunk, if needed>
assembly commit
assembly record <base64 of binding metadata>
assembly data <binding JSON chunk>
assembly commit
assembly end
```

`kind` is exactly `rule` or `binding`. `bytes` and SHA-256 cover the complete canonical JSON payload; the rule fingerprint is the same hash. Chunks may split a UTF-8 character because decoding joins bytes before JSON parsing. A record must fit 8191 bytes. Extra fields, duplicate identities, missing sources, truncated blocks, wrong lengths and hashes reject the entire scene. Rules and material/parameter definitions precede bindings. No persisted derived geometry or effective-value cache substitutes for definitions.

Project format `geometry-canvas/7` is required when the capability or an assembly draft is present. Drafts are project attachments, not World definitions.

## Exact JSON shapes

Rule (IDs are positive 32-bit integers):

```json
{"id":1,"version":1,"name":"Frame","slots":[{"id":1,"name":"Frame"},{"id":2,"name":"Cross member"}],"members":[{"id":1,"slotId":1},{"id":2,"slotId":2}],"joints":[{"id":1,"kind":"end-to-side","scope":"left","terminatedMember":2,"targetMember":1,"end":"start","side":"+u","dir":"u"}]}
```

`ortho-split` replaces `terminatedMember`, `targetMember`, `end` with `continuousMember` and `splitMembers:[first,second]`. The first split member's finish and second split member's start meet opposite sides of the continuous member. The declared `side` identifies the first contact; the second uses its opposite. Members are three distinct occurrences. Local direction and side tokens are not screen coordinates. Rotation/zoom do not change them.

A rule has 1–8 slots, 1–12 member occurrences, 1–16 joints. A world supports 32 published versions and 64 bindings. Names occupy 1–96 UTF-8 bytes; junction scopes 1–64 bytes. Capacity failures are explicit. Junction scopes cannot repeat, and an occurrence's same endpoint cannot be assigned by two joints, even with different scope strings. Adjacency cycles are allowed.

```json
{"id":1,"name":"Timber set","rule":{"id":1,"version":1},"slots":[{"slotId":1,"A":{"kind":"literal","value":27},"B":{"kind":"literal","value":33},"contactFace":"A","orientation":"B"},{"slotId":2,"A":null,"B":null,"contactFace":null,"orientation":null}]}
```

Every rule slot must appear exactly once. A/B accept the existing engineering source union: `literal`, `spec`, `parameter`, or a fixed timber `material` version with its matching A/B field. Each resolved dimension must be positive integer mm within D1. `contactFace` is A/B; `orientation` names the section axis along local u. Null means deliberately unset, never a missing reference. No concrete placement is necessary.

## Operations and transport

`POST /assembly/preview` accepts `{"schema":"assembly-transaction/1","expectedRevision":N,"operations":[...]}` and uses the shared bounded file transport. Supported operations:

- `publish-rule`, `put-binding`: `value` contains the shapes above.
- `delete-rule`: `id`, `version`; still-used versions reject final validation.
- `delete-binding`: `id`.
- `copy-rule`: `id`, `version`, `newId`; destination must be unused, starts at version 1.
- Existing engineering operations may join the same candidate, so unbinding and source deletion can be atomic. Parameters resolve after all operations, before bindings validate.

`assembly-read` returns revision, definition SHA-256, all published versions with fingerprints, and bindings with derived completeness and per-slot effective values/source paths. Preview returns complete before/after assembly states and violations. Cancel is a no-op on World/history. Confirm checks token protocol, revision, unchanged definitions and all invariants again. Display-only card moves survive confirmation and do not stale the token. Repeating an identical publication creates no history step. `newid` returns `assemblyRule` and `assemblyBinding` in their independent native ID spaces.

## Project and history

`manifest.assemblyDrafts={"schema":"assembly-drafts/1","records":[...]}` is independent of engineering drafts. Each record contains string `id`, `kind` (`rule`/`binding`), `base_ref` (null or fixed rule id/version/fingerprint), editable `data`, and ISO `updated_at`. At most 256 drafts, 256 KiB each. Incomplete draft values are preserved without publishing them.

Binding drafts may additionally contain `binding_intent`: `{mode:"create"}` for a newly allocated binding, or `{mode:"update",source:<original binding value>}` when explicitly editing a published binding. The source is the complete original definition, not derived effective dimensions. It must have the same binding ID as the editable data. Archive validation checks both definitions and preserves this intent through save/reopen and history. An older draft without this field remains readable; it may create an unoccupied ID but cannot authorize overwriting an existing binding. Older clients that do not understand the optional field reject the draft instead of silently dropping its protection.

Immediately before preview, the UI checks the current native state: create IDs must still be unoccupied; updates must still match their original source (object key order is immaterial). Missing/changed sources, including a different binding recreated under the same ID, refuse preview while retaining the draft. That same read revision scopes the native transaction, so later native changes are rejected by the existing revision/token guard. Rule revisions likewise retain their fixed `base_ref`; new/copy rule drafts cannot reuse a published rule identity. These checks do not change the native `put-binding` update operation.

Draft allocation combines the native `newid` suggestion with all published and reserved draft IDs in the same assembly namespace. Search is bounded, wraps `UINT32_MAX` to 1, and rechecks every candidate against both sets. Local slot/member/joint IDs use the same bounded positive range. Rule versions never wrap: editing retains the rule ID, advances beyond published and reserved draft versions, and refuses the uint32 ceiling without replacing the active draft.

The common project bar saves current edits. Import validates the complete archive, capability declarations and native scene before replacing the current context. Local draft changes and native confirmations share ContextHistory; undoing publication restores its draft. Async responses are scoped to the original project context and edit generation. Formats 1–6 retain their original meaning. The modeling executor rejects assembly scenes as unsupported, even when a `requires` line was stripped: authoring does not imply construction generation.

## Historical generator handoff — #25 (2026-10-02)

Superseded on 2026-10-03 by the user-approved [AR06 contract](ASSEMBLY-GENERATION-PROPOSAL.md) and [generation implementation](../geometry-web/docs/ASSEMBLY-GENERATION.md). The following records the earlier deferred decision.

The user chose to finish repairs and closeout while retaining the previous product decisions and organizing future specifications. #25 remains deferred. This section is a review proposal, not an adopted axiom, implemented API, or authorization to generate timber. [公理層.md](../公理層.md) remains the behavior SSOT; [issue #25](https://github.com/ZhiQiYang/geometry-axiom/issues/25) tracks the outstanding decision.

### Reuse and missing inputs

Reuse immutable rule versions/fingerprints, typed A/B sources, local member/joint identities, native candidate validation, revision/token confirmation and project context guards above. A complete authoring binding only establishes material input completeness; it does not supply placement or establish geometric validity.

The smallest proposed evaluator accepts one binding plus an explicit finite placement definition:

| Input | Required contract before implementation |
|---|---|
| Rule/material source | Fixed rule version and fingerprint; binding id; typed source references. A material or rule upgrade is an explicit action. |
| Coordinate context | Explicit placement surface/frame and boundary references; never use the currently selected UI surface implicitly. |
| Member mapping | Every member occurrence maps to a specified guide, actual signed grid index, or named existing member. Repetition lists its finite indices; screen samples and visible grid lines cannot select members. |
| End conditions | Local contact face, section orientation, and both supporting/blocking faces must resolve uniquely under the approved rules. Missing inputs, ambiguity and contradictions retain separate diagnostics. |
| Evaluation bounds | Explicit boundary/finite index range or finite member set, with capacity checked before expansion. An unbounded request is not an empty result. |

Proposed output is an `AssemblyInstance` definition plus a derived preview: each member retains its rule/member identity, placement reference, source dimensions, contact relationships and computed finished dimensions. Instance/segment identity must derive from stable placement and segment keys, not list order or name. The exact key, split/merge correspondence and persisted schema are unresolved; no new capability name or format number is reserved here. Pure geometry export cannot substitute for a reconstructible source definition.

For source edits, preview added/removed/changed members and per-member geometry/contact violations before confirmation. Cancel, failed validation, stale confirmation, transport retry and project replacement must preserve the original World/history; a lost response cannot cause duplicate creation. Save/reopen must preserve the placement definition and dependency closure, and recompute derived geometry for comparison.

### Axiom review required before implementation

| Current clause | Minimum proposal / unresolved difference |
|---|---|
| D1 / D7 | Retain exact integer-mm geometry and environment-derived length; no rounding, frozen final lengths or diagram coordinates as construction input. |
| D15 | Current roles select global cutting priority. A first evaluator can accept only mappings that satisfy these roles. Supporting locally reversed priority needs an explicit clause diff; changing one global priority is insufficient. |
| D17 | Current primary members share a surface axis; boundary/secondary directions are constrained. Keep this for the initial legal fixture. Mixed local axes need a separately approved scope and validation rule. |
| I19 | End supports obey strict owner priority, outer-boundary restrictions and existing exceptions. Authoring a local contact does not waive these checks; any new exception needs its exact condition and negative tests. |
| R6 | Retain legal footprint, finite span selection and unique full-width end support. A member segment must not be cut to a viewport/boundary without valid end support. Explicit member-to-span selection remains to be specified. |
| D33 / I41 / R34 | Binding currently creates no timber and authoring declares no generation capability. Add a separate instance/evaluation contract, capability and persistence rules only after approval; old readers must reject required unsupported capabilities. |

No clause is changed by this handoff. Before approval, the follow-up must present the exact clause edits (or establish that the initial restricted evaluator requires no relaxation), API/error shapes, identity/update rules and resource limits together.

### Implementation gate and acceptance order

1. Specify a legal fixture with two different main-member occurrences sharing one role and a cross member whose ends meet explicit sides, including all existing boundary/support requirements. Compare the exact expected member identities, sources, spans and contacts, not only an outer box or volume.
2. Specify a second material/configuration case and a rejected ambiguous/unsupported case. Distinguish missing input, invalid definition and missing executor capability; never claim construction or structural safety from geometry alone.
3. Obtain approval for the concrete evaluation contract and clause differences. Only then split #25 into native evaluator/transactions, persistence/update and formal UI implementation issues with measurable tests.
4. Verify source edits, fixed-version upgrades, cancel/stale/lost-response behavior and save/reopen. Extend to concave bounds/holes only within the approved evaluator scope. Opposite assembly arrangements require their own approved clauses and identity-aware tests.

Cabinet panels, fasteners, machining allowances, structural analysis, construction sequence and arbitrary nested rules remain outside this proposal. Completing #20–#24 does not close #25.
