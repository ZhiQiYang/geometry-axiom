# PR344 formal full-canvas fixed / withdrawn / restored plan

Status: **static scheduling correction only; nothing in this plan has run**.
Wait for root to close R06's census and verify #344's official mutation ledger,
then pin the resulting complete source SHA before preparing the browser window.

The governing [review6398950277](https://github.com/ZhiQiYang/geometry-axiom/pull/344#issuecomment-6398950277)
B1 requires **complete canvas fixed / only withdraw the app error-clear line /
restored**. Formal acceptance therefore uses the original full
`geometry-web/cdp_test.js` three times, serially. No `_ONLY` scope, engineering
modifier, from-P31 filter, golden update or added skip is enabled.

Known publication E is `503cfc59354893859ae9e6e4a6ab7c11d7972517`. Earlier
Node 9 controls and architecture 205/18 actually executed at S
`eccebabc85acf74e30274b8ea8e24db863d8843b`; they remain bound to S. If official
ledger adoption changes E, the formal browser fixed/restored source is that new
root-pinned SHA **F**, not an assumed old head. The exact 40-character F must be
recorded before any service/build/browser starts.

## Three independent clean phases

| Phase | Clean source | HTTP | CDP | Output root |
|---|---|---:|---:|---|
| fixed | dedicated clean worktree at F |18844|9344|`/tmp/geometry-resume-20261102/pr344/full-canvas/fixed`|
| withdrawn | dedicated clean local control commit V, parent F |18845|9345|`/tmp/geometry-resume-20261102/pr344/full-canvas/withdrawn`|
| restored | independent clean worktree at F |18846|9346|`/tmp/geometry-resume-20261102/pr344/full-canvas/restored`|

V changes exactly one occurrence in `geometry-web/app.js`:

```text
connection.phase = "ready"; connection.known = true; connection.error = "";
→ connection.phase = "ready"; connection.known = true;
```

Every other app byte and every other Git entry—including original CDP checks,
golden, fixtures, expected, ledger, SSOT and tools—must equal F. Record V's full
SHA and the one-line diff. A clean private control commit is necessary because
the original release gate rejects a dirty source before it reaches the browser.
Do not alter the publication branch, substitute a runtime refusal for the three
assertion failures, or commit/push V to the publication branch.

Restored uses a new worktree at F and a new server/profile/runtime; it does not
reuse V's browser storage, server or modified file. Final publication source and
its index remain untouched. Preserve F/V/F Git tree identities and raw hashes
before and after each actual phase. No reset of a user service is involved.

## Original command and 35-minute bound

Use existing `tests/release_gate.py --timeout 2100 -- <Node24> geometry-web/cdp_test.js`.
That is the original full canvas command with the original 35-minute command
limit; run one phase to a terminal receipt and cleanup before starting the next.
Do not increase 2100, reduce coverage to fit a short window, or run the phases in
parallel. Allow up to 105 minutes for the three browser commands, plus separately
scheduled private build/startup prechecks. No duration under 10 minutes is claimed.

For each phase, set these task-local values to the corresponding table row.
`PR344_SOURCE_ROOT` and `PR344_PHASE_HEAD` must be that exact clean F or V root
and full SHA; the placeholders are to be filled from root's future pin, not run
as literal values. The following is a **planned command**, not an execution:

```sh
PR344_SOURCE_ROOT='<exact clean phase worktree>'
PR344_PHASE_HEAD='<root-pinned full F or V SHA>'
PR344_PHASE_ROOT=/tmp/geometry-resume-20261102/pr344/full-canvas/fixed
PR344_HTTP_PORT=18844
PR344_CDP_PORT=9344

cd "$PR344_SOURCE_ROOT"
test "$(git rev-parse HEAD)" = "$PR344_PHASE_HEAD"
test -z "$(git status --porcelain=v1 --untracked-files=all)"
mkdir -p "$PR344_PHASE_ROOT/tmp/feedback" "$PR344_PHASE_ROOT/tmp/screens"
export TMPDIR="$PR344_PHASE_ROOT/tmp"
export GEOMETRY_FEEDBACK_DIR="$TMPDIR/feedback"
export GEOMETRY_TEST_URL="http://127.0.0.1:$PR344_HTTP_PORT/"
export GEOMETRY_CHROME=/tmp/google-chrome-local-20261102/opt/google/chrome/google-chrome
export GEOMETRY_CHROME_FLAGS=--no-sandbox
export GEOMETRY_CHROME_PROFILE="$TMPDIR/chrome-profile"
export GEOMETRY_CDP_PORT="$PR344_CDP_PORT"
export GEOMETRY_TEST_SCREENSHOT="$TMPDIR/screens/phase1-shell.png"
export GEOMETRY_GRID_SCREENSHOT_DIR="$TMPDIR/screens/grid"
export GEOMETRY_REPAIR_SCREENSHOT_DIR="$TMPDIR/screens/repair"
export GEOMETRY_TEST_BRIDGE="$TMPDIR/runtime/bridge"
export GEOMETRY_BRIDGE="$GEOMETRY_TEST_BRIDGE"
export GEOMETRY_MODEL_BASE="$TMPDIR/runtime/model-base"
export GEOMETRY_TEST_CORE="$TMPDIR/runtime/core"
ulimit -s 16384
```

Preserve inherited proxy, CA and runtime authentication variables; do not use
`env -i`. Explicitly unset **all** existing scope/modifier/update flags before
starting either the runtime or command. The current original list is:

```sh
unset GEOMETRY_ROOM_OUTLINE_ONLY GEOMETRY_TIMBER_SCHEDULE_ONLY
unset GEOMETRY_ASSEMBLY_ONLY GEOMETRY_PARAMETERS_ONLY
unset GEOMETRY_SELECTION_CURSOR_ONLY GEOMETRY_UX_REFINEMENT_ONLY
unset GEOMETRY_UIUX_FIX_ONLY GEOMETRY_MARQUEE_ONLY GEOMETRY_PROJECT_AUDIT_ONLY
unset GEOMETRY_ENGINEERING_WORKFLOW_ONLY GEOMETRY_GRID_SYSTEM_ONLY
unset GEOMETRY_INFINITE_FACE_ONLY GEOMETRY_COMPOSITION_ONLY
unset GEOMETRY_UI_REVIEW_ONLY GEOMETRY_REPAIR_ONLY GEOMETRY_FLOW_REPAIR_ONLY
unset GEOMETRY_REFERENCE_ONLY GEOMETRY_CDP_FROM_P31
unset GEOMETRY_ENGINEERING_EXAMPLE_ONLY GEOMETRY_ENGINEERING_NAVIGATION_ONLY
unset GEOMETRY_ENGINEERING_SUBGRID_ONLY GEOMETRY_CDP_UPDATE_GOLDEN
```

After root releases the window, start the official service in a dedicated
terminal/process, preserving its exact PID, command, stdout and stderr:

```sh
python -B geometry-web/start_local.py --port "$PR344_HTTP_PORT" \
  --binary-dir "$TMPDIR/runtime"
```

`start_local.py` officially builds/verifies **core, bridge and model-base** in
that private directory and enforces 16 MiB stack. Do not use R06's changed ELF or
the default shared cache. If reusing a separately verified main-equivalent
binary, retain the exact ELF/sidecar bytes and let the original freshness oracle
accept them against this phase's unchanged C closure; no hash editing or missing
sidecar exemption is allowed. Each phase still owns a private runtime path.

Before the test command, the unchanged official probe must succeed:

```sh
python -B geometry-web/runtime_version.py --probe "$PR344_HTTP_PORT"
```

The formal original test command is identical in all three phases, except their
explicit source/port/output paths:

```sh
python -B tests/release_gate.py --url "$GEOMETRY_TEST_URL" \
  --output "$PR344_PHASE_ROOT/gate" --timeout 2100 -- \
  /tmp/geometry-resume-20261102/pr363/node-v24.22.1-linux-x64/bin/node \
  geometry-web/cdp_test.js
```

Chrome 156 and Node 24.22.1 are root's supplied installations; only read/execute
them. The release gate's process-group timeout/cleanup remains unchanged. It
does not start or own the server: after each terminal result, stop and reap only
that recorded phase's server/Chrome children, preserving all raw outputs and
ELF/sidecar identities. Never blindly kill other browser/server processes.

## Fixture, ELF and identity prechecks

Before each formal command, record the following from actual files/processes;
none has been asserted to have passed by this static plan:

- free phase ports and fresh, non-reused output/profile/feedback directories;
- actual Python, Chrome and Node executable paths/versions; 16 MiB stack;
- F/V/F clean Git head/tree/status, app, original `cdp_test.js`,
  `cdp_floor.js`, `cdp_sections.golden.json` and every declared fixture Git/raw
  identity, including `tests/reference_pdf_fixture.js` and original public
  assets/examples/documents exposed by `runtime_version.py`'s route catalog;
- presence and unchanged bytes of the vendored PDF.js/worker and archive assets
  referenced by the original app; no mocked PDF transport or substitute oracle;
- each private core/bridge/model-base ELF's type, size, raw SHA-256, executable
  mode and complete original fingerprint sidecar; original registry freshness
  accepted against the phase's source closure;
- `/runtime` schema/root/version/fresh/session/PID match this exact phase and
  source, plus recorded actual owned native child executable paths/PIDs where
  observable. A `/runtime` response alone is not ELF process attestation.

`tests/release_gate.py` already captures and compares clean Git/runtime/native
snapshots. Retain them and the actual raw inputs/outputs; do not replace those
checks with an assertion that an empty cache or successful build means fresh.

Each phase begins with a fresh synthetic app/test state. Preserve all original
fixture setup/reset/upload/dialog/Undo/Redo behavior and existing negative probes.
Full mode includes the original P38 feedback submission and its deliberately
injected `fb-auto-probe` exception. Keep the isolated feedback folder and that
expected exception's original assertions/raw count. Require zero **unexpected**
browser errors; do not rewrite its raw exception count to zero or add a skip.

## Terminal criteria and restore guarantee

Fixed/restored must each finish the complete original command: exit 0,
`completed=true`, `scope.mode=full`, `filters=[]`, `modifiers=[]`, `skipped=[]`,
`goldenCompare=matched`, exact committed `golden.sections`/`golden.total`, and no
failed assertions or unexpected errors. No result from FLOW mode qualifies.

Withdrawn must complete the **same full command** with the three named semantic
failures `P53-3`, `P61-10` and `P61-11`. Original golden remains active: lost passed
assertions in their original sections can also cause the original full golden
comparator's expected section-count mismatch diagnostics. Record these in raw
`CDP_RESULT`; do not disable golden, change its bytes, or pretend withdrawn had
`goldenCompare=matched`. Independently reconcile its named semantic failures and
unchanged comparator consequences; additional unrelated failures, runtime/source
rejection, crash or timeout do not count as the requested withdrawal proof.

The original release gate reports a nonzero withdrawn command as command-failed;
retain that exit and the canonical negative result, without labelling it a
positive gate. Before/after product/test/golden/native identities must remain
stable within every phase. Restored must return to exact F, rerun full to exit 0
and strict golden match, and leave the publication source clean. No whole PR or
full-native acceptance is inferred from these three browser commands.

## Optional diagnostic only

The existing `GEOMETRY_FLOW_REPAIR_ONLY=1` partial mode remains a possible
separately scheduled diagnostic. It covers P53–P66 plus P67/P68/P69 plugins and
contains the three target assertions, but its original mode does not compare
full golden. It is **not** the formal full-canvas S/V/S required by review B1,
must not replace any phase above, and has not been executed here.
