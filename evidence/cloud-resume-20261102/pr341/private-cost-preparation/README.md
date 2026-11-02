# Private #341 cost preparation — functional only

Fixed source: `edf556eedc204bb285fb4504e246e4310f4e1e88` (F340).
The source worktree, #341 branch/base and all public PRs remain unchanged.
This is not B1 acceptance and contains no CPU/wall/RSS cost samples.

`C.c` is the exact fixed `contact_world.c`. `R_fallback.diff` changes only
the ownership of the bounded bitmap/compaction route: the #343 indexed
route stays intact; the other route uses the existing immediate memmove
fallback. It retains the active stack declaration, so it cannot establish
bitmap storage savings. Unique-ID U/S are pipeline controls, not isolated
#341 benefit on this pair.

`R_joint.diff` replaces only F lines225–270 with the exact sort/dedup tail
at lines84–107 of true pre341 parent
`d1578d22f6d085ebd109ae1ce5a82b41c9d6a8a2`. This restores unconditional
stable insertion sort and original immediate deletion. It is a #341 plus
#343 indexed-pipeline withdrawal, not a standalone #341 comparison.
Uncalled #343 helper definitions and shared order-index `unique`
bookkeeping remain, so this does not restore every pre343 cost. Collection,
truncation, all public contracts and all other F source remain intact.
The historical whole823 source was not transplanted.

## Four same-input recipes

All constructors, literal geometry and expected fields come from the original
native fixture. No new geometric policy or acceptance threshold was added.

| Recipe | Input and independent expected output | Attribution |
|---|---|---|
| U | Original regions fixture's64 separated facts, IDs100+i, order64-i; no RC; expected128 complete ordered faces | C/Rf retain343; Rj compares combined pipeline |
| S | U, with fact1 footprint equal to fact0; strict original orders; expected126 faces, retaining earlier ID101 | Same scope as U |
| D | Original active-dedup generator's bounded64-fact prefix, same member42 pointer/orderi/rectangle0,0,100,27; expected final pair2 | Duplicate IDs select public fallback; eligible for fallback-local comparison |
| X | Original full MANY=2432/2+1 generator and caller cap2434; expected final pair2 and original uncollected tail | Existing large-public-buffer fallback, not increased World capacity |

The branch depends on admitted face count, not caller cap. World stays64
members/8 components; the helper accepts a pointer/count public view.
Returned count, all nine fields, order and uncollected tail are checked.
Discarded-but-previously-collected buffer bytes are not compared as outputs.

## Actual bounded execution

`PREPARE_COMMAND.json` records the successful private preparation command.
`POSITIVE_REQUEST.json` and `POSITIVE_COMMAND.json` record the actual original
NativeBuild compile/link invocation, source identity, exit0 and raw hashes.
The original `NativeBuild.compile/link` methods compiled only the necessary
five C implementations and client objects from a16-file/118494-byte copied
source/header/fixture closure. This is a smaller standalone link closure than
the original full native suite, not a claim to have run that suite.

Each of C/Rf/Rj ran the eight unchanged original C subjects and the four
private recipes once:36 actual normal exits0, original20-second subject
and300-second build limits, actual16MiB stack limit. All four recipe output
streams are byte-identical across variants after their independent literal
oracles and uncollected-tail checks. The original fixture was not edited.
No timer, work counter, peak-memory or performance sample was collected.

`POSITIVE_RESULT.json`, per-run stdout/stderr, original `build/build-log.json`
and `EXECUTION_INPUT_READBACK.json` retain the actual commands, hashes and
scope. The latter independently read back all16 fixed-source input copies,
the actual compiled variant/fixture/replay copies, original tool/import
closure and all six executed binaries;66 checks pass. Preparation-only
include/AST handling errors and a self-matching preflight probe were retained;
no C build or product execution had occurred at those failures.

## Unverified boundaries and next action

All14 original Python methods and41 named controls remain unchanged.
They were inventoried, not run here. `CONTROL_APPLICABILITY.json` distinguishes
missing anchors from helper anchors left textually present but unreachable
in Rj. Missing anchors, setup errors and unchanged optimization withdrawals
cannot be counted as semantic mutation kills.

Dynamic restored-C, full14/41 execution, runtime path instrumentation,
counter round-trip, collector-only timing/CPU boundaries, peak memory and all
four-class cost comparisons remain UNRUN. The current driver is a semantic
replay harness; timed/counter instrumentation has not been implemented.
The pre-execution request froze the preparation script and C/R variant
hashes; replay has a post-execution exact-copy readback, not a separate
pre-execution immutable manifest. Timeout partial-output capture was not
exercised; it must be fixed before formal samples. Completed36 runs did not
time out, and they were not repeated to test that unrelated supervisor path.

The next minimal action is root review of the two attribution scopes and
this bounded evidence. After #340 actually merges, freeze the real final
source and compare the complete input closure before reusing these functional
results. Then add a pre-execution input manifest and failed/timeout raw
capture to the private driver, followed by reversible work/timer boundaries
under the already proposed finite schedule. No formal #341 measurement,
branch update or publication is authorized by this preparation alone.
