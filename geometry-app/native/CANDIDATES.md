# Native candidate ownership

`AppWorldCandidate` owns complete before/after application snapshots, its typed
operation context, and one `AppCandidate`/`GeoCandidate` identity. The current
POD layout includes the actual K stores, W recipe/source state, and H metadata.
K hashes only its explicitly bound store ranges; H additionally seals every
byte in both full snapshots and the operation context.

Legacy parsers may prepare a local staging value. `app_world_revalidate_staged`
swaps that value into the exact retained after snapshot before validation. Its
old bytes remain available as the validation baseline and are restored on
failure. Provider state therefore never points at a discarded staging World.

An explicit/implicit preview retains that identity and its evaluated source
graph without changing the live root or consuming formal source-rule keys.
Confirmation checks the previous seal, revision, provider composition and live
baseline, reopens the same candidate, runs the full ordered validation pipeline
required by I8a, and seals it again. Candidate ID and snapshot buffers remain
the same; the resolver is fresh for that evaluation generation. Keyed-boundary
permission is retained as sealed typed operation context rather than inferred
from editable command text. Publication then replaces the complete live root
once; existing canvas/history policy remains a host concern.

Scene preparation retains its parsed, validated candidate. Confirmation uses
those bytes and the pre-existing full-live-snapshot freshness rule, without
rereading a changed input file. Readonly validation temporarily detaches a live
preview and restores its ownership afterward. Direct file loading, reset and
default construction also publish through the complete candidate boundary.
History restoration continues to use H-owned complete snapshots and its
existing presentation merge rules.

Native proof suites are `test_geo261_native_candidate`,
`test_geo261_host_candidate`, `test_geo261_candidate_product`, and
`test_geo261_staged_candidate_graph`. They include actual-object relink controls,
full-byte tampering, candidate generation checks, all seven legacy staging
handlers, import freshness and undo. A successful source/discovery check is not
evidence of native execution; run receipts record that separately.
