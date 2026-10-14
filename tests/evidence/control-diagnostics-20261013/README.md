# Task 5: second-tab control failure diagnostics

Base/claim: 6c69694baf406ebe6ec14d8cec071c081db314cd (origin/main plus empty claim).
Tested source: this branch's ux_refinement_test.js patch, before evidence commit; no source edits during the runs.

Only the second-tab unreachable error now includes the measurement captured in the original evaluate call: rect, disabled, hit outerHTML (at most 200 characters), file menu display/visibility/hidden and aria-expanded. It then calls the existing diagnostics() for connection/project/busy/locks, preserving diagnostic errors rather than replacing the original failure. The usable predicate, scroll, click coordinates, pressed/released events and 180ms sleep stay unchanged. Successful control calls do not request diagnostics. Missing-control evaluation remains unchanged.

Per the board's 2026-10-13 17:00 update, grid_rule_editor_test.js is unchanged until #201 enters main; this is the ux half only.

Evidence:

- diagnostic-oracle.json/log: real Chromium DOM, the extracted actual control closure; disabled button plus hidden menu. Old source lacks the requested fields (oracle exit1), patched source includes them (exit0), removed patch again exit1, restored exit0. A successful button emits the same mousePressed/mouseReleased events without invoking diagnostics. These exit fields are diagnostic assertion outcomes collected by the helper; the outer helper succeeds after verifying the full 1/0/1/0 sequence. This controlled case does not recreate the historic intermittent failure or repair it.
- native-core.json/log: original tests/run_tests.py, 139/139 pass, no fail/infrastructure, parent exit0, 5.575s. This is the core fixture runner, not the complete run_all native job.
- ux-subset.json/log: original cdp_test.js with GEOMETRY_UX_REFINEMENT_ONLY=1, P74 52 pass/0 fail/0 skipped groups, completed=true, parent exit0, 33.916s; partial mode, golden not compared.
- Both target files passed node --check; syntax.log/syntax.json capture original output and exits.
- oracle.py.txt and run.py.txt are the exact temporary diagnostic/launch helpers, not newly registered suites. No expected counts, runner registrations, assertions or deadlines changed.

Environment: Linux, Python 3.12, system Chromium; fresh source-derived core/bridge/model-base built through original tests/binaries.py into /tmp/control-diag-binaries; stack limit 16384 KiB. Isolated service 8970/profile/feedback, stopped after the run. During the run runtime_version.py --probe reported fresh:true, root /tmp/geometry-control-diagnostics, session 030d4ae867d842e39d71a11830a52776. environment.json contains tool/source/binary hashes. This is not a formal WSL receipt.

Unverified: full native aggregate, full canvas/golden and grid gate; pending grid diagnostic half; historical P74 failure root cause and recovery under the original slow-machine profile. No product, C, SSOT, plain-language guide, canonical reader, locked lines, backlog or decision queue changes. Core mutation coverage unchanged; no core mutation rerun is claimed. GEO-219: no new entrance.
