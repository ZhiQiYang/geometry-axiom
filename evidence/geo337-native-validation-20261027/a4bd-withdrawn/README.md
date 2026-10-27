# Withdrawn a4bd77e native execution — original failure retained

Executed SHA: `a4bd77e8090f5a82f0c8934c30c5335782293922`.
This execution began before the coordinator corrected the target to recovery F `cbf0fb621888596aa14ad5f2349b503e23b1b72d`. It completed safely and is not relabelled or counted as F acceptance.

- Original command: `ulimit -s 16384` then `python3 tests/run_all.py --build`.
- Full 230 suites completed; actual process exit 1; no timeout; elapsed 1882.5009 seconds (31m22.5s), within the 2100-second cap.
- Counted assertions/tests: 5329 total, 5327 pass, 1 fail, 1 allowed skip (compiled Windows GDI harness unavailable).
- Test failure: `test_assembly_mutation_check.AssemblyMutationCheck.test_run_logged_kills_the_whole_group_and_records_that_nothing_is_left`. Two killed sleep children remained zombies, adopted by container PID 1 (`tail`); unchanged assertion required `afterKill == []`.
- Separate exit-code-only failure: `mutation:check`, exit 1, stale mutation ledger. See original `mutation_check.log` in the archive.
- Fresh Linux binaries built from this checkout. No test, assertion, source, expected count, workflow, or timeout modified. Clean checkout after execution.
- Sampled output maximum: 7,122,944 allocated bytes, 5,487,416 logical bytes; five-second sampling, not an exact instantaneous peak.
- No mounts, symlinks, or SHM used. Compiler/tempfile scratch directed via TMPDIR to this receipt's `temp` directory; fixed native binaries/logs stayed at `/tmp/geometry-tests` during execution.

`stdout.bin` and `stderr.bin` preserve the full original streams. `native-output.original.tar.gz` preserves all native outputs, binary fingerprints, and suite logs. `REQUEST.json`, `RESULT.json`, and `samples.jsonl` record command/environment, identity, actual status, timing and capacity. `SHA256.json` is the original end-of-run manifest; later README, launcher copy and preservation receipt are separate additions.

After verification of every original manifest entry, the owned output directory was renamed to `/tmp/geo337-a4bd77e-native-output-preserved`. No original output was deleted. See `OUTPUT_PRESERVATION.json`. Only then was the recovery F run started with a fresh `/tmp/geometry-tests`.
