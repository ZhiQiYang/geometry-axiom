# Minimal assembly generation contract

Status: implementation work in progress. This document does not claim that the
generator or its acceptance tests are complete.

The first supported operation instantiates one fixed published rule version and
one complete binding. It supports exactly three distinct members: two continuous
primary members and a secondary member whose start and finish terminate on the
respective primary members. Both joints are `end-to-side`, with `Joint.dir=u`
evaluated in each designated primary target's section frame, first target side
`+u`, and second target side `-u`. It does not refer to the secondary's own section
u axis. Member and joint
IDs remain rule-local identities; generated timber IDs are separate world IDs.

The carrier, two primary guide references, a separate secondary guide reference,
existing lawful boundary end
supports, and member timber IDs are explicit inputs. Generation never manufactures
boundary supports or promotes a primary member to boundary priority. Primary
members have priority 2 and the secondary member has priority 3. Existing D15,
D17, I19 and R6 placement, span, support-width and unique-blocker checks remain
mandatory.

The supported binding uses contact face A and orientation A for every slot.
Native timber axes are X=L, Y=A and Z=B. Local section u is native Y; local
section v is native Z. Thus target +u is native B1 and target -u is native B0.
Primary length direction is carrier -v, secondary length direction is carrier
+u, and depth is carrier +n. Authoring diagrams do not supply geometric positions.
Orientation B, contact face B, v-side joints, nested rules, ortho-split joints,
holes requiring automatic segmentation, and other topologies return an explicit
unsupported diagnostic before any world change.

An instance records its own stable ID, fixed rule ID/version/fingerprint, binding
ID, rule-local member to timber ID mapping, and placement/source references.
Published rule versions are immutable. A later version does not silently upgrade
an existing instance. An explicit upgrade must pass a fresh atomic preview and
confirmation and preserve member identities or diagnose an incompatible mapping.

An instance follows dimension/source edits of the same binding ID through native
atomic recomputation; it does not freeze effective A/B values. Changing that
binding's fixed rule version requires an explicit compatible instance upgrade in
the same candidate, otherwise validation rejects the entire change. Parameter and
material source changes retain their typed references and recompute contacts.

A/B retain engineering dimension sources. L retains native placement references
and is recomputed by the existing span resolver. Changed source dimensions,
primary positions or boundary supports revalidate the entire instance. Each local
joint is checked against its designated target member, endpoint, face plane,
opposite normals and complete contact width after geometry recomputation.
Global priority alone is not proof of a local joint.

Preview, cancel, stale-preview rejection, confirm, undo and redo use the existing
native candidate transaction. Failed validation leaves world, revision, history
and saved output unchanged. Saving and reopening must retain all instance,
member, local-joint, fixed-version, source and placement identities. A required
generation capability makes an older loader reject the project instead of
silently discarding instances.

The authoring identity allocator must account for formal IDs and unpublished draft
reservations. It must never increment a wrapped native allocation in JavaScript
and accidentally select a formal binding. Exhaustion is an explicit diagnostic;
creating a new binding must reject an existing formal ID, while editing an
existing binding is a separate intentional operation.

## Authoring allocation protocol and lifecycle

`assembly-newid {"kind":"rule|binding","reserved":[...]}` is a native read-only
query. It accepts at most 256 positive uint32 draft reservations, computes the
successor above the namespace's formal high water and every reservation, and
returns `CAPACITY` at uint32 exhaustion. It never wraps into a hole. The legacy
`newid` response uses 0 as the exhausted sentinel only for assembly namespaces;
all other existing object namespaces retain their previous allocation behavior.

Successful native publication advances the formal allocation high-water mark;
automatic allocation does not recycle it. Explicit currently unused lower IDs
remain legal for out-of-order draft publication. Delete, undo and
redo do not lower formal high water. The hashed final `identity` scene record
preserves it even when every assembly object has been removed. Older scenes
without this record initialize high water from their published definitions.
Duplicate, misplaced or lower-than-definition identity records are rejected.
Older loaders reject the unknown record instead of silently discarding it.
Archive `sceneHash` protects the record together with the rest of the scene.
Loading a different project replaces the namespace with that project's state.

Allocation queries and cancelled previews do not retire identities or create
native history. An unpublished candidate ID is reserved while its draft exists;
discarding the entire unpublished draft releases that provisional reservation.
The externally stable draft identity is its UUID. Rule-local slot/member/joint
high water lives in the draft, survives removal and undo, and is saved with it.
Creating a new published rule from a later revision initializes these counters
from every existing version of the same rule.

New bindings use `create-binding`, which rejects an existing formal ID. Explicit
edits use `edit-binding` with the binding ID and the original content fingerprint;
a changed source returns `STALE`. Drafts preserve create/edit intent across save
and reopen. Legacy drafts lacking intent are treated as creates, so a colliding
legacy draft is preserved and refused rather than silently becoming an edit.
The legacy explicit `put-binding` API remains available for existing integrations.
