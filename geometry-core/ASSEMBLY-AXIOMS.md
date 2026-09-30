# Adopted axiom deltas for #20

These are the seven approved semantics. They do not relax D1, D7, D15, D17, I19 or R6.

## D32
World may store AssemblyRuleVersion records with stable rule identity, version, name, role slots and local joints. Identity is not name, order or canvas position. Joints describe continuity, segmentation and end-to-face contact for orthogonal members. They are not fasteners, joints of joinery, construction order or a structural approval. A rule need not bind a material, grid or carrier. A published version is immutable. A draft is not a citable version. A legal definition is not the same claim as generated construction geometry.

## D33
AssemblyBinding cites one fixed rule version and maps each role to an existing typed timber source, contact face and section orientation. Unset material or orientation may be saved as incomplete. A missing or wrong-type source is rejected. Publishing a new rule or material version does not move a binding.

## I40
Identities and references must be unique and typed. The same junction scope cannot hold contradictory settings. A geometric adjacency loop is not a definition cycle. Nested rule references are rejected in this capability. Unknown joint types are rejected. Mutations are candidate-world transactions.

## I41
Published rules, unused versions, incomplete bindings and canvas positions are saved. Drafts live in the project attachment area. Projects that use this capability or only a draft use geometry-canvas/7 and declare assembly-rule-authoring/1. The capability does not mean construction generation.

## R34
Edit draft, validate slots and joints, publish, choose material binding, preview, confirm, save. Authoring executors must not report generated construction timber.

## R4 addition
When assembly-rule-authoring/1 is supported, dump includes every published rule version and binding, rules and material sources before bindings.
