# Grid control diagnostics gates (2026-10-14)

All three gates tested `b7b239e94c5813218cb3c5374aa0ae36c5a47227`, with identical before/after HEAD. Base main is f9ada220. Evidence commit comes after completed gates; no mid-test commit.

Native: 88 suites, 2775 pass / 0 fail / 1 named allowed Windows GDI skip, Node703/703, parent exit0, 654.294 seconds. Original runner/expected unchanged. Archive contains 201 native raw members with exact bytes/SHA manifest.
Canvas: full, 2207/0/0, completed=true, golden matched (section assertion counts, not pixel comparison), parent exit0, 1881.587 seconds. P87=60. Original uncaughtBrowserExceptions=1 is the expected P38 fb-auto-probe; preserved, not erased.
Grid: GRID_SYSTEM_ONLY partial scope, 346/0/0, completed=true, parent exit0, 468.378 seconds; no full-canvas golden comparison.

Before/after samples cover 441 selected tracked code files and five binary hashes, identical. Runtime/probe captures are startup observations on distinct services/profiles; not continuous monitoring. Sidecars are supplied but executable bytes are not; do not claim independent binary re-verification.

Diagnostic oracle extracts real makeCtl/ctl into actual Chromium DOM. It records internal before/fixed/removed/restored oracle false/true/false/true; parent baseline/fixed actual exits1/0. Sleep/click are recorders. Success and Missing traces match exactly. Initial helper aggregation KeyError is preserved. This proves diagnostic data, not historical P87 cause or product recovery.

No product C/include/ledger/runner/expected edits relative to main, no new executable suite or core mutation coverage, no WSL. Native aggregate does not replace separately required owner/browser suites. Service wrappers stop only their own services.
