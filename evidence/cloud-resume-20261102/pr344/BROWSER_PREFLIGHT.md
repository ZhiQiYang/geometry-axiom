# Pending original FLOW_REPAIR_ONLY S/V/S

Status: **preflight only; no server, Chrome, native build or browser command has
been started**. Root reserved the current local window for #363's census.

Publication candidate E is
`503cfc59354893859ae9e6e4a6ab7c11d7972517`; product/test bytes equal actual prior
Node/architecture execution S `eccebabc85acf74e30274b8ea8e24db863d8843b`.
The next browser execution must name E (and its separately identified withdrawal
variant), without relabelling S's previous receipts.

## Existing scope and limits

`GEOMETRY_FLOW_REPAIR_ONLY=1` is an existing `cdp_test.js` scope flag. It skips the
original guarded P1–P52 region and executes the original flow region P53–P66,
plus existing P67 marquee, P68 project audit, and P69 engineering workflow
plugins. It includes the three required original labels:

- `P53-3 重試只讀取，不重送修改`;
- `P61-10 載入未送達時，重試連線保留原幾何與來源`;
- `P61-11 載入已送達但回應遺失時，核對核心後恢復正確來源`.

For context only, the unchanged full-mode golden lists floors28/56/38/18/24/5/4/
96/36/160 for sections P53/P57/P62/P63/P64/P65/P66/P67/P68/P69, summing465.
These static floors are not a measured partial-run count or duration.

This existing selector is broader than only those three checks. No existing
P53/P61-only selector was found. No new selector, removed assertion, extra skip
or modified golden is proposed. The original result must declare partial mode,
and its existing golden behavior is `not compared (partial mode)`; this cannot
be called a full-canvas/golden acceptance result.

The integration workflow's original canvas upper bound is35minutes. The existing
`tests/release_gate.py` accepts an explicit timeout, so the planned original
CDP command uses `--timeout 2100` per phase. There is no measured execution time
for this new source/scope. A sub10-minute S/V/S total cannot be guaranteed from
static evidence; the strict upper bound is3×2100seconds plus startup/build.
Root should allocate the window after the priority census, rather than relying
on an invented short-duration estimate. A baseline partial run can establish
actual duration before the remaining phases are scheduled.

## Existing commands, not executed

Use a dedicated source root per clean phase. Fixed and restored roots must have
E's exact product/test bytes. A private withdrawal root must have only the ready
success line changed from
`connection.phase = "ready"; connection.known = true; connection.error = "";`
to `connection.phase = "ready"; connection.known = true;`. The original release
gate requires a clean Git root, so that isolated counterfactual must receive an
explicit local control commit and be recorded as that variant head; a dirty
working copy would be rejected before reaching the original browser assertions.
The publication branch remains E. No control commit is pushed.

For each phase, use its own HTTP port18844/18845/18846, CDP port9344/9345/9346,
feedback directory, browser profile and TEMP runtime directory. Start with the
official entry (example fixed phase):

```sh
GEOMETRY_FEEDBACK_DIR=/tmp/geometry-resume-20261102/pr344/browser/fixed/feedback \
  python -B geometry-web/start_local.py --port 18844 \
  --binary-dir /tmp/geometry-resume-20261102/pr344/browser/fixed/runtime
python -B geometry-web/runtime_version.py --probe 18844
```

`start_local.py` officially creates/verifies private registry-backed core,
bridge and model-base binaries and enforces16MiB stack. No R06 binary is reused.
All195 C build inputs equal main. Root may approve a private exact copy of a
fresh main-equivalent registry binary/sidecar, but its original freshness oracle
must accept it before any browser command. The default shared cache need not be
modified. No build is permitted during #363's priority census window.

Example original gate command, run from that phase's exact clean source root
after its original runtime probe succeeds:

```sh
GEOMETRY_TEST_URL=http://127.0.0.1:18844/ \
GEOMETRY_FEEDBACK_DIR=/tmp/geometry-resume-20261102/pr344/browser/fixed/feedback \
GEOMETRY_CHROME=/tmp/google-chrome-local-20261102/opt/google/chrome/google-chrome \
GEOMETRY_CHROME_FLAGS=--no-sandbox \
GEOMETRY_CHROME_PROFILE=/tmp/geometry-resume-20261102/pr344/browser/fixed/profile \
GEOMETRY_CDP_PORT=9344 \
GEOMETRY_FLOW_REPAIR_ONLY=1 \
GEOMETRY_TEST_BRIDGE=/tmp/geometry-resume-20261102/pr344/browser/fixed/runtime/bridge \
GEOMETRY_MODEL_BASE=/tmp/geometry-resume-20261102/pr344/browser/fixed/runtime/model-base \
  python -B tests/release_gate.py --url http://127.0.0.1:18844/ \
  --output /tmp/geometry-resume-20261102/pr344/browser/fixed/gate --timeout 2100 -- \
  /tmp/geometry-resume-20261102/pr363/node-v24.22.1-linux-x64/bin/node \
  geometry-web/cdp_test.js
```

The other phases change only their explicit root/port/profile/runtime/output
locations and their recorded app variant. Chrome156 and Node24.22.1 are the
root-provided executables; neither installation is modified.

Each phase preserves original app/test/golden bytes and Git identities before
and after, receipt-backed native identities, `/runtime` freshness, full command
streams and canonical `CDP_RESULT`. Fixed/restored require exit0, completed=true,
zero failed assertions, zero skipped groups and zero unexpected browser errors.
Withdrawal must finish with the three named assertion failures; crash, timeout,
source/runtime rejection or unrelated errors cannot substitute. The original
release gate classifies a nonzero command as failed, so its raw negative
`CDP_RESULT` and named failures must be independently read, not relabelled as a
positive release-gate result.
