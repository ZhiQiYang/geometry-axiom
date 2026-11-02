# Local canvas integration checkpoint — A → E → canvas

Local branch `codex/canvas-validation-20261102`, worktree
`/tmp/geometry-canvas-shards-20261102`, fixed clean HEAD:
`e45670d9bb864dcf6b5a07fd4ccf11c188e54818`.
Nothing from this integration was pushed and no PR was opened. The original
canvas commit and its `codex/canvas-shards-20261102` branch remain at
`6c7a7b1ece271f0f3e66fdbb361f55c49c8e7343` unchanged.

## Actual ordinary merge chain

| Commit | Actual parents |
|---|---|
| `86282523501608c7fdece026ab529182e668f840` | `502a64ff6214dd6060927b7f14643a533536f20d` + R06 A `e9f4dd75cfd4eb9965e3af249200b918907d62db` |
| `93c1553d3254abd65f3147eb6802b4e8c5f0deab` | `86282523501608c7fdece026ab529182e668f840` + recovery E `503cfc59354893859ae9e6e4a6ab7c11d7972517` |
| `f79e94dd20f7a5a57175d9d8e539499f13dc7cd6` | `93c1553d3254abd65f3147eb6802b4e8c5f0deab` + canvas `6c7a7b1ece271f0f3e66fdbb361f55c49c8e7343` |
| `e45670d9bb864dcf6b5a07fd4ccf11c188e54818` | `f79e94dd20f7a5a57175d9d8e539499f13dc7cd6`; only two registry lines and the existing CDP LF pin updated |

`01-*` through `12-*` directories preserve exact commands, exits, stdout/stderr,
before/after status, unmerged stage records and copies/hashes of dirty source
bytes. Merge E produced only three architecture metadata conflicts; these were
resolved to A originals. Canvas produced one CDP tail conflict; it was resolved
to the original routing plus an explicit lazy R06 extension unit. No reset,
rebase, force operation or change to another worktree occurred.

## Preserved source contracts

- Manifest equals A apart from the existing CDP driver's actual LF SHA-256
  `14291f6f1114a9f4dd5ceaf3b6b02297b673870d5b903282fdd4090a31ff49e7`.
  Policy remains 985 identifiers / 55 strings; 335 owned / 272 excluded.
- App blob equals E, including successful recovery clearing connection.error.
  E's expanded P53/P61 proofs and A's allApi/expected-fault/full transport trace
  fields survive in both successful and fatal results.
- The legacy statement body is byte-identical to pre-canvas `93c1553d`:
  478,849 UTF-8 bytes, SHA-256
  `3abdbcc3e64fc5ecd9ab97c975bb2c0175e513246847f111d2cf1078fbc76077`.
  All 22 tail module calls retain their original order and argument source.
- R41 product/fixture/IO blobs equal A. Other product source is A unchanged
  except E's app and the canvas harness; the manifest changes only its allowed pin.
- The golden file equals A: 86 keys / 2317 assertions, R06=50 and P77=134.
  Legacy owns 62 / 898; extensions owns 24 / 1419. R06 is explicitly registered
  after assembly-context and before timber, with the original full/ASSEMBLY_ONLY
  predicate retained. No old 85-key universe was relabeled as this source.
- Expected values are the automatic merge of all A originals plus E's original
  connection_recovery=9 entry. Ledger bytes equal A. These are retained source
  records, not newly generated evidence for this integrated head.

Independent static peer `/root/pr366_evidence/tool_review` confirmed these
contracts and actual parent chain at fixed e45670d9; no confirmed blocker.
The peer did not run browser/native/mutation gates or modify source.

## Pure gate results and unchanged dependency evidence

`gates-e45670d9bb864dcf6b5a07fd4ccf11c188e54818/receipt.json` binds actual commands,
environment, SHA/tree, raw hashes and exits to this head:

- New Node shard tests: 19, exit 0, no skip.
- Original pure CDP tests affected by the floor/harness merge: 32, exit 0, no skip.
- Original architecture scanner: exit 0, 335 sources, 803 edges, diagnostics [].
- Original architecture unit and product tests: 205 and 18, exit 0, no skip.
- Current dynamic plan generation: exit 0, including the independent R06 unit.

Python 12 was not repeated without a changed dependency. The complete static
test/function/input closure is recorded in `python-control-closure.json`:
only the unchanged test/supervisor code imports read repository files; tested
data reads use isolated TemporaryDirectory fixtures. Both source_identity tests
mock every Git call and environment; real runtime_version/plan/node/run/verify
are uncalled. Python/stdlib imports and ROOT path are unchanged. The actual
12-test result stays attached to 6c7a7, not relabeled as an e456 rerun.

Both new suites are now registered with zero native dependencies. Their expected
entries have not been hand-filled; final expected/ledger adoption remains pending.
Historical architecture scan/report/receipt files remain A originals; the new
three-command evidence is this checkpoint's raw receipt, not rewritten metadata.

## UNRUN and resume requirements

Chrome shards, same-source original full canvas, real harness false-assertion
0/1/0, builds/native/full census and fresh mutations/official aggregate acceptance
are UNRUN. No such process was started during this merge task; root retains the
exclusive Chrome/native schedule.

Final R06 census/expected and recovery official ledger/source adoptions must
still be normally merged when root supplies their final commits. Recompute
current ownership, LF pin, full source identities and affected evidence after
those merges. Do not call A's ongoing census or E's ledger-freshness failures
green; do not turn either retained ledger into integrated execution evidence.

Erratum for the earlier checkpoint prose: its 438,940 figure was a character
count, not UTF-8 bytes. The unchanged original JSON correctly records 476,653
bytes for the original 502 comparison. The equality/hash evidence was correct;
the old source and raw/hash references have not been rewritten.
