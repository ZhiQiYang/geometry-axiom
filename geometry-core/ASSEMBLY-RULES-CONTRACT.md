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

The common project bar saves current edits. Import validates the complete archive, capability declarations and native scene before replacing the current context. Local draft changes and native confirmations share ContextHistory; undoing publication restores its draft. Async responses are scoped to the original project context and edit generation. Formats 1–6 retain their original meaning. The modeling executor rejects assembly scenes as unsupported, even when a `requires` line was stripped: authoring does not imply construction generation.
