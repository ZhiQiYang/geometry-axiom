# GEO-261 dependency gate evidence at 99455b9f

This is the **preproduction K/W/H dependency scanner fixture gate**. It verifies the
scanner and its synthetic owned-source fixtures. It is **not a final product
manifest**, a scan of the completed product, a native build, or a product acceptance
result. No C compilation or WSL execution was needed for this evidence package.

The tested source is `99455b9f73c4175c1154f7e7be514204019930b8`. The complete
synthetic baseline ran **205 tests: 204 passed, 1 Windows symlink capability skip,
0 failures, 0 errors**. The only skipped test was
`test_symlink_escape_is_rejected`; a skip is not a pass. The 43 focused guard-removal
controls produced **99 expected failing test executions and 0 errors**, exactly
matching their named expected failures. These are 43 separate scanner mutations,
not 43 product mutations and not 99 distinct new tests.

## Evidence and lineage

- `final-delivery-205.json` is the author's unchanged delivery receipt. It records
  the final commit, four source hashes, clean source state, and the raw mutation
  receipt hash.
- `architecture-comprehension-mutation-205/` contains the complete original
  baseline log, 43 mutation logs, 43 mutation diffs, and `mutation-results.json`.
  The mutation receipt honestly records HEAD
  `70ccab62d4fb3d3aba4dbac919f19ad3e4f8a7c8`: the tests ran against the modified
  worktree before the final source commit. Its four `inputsBefore` hashes match
  the raw input hashes bound to `99455b9f` by the final delivery receipt. The
  archived receipt was not rewritten to imply a postcommit run.
- `architecture-comprehension-root-proof-portable/` contains the independent
  root review receipt and full frozen baseline log. The reviewer loaded Git
  blobs from both commits, reproduced two false greens at `70ccab62`, then
  observed explicit `CORE_PATH_INJECTION` rejection for both at `99455b9f`.
  Its independent 205-test run used the two frozen Git blobs from `99455b9f`
  and also reported 204 passes and the same 1 Windows skip.
- `runners/` preserves the exact five mutation runners, v5 through v9, and the
  exact independent root proof script. The v9 runner loads v8, v8 loads v7,
  v7 loads v6, and v6 loads v5. Keep all five adjacent. Original absolute paths
  inside historical receipts describe the execution machine; the local copies
  are bound by basename and raw SHA-256, not by those paths.
- `artifact-manifest.json` records raw SHA-256 and byte count for every other
  file in this package. The repository's `.gitattributes` marks the whole
  package `-text`, preserving logs, diffs, receipts and runner bytes across
  checkout. Source receipt `lfSha256` values normalize only CRLF to LF when
  comparing Git blobs; original `rawSha256` values remain unchanged.

## Reproduce the checks

From a checkout containing the source commit and its history, verify the package
and compare its source bindings to Git blobs:

```powershell
python -B evidence/architecture-gate-99455b9f/verify_evidence.py --repo .
```

The verifier checks every archived file hash, all log hashes and reported counts,
the runner dependency hashes, both independent regression outcomes, and the
four final source bindings. It regenerates the 43 mutant source bodies and diffs
in memory from the exact archived runners and frozen scanner Git blob, checking
their recorded hashes. It does not execute the scanner tests or a product.

Re-run the independent two-version regression and frozen 205-test suite into a
new directory outside the source checkout (choose your own output path):

```powershell
python -B evidence/architecture-gate-99455b9f/runners/verify_architecture_comprehension_root.py --repo . --out "$env:TEMP/geo261-root-proof-new"
```

Re-run the original 43 mutation controls against an unchanged checkout of the
four source inputs from `99455b9f`, again choosing a new external output directory:

```powershell
python -B evidence/architecture-gate-99455b9f/runners/mutate_architecture_comprehension_v9.py.txt --root . --out "$env:TEMP/geo261-mutation-205-new" --expected-tests 205
```

The mutation runner refuses an existing output directory or one inside the
source checkout. It changes only temporary scanner copies and records source
hashes before and after. Logs from a fresh run can have different timing and
temporary-path text, so their hashes need not equal these historical logs.
The symlink test may execute on a host with symlink capability instead of
reporting the original Windows skip. No result here substitutes for the final
frozen product dependency manifest and its later acceptance gates.
