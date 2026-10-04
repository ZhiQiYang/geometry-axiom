# #44 F1b validation and delivery

Validated on 2026-10-04 against main
`1075058be37d37b98a2a910f4f67b87583be85b3`, with the four product modules at
commit `37c1be5`. Later changes only document the PR100 contract mapping and
correct the owner patch's saved-source explanatory sentence. No existing
schema/store/history/app/native files are changed on this branch.
Latest main `8d08f1aceda7f26b6f05c64010f4b47a41df9c31` was then incorporated;
its #24 merge changes only assembly tests/evidence. The strengthened assembly
suite was rerun on that base: 35 pass, zero fail/skip, exit 0. Product modules
remain byte-identical; the older full-run count is not represented as a new-head
full run.

Draft PR: https://github.com/ZhiQiYang/geometry-axiom/pull/99.
Shared owner contract compared at PR100 head
`0230e436870ec3ba06fcb0735ffabc3b7427979d`; it is still a draft, not main.
The candidate mapping and owner-only wiring are in
`MODEL-UPDATE-INTEGRATION.md` and `MODEL-UPDATE-INTEGRATION.patch`.

## Focused acceptance

| Actual run | Passed | Failed / skipped | Evidence |
|---|---:|---:|---|
| Python producer with actual native bridge/model-base | 20 | 0 / 0 | `tests/test_model_update.py` |
| Node controller/history/import, including five true native cases | 36 | 0 / 0 | `tests/test_model_update.js` |
| Real app, real HTTP producer, desktop + 390px | 25 | 0 / 0 | `model_update_browser_check.js` |
| Actual owner-patch edit entry through native confirm | 1 flow | 0 / 0 | Saved model volume 36 → 37.8 m³, same ID, one undo |

The producer's tests retain real live engineering and assembly preview tokens
while isolated subprocesses run. They reject fixed-version changes, same-value
A/B version swaps, two-root swaps with an unchanged global version set, unknown
exact supports, unsupported capabilities, incomplete graphs and failed replay.
The controller checks mutable host-state aliasing, retained producer aliases,
changed history/context/source/runtime, replaced same-ID records, deletion,
cancel/duplicate confirm and reentrant store events.

The browser's successful candidate shows old 4000 × 27 × 33 mm and new
4000 × 29 × 33 mm, with volume 3,564,000 → 3,828,000 mm³. Preparing changes no
model, live World, dirty flag or history. Confirm replaces the complete record
once; one undo restores the complete old source/input/result while the current
native scene remains unchanged. Real ZIP export and fresh-context reopen pass
the existing native model verification. Source choices begin blank and identity
stays unknown. At 390px there is no horizontal overflow and visible buttons and
selectors are at least 44px high. No uncaught exceptions or console errors.

Ten browser races delay an actual successful HTTP receipt, rather than inventing
a receipt: cancel, close, native-source change, undo-history change, project
revision change, same-ID record replacement, deletion, project switch, cancel
during final replay and source change during final replay. Every case rejects
the old intent without adding an update. The positive path uses actual native
geometry; mocks do not stand in for native domain correctness.

## Broader regression in an isolated integration checkout

The owner wiring patch was applied only in `/tmp/geometry-f1b-integration`.
The four product modules and both focused test files there are byte-identical
to this branch. Full test registration exists only in that owner patch.

| Actual run | Result |
|---|---|
| `python3 tests/run_all.py`, all 57 suites | exit 0; 1734 pass, 0 fail, one named Windows-only GDI skip |
| `geometry-web/space_model_test.js`, default full-space scope | exit 0; 183 pass, 0 fail, completed, complete group census |
| Same script with `GEOMETRY_TIMBER_ONLY=1` | exit 0; 79 pass, 0 fail, completed; partial scope adds the two omitted timber groups |
| `geometry-web/cdp_test.js`, no scope filter | exit 0; 1970 passing assertions, 0 failures, 0 skipped groups; completed; all 82 section counts match golden |

The 1734 count already includes the 20 producer tests and 36 controller tests;
the focused counts must not be added to it. The full-space run explicitly omits
the two timber groups, which the separate partial run exercises. Overlapping
setup/font/health checks between those two runs are not distinct test totals.
The full runner retains main's existing #85 freshness checks and expected
counts; this branch does not modify mutation or its baseline.
The CDP result counts assertions, not end-to-end scenarios. Its single reported
browser exception is P38's declared `fb-auto-probe` expected exception; there
are no unplanned exceptions. No golden/expected counts were weakened to pass.

The final native test services use a 16 MiB stack. Earlier browser launch
attempts lacked Chromium's container flags; an earlier CDP service used 8 MiB
and its bridge stopped during P8v4. Those attempts are not pass evidence. The
final isolated services use 16 MiB and
`GEOMETRY_CHROME_FLAGS='--no-sandbox --disable-dev-shm-usage'`. An initial space
regression identified the missing saved-source explanation; the owner patch
now says `已保存的完整原來源`, and the final 183-check run passes unchanged tests.

## Reproduction and artifacts

```sh
python3 tests/binaries.py build core bridge model-base integrity engjson
GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge python3 -m unittest tests.test_model_update -v
GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge node --test tests/test_model_update.js
GEOMETRY_MODEL_BASE=/tmp/geometry-tests/model-base GEOMETRY_TEST_BRIDGE=/tmp/geometry-tests/bridge python3 -m unittest tests.test_assembly_rules -v
git apply --check geometry-web/docs/MODEL-UPDATE-INTEGRATION.patch
```

Apply the patch in an isolated checkout for the full registry/serve/index/edit
entry integration. Start its own server with the 16 MiB stack and actual native
binaries, a separate `/tmp` feedback directory and unused ports. Use
`GEOMETRY_TEST_URL`, `GEOMETRY_FEEDBACK_DIR`, `GEOMETRY_CHROME=/usr/bin/chromium`
and the container flags above for the existing browser suites. The new F1b
script also accepts `GEOMETRY_MODEL_UPDATE_TEST_DIR` for output and injects its
scripts only if shared-owner index wiring is absent.

Focused browser artifacts are at `/tmp/geometry-f1b/browser/`: `evidence.json`,
desktop/mobile review screenshots, committed screenshot and `updated.gcanvas`.
Logs: `/tmp/geometry-f1b-browser-final.log`, `/tmp/geometry-f1b-regression.log`,
`/tmp/geometry-f1b-space-verified.log`, `/tmp/geometry-f1b-timber-verified.log`,
`/tmp/geometry-f1b-cdp-verified.log`, `/tmp/geometry-f1b-entry-smoke.log`.

Manual `/runtime` probes, separate from the browser script, found the same fresh
focused runtime before and after acceptance:
`3f35b9abe36a66d6cbd71a52b151be2913829f10950d80bfd4c7df8f434df184`.
Manual probes of both actual owner-patch regression services reported fresh runtime
`6f9f76bd18a7fb9f40d4fd848b89ef1d4a5d49685c32df9c180be1c8797bdb11`.
Different service hashes reflect the owner wiring and browser harness copies;
they do not imply different product modules. Final probe responses are retained
at `/tmp/geometry-f1b/runtime-final.json`. All self-owned services are stopped
after validation; no user's interactive World or feedback directory is used.

## Remaining integration and limits

Shared owner must apply/adapt the small wiring patch, supply context/frame/history
guards and a synchronous complete-record callback, then register tests under
its single-writer ownership. Independent root review remains required. This
draft is neither merged nor deployed and does not close #44 or deliver its
unsupported owned/multiple-carrier cases. Changed protected timber/obstacle
roots without an explicit correspondence contract fail conservatively; their
identity is not guessed. No feature attachment, persistent identity ledger,
new axiom or fixed-version upgrade is added. Physical iOS Safari and OS file
picker acceptance were not exercised.
