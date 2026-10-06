# Independent acceptance verification

Scope: the work-manager tool only. All committed tests use synthetic records;
they do not read product feedback, credentials, actual task transcripts, or
private queue snapshots. Product files and product runtime tests are untouched.

## Execution record

Executed against the completed tool implementation:

```sh
python3 -m unittest discover -s geometry-web/work-manager -p test_acceptance.py -v
```

Exit **0**: **46 tests passed** (latest rerun: `Ran 46 tests in 1.086s`, `OK`). This includes
real subprocess CLI calls, a temporary loopback HTTP server, and a real SQLite
concurrent writer. Test clocks use relative UTC times so source freshness does
not make the CLI tests expire after a fixed calendar date.

Python compilation of the acceptance suite and `node --check` on the dashboard
JavaScript both exited **0**.

An independent Chromium/Playwright smoke run with a **mocked synthetic API** at
390 px exited **0**: the HTML attack string remained text, no image element or
script execution appeared, document width was exactly 390 px, page errors were
empty, and a subsequent HTTP 503 preserved the previously rendered rows and
state hash. This smoke run is not evidence of a real queue synchronization.
The integration owner separately verifies actual-state desktop/390 px captures.

## Findings addressed during review

- Reconciliation now opens an explicit read transaction. A concurrent import
  cannot combine old source rows with newer event rows.
- Malformed CI `steps: [{}]` previously produced a false `done` result in both
  evidence and PR-job paths. The failing regression was reproduced; the final
  suite passes with malformed/unexecuted steps unable to certify completion.
- Subsecond event times previously lost precision and could let an older
  independent source replace a newer head. The failing regression was
  reproduced; replay now preserves original timestamp precision.
- A later valid failed verification is exposed as the last verified result;
  an older passing attempt cannot hide that failure or certify completion.
- Stale server code returns 503 until restart. The test changes only the
  fingerprint function via a mock and verifies normal reads recover afterward.
- UI review identified missing PR-only references, criterion/timestamp field
  mismatches, and raw pass badges on expired evidence. The UI owner aligned
  these with the store projection and effective evidence/CI results.
- Follow-up review verified `pr.effective_review_state` distinguishes current
  head validity from the original imported review claim. The focused
  `test_new_head_exposes_old_review_as_expired` test exited **0**. An independent
  synthetic store query returned current head B, imported PR head A, raw
  `approved`, effective `stale`, evidence result `unknown`, delivery
  `verification_pending`, and next action `verify_acceptance`. The UI reads the
  derived field under “目前 head 的審查” and labels the original claim separately.

## Required checks

- Idempotent imports; conflicting IDs; older source and event versions.
- Transactional batch rejection, close/reopen persistence, checksum restoration.
- Exact-head acceptance and merge proof; changed-head stale evidence.
- Empty/no-runner CI is unexecuted; blocked is never complete.
- Stopped executors retain the delivery gap; a submitted PR remains pending review.
- File ownership conflicts, directory overlap, dependency cycles.
- Missing owners, future schedules, approval gates, failed/unknown sources.
- CLI/API/UI state hash consistency; loopback read-only API; XSS-safe rendering.
- Actual desktop and 390 px browser verification and screenshots are owned by the parent.

All 46 independent automated cases pass. No remaining blocker was found in this
test scope. Private live inputs, final actual-state screenshots, commit identity,
and draft PR delivery remain the integration owner's deliverables.

## Environment evidence

- Chromium is available in the cloud environment.
- Node resolves `playwright` from the preinstalled runtime dependency tree.
- Repository `AGENTS.md` and `geometry-guide/PRODUCT-VISION.md` were read.
- The workspace `.agents` directory is empty. No local skill instructions were present there.
