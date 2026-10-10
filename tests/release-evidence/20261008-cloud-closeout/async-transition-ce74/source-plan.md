# #173 successful edge submission and three-view transition supplement

Prepared before execution against source HEAD `5174a8dafd8c48329d7166abbd3d104e3c28c0c4`.
This is an independent private probe. No browser execution is authorized by this
file; the integration owner must assign the exclusive browser slot separately.

## Scope and source basis

Eight cases: 1400 px / 390 px × main object inspector / focused-face property
inspector × ordinary 4200 mm success / held-success-to-B. Each uses a fresh browser
context and native synthetic fixture A 731, 4000 × 3000 with a contained hole at
3000..3500 × 1000..1500, and independent placed B 732, 4000 × 3000. Both placements
are at z=2500; explicit canvas positions prevent renderer persistence from changing
the test World during the measured route. Setup uses native `reset`, `line`, and
`renderObjects`; setup is not represented as a product creation workflow.

The legal expected change follows D3 / D4 / I2 / I8: move only A's right exterior
edge from x=4000 to x=4200, preserving its hole, both placements, B, fixity and all
other persisted data. The expected complete dump is fixed from the initial dump by
one exact replacement of A's canonical boundary line. This is not inferred from
the post-submit output.

The input is `#mainEdgeLength0` or `#edgeLength0`. Submit with a real locator click,
Control+A, text insertion and Tab. Do not edit a sibling or leave a concurrent
draft. The native `line boundary 731 outline ...` reply is targeted only when its
actual stack includes `commitEdgeLength`; payloads are unchanged. The control
observes the response without holding it. The transition holds response JSON only
after the native successful commit has already happened.

For the face route, close an existing drawer with Escape, then click the real
`#workspaceBackButton` and await exit. For both scopes click the real `#btnObj`,
select B via a real click on `#workSurf` followed by Home / ArrowDown / Enter
(initial selection must be A), close its drawer with Escape when needed, click the real
Edit tool, and wait for B's actual `drawEditHandles` promise to settle. Do not call
`setView3`, `leaveFocus`, canvas handlers, `.click()` in page JavaScript or focus
methods to simulate this navigation. No forced clicks, sleep oracle or retries.
There is no three-view edge-length input; this probe covers a pending edge commit
transitioning into B's three-view editor, not direct edge entry in three-view.

## Fixed acceptance oracle

All cases require exactly one trusted original edge change callback, submitted
value 4200, exact expected native command and `ok:true` without preview. Wait for
that callback and every recorded handle draw promise to settle. Page errors fail
the case. Runtime and source identity changes invalidate the run.

Control: the still-visible input must have both value and defaultValue 4200; the
complete World must equal the predeclared expected dump. A native success alone
does not pass if the visible field or World is wrong.

Held transition: capture complete dumps before submission, while reply is held,
after B is fully drawn, and after A is released. Gate World must equal the expected
A-only change. B-ready and released dumps must equal gate World exactly. B must
have a positive handle count and its original 4000 × 3000 outer loop before release.
The observed trusted navigation sequence must be Back (face only), #btnObj,
#workSurf=732, Edit. Release A and await the original edge callback plus all draws.

Compare B before/after in three independent categories:

- Ownership: workSurf, view3, tool, editBid, editToken, oc.on, oc.edit, oc.focus.
- Visible presentation: preview group count and SVG content, handle count and SVG
  shapes, canvas visibility, workspace/inspector hidden state.
- Edit model: complete editLoops and editDrag.

Aggregate acceptance requires every category and complete World to remain stable.
If editToken alone changes while visible presentation and edit model remain equal,
report `ownershipTokenOnlyChange:true` and fail only the ownership category; do not
describe it as lost handles, wrong geometry or World corruption. Status text,
body classes and navigationSequence are captured for context but do not determine
acceptance. Node object identity is not an oracle; semantic SVG serialization and
the ownership token are compared explicitly.

## Evidence and execution boundaries

Before/after: actual HEAD, origin/main, both dirty diffs and short status, app and
space source, index and all top-level CSS hashes, exact probe/instrumentation/
wrapper/plan hashes, raw `/runtime` response and body hash. Save executable probe
copies, full native JSON and stacks, all World dumps including expected, per-case
raw JSON, Chromium version, screenshots and full Playwright traces. Wrapper retains
stdout, stderr, actual command, UTC times and exit code. Chromium uses existing
`/usr/bin/chromium` with `chromium_sandbox=True`. Require fresh runtime before
launch; do not alter services, policy, database or repository. Contexts and browser
close in `finally`; failures and precondition blockers remain recorded.

Existing original probes remain unchanged: browser_probe.py SHA256
`624db4fca454832bb9fbe3b0837571472ce6360baffef172486b2a27826e9dfd`;
browser_instrumentation.js SHA256
`83e8f28a97b4d03339d27f7646756e8d6bedd4e7f7f9745984d51e1dee54fb44`.
This supplement does not change their oracles, backfill their unknowns, or publish
anything. Physical devices, IME, save/reopen and operating-system dialogs are outside
this eight-case probe.

Planned invocation after the explicit slot grant:
`python /workspace/closure-evidence/async-review/run_edge_transition_probe.py browser-edge-transition-<unique-label>`.


Deadline supplement (prepared before any execution): each UI state wait is 15 s,
locator click 7 s, navigation 30 s, and Playwright keyboard/locator defaults are
30 s. Native fixture construction and full-dump evaluations have a 60 s fail-only
Promise.race deadline, preserving the original operation/payload/promise and
never using time as success. Read-only identity shell commands have 15 s bounds,
runtime HTTP 10 s. The held reply itself is released only after actual B-ready
draw completion; any earlier step timeout records a precondition/harness error
and closes that owned context without passing the scenario.
