# #118 native cost audit — source 5e0e92b

Source SHA: `5e0e92b850209e9e2895612148694c1d1e1e4815` in
`/tmp/issue118-cost-audit-20261006`. Initial baseline SHA:
`11dc339152e05ea811972b8c0c15ff29520207cd` in
`/tmp/issue118-reporter-20261006/baseline`. Historical execution evidence is
the archived PR136 head `3019c036`, not an execution of either audit source.
PR149 and shared repository files were not modified by this task.

Methods: AGENTS/tests guidance already read at the same 11dc source; rg/AST
caller tracing; bounded pure read-only fingerprint profiling (five measured
samples per applicable binary, one excluded warmup; three raw-byte identity
samples). Imported only `tests/binaries.py`, with bytecode disabled. No tests,
native executable launches, builds, services, or browser runs. Each profiling
run completed in less than 0.5 seconds. Raw executables were read, never executed;
these component measurements are not acceptance or fresh-status receipts.

## Most concrete finding

The normal aggregate's demonstrated repetition is **freshness work**, not an
identified same-source/same-flags unused compile. Every `inspect_one` computes
the same broad C dependency closure again. `_scan_shared()` traverses each of
two native directories separately for `.c`, `.h`, and `.inc`: six recursive
walks per inspection, and exclusions are checked after `rglob` traversal.
`compute_fingerprint` then reads every included source's current bytes. For
core, bridge and model-base it also reads the main source a second time even
though that path already appears in the shared closure.

Exact source anchors: `tests/binaries.py:222–255` (scan and source reads),
`:284–330` (source/sidecar/raw binary verification), `:338–343` (require_fresh).
The closure is deliberately broad and part of the existing freshness contract;
this audit does not propose narrowing it or replacing hashes with timestamps.

## Actual caller chains and static call/byte bounds

| Chain | Proven behavior and source locations |
| --- | --- |
| aggregate → preflight | `tests/run_all.py:820` calls `inspect_all`; `child_env` at :297–298 exports all fresh native overrides. The merged `_unittest_runner.py:222–226` checks every populated applicable registry env before loading each Python test module. |
| bridge lookup → spawn | `_bridge.py:87–92` → `_lookup:53–66` → `_explicit:46–50` → `inspect_one`. `BridgeSession(explicit)` then uses `_checked_explicit:95–106` → `_explicit`, before `Popen:122–123`. `run_once:169–176` similarly verifies before a new child. These are launch guards, not compiler calls. |
| concrete adjacent bridge checks | `test_assembly_generation.py:14` calls `BridgeSession(find_bridge())`; for the 21 successful test setups this implies 42 freshness checks before the setup children, plus extra checks at explicit later child sites :78/:176. `test_engineering_core.py:20,26` checks once at class lookup and once per each of 18 setup children. |
| core helper | `test_cli_args.py:22–27` calls `require_fresh` on each `run_core` child. Its static POSIX successful full path has 22 calls, counting fixed loop cardinalities and the extra upper-bound help call at :82; this is not a runtime measurement. |
| model-base reuse | `modeling/base.py:106` selects explicit executable, then `GEOMETRY_MODEL_BASE`, before `_build_adapter`. `run_all` supplies this override. The fallback `_build_adapter:29–52` is already cached once per process and private; it does not run along the ordinary configured path. The bridge-only compiler-fallback test patches `_build_adapter` to return the registry binary (`test_model_update.py:124`). |
| rule-case identity | `rule_cases/runtime.py:27,31,47,49`: two source inspections plus two extra raw hashes per `runtime_identity`, or four raw binary hash reads on a successful path. `executor.py:440,480` uses that identity before/after each case and :459–463 verifies a copied child binary. Thus one complete case statically has four source scans, eight origin binary hashes and one copied-binary hash. The pre/post/copy guards are required evidence boundaries. |
| scenario identity | `scenario_verify.py:156–190` hashes raw bytes, then inspects; `_source_receipt` performs another inspection. `verify` calls these before work at :531–535 and again at :576–578. For each active runtime binary on a successful path this is four inspections, plus two explicit raw hashes. Records activate model-base in addition to bridge. Preserve both before/after checks. |
| model-update pins | `model_update.py:378–380` resolves/hashes base and bridge, then `_runtime` hashes them again. `:414` checks `_runtime` after the work. Therefore each runtime has three raw byte reads per successful prepare call, and producer/axiom hashes are checked before/after. Full native replay is separate work, not compilation. |

The exact preflight projection assumes a full POSIX run with all applicable
overrides fresh and all registered Python modules selected. It does not include
additional test helper lookups, deliberate tamper controls, child process import
work, sidecar text reads, or extra generated HARNESS AST reads. It is a static
budget, not an actual full-run counter or physical disk I/O measurement.

| Snapshot | Python suites | env inspections | duplicate bridge-alias inspections | logical source bytes | logical binary bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline 11dc | 46 | 230 | 46 | 253,210,266 | 84,470,720 |
| merged source 5e0 | 47 | 235 | 47 | 258,714,837 | 86,307,040 |

Both bridge variables are set by the same registry entry to one canonical path.
Five env inspections per suite are core + bridge primary + bridge legacy +
model-base + engjson. The merged runner's newly registered suite adds five
inspections; it does not alter the freshness implementation.

Each shared closure has 36 files / 987,043 raw bytes. The five env inspections
per suite issue 184 `_normalized_sha` calls and read 5,504,571 logical raw source
bytes; every subsequent `inspect_one` reads current source bytes again.
The extra bridge alias accounts for 48,368,217 source bytes and 24,824,648 binary
bytes across the merged 47-suite projection.

## Bounded component timings — not end-to-end speedup

Merged-source warm page-cache component medians:

| Binary | fingerprint ms | recursive scan ms | raw binary identity ms | source bytes per fingerprint |
| --- | ---: | ---: | ---: | ---: |
| core | 14.132 | 6.712 | 0.451 | 1,453,189 |
| bridge | 11.533 | 6.288 | 0.482 | 1,029,111 |
| integrity | 11.459 | 6.294 | 0.428 | 994,946 |
| model-base | 11.482 | 6.293 | 0.394 | 1,006,117 |
| engjson | 15.107 | 6.795 | 0.050 | 987,043 |

Sources/fingerprints stayed stable within each set of samples. All five native
fingerprints are identical across the baseline and merged audit snapshots;
profiling variation between the runs is not a code improvement. Instrumentation
adds small Python/stat overhead. The raw binaries read here have the listed
sizes but the profile does not issue a fresh-status verdict about shared cache.

Multiplying these component medians by the merged static preflight budget gives
about 3.00 seconds for source fingerprints and 0.09 seconds for raw hashes,
excluding other inspection work. This is a projection, not measured aggregate
time. Same-alias deduplication projects about **0.56 seconds**, so it cannot be
claimed as the cause or cure of an 87-second reader wait. Actual full-run
inspection counts, cold disk costs, Windows/SAC costs and optimization savings
remain **unmeasured**.

## Compile census: reuse versus required separate builds

`binaries.py:539–544` returns `reused` for a fresh registry binary before compiling.
The pending/SAC path at :553–556 retries the existing bytes without recompiling.
Postcompile source checks at :578,583,592 and atomic sidecar publication at
:595–602 must remain. Ordinary full aggregate with fresh binaries therefore
has no registry compiler call; a cold/stale full run builds the applicable
needed registry binaries once each. No ordinary unused native prebuild was
found; #122's removed prebuild is not being proposed again.

Archived `native-sidecars/*.fingerprint.json` records these build-stage durations:
bridge 10.3s, core 6.4s, engjson 0.4s, integrity 6.6s, model-base 7.0s; total
**30.7s**. `08-aggregate.log:3–7` says all five outputs were missing, so these
were necessary cold builds, not duplicate unused compiles. `build_seconds`
starts at `binaries.py:549` and includes compiler, smoke and integrity checks;
compiler-only time is **unmeasured**. Historical aggregate wall time was 363.113s
(`receipts/08-aggregate.json:13`), not the time of this audit source.

| Compile route | Classification |
| --- | --- |
| `test_engineering_json.py:97–107` | Aggregate uses prebuilt/require_fresh and returns before fallback compile :108–128. Direct standalone runs without override compile their harness once per class; potential repeated standalone cost, not demonstrated aggregate duplication. |
| `_timber_support_bridge.build:43–93` | A required instrumented bridge; generated source injects `__support_missing`, `__support_ambiguous`, `__support_free` at :63–83. `test_timber_support_projection.py:19` builds it once per class and tests invoke those controls at :242/:247. It differs from ordinary registry bridge source. |
| `test_model_update.py:447–463` | A separate required C projection fault (`if(t->id==0) count=0` at :456), with the support override explicitly cleared. It must not reuse the ordinary or normally instrumented bridge. |
| `test_rule_case_executor.py:589–604` | One small synthetic native control binary per class, distinct source/protocol behavior for crash/timeout/output boundary tests; needed for the control acceptance. |
| `test_binaries.py` | `setUp:36–43` mocks `_compile` and smoke, writing harmless fixture bytes. Static `build_one` calls in these tests are not real compiler work. |
| `test_mutation_freshness.py:185–199` | Compiler subprocesses are intercepted by fixture commands that write harmless bytes; no real mutant compiler can be inferred from those call sites. |
| normal aggregate `mutation:check` | `run_all.py:259–261` selects `mutate.py --check`; `mutate.py:1097–1117` checks saved evidence without compile or native execution. |
| explicit mutant tools | `mutate.py:533–558,561–585` rebuild on changed mutation/closure/flags or missing/invalid sidecar, reuse only verified `cache_state == hit` (:500–522). `assembly_mutation_check.py:45–54` deliberately compiles baseline and different mutated sources outside aggregate. These cannot be replaced by an unmodified binary. |

The archive gives whole-suite 10.25s for timber-support projection,
58.65s for model-update and 1.90s for rule-case executor. These include execution
and guard work. Exact instrumented/synthetic compile durations and native replay
durations are **unmeasured**, so the archive cannot assign those suite totals to
compilation alone.

## Minimal proposal that retains every freshness guard

First proposal: change only `_scan_shared` enumeration to one traversal per
native directory, pruning the existing `EXTRA_SCAN_SKIP_DIRS` while preserving
the exact current included file set, platform matching and symlink semantics.
Keep root include handling, relative path labels, command fingerprints and
CRLF normalization identical. Every `compute_fingerprint` invocation still
reads/hash-verifies all current included source bytes, and every `inspect_one`
still performs its raw binary hash and replacement checks. This removes
repeated directory enumeration without any process-wide source/hash cache.
Observed scan cost is about 6.3–6.8ms per inspection; saved time is **unmeasured**.
Validate file-set/fingerprint equality with pure source fixtures and retain
same-size/mtime tamper, replaced-during-hash, copied sidecar and cwd/PATH tests.

Separate optional small cleanup: inside one runner preflight invocation, resolve
both env aliases and group only identical `(binary kind, canonical path)` pairs,
perform one current-byte inspection per pair and assign the checked canonical
path to both envs. Different alias targets must still receive separate checks.
Do not carry the result into subsequent launch guards or cache it across tests;
`BridgeSession`, `run_once`, core/GDI helpers and receipt pre/post checks keep
their current-byte guards. Estimated alias benefit is only 0.56s for this warm
47-suite projection; this is not a measured implementation improvement.

If later optimizing rule-case/scenario raw-hash duplication, return the raw
identity just verified by `inspect_one` in its result and consume that identity
within the same pre/post observation boundary. Preserve both source inspections,
both raw-byte observations and the copied-child hash; never memoize an old
`fresh` verdict, trust size/mtime alone, bless sidecars from saved results, or
substitute ordinary bridge bytes for fault/mutant sources. This API cleanup is
a separate unimplemented proposal with small raw-hash cost in the current sample.

Deliverables: this report, `profile_readonly.py`, baseline `profile.json`, merged
`profile-merged.json`. No task blockers. No optimized code, compiler benchmark,
or new aggregate acceptance is claimed.
