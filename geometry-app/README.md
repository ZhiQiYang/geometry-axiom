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

The PY2 checkpoint has intentionally incomplete native source separation:
native-evaluated specification values are translated to typed source descriptors,
but the complete same-candidate source graph DTO is still required from the
native implementation. There is no Python scene parser. This checkpoint must
not be described as complete source decoupling or a real native replay result.

`tests/test_geometry_kernel_runtime.py` pins 27 full success/error wire digests
captured from the pre-controller-extraction `3a9dc84` source through the native
loader seam. Those fixtures prove controller/wire compatibility, not native
transport correctness. Existing native-backed modeling suites remain required.
