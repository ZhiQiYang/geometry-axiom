# #344 Mutation evidence: bounded peer passed

Fixed source `503cfc59354893859ae9e6e4a6ab7c11d7972517`; actual integration
checkout `56250470746f8a7bf6b4a235a586f2744ae3cddf` has the identical tree
`ff068df7b220d63e64832d3648a0b81ff8cbca57`. Fixed Git objects and captured source
identity remain authoritative if the single writer starts a ledger-only successor.

Mutation `41388718083`, attempt 1, is successful. The unchanged original verifier
has actual exit 0, correct source ROOT/command/tool hashes and matching raw stream
hashes; its ledger and summary equal official bytes. 123 records / 120 active:
114 killed, 1 crashed, 5 equivalent, 3 retired; all other categories zero.

- Official ledger SHA256:
  `aaaad44b2470d5f5d937a8ba8f431dd554f0ee95a82958f9ff48b19aa86a5ee8`.
- Official summary SHA256:
  `cad001944ec1e2a5792be56a8d2f03b14c0fd039cf66a67f558dc2b36117513d`.
- 21 ZIP API identities match. Seven original cache tar contents, binary bytes and
  sidecars match; 159 bridge raw structured results independently reparse exactly.
- Seven official workflow negative controls show original strict 0/1/0 in raw
  logs and manifests. No local probe was invoked.
- 185 fixed Git source inputs and closure, 53 bridge oracle identities, seven
  native build fingerprint records / 1369 input identities match the captured
  source identity. Architecture has three original exit-0 commands, matching raw
  hashes and the 604-input closure identity.

Integration `41388718270` remains failure with exactly native (2/3) and native
complete coverage failed. This review accepts Mutation evidence and preserves
overall rejection; another agent owns native/browser raw review. No artifact is
relabelled to a successor commit.

Machine evidence: `MUTATION_PEER.json`, `command-receipt.json`.
Only saved bytes, JSON, tar/ZIP and Git metadata were read. No source runner
import, original validator rerun, product/native test, Chrome, build/compiler,
API, local negative control, binary execution or source/PR edit occurred.
