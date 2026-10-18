# Python host assembly

`geometry_app` owns the legacy model wire, diagnostic associations, explicit
woodworking provider assembly, native snapshot translation and model sessions.
`modeling` remains the historical public facade and the only axiom-version owner.
Its `build_package` and `verify_package` authority is passed into the host world;
no second copy of the version constants or historical exact pairs exists here.

The product path is `modeling.engine.evaluate` → explicitly assembled
`ModelingRuntime(source_graph=True)` → `geometry_kernel.evaluate`. Its native
loader is `modeling.base.load_candidate`, preserving the historical builder and
literal argv seams. The host compiles shell,
extrusion, KEEP, Boolean and composite-space wire records to typed K nodes.
Woodworking admission and profile member/envelope policy reside in
`geometry_woodworking`; K never selects behavior from those names.

`source_closure.source_paths` exposes ordered logical paths and actual files.
`source_inventory` supplies each normalized source hash. Receipt consumers keep
their own encoding and hash rules. The compatibility bootstrap captures a load
snapshot before loading host runtime/provider modules. `ModelWorld` uses the
same `CandidateCell` as the neutral `ProgramSession`, and additionally pins the
loaded/current source inventory and actual selected native binary bytes.

`model_native` owns compiler invocation, temporary scene files, native transport
and protocol validation. The compatibility facade passes its historical build
callback explicitly. Compiler cache entries bind the recursive project include
closure, command, compiler bytes and environment, and reuse also verifies the
actual output bytes. Scene execution checks loaded/current sources and binary
bytes before and after the call. Source capability admission comes from the
explicit woodworking provider. The native-host tests use real temporary file
bytes with a mocked process boundary and include five removed-guard controls.

`model_native.load_candidate` is the one-invocation typed source
transport. `model_sources` decodes the schema fixed by native source commit
`a6d383bc6a7d7254ff3f2b61291cb280c6a8a78f`, validates the original input hash,
canonical candidate identity, provider identities, exact source values, complete
dependency graph and root associations, then supplies immutable K descriptors.
Box face keys and local coordinate owners retain their complete opaque identity.
Incomplete coverage is rejected; there is no snapshot-only fallback on this API.
The existing `load_base` snapshot API remains available to explicit historical
callers; it is never retried after the product candidate loader rejects input.

The decoder also accepts declared-but-unevaluated native nodes: status
`unevaluated` requires `value: null` and maps to K `INCOMPLETE`. The full typed
descriptor and all three dependency kinds remain required. Definition-required
and evaluate-before edges retain the source closure without pretending to have
a computed value; a value-required edge still makes its consumer incomplete.
The strict `ok` if and only if value-is-present rule remains intact. Existing
failed/missing/cycle/invalid/memory statuses keep their prior outcomes.

The neutral `definition` value type uses scalar units and an exact payload
`{schema, contentBase64}`. It becomes K `DefinitionValue(schema, content)` with
immutable, complete bytes. Empty content is valid; schema is nonempty valid
Unicode without NUL, and whitespace is not trimmed. Base64 must be canonical.
K preserves the provider's encoding without parsing domain content or treating
a definition as a geometric feature. Candidate fingerprints include its schema
and every content byte. Complete native coverage is a required transport gate,
not a Python flag that can be used to fill absent source definitions.

`ModelingRuntime(source_graph=True)` is the explicit source-reference compile
path. It requires a `NativeCandidate`; a snapshot or incomplete DTO cannot
select the older path. The W provider binds the full root association catalog
to placement, box, named quantity and profile member/envelope inputs. It retains
all native source nodes and edges, including unselected definitions. Geometry
nodes consume `SourceRef` values directly; box features keep their opaque origin
and feature identities until H encodes the unchanged legacy output fields.

The source-reference path passes all 27 existing frozen legacy wire/error
digests. Ten additional cases exercise source updates, complete dependency
closure, rotated box frames, all region components, strict binding and three
copied-production guard removals. The `source-runtime` preset runs 146 tests.
These remain synthetic transport fixtures, not actual native replay evidence.
The legacy wire cannot encode a multi-component extrusion's complete feature
identity; the source path rejects that output explicitly instead of truncating
the source. K still receives and evaluates the full region set. Existing source
capabilities have not expanded.

The current 29 source transport tests use synthetic envelopes at a mocked
process boundary and feed decoded descriptors to the actual K evaluator. Eight
named production-source mutation controls must fail their behavioral oracles,
including unevaluated/value mismatches, ok/null, canonical Base64 and complete
definition bytes. The `definition-sources` frozen receipt preset runs 167 tests,
preserving the prior wire/runtime and second-template synthetic comparisons.
The historical `source-transport` preset retains its original 136-case census.
These tests are not actual native execution evidence; the C producer/consumer
integration cases remain unrun in this Python-only validation phase.

The isolated default-source candidate adds seven tests and a `default-sources`
receipt preset of 174 methods. It exercises the actual public facade and
transport selection, typed value changes with an unchanged legacy snapshot,
complete dependency retention, and rejection without fallback. Two copied
production controls restore legacy loading or discard the graph; both must fail
the same default-path oracle. The 27 historical wire digests remain unchanged.
These synthetic checks do not establish native coverage or old-package replay.
Native coverage, source-matched C→Python replay and complete product validation
remain release prerequisites for this candidate. There is no Python scene parser.

`tests/test_geometry_kernel_runtime.py` pins 27 full success/error wire digests
captured from the pre-controller-extraction `3a9dc84` source through the native
loader seam. Those fixtures prove controller/wire compatibility, not native
transport correctness. Existing native-backed modeling suites remain required.
