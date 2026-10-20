# Same-candidate model source transport

`model-base --neutral-sources <scene>` emits one JSON envelope from one validated
process-owned candidate. The existing one-argument invocation keeps its original
`geometry-base-snapshot/1` output. This is internal transport, not a scene or project
file format.

The opt-in mode also accepts the core's existing `finish-surface`, `panel-fill`,
and `derived-placement` source declarations to expose derived multi-component
regions. This does not expand the original one-argument mode's command allowlist
or downstream modeling capabilities. Its legacy-shaped placement record can only
carry the historical single outline; all components are in the typed region root.

The envelope has `ok: true`, `schema: "geometry-neutral-source-envelope/1"`,
`candidate: {id, baseRevision: 0}`, `source: {sha256Before, sha256After}`,
`legacySnapshot`, and `neutralSources`. `id` is lowercase SHA-256 of UTF-8
`legacySnapshot.base_scene`: canonical definitions in full, without presentation
positions or derived comment lines, with one final LF. The raw source file must
have equal before/after hashes. The caller separately pins the executable hash;
the native process does not claim to prove its own binary identity.

`neutralSources` has schema `geometry-neutral-sources/1`, the same `candidate`,
and these fields:

- `coverage: {complete: true, rootsComplete: true, missingGroups: []}`.
  `rootsComplete` covers every placement frame/region, column/beam/member box,
  named spec, parameter field, and profile run envelope/member frame/region/length.
  `complete` covers the supported source graph, including grid fields and bindings,
  material sources and overrides, profile definitions, derived-region provenance,
  and ordered stop features. It does not require unused value nodes to evaluate.
  Consumers must reject incomplete coverage for production composition and must
  never silently fall back to snapshot-only geometry.
- `providers`: unique `{namespace, implementationFingerprint}` records. The
  fingerprint is the provider contract revision, not a self-verified binary hash.
- `nodes`: `{ref, descriptor, status, value}`. A ref is
  `{namespace, keyBase64}`; keys are exact bytes, including embedded NULs. The
  public K engine copies keys and binds callbacks to this same candidate.
- `edges`: `{consumer: ref, source: ref, kind}`. `kind` is `value-required`,
  `definition-required`, or `evaluate-before`. The last retains the historical
  ordering policy and does not imply that a failed earlier candidate is required.
- `roots`: `{kind, id, slot, memberId, name, ref}`. `kind` is `placement`, `column`,
  `beam`, `timber`, `spec`, `parameter`, or `profile-run`. `memberId` is null for a
  profile envelope and the real member ID for its members. Named specs use `id: 0` and
  exact `name`; parameter fields use card `id` and field `memberId`. `slot` is
  `placement.frame`, `placement.region`, `solid.box`, `spec.value`,
  `parameter.value`, `profile.frame`, `profile.region`, or `profile.length`.
  Box roots additionally contain `faces`, six ordered records with `axis`, `side`,
  `legacyFeature`, and exact `featureKeyBase64`, preserving native face provenance.
  Face keys inherit the root ref's namespace and provider fingerprint. They are
  provenance identities, not separately evaluated graph nodes.

Each descriptor is `{valueType, unit, context}`. Types are `quantity`,
`axis-position`, `frame`, `region-set`, `box`, `feature`, and `definition`; units
are `length` or `scalar`. Context is `{placementId, axis, owner}`, using null where absent.
`owner` is an opaque ref for the local profile-run coordinate domain. It need not
be an evaluated graph node. Different local runs never share a coordinate domain.

A metadata-only dependency may retain a node with `status: "unevaluated"` and
`value: null`, such as the world-frame identity of an unplaced profile run. These
nodes are valid in complete coverage; all exported roots must have `status: "ok"`
and their typed values. Failed nodes also have null values.

Successful node values use these shapes:

- quantity: `{num, den, unit, quantityType}`; numerator/positive denominator are
  exact decimal strings, and dimension/count/ratio remain distinct.
- axis position: `{coordinate, context}`.
- frame: `{origin, u, v, n, coordinateDomain, owner}`, with three integer components
  per point/vector and domain `world` or `local`.
- region set: `{components: [{outer, holes, vertexKeys}]}`; each loop is ordered
  integer UV pairs. Every component and hole is retained. `vertexKeys` is null
  when no authored boundary identity table exists, otherwise parallel loop arrays.
- box: `{frame, lo: [0,0,0], hi: [length,a,b]}` in its exact cardinal local frame.
- feature: `{keyBase64, segment: [start,end]}`.
- definition: `{schema, contentBase64}`; `schema` identifies the definition codec,
  and `contentBase64` preserves its exact canonical bytes, including binary data.

The producer builds and resolves all roots before emitting a successful envelope.
The old snapshot and typed roots share the candidate. Complete native transport
coverage does not replace the caller's executable pinning or the end-to-end
native-to-Python adoption evidence; this declaration alone is not N4 completion.


The H consumer independently derives the exact root association set from the
snapshot catalogs: placements have two roots, solids one, named specs one,
parameter fields one, and each profile run envelope/member three. The snapshot
includes `parameter_fields: [{parameterId, fieldId, name}]`, read directly from
the canonical parameter store in both invocation modes. This additive identity
catalog contains no evaluated quantity or duplicate parameter parser. Duplicate
catalog identities, missing roots, extra roots and wrong associations are errors;
coverage booleans cannot substitute for this comparison. The comparison runs only
after every older decoding check and, at the native process boundary, after the
loader's legacy snapshot contract. An input those checks reject keeps its exact
status, code, clause and message.

Generic typed decoding preserves opaque provider keys and INCOMPLETE values for
independent program consumers. The actual native process boundary additionally
requires every root to be COMPLETE and to use `app.model-snapshot` with provider
fingerprint `geo261-model-snapshot/1`. This H adapter encodes named specs as UTF-8
`spec:<name>` and other root keys as
`<kind>:<id>:<slot>:envelope:0` or `<kind>:<id>:<slot>:member:<memberId>`.
The private native decoder verifies the association-to-key binding before the
candidate reaches the product runtime. K and W continue to treat keys as opaque;
there is no configurable bypass or snapshot fallback.
