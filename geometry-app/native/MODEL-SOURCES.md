# Same-candidate model source transport

`model-base --neutral-sources <scene>` emits one JSON envelope from one validated
process-owned candidate. The existing one-argument invocation keeps its original
`geometry-base-snapshot/1` output. This is internal transport, not a scene or project
file format.

The envelope has `ok: true`, `schema: "geometry-neutral-source-envelope/1"`,
`candidate: {id, baseRevision: 0}`, `source: {sha256Before, sha256After}`,
`legacySnapshot`, and `neutralSources`. `id` is lowercase SHA-256 of UTF-8
`legacySnapshot.base_scene`: canonical definitions in full, without presentation
positions or derived comment lines, with one final LF. The raw source file must
have equal before/after hashes. The caller separately pins the executable hash;
the native process does not claim to prove its own binary identity.

`neutralSources` has schema `geometry-neutral-sources/1`, the same `candidate`,
and these fields:

- `coverage: {complete: false, rootsComplete: true, missingGroups: [...]}`.
  `rootsComplete` covers every placement frame/region, column/beam/member box,
  named spec, and profile run envelope/member frame/region/length. It does not
  claim complete dependency semantics. Consumers must reject `complete: false`
  for production composition and must never silently fall back to snapshot-only
  geometry. Missing groups remain explicit until their real graph consumers move.
- `providers`: unique `{namespace, implementationFingerprint}` records. The
  fingerprint is the provider contract revision, not a self-verified binary hash.
- `nodes`: `{ref, descriptor, status, value}`. A ref is
  `{namespace, keyBase64}`; keys are exact bytes, including embedded NULs. The
  public K engine copies keys and binds callbacks to this same candidate.
- `edges`: `{consumer: ref, source: ref, kind}`. `kind` is `value-required`,
  `definition-required`, or `evaluate-before`. The last retains the historical
  ordering policy and does not imply that a failed earlier candidate is required.
- `roots`: `{kind, id, slot, memberId, name, ref}`. `memberId` is null for a profile
  envelope and the real member ID for its members. Named specs use `id: 0` and
  exact `name`; parameter fields use card `id` and field `memberId`. `slot` is
  `placement.frame`, `placement.region`, `solid.box`, `spec.value`,
  `parameter.value`, `profile.frame`, `profile.region`, or `profile.length`.
  Box roots additionally contain `faces`, six ordered records with `axis`, `side`,
  `legacyFeature`, and exact `featureKeyBase64`, preserving native face provenance.
  Face keys inherit the root ref's namespace and provider fingerprint. They are
  provenance identities, not separately evaluated graph nodes.

Each descriptor is `{valueType, unit, context}`. Types are `quantity`,
`axis-position`, `frame`, `region-set`, `box`, and `feature`; units are `length`
or `scalar`. Context is `{placementId, axis, owner}`, using null where absent.
`owner` is an opaque ref for the local profile-run coordinate domain. It need not
be an evaluated graph node. Different local runs never share a coordinate domain.

Successful node values use these shapes (failed nodes have null values):

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

The producer builds and resolves all roots before emitting a successful envelope.
The old snapshot and typed roots share the candidate. The current dependency
coverage is deliberately incomplete; this transport alone is not N4 completion.
