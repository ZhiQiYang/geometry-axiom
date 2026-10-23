# Pure exact geometry and typed program evaluation

This package uses only the Python standard library. It does not load a template,
interpret legacy source kinds, read a repository, or start a native process.

`types.py` exposes immutable validated `FrameDef`, `RegionDef`, `RegionSetDef`,
`BoxDef`, exact `Quantity`, stable `SourceKey`, opaque `Provenance` records and
`DefinitionValue(schema, content)` for complete provider definition bytes.
Definition values keep immutable bytes, including empty content, without
parsing domain syntax or converting the definition into a geometric feature.
Their schema is nonempty valid Unicode without NUL; K applies no naming or
whitespace policy. The provider owns the content's canonical encoding.
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
An uncomputed source can retain its declared type and `INCOMPLETE` status in
the definition or ordering closure. Only a value-required edge propagates its
unavailable value to the consumer; invalid source definitions remain invalid.
`SourceBoxDef` consumes a typed box source through that same evaluator, including
Boolean operations, dependency closure and partial-root handling. Source context
keeps an opaque owner identity separate from the coordinate domain and axis.
Validation-only evaluation checks all definitions before the host's output
capability gate, preserving the existing definition-versus-output error order.

`transactions.py` owns candidate identity and one-time publication tokens.
`session.py` is its neutral program consumer. The product's `ModelWorld` uses
the same candidate cell through `geometry_app.model_world`; the host supplies
runtime source and adapter identities. The woodworking provider contributes
admission policy and typed profile objects rather than geometry algorithms.
The neutral `ProgramSession` fingerprint includes every definition content byte
and its schema, even when the geometry is unchanged.

The source snapshot in this slice is translated from the existing native
snapshot. The host now pins adapter execution inputs; complete same-candidate
native source DTOs and native replay evidence remain subsequent work. These Python tests do not
establish the final domain-decoupling gate.

Lightweight validation (no native compiler or binary):

```text
python -m unittest tests.test_geometry_kernel_geometry tests.test_geometry_kernel_graph tests.test_geometry_kernel_compatibility tests.test_geometry_kernel_isolation tests.test_geometry_kernel_runtime tests.test_geometry_kernel_transactions tests.test_geometry_kernel_session tests.test_geometry_host_world tests.test_geometry_host_native -v
```

The original 119 tests include geometry, graph, candidate transactions, both real
candidate consumers, product runtime differential oracles and isolation
controls. The no-template test copies only this package and its four neutral
test modules (now 86 tests, including definition values and their session identity) into a new temporary directory, then runs
Python with `-I -B` and a blocking import finder for host/template/legacy names.
It checks actual loaded module paths. The control test edits copied production
source for hole containment and source normal sign; each mutation must fail
both its pure geometry oracle and the legacy facade's frozen mesh oracle, and
restoration must make both pass. Native fixture replays are not claimed by this
lightweight suite.

`geometry_kernel_receipt.py --suite-set definition-sources` runs the current
167-case aggregate, including strict transport, source runtime and the synthetic
second-template consumer, from an explicit frozen commit. The historical
`typed-sources` preset retains its original 119-case aggregate; `py2`
retains 91 expected cases for its original `10cbda745bf9692e1108d6da3351d69ddf3a4306`
source receipt; those counts do not describe the current source tree.

The product runtime oracle compares complete outputs or complete diagnostic
records for 27 cases against the frozen pre-move engine at `3a9dc84b`. It also
checks that the product path invokes this package's typed program evaluator.
The tests supply native data at the established loader boundary; they do not
parse native scene text or execute an adapter.

The frozen wire digests were captured from base commit
`cdaa2010ca27ba011b5e21fabccbab93a574c7b4` before extraction. They cover a through
hole, reversed source winding, a Boolean cavity, split components and EMPTY.
