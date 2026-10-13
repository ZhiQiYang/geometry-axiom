# #212 Linux cloud sampling (partial evidence)

Source commit: `1a59208e8c07f5fd8d44d6510e218e16dcc473c8`.
Claim commit: `e047028e72f4104edc2d381b97e4bac68c2e9d56`.
Board blob: `1dc3c49853af76c184020128192306c96be1d469`.

## Verdict
Not reproduced; inconclusive. This is Linux overlayfs, not WSL/ext4.
No observed failure, no matching-before/restore ctime collision, no justification for A/B patches or mutation claims.
This does not resolve the review blocker requiring the original filesystem and a passing unified-runner baseline.

## Source provenance
Git clone via git.chatgpt-team.site failed (exit 128, missing username); public GitHub transport was unavailable.
Files were fetched at the exact source commit using the GitHub connector into a partial source snapshot, not a Git checkout.
Every file listed in exact-source-manifest.json was byte-for-byte Git blob SHA matched before the final run.
The probe faithfully records git rev-parse/status exit 128. The remote SHA above is independently retrieved provenance, not a fabricated local HEAD.
An initial run had extra final newline in transferred files; it is not delivered as exact-source evidence. Files were restored byte-exactly and the entire experiment rerun. Only exact-* results are retained here.

## Commands and results
Each command used Bash `ulimit -s 16384`; soft/hard limit 16777216 bytes.
- `python3 tests/diagnostics/binaries_ctime_probe.py --iterations 200 --samples 10000 --temp-root /tmp --output ../evidence/exact-ctime`: exit 0; control 200 pass / 0 failure / 0 error / 0 skip; observed same; complete telemetry 200/200.
- `python3 tests/test_binaries.py`: exit 0; 32 tests passed, 0 failures/errors/skips, 0.092 s. This uses the original unittest setup/assertions/cleanup and mock binary fixtures, not real native compilation.
- `python3 tests/run_all.py --build --only py:test_binaries`: exit 1. Partial snapshot lacks registered files and C sources. No selected suite was run; compile/registry errors are environmental, not a demonstrated product regression. Full unedited log retained. The direct invocation cannot replace this required baseline.
- Diagnostic pipeline synthetic tests: 14 passed / exit 0 (pre-final transfer-normalization); synthetic evidence alone does not support the ctime claim.

ctime calibration: 10000 deltas, zero 0, negative 0, positive 10000; minimum observed positive 2584 ns, maximum 325500 ns. Not a universal resolution claim.
Filesystem: overlayfs, fsync=volatile; underlying WSL ext4 behavior is not represented.
OS Linux kernel 6.18.44 x86_64 / glibc2.39; Python 3.12.14; GCC Ubuntu 13.3.0.
Original commands and metadata are in report.json.gz and exact-probe.log.

## Raw artifacts
The four exact-ctime *.gz files are lossless gzip of the unmodified JSON/CSV/log output, not summaries; decompress with `gzip -dk`.
Baseline/direct logs and exit files are plain text. No raw base64 is posted in a comment.

## Outstanding
A complete authenticated checkout and unified baseline are still needed. WSL/ext4 reproduction remains open, no local WSL was used, no 7-job run scheduled.
This upload changes evidence files only; no product, test assertions, timeouts, axioms, reader, or SketchUp changes.
