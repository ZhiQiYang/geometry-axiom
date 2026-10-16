# Pure exact geometry and typed program evaluation

This package uses only the Python standard library. It does not load a template,
interpret legacy source kinds, read a repository, or start a native process.

`types.py` exposes immutable validated `FrameDef`, `RegionDef`, `RegionSetDef`,
`BoxDef`, exact `Quantity`, stable `SourceKey`, and opaque `Provenance` records.
Region validation checks complete loops and holes; a box is constructed from
positive extents and a right-handed frame. Private evaluated geometry retains
an inside predicate; it is not a public template input.
Exact arrangements retain their coordinate domain. Shells, Boolean inputs and
mesh arrangements reject mixing distinct domains, including equal coordinates
belonging to different local spaces. Counts are nonnegative exact integers;
provided stable vertex identities must be complete and unique.

`geometry.py` owns the single product implementation of region extrusion,
exact arrangements, shell topology, regularized Boolean operations, source
coverage, canonical triangle ordering, components, cavities and volume.
The host package `geometry_app` translates legacy input/output and diagnostics
to this implementation. Opaque provenance ordering preserves legacy mesh
ordering. The modules under `modeling` are compatibility facades.

`graph.py` owns typed immutable definitions, source descriptors and dependency
edges. It validates the complete program before evaluation, including unused
definitions, reference types, cycles, declaration order and resource limits.
`evaluate.py` evaluates those definitions without a legacy kind dispatch or
template import. Source dependencies distinguish value requirements, definition
requirements and evaluation ordering. Export roots select geometry views;
partial output is restricted to incomplete roots and each root is atomic.

`transactions.py` owns candidate identity and one-time publication tokens.
`session.py` is its neutral program consumer. The product's `ModelWorld` uses
the same candidate cell through `geometry_app.model_world`; the host supplies
runtime source and adapter identities. The woodworking provider contributes
admission policy and typed profile objects rather than geometry algorithms.

The source snapshot in this slice is translated from the existing native
snapshot. Complete same-candidate native source DTOs, adapter execution pinning
and native replay evidence remain subsequent work. These Python tests do not
establish the final domain-decoupling gate.

Lightweight validation (no native compiler or binary):

```text
python -m unittest tests.test_geometry_kernel_geometry tests.test_geometry_kernel_graph tests.test_geometry_kernel_compatibility tests.test_geometry_kernel_isolation tests.test_geometry_kernel_runtime tests.test_geometry_kernel_transactions tests.test_geometry_kernel_session tests.test_geometry_host_world -v
```

The 91 tests include geometry, graph, candidate transactions, both real
candidate consumers, product runtime differential oracles and isolation
controls. The no-template test copies only this package and its four neutral
test modules (78 tests) into a new temporary directory, then runs
Python with `-I -B` and a blocking import finder for host/template/legacy names.
It checks actual loaded module paths. The control test edits copied production
source for hole containment and source normal sign; each mutation must fail
both its pure geometry oracle and the legacy facade's frozen mesh oracle, and
restoration must make both pass. Native fixture replays are not claimed by this
lightweight suite.

The product runtime oracle compares complete outputs or complete diagnostic
records for 27 cases against the frozen pre-move engine at `3a9dc84b`. It also
checks that the product path invokes this package's typed program evaluator.
The tests supply native data at the established loader boundary; they do not
parse native scene text or execute an adapter.

The frozen wire digests were captured from base commit
`cdaa2010ca27ba011b5e21fabccbab93a574c7b4` before extraction. They cover a through
hole, reversed source winding, a Boolean cavity, split components and EMPTY.
