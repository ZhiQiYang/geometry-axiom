# #49 independent component validation

> Historical evidence for the standalone #141 component, at the exact source
> recorded below. It is not an acceptance receipt for the integrated release
> candidate. Current formal app/ZIP/race gates are listed in
> [INTEGRATION-GATES.md](../../../tests/INTEGRATION-GATES.md).

Validated executable source: `b9ef20818eaccd4d72339b58e3935cc5e1e03b8c`.
Base main: `6ee719d0e4ba3740e2f0b93223b323838f6a20f8`.
Final upstream recheck: main advanced to
`2437e4aa641759f727e2a79b0e4cba098016f011` by merging reviewed #138/#139/#140
evidence/handoff documents. `git diff --exit-code 6ee719d origin/main -- .
':!geometry-web/docs'` returned 0: production/core/tests/AGENTS/axioms unchanged.
This add-only branch keeps its reviewed/tested base; no unrelated evidence
files were copied, read for content or republished by this worker.
Draft: [PR #141](https://github.com/ZhiQiYang/geometry-axiom/pull/141).
The following documentation-only commit preserves all seven source/test file
hashes below. This proves the tested bytes without treating an older checkpoint
as a full-app acceptance result.

## Results

| Gate | Observed result |
| --- | --- |
| Focused Python | 105 tests, exit 0, 29.341s; 19 new real HTTP/native workbench tests + 86 existing definition/catalog/executor/request checks |
| Controller with actual HTTP/native adapter | 17 tests, exit 0, 12.227s; no skips |
| Real Chromium/Playwright UI | 91 explicit checks, exit 0; 1280×900 and 390×900; zero unexpected console warnings/errors or page exceptions |
| Six native cases | Six passed: four actual accepted, two actual rejected with exact typed diagnostics |
| Resource cleanup | Every six-case native PID reaped, private directory removed; before/after TEMP directory sets equal; held cancel/close/context retirement and host shutdown reclaim their real children |
| Formal native isolation control | Separate true native World/read/revision/dump unchanged; its existing assembly candidate still confirms after private HTTP run/cancel |
| Existing generic historical receipt | Repository-authored `rule_case_generic_immutable_receipt.json` accepted as historical-unverified; original blocked receipt unchanged; separate view stale with recordedStatus=blocked |

Exact negative observations: `DIMENSION_TYPE / D33 / {kind:parameter,id:41,
fieldId:9}` and `RULE_VERSION_IMMUTABLE / D32 / {kind:rule,id:17,version:1}`.
Negative before/after native states, revisions and dump hashes match. Typed
predicate checks remain separate from actual acceptance/rejection. Changing
candidate joint 101's side while preserving the author oracle produces an
actual accepted candidate with verification failed, never a false pass.

## Parent review findings and concrete regression coverage

- **Portable receipt schema:** all statuses, including blocked, reject unknown
  receipt/context/executor/conditions/diagnostic/assertion/observation fields,
  malformed types, excessive depth/bytes and mismatched ORIGINAL
  definitionHash/sourceHash/authorExpected. No data replacement or host/native
  mutation occurs on rejection. Legitimate edited CURRENT definitions keep old
  recorded definitions/receipts and produce stale views. An internally
  consistent fabricated PID still has historical-unverified trust.
- **Initialization ownership:** original scope and context subscription precede
  the first await. Pending controller/mount promises expose teardown. Held open
  with close, project/generation/undo/reopen retirement, late B response matching
  the new host, and load-data retirement rejects precisely and closes its real
  session. Real browser held first open/newer mount and pending-open close never
  repaint the retired panel at either viewport.
- **Data-operation serialization:** reset/import/edit/refresh/retain hold one
  lease through completion. Held reset/import excludes retain/run and atomically
  adopts its exact complete data. Held retain excludes replacements; cancellation
  invalidates the host's `lease.isCurrent()` commit gate and writes zero steps.
  Normal explicit retain is one in-memory metadata step; no-op retain adds none.
- **Local harness Host/Origin gate:** GET and POST reject arbitrary Host with
  matching forged Origin, wrong port and foreign Origin. Exact localhost or
  127.0.0.1 with the actual service port is accepted.

Additional controller/native gates cover delayed run/assessment after cancel,
case/definition change, teardown/new mount and original project/generation/
history token retirement; cancel before late run; used run IDs; finite session,
TTL and 64-ID bounds; 100 normal open/close cycles; unsupported transport/data
formats, missing capability, unknown runtime, output capacity and timeout.
Runtime/source/project/generation drift remains a separate copied view. No new
token extends an old run. No assembly invalidation function is called.

## Reproduction and raw evidence

Environment: Linux, Python 3.12.14, Node 24.19.0, installed Playwright and
headless `/usr/bin/chromium`. Browser plugin was unavailable. The sole browser
URL was the explicitly isolated `http://127.0.0.1:8879/` harness, started from
the validated source. It was stopped after verification. Only synthetic/catalog
data was used; no private PDF, user design ZIP or user feedback was read.

```sh
python3 tests/binaries.py build bridge
GEOMETRY_RULE_CASE_EVIDENCE_DIR=/tmp/rule-case-workbench-validation \
  python3 -m unittest tests.test_rule_case_workbench_http \
    tests.test_rule_case_definition tests.test_rule_case_catalog \
    tests.test_rule_case_executor tests.test_rule_case_request -v

python3 geometry-web/rule_case_workbench_standalone.py --port 8879
# In another shell, run these sequentially against that isolated adapter:
GEOMETRY_RULE_CASE_TEST_URL=http://127.0.0.1:8879 \
  node --test tests/rule-case-workbench-controller.cjs
GEOMETRY_RULE_CASE_TEST_URL=http://127.0.0.1:8879 \
  node tests/rule-case-workbench-browser.cjs
```

Registry verified bridge:
`nativeBinaryHash=77348beed95f77fb56af84d29b7329d8dc6a857b67a8a504bc40bcc97881bcf4`,
`nativeSourceHash=be5493941b0d180ea7eaf171ba9e44074534e7f6c42d05776c5243266fabb87a`.
No unverified fallback executable was used.

Raw evidence remains local TEMP, outside the PR:

- `/tmp/rule-case-workbench-b9ef208-focused.log`
- `/tmp/rule-case-workbench-b9ef208-controller.log`
- `/tmp/rule-case-workbench-b9ef208-browser.log`
- `/tmp/rule-case-workbench-validation/native.json` and `source-hashes.json`
- `/tmp/rule-case-workbench-browser/browser.json`
- `/tmp/rule-case-workbench-browser/{1280,390}-{initial,dimension-diagnostic,historical}.png`

Earlier failed attempts are preserved separately. The first new HTTP test run
had one assertion mismatch and two test errors (wrong native dump key/reason
literal and urllib broken pipe when sending an oversized body); corrected tests
then passed. A browser run made concurrently with controller against the same
serial adapter timed out waiting for a pass. Its HTTP response was not recorded,
so BUSY is a possible coordination cause, not a proven diagnosis. The final
controller and browser runs above were sequential and separately exited 0.

## Tested source SHA-256

| File | SHA-256 |
| --- | --- |
| geometry-web/rule-case-workbench.js | 991eb401ad19ffbd40d5956d7f4ff55854d4854c804c31292ff60b41bc4f52d7 |
| geometry-web/rule-case-workbench.css | 0e7460cec3737f3967e828b65c40f965e4fb3c14c666ca38588668ce299759d4 |
| geometry-web/rule_case_workbench_adapter.py | 52d77dd25b2cf87a0b4777c677430fdd9666902085a6cc57cb0bbb72046992be |
| geometry-web/rule_case_workbench_standalone.py | 80d8f21dda1a7cbc571710f30e3203fc77e81a35067f9a9ae0ff8b501698cdba |
| tests/test_rule_case_workbench_http.py | a5eae2c6cdadc80354503d858930a0a4d728d53eb63e528f150d42fa60c492bc |
| tests/rule-case-workbench-controller.cjs | 62474aafde713247652df74c4d9edb60564b360ed557e3afa2f5cefa0b2dfb81 |
| tests/rule-case-workbench-browser.cjs | 7960607a6a1685703c210544fb0d069f73421016eb572b32f7a05b114142be68 |

## Remaining shared integration

Parent independently reviews the exact draft head before the shared owner
allocates formal kind/capability/format and routes root catalog/assets/history.
Owner installs the scoped serve route and lifecycle invalidation, mounts the
component in AssemblyWorkspace, and implements the atomic original-context AND
operation-lease metadata write port. No formal canvas /14 or /15 allocation was
made here. Real root .gcanvas/ZIP save/reopen, native undo/redo integration,
formal app/browser regression registration and complete product acceptance
remain pending. These tests exercise an independent component and a clearly
labeled in-memory retain/restore port. Headless Linux evidence does not cover
Windows/SAC, actual iOS/Android, OS file chooser or real project archive saving.
