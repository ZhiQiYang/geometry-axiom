# Independent acceptance verification

Scope: the work-manager tool only. All committed tests use synthetic records;
they do not read product feedback, credentials, actual task transcripts, or
private queue snapshots. Product files and product runtime tests are untouched.

## Execution record

Executed against the current tool implementation:

```sh
python3 -m unittest discover -s geometry-web/work-manager -p test_acceptance.py -v
```

Exit **0**: **46 tests passed** (latest rerun: `Ran 46 tests in 1.164s`, `OK`). This includes
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

## Seven later review regressions: red before fixes

The initial suite did not cover seven further cases reported during review.
They were reproduced before their repairs, using only valid legacy input shapes
and synthetic data. Baseline commit:
`00e348bf62f575d63b5df4f081759699a77d6d2c`.

```sh
python3 -m unittest discover -s geometry-web/work-manager -p test_review_regressions.py -v
```

Initial **red** result: exit **1**, **9 tests / 13 failures**, reproducing the
first six issues. The seventh freshness case was then added and independently
ran **red** with exit **1**, one test / one failure, before its repair.

The repaired contract is covered by **24 passing cases** (exit **0**, `Ran 24
tests in 0.133s`, `OK`):

1. Unscoped approval constraints default to completion gates and cannot release
   dependent work. Explicit action-only publication holds preserve already
   accepted historical merges without granting permission to publish.
2. Completed actions have structured receipts keyed by task, action and input
   pin. The same input stays out of `ready`; relevant head, owner, acceptance,
   constraints or dependency changes invalidate the receipt. Active executors
   with pending PRs are not offered as duplicate review work. Source refreshes
   and unrelated old-head proofs do not requeue a completed action.
3. Nested malformed CI fields are rejected before commit. Both evidence-CI and
   PR-CI paths retain the previous state hash and remain readable after reopen.
4. Aggregate `approved` claims require an explicit matching `reviewed_sha`.
   Missing pins are unknown; old-head pins are stale even when the PR's current
   head matches the task. Neither can certify current approval or completion.
5. Evidence IDs are immutable within each task. Conflicting content is rejected
   atomically within an event, across events and across batches. Identical
   duplicates remain idempotent, and different tasks may use the same ID.
6. A later old-head proof cannot replace a valid current-head acceptance result.
   It remains in history. A newer failure on the current head still supersedes
   the earlier pass and invalidates the completed action receipt. This also
   covers an entirely missing current-head proof: adding only an old-head proof
   must not change the action pin or requeue a completed verification receipt.
7. A successful repeated observation refreshes the task's verification watermark
   without adding an event or rewriting its timestamp. Partial observations do
   not refresh other tasks; failed fetches preserve the last successful
   watermark. `payload_hash` stays stable while freshness changes `state_hash`.

After the initial red run, positive review fixtures were updated to provide
`reviewed_sha`, and the legacy summary-only completion repro was migrated to the
new explicit receipt format. Distinct synthetic CI attempts now use distinct
evidence IDs. Existing assertions were not weakened.

The missing-current-proof boundary was added as a further focused regression
before its fix. `-k no_current_proof` exited **1** with one failure: acceptance
remained unknown but the input pin changed. After the pin used only applicable
current-head evidence, the full 24-case review suite exited **0**; old-head proof
history was retained and the existing completed receipt stayed effective.

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

All 70 independent automated cases pass. No remaining blocker was found in this
test scope. Private live inputs, final actual-state screenshots, commit identity,
and draft PR delivery remain the integration owner's deliverables.

## Environment evidence

- Chromium is available in the cloud environment.
- Node resolves `playwright` from the preinstalled runtime dependency tree.
- Repository `AGENTS.md` and `geometry-guide/PRODUCT-VISION.md` were read.
- The workspace `.agents` directory is empty. No local skill instructions were present there.
