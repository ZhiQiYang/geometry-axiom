# Python host assembly

`geometry_app` owns the legacy model wire, diagnostic associations, explicit
woodworking provider assembly, native snapshot translation and model sessions.
`modeling` remains the historical public facade and the only axiom-version owner.
Its `build_package` and `verify_package` authority is passed into the host world;
no second copy of the version constants or historical exact pairs exists here.

The product path is `modeling.engine.evaluate` → explicitly assembled
`ModelingRuntime` → `geometry_kernel.evaluate`. The host compiles shell,
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

`model_native.load_candidate` is the opt-in, one-invocation typed source
transport. `model_sources` decodes the schema fixed by native source commit
`a6d383bc6a7d7254ff3f2b61291cb280c6a8a78f`, validates the original input hash,
canonical candidate identity, provider identities, exact source values, complete
dependency graph and root associations, then supplies immutable K descriptors.
Box face keys and local coordinate owners retain their complete opaque identity.
Incomplete coverage is rejected; there is no snapshot-only fallback on this API.
The existing `load_base` API and the product's current loader remain unchanged.

The 17 source transport tests use synthetic envelopes at a mocked process
boundary and feed their decoded descriptors to the actual K evaluator. Three
production-source guard removals must fail the same behavioral oracles. The
`source-transport` frozen receipt preset runs these with the prior 119 tests,
for 136 discovered cases. These tests are not actual native execution evidence.

The PY2 checkpoint has intentionally incomplete native source separation:
native-evaluated specification values are translated to typed source descriptors,
but the complete same-candidate source graph DTO is still required from the
native implementation. There is no Python scene parser. This checkpoint must
not be described as complete source decoupling or a real native replay result.

`tests/test_geometry_kernel_runtime.py` pins 27 full success/error wire digests
captured from the pre-controller-extraction `3a9dc84` source through the native
loader seam. Those fixtures prove controller/wire compatibility, not native
transport correctness. Existing native-backed modeling suites remain required.
