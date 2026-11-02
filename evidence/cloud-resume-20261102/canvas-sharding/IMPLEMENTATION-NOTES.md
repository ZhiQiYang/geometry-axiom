# Canvas implementation checkpoint — not browser acceptance

Source commit: `6c7a7b1ece271f0f3e66fdbb361f55c49c8e7343`
(`Shard canvas execution with exact coverage receipts`), branch
`codex/canvas-shards-20261102`, worktree `/tmp/geometry-canvas-shards-20261102`.
The commit contains seven harness/tool/workflow/test/documentation files; no
product behavior, SSOT, golden, expected counts or mutation ledger was changed.
The worktree is clean and the branch has not been pushed.

## Correction to the initial static plan

Independent peer found that the initial PLAN's three inner gates would leave
late P57–P66 blocks executing in the extensions shard. The implementation uses
the complete original outer gate at old line 400 through its old line 7122
closure, preserving every inner lexical scope. The initial PLAN remains a
historical proposal; its inner-gate suggestion is superseded by this correction.

The original legacy statement body (old lines 401–7121) remains byte-identical
to source 502: 438,940 UTF-8 bytes. The original 21 tail module calls preserve
their order and argument source. Exact comparison records are in
`legacy-body-equivalence.json` and `tail-call-equivalence.json` and are explicitly
comparisons against 502, not a future R06/recovery acceptance claim.

## Independent adversarial review

Peer: `/root/pr366_evidence/tool_review`; two implementation rounds plus the
final commit-header regression review. The peer read the six implementation
code/test files and ran pure tests without Chrome, native binaries, API or CI.
The peer confirmed complete legacy ownership, original full/partial predicates,
lazy extension routing, the P83/P86 producer-consumer group, zero-count section
events, repeated-header ordinals, unique JSON keys, run/attempt/head/tree/raw
binding and actual parent-process exit handling.

The following review findings were corrected before commit:

- Require the original CDP_RESULT schema and successful original-golden shard projection.
- Bind the browser URL/port to the same isolated loopback runtime probe; require the original probe command and runtime root/version.
- Read merge parents from the raw commit object for shallow Actions checkout; only parse its header, so commit-message text cannot forge a parent.
- Label the saved false-verdict control accurately; it is verifier evidence, not the still-unrun real harness 0/1/0 browser control.

Final peer conclusion: no remaining confirmed must-fix in the reviewed draft.

## Fixed-commit pure evidence

`commit-6c7a7b1ece271f0f3e66fdbb361f55c49c8e7343/receipt.json` records commands,
environment, full SHA/tree, raw output hashes and exit codes:

- New shard contract tests: 19 Node tests, exit 0, no skip.
- New supervisor provenance/raw tests: 12 Python tests, exit 0, no skip.
- Original pure CDP floor/evaluation/settle tests: 32, exit 0, no skip.
- Current plan generation: exit 0; ownership derives from current golden/header closure rather than fixed historic totals.
- Original architecture CLI: expected unresolved exit 1, sole `EXCLUSION_DIGEST` for the edited CDP harness. The raw failure is retained. Root authorized updating only that existing LF exclusion pin after final upstream integration and source freeze.

Pending registry entries were reported to root, not silently added or counted:
`PY_NEEDS['test_canvas_evidence']=[]` and
`NODE_PURE_TEST_FILES['node:canvas_shards']='tests/test_canvas_shards.js'`.
Observed counts are evidence only; root will generate expected counts and the
fresh mutation ledger once for the final source.

## Explicitly UNRUN / pending

No actual canvas shard, same-source original full, or real harness false-assertion
0/1/0 control has run. No performance improvement is claimed. Root controls the
browser schedule because the R06 browser work is active and full canvas/perf
must be exclusive.

The final acceptance integration must use root-approved repaired sources in
the order PR363 → PR344 → this canvas implementation, with ordinary merges.
Its golden/header universe must be derived again after those merges, including
the new R06 independent section. This 502-based checkpoint does not re-label
the old 85-key/2267-assertion universe or past green runs as final acceptance.
