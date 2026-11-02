# One bounded private pilot — plan ready, samples UNRUN

Fixed primary source is F340 `edf556eedc204bb285fb4504e246e4310f4e1e88`,
not new main `fca3f1a80f1dab564f5dd4c01c9e1226eaf09e2d` and not a future
340 merge. v1 and v2 cannot be relabeled to a later source.
Root must review this plan before any samples start. Timed/counter pilot
drivers and their binaries are not yet built; their exact new input seal is
required before the performance window can begin.

## Fixed scope and cost

Exactly12 groups: C/Rf/Rj × the existing U/S/D/X replay. Each group contains
one uninstrumented timed call in one fresh process and one separate work-only
call in one fresh process: at most24 child invocations, no warm-up repeats,
R8/R16 retakes, best-of selection or adaptive extension. The original eight
C subjects and36 v1 functional executions are not rerun. No Chrome, bridge,
full native suite,512-member World, mutants or full14/41 controls are run.

Compilation, source checks and sealing finish before requesting the exclusive
performance window. All use original NativeBuild compile/link flag generation,
O0 and300-second build limits; no build is included in subject timing.

Expected execution is under5 seconds from the v1 workload sizes; this is a
planning estimate, not an observed result. The exclusive execution window is
at most60 seconds. Stop launching children once30 seconds of the cohort have
elapsed. Any last launched child retains its full original20-second deadline;
the original cleanup can use at most5 further seconds. Reserve the remaining
5 seconds for bounded status/raw finalization. Unstarted groups are UNRUN.
This is a global diagnostic budget, not a speed acceptance threshold or a
change to the original per-subject deadline. No retries or extra samples are
permitted after a timeout, crash, invalid oracle or input mismatch.

The predetermined group order is:

```text
U:C U:Rf U:Rj S:Rf S:Rj S:C D:Rj D:C D:Rf X:C X:Rj X:Rf
```

Within every group run timed first, then work-only. Root releases one local
performance slot; no other local CLI, hashing, packing, build or Chrome task
runs during the sample window. Verify the complete externally anchored seal
before opening that window. Hash raw outputs and verify inputs again after
closing it. No background monitor or continuous watcher is added.

## Same inputs and output oracle

The four recipes, independent returned counts128/126/2/2, complete nine fields,
ordering and uncollected-tail sentinel are precisely those in v1/replay.c and
v2/FIXTURES.json. World capacity stays64/8; X is only the original helper's
large caller-buffer contract. No new geometry or numerical threshold appears.

Use the exact uninstrumented v1 C/Rf/Rj objects for timed collector execution,
with only an external driver placing timer reads around the one collector
call. Original fixture assertions remain unchanged. The work-only object is
a separately instrumented private source copy. Its reversible patch must
remove to the exact respective C/Rf/Rj source hash. It runs the same replay
and independent literal oracle. Compare its returned count, ordered nine
fields and tail to the uninstrumented result as well. An instrumentation
or baseline semantic failure is invalid evidence, not a product regression
or a killed optimization.

## Measurements and their limits

Primary CPU/wall use CLOCK_MONOTONIC and getrusage(RUSAGE_SELF) immediately
before/after the uninstrumented collector. Keep world/fixture construction,
assertion checking and output serialization outside that interval. Also
retain whole-child user/system/wall/ru_maxrss/actual exit, with Linux maxrss
units KiB. Whole-child figures include setup/oracle/serialization and are
reported separately. Both use the original16MiB stack. No counter-instrumented
CPU/wall number is promoted to uninstrumented performance.

Work is a vector, never a weighted scalar: admitted faces and actual route;
contact_order/contact_earlier calls; bitmap initialization/writes and inactive
skips; fallback pair visits/full-cover checks; duplicate removals; final
compaction scans/moves; memmove calls/actual bytes; indexed sort/plane-compare
calls and Fenwick insert/query node visits where present. Missing mechanisms
are N/A or zero observed as appropriate. The exact counter inventory and each
source anchor must be reviewed and sealed before any work call. This vector
does not claim to count every CPU instruction.

One observation per group cannot establish statistical significance. Preserve
all raw values, zero benefit, regressions, quantization and noise; if timing or
RSS granularity cannot resolve a difference, report UNMEASURABLE. Do not repeat
to obtain a favorable number. Shared driver/storage and page granularity may
hide a bitmap storage change; zero observed RSS delta is not zero storage.

Rf isolates only the nonindexed341 route and retains its active declaration;
U/S still retain343, so no standalone341 benefit follows there. Rj withdraws
the341+343 indexed pipeline while preserving uncalled helpers and common
unique bookkeeping; it is not a full343 cost withdrawal. All results are
private diagnostics, never formal341 B1, old R16 acceptance or512-World proof.

## Next exact action

Root reviews v2 and this plan. Then prepare only the small external timed
driver/work-copy instrumentation, compile outside the performance window,
and seal their actual source/inputs/flags/env/tool/objects/binaries plus the
fixed24 invocation schedule before their first call. If that preparation
is valid, report the seal and READY_FOR_ONE_PILOT and wait for root's explicit
window release. The current plan alone is not execution readiness; all cost
and work values remain UNRUN, and no samples have started.
