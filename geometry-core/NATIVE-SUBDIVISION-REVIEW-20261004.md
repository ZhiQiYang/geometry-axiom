# Independent review — REPEAT-only source subdivision

Verdict: **PASS for the current native diff and both review repro fixes.** This is a new review of frozen C `f0a185df8a8a5e15d792fad7f35fcd1a68d38478` against `90dd2ff`; the earlier `/tmp/subdivision-final-independent-review.md` describes a superseded, broader source-kind scope and is historical evidence only.

Native source include closure: `252befe533dd26cdede2735ec1c596cfb19787efabf487ad6a572f5522452351`.
Unchanged 139-scene oracle: `eb5a850003998f3e2a5ca67dbbe56dc3d15038c0f19205bba36311c92fad3f63`.
Microchecks used the actual registry-fresh `/tmp/geometry-tests/bridge` built 2026-10-04T05:51:01Z, with the ordinary 8 MiB stack. No repository code/tests/floors were edited.

## Scope and source-kind guards

PASS. [D19a](../公理層.md), [I25a](../公理層.md) and [the amended native contract](GRID-SUBDIVISION-NATIVE-CONTRACT.md) now limit new or retained source rules to two nonstagger `GRID_SRC_REPEAT` axes. This review accepts that latest restricted handoff scope; it does not certify REPEAT_PANEL source-rule support.

Both the full source-rule validation guard and query/dereference target guard require the exact repeat kind: [grid_subdivision.inc:20](grid_subdivision.inc), [grid_subdivision.inc:128](grid_subdivision.inc). Unconfigured rules and source edits retaining existing rules pass through the full candidate guard. No source auto-conversion was added.

Only `current_geometry.c`, `grid_subdivision.inc` and `grid_subdivision_query.inc` have C changes from `90dd2ff`. The original grid_systems, grid_bindings, grid_lattice, references and transactions implementations are unchanged. Therefore existing REPEAT_PANEL sources/bindings/grids, legacy stagger, D11/R6 support and anchor semantics are not redefined by this diff.

Actual microchecks passed: either axis using a divisible 917 mm REPEAT_PANEL pitch rejects rule creation with `SOURCE_KIND`, while its ordinary exact grid query succeeds. Changing a source with an existing valid REPEAT rule to REPEAT_PANEL rejects and retains the complete definitions. The retained one-level selectors, 1..65 exact divisions, source-local keys/highwater, compound refs, manual conflict checks and atomic support/reference rebuild are unchanged.

## Scene encounter flag lifecycle

PASS. [g_rule_scene_encountered](grid_subdivision.inc) is parser-local transient state, not a World/history field. It is set only when rule/highwater handlers are entered while parsing a scene: [rule handler](grid_subdivision.inc), [highwater handler](grid_subdivision.inc). [parse_scene_file](../current_geometry.c) clears it at the start of each successfully opened input file.

[Scene integrity](grid_subdivision.inc) checks encountered syntax before deciding that final World usage is empty. It therefore enforces the capability marker for a default-only `next 1`, a source later deleted and a World reset later in the same file. Keeping encounter evidence through delete/reset is intentional lexical capability enforcement, not persisted identity or geometry. The existing highwater slot maintenance and native candidate-load restoration remain unchanged.

Actual microchecks passed for all three marker-less scenes (default allocator, later-deleted source, later reset), with old definitions and pending confirm/undo preserved. A marked default-only file then loads successfully; the next ordinary legacy file without new syntax also loads successfully, demonstrating no cross-load flag contamination.

## Whole-cell sampling termination and required counts

PASS. [The updated preflight loop](grid_subdivision_query.inc) retains whole cells and unchanged line identities. Ordinal zero is always selected; a stride at least the required cell count selects only that first whole cell. If that cell alone exceeds 4096 segments, [the terminal guard](grid_subdivision_query.inc) returns `QUERY_CAPACITY` rather than repeatedly growing stride to overflow.

For segment count S>4096, `factor=ceil(S/4096)` is at least two. For positive required cell count R, the loop maintains `1 <= stride <= R`. [The clamp](grid_subdivision_query.inc) multiplies only when the product is at most R-1; otherwise it assigns R. Every retry strictly increases stride, so at most ceil(log2(R)) retries can reach the terminal selection. Arithmetic cannot overflow in this update. Zero matches return before the loop. Exact and sample limits and all selected inner lines remain intact; no inner-line thinning was introduced.

The required segment count is obtained from complete selected-cell preflight and `segments_counted` is set before capacity refusal. Required cell count is retained throughout. Allocation/write JSON still begins only after a successful preflight; failure does not alter World, history or pending confirmation.

Actual numerical microchecks used `/tmp/grid_subdivision_unthinnable_4232.json`: eight legal comb holes, 65x65 divisions, 64 vertical lines x 65 visible intervals = 4160 vertical segments plus 72 horizontal segments = 4232. Cell, exact rectangle and sample rectangle each return `QUERY_CAPACITY` with requiredCells=`1`, requiredSegments=`4232`; a two-cell sample request terminates with requiredCells=`2` and requiredSegments=`4232`. Each query completed in approximately 0.4–0.9 ms in this run. All definitions remained unchanged and the pre-existing confirmation and undo succeeded. The baseline `/tmp/unthinnable_before_fix.log` records the old sample overflow and old missing-marker acceptance; it is not new PASS evidence.

## Capacity/stack and verification boundaries

No new automatic arrays, World fields, recursive call chains or heap structures are introduced in this diff. The new bool is static parser state; the existing stride/count locals remain uint64. The reviewed shared clipping capacity remains 288 and the source-query segment budget remains 4096. Previous measured stack sizes apply to the unchanged clip buffers; the fresh microchecks run at 8 MiB. No additional stack measurement was necessary for this scalar/guard-only diff.

Microcheck artifact: [subdivision-repeat-only-review-microchecks.log](/tmp/subdivision-repeat-only-review-microchecks.log). Final `git diff --check` passed. Root owns the fresh full-strict/SAN and production oracle integration, including the three new regressions; they are not fabricated by this review. `.gcanvas` attachment/schema/history and full UI acceptance remain external integration-owner deliverables.

**No native review blocker remains.** The fresh mutation partition below completes the authorized independent execution check. Earlier 48-result metadata was not reused for this source closure.

## Fresh actual mutation partition B

PASS. The unchanged `tests/mutate.py` runner executed M17..M32 at the default 8 MiB stack. A private source-identical checkout at `/tmp/subdivision-repeat-only-source-b-rsl3e8s3` used genuine shared Git objects with detached HEAD `f0a185df8a8a5e15d792fad7f35fcd1a68d38478`. All 23 native include-closure files were compared with that commit (CRLF normalized to LF) before compiling. Native source closure was verified unchanged after execution.

The baseline was freshly compiled and passed 139/139 scenes. All 16 selected mutation compilations exited zero. Actual results were 14 killed, one crashed (M20), one equivalent (M23), and zero survived, invalid, stale or blocked. M20 reproduced SIGSEGV exit -11 on `_test_lshape.scene` on three actual attempts after a passing baseline; its crash classification remains distinct from an assertion kill. M23 was actually compiled and executed for the declared equivalence audit.

The source-fresh selected-16 `check_pass(require_execution=True)` exited zero. Each receipt records frozen HEAD f0a185df, source closure `252befe533dd26cdede2735ec1c596cfb19787efabf487ad6a572f5522452351`, unchanged scene oracle `eb5a850003998f3e2a5ca67dbbe56dc3d15038c0f19205bba36311c92fad3f63` and unchanged mutation tool `25b6f6841655b71e22a3eb078dbcda016b4c5885bcd35b821a7b085338599a9d`.

Fresh artifacts: [actual receipts](/tmp/subdivision-repeat-only-mutations-b.json), [execution log](/tmp/subdivision-repeat-only-mutations-b.log), [selected strict verification](/tmp/subdivision-repeat-only-mutations-b-check.log). Root owns the final A/B/C merge and full-project strict gate. No repository source, test, floor or runner was edited by this review or execution.
