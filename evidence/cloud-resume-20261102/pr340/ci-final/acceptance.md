# #340 fixed-source CI accepted

Source `b3a248607d7eb68d3167abbb926cf491d9b35a26`; true integration merge
`fc1c9f565a2e15660e931b3884dca2220cb1b7b2` has exactly the source tree and
real GitHub API parents. Integration `41382015317` and Mutation `41382015277`,
both attempt 1, are **success**: all 20 jobs completed successfully.

21 official ZIP API digests and all extracted members match; both official run-log
ZIPs match all 20 direct job logs byte for byte. The original Mutation verifier,
run from the fixed source root into a fresh output directory, exits 0 and produces
the exact official summary and ledger: 123 rows / 120 active; 114 killed,
1 crashed, 5 equivalent, 3 retired; survived/invalid/stale/blocked/unrun all 0.
All seven unchanged cache negative guards reproduce strict 0/1/0. All original
binary bytes, sidecars, closures and source/tool hashes pass; 159 bridge raw
structured results independently reparse exactly.

- Ledger SHA256: `52bbad63cc0a281f6d9a5304bc8ddc65ddd96213aeea98057dcb6be0b287b962`.
- Summary SHA256: `df5c9d95aa4a7a8d128b68af33f7f0b0aa6be0b87c4c3662d08c482f99ea9d7a`.
- Native: original reaggregation equals official bytes; 230 suites, 5340 counted,
  5339 passed, one specifically allowed Windows GDI skip. Official and fresh
  registry-only negative controls contain real AssertionError 0/1/0.
- Browser assertion passes: space 242, assembly 150, documents 47, grid 356,
  timber 79, canvas 2267. Canvas 85 sections match the current source golden;
  original full scope is complete with no filters/modifiers/skips.
- Architecture: the original three command receipts have exit 0; the full
  604-input closure, scanner, manifest, scripts and raw stream hashes match.

The canvas workflow appends one chained server request BrokenPipe traceback
after `CDP_RESULT`. It is retained in
`independent-review/pr340-canvas-server-diagnostics.txt`; the cause of socket
closure is not established. It is not an additional uncaught browser exception
or a failed controlled assertion in the original result.

Machine evidence: `acceptance.json`, `mutation-verify-receipt.json`,
`mutation-local-cache-probes.json`, and
`independent-review/pr340-terminal-adversarial-review.json`.
No product suite, compiler, browser or downloaded binary was executed locally.
No source, PR, comment, base or CI invocation was changed. Source is clean.
