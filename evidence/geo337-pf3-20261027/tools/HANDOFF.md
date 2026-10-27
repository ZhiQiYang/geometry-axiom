# Fixed-F PF3 complete mutation acceptance

Execution source `cbf0fb621888596aa14ad5f2349b503e23b1b72d`. Original producer exit **0**, no test/source/assertion changes. Started 2026-10-27T03:56:17.050481+00:00; completed 2026-10-27T04:08:42.851118+00:00; elapsed 745.697 seconds.

- Baseline: 20 passed, zero failures/errors/skips.
- Original 19 mutations: 19 killed by the named original assertion; each ran one test with one AssertionError, zero errors/skips. Every bridge differs from baseline. No compile failure, crash, timeout or identical binary counted as a kill.
- Restored: 20 passed, zero failures/errors/skips.
- All 21 source variants match the original source plus the exact producer-prescribed patch list. The host-identity case intentionally has the two original patches; the judge is unchanged.
- Original checkout stays clean at F; 205 input source files retain their original bytes. No remaining owned subject processes found.

Command: `python3 -B tests/pf3_mutation_check.py --out /workspace/scratch/geo337-pf3-F-cbf0fb62-20261027/subject --jobs 1`, from the fixed-F clean checkout. Stack 16 MiB. Original timeout is 900 seconds per build/test subprocess; original producer has no overall timeout. Full argv and explicit environment are in REQUEST.json. Scope authority is the original producer, PF3-NATIVE.md and the retained original formal command plan. D43/D44 and R42/R43 remain the behavior SSOT.

Operational capture only: private output/TMPDIR, exclusive owner lock and a process-local subreaper for this container's non-reaping PID1. No mount, symlink or shared native output rewrite. Source variants and binaries are private to this run. Previous native, oracle, reader and required-eight results were not rerun.

`subject.original.tar.gz` preserves every original source copy, ELF, fingerprint, full build/test stdout/stderr, execution record, result and summary: 4580 files, 93718659 uncompressed bytes. Every archived file was read back and compared with the retained original; SUBJECT_INVENTORY.json indexes exact hashes. VERIFICATION.json independently checks all 21 patch identities and all original classifications. Original stdout.bin/stderr.bin and the capture tools are retained separately. No original is deleted.

This is fixed-F cloud PF3 validation, with its own identity; the historical WSL results are not relabelled. It makes no claim about browser, Q38, P189 or remote CI acceptance. The next non-overlapping missing fixed-F scope is the original complete Q38 registry (SPM01–SPM44); browser remains assigned elsewhere.
