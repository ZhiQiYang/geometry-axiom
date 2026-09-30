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

DSL records are separate lines (`assembly-rule`, `assembly-slot`, `assembly-member`, `assembly-joint`, `assembly-binding`, `assembly-bind-slot`) plus `requires assembly-rule-authoring/1`. Replay is atomic through the existing scene loader. Canvas kinds `assembly-rule` and `assembly-binding` are display metadata only.

Project format `geometry-canvas/7` is required when the capability or an assembly draft is present. Drafts are project attachments, not World definitions.
