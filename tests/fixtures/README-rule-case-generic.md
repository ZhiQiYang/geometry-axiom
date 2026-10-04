# Historical generic rule-case receipt

`rule_case_generic_immutable_receipt.json` is the complete
`fixed-version-immutable` row extracted from the real six-case CLI receipts at
module/code head `46c9a9dd4a011fa7a1771d98cc404dc870f300b4`. The cloud source file
was `/tmp/geometry-rule-cases-49/receipts-46c9a9d.json`; its SHA-256 is
`782d73d912e2b3e5e977279b34e08adc88b6d3bedf0884cba72fe0bf0da5f549`.

Only JSON whitespace/key ordering changed. All original fields are retained:
status/reason, actual and expected diagnostics, context/PID/elapsed conditions,
native/validator identities, assertions, full before/after states and dump hashes.
The stored generic rejection is `blocked / diagnostic-unavailable`, with actual
outcome rejected, unchanged World and passing predicates. It must never be
rewritten into a passed receipt when a later runtime supports precise diagnostics.

The extracted row is 5430 canonical UTF-8 bytes. Canonicalization here is
`json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
allow_nan=False).encode('utf-8')`; its SHA-256 is
`4ce979de844171ac995c2c71d37d0958416ce6255f95f1a0c5bd9bb305662493`.
This JSON receipt includes elapsed floating-point evidence, so this checksum
uses ordinary finite JSON rather than the integer-only case-definition canonical
encoder. No wrapper or extra saved format is introduced.

Tests load this as historical data, not as current runtime authorization. They
check its literal generic code/clause/no-ref, rejected outcome, unchanged native
states/revisions/dumps and original typed expectation. Refresh against the
currently registry-verified typed runtime must mark it stale with recordedStatus
blocked while preserving original scope and evidence. A forged passed label
must fail exact rejection validation.

Current true-native cases independently require six passes, including two
precisely rejected negatives. Wrong-diagnostic controls explicitly use generic,
missing-ref and wrong code/clause/ref values; they do not treat the now-correct
live diagnostic as a wrong control. Cancellation and missing capabilities remain
nonpass. These changes apply on the paired PR103 native head, not the older main
runtime that generated this fixture.

Validation on PR103 base `e8174f4d8b4e77bf1b8e0c2f8e18e994b1ec5634` plus these
test changes: the 86 rule-case tests and 8 native diagnostic tests passed together
(94 tests, exit 0, 3.210s). Independent read-only review reran the five changed
methods (5 tests, exit 0, 1.002s), with no blockers. The six-case CLI returned
exit 0: four accepted, two exactly rejected, all passed, six distinct PIDs and
all private directories removed. Fresh receipt evidence is
`/tmp/geometry-rule-cases-49/receipts-typed-case-tests.json`.

Registry-verified native source fingerprint:
`9193c6ac4d8000621fdfc59ceabf57996e9e2725bc5e5422e92847857d9ca258`;
binary SHA-256:
`8b9178227970a664b0ac1a8c2dbe92b7e0c6bfbd85a582d21925c1cef50a80fe`.
The partial shared runner also executed 94/94 pass, zero fail/skip, but returned
exit 1 because its expected manifest had not registered the four case suites
(catalog 14, definition 27, executor 40, request 5). That registration/full gate
remains the shared owner's work; this patch changes neither runner nor expected
counts, native source, executor code, transport, app or saved format.
