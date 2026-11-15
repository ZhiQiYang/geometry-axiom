# R22 App manual correction → Save → new-process Open

Prepared follow-up for draft PR #421; **not an App acceptance pass**. This adds
only an independent diagnostic. It does not change products, existing tests,
expected/golden data, CDP scopes, shards, registry, workflows or axioms. The
earlier component/native evidence in this PR is not reused as App evidence.

The flow under test is: import public PDF/PNG → calibrate → select one existing
face's outer-ring candidate → manually correct vertices and edge dimensions →
review → confirm → Undo/Redo → define placement/projection → UI Save → shut down
the owned browser and native service → new browser process and new native
service → New blank project → UI Open → inspect source alignment → preview the
corrected plane as a space boundary.

## Replay

Prerequisite: **the same authorized cloud environment** must provide a supported,
installed Playwright browser whose sandbox works without security changes or
extra flags. An authorized environment maintainer must resolve the current
provisioning blocker before this task can run. Do not switch executor, disable
sandbox, change helper ownership/mode, alter proxy/network settings, install a
browser opportunistically, or retry a known denied launch.

From the isolated checkout, using a new directory for each receipt:

```sh
node --check tests/diagnostics/r22_app_manual_review.cjs
node tests/diagnostics/r22_app_manual_review.cjs /tmp/r22-app-preflight-unique --preflight-only
node tests/diagnostics/r22_app_manual_review.cjs /tmp/r22-app-run-unique
```

The final command is for use **after** the environment prerequisite is met.
`GEOMETRY_CHROME` may identify an already provisioned, explicitly authorized
browser; it is not a fallback discovery mechanism. `GEOMETRY_CHROME_FLAGS` must
not be set. The runner uses `chromiumSandbox: true`, no `args`, and no installs.
It checks availability before starting services or compiling native programs.

Each scenario owns two sequential `geometry-web/start_local.py` processes on
unused local ports. That existing launcher supplies the repository's native
registry/freshness checks and established 16 MiB stack; the diagnostic does not
change these policies. The receipt records `/runtime` root, freshness, PID and
native session plus the official `runtime_version.py --probe` result. A new
browser **process** is launched after the first one closes. The service PID and
native session must change, and UI New must yield zero faces and zero sources
before Open. Merely opening a new tab/context on a surviving native service is
insufficient. Dumps are captured before stopping only owned child processes;
SIGINT exit/signal and remaining native children are recorded.

## Prepared assertions

All six cases are mandatory: rectangle, L shape and notch, each as real PDF
vector import and real PNG image import. Fixtures are self-authored public
geometry. No PDF operator-list, Worker, canvas-decoding, DOM or core mocks are
used. `evaluate` observes state/DOM or computes pointer locations; editing uses
actual click/fill/Tab/filechooser/download controls.

- Check exact cyclic candidate topology, independent of bbox/area; cancellation
  and invalid dimensions preserve formal geometry. UI Save must reject a
  session-only candidate. Calibration must not scale the formal face.
- Insert/deepen a notch or extend an L leg using the vertex editor, then change
  the first edge from 1960 to 2000 mm through its actual direct input row.
  The changed outline stays changed through the remaining flow. Every edge is
  filled and blurred; exact ordered vertices, displayed dimensions and cleared
  review are checked after edits. Formal native dump stays unchanged until
  explicit confirmation. An I8a dialog, if present, is captured and confirmed
  using its visible control, with pre-confirmation dump equality.
- Check exact confirmed vertices, source receipt, full native Undo/Redo, actual
  downloaded `.gcanvas` bytes and archive native scene. After fresh-process
  Open compare the full scene, complete ordered loops, source bytes/meta, page,
  crop, transform, calibration, receipt, placement and explicit projection.
- Independently compare the rendered SVG image transform at four original
  source points, then preview the corrected polygon using explicit bottom,
  height and wall settings. Volume/face-count checks supplement the exact
  topology checks. Preview must leave the formal scene unchanged.

The optional native OS pickers are hidden before navigation to select the
product's supported download/file-input path. This does not verify OS picker
UI. Screenshots, if execution becomes possible, contain only synthetic inputs
and stay in the output directory; no uploads or public sharing happen in the
runner. No physical phone/IME/private-PDF/human-efficiency claims are made.

## Outcomes and current route assessment

`receipt.json` records UTC, command, full Git SHA, worktree state, input hashes,
per-assertion results, console errors, service identities and cleanup. Exit 0
requires all six completed App scenarios. Exit 1 is an explicit assertion
failure; exit 3 is execution/cleanup failure. Exit 2 is **not started** (including
`--preflight-only`, even if ready). A missing executable yields zero App
assertions and zero browser launch attempts; it is not a product failure.

At preparation baseline `fd96b8bf7094bd57e74e3226aeba1f24a73b74fc`:

- #421 head `53ca7981dacce887f623a437a7b14b037e76ccaf`, Geometry run
  `43756680091`: nine actual jobs succeeded; browser matrix skipped due to path
  scope. Neither that scope decision nor old P cases execute this diagnostic.
- `integration-tests.yml` has no manual-dispatch entry and runs registered CDP
  scopes. This test-only addition does not wire this new scenario into that
  matrix. Do not edit shared paths just to trigger CI.
- `r11-canvas-context-menu-mutations.yml` supports a manifest input, but its
  runner hardcodes `geometry-web/cdp_test.js`. The `keep` path executes sandbox
  helper `sudo chown`/`chmod`; the other option adds `--no-sandbox`. Neither is
  authorized for this follow-up. It was not dispatched. R06 is a separate
  scope; Mutation evidence is not an entry for this App scenario.
- The default Playwright path was missing. System Chromium has the previously
  recorded invalid sandbox-helper ownership. No launch was retried and no
  restricted `/root/.cache/ms-playwright` inventory was retried.

The new run's raw preflight/command receipts live under
`tests/evidence/r22-app-preflight-20261115/`. They establish only environment
readiness and static preparation. The App correction/Save/cold-Open slice
remains unverified; this does not downgrade or replace #405's narrower existing
R22 evidence and does not elevate this new slice to L4. #54 remains open.
